from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from database import DEFAULT_DB_PATH, connect, initialize_database


class ValidationError(ValueError):
    """Raised when user-supplied expense data is invalid."""


class NotFoundError(LookupError):
    """Raised when a requested record does not exist."""


def _validate_iso_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise ValidationError("expense_date must use YYYY-MM-DD format") from None


def _validate_amount(value: Any) -> float:
    try:
        amount = round(float(value), 2)
    except (TypeError, ValueError):
        raise ValidationError("amount must be a number") from None
    if amount <= 0:
        raise ValidationError("amount must be greater than 0")
    if amount > 1_000_000_000:
        raise ValidationError("amount is too large")
    return amount


def _clean_text(value: Any, field: str, max_length: int, required: bool = True) -> str:
    text = "" if value is None else str(value).strip()
    if required and not text:
        raise ValidationError(f"{field} is required")
    if len(text) > max_length:
        raise ValidationError(f"{field} must be {max_length} characters or fewer")
    return text


class ExpenseRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        initialize_database(self.db_path)

    def list_categories(self) -> list[dict[str, Any]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT id, name FROM categories ORDER BY name"
            ).fetchall()
        return [dict(row) for row in rows]

    def _category_exists(self, category_id: int) -> bool:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM categories WHERE id = ?", (category_id,)
            ).fetchone()
        return row is not None

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            category_id = int(data.get("category_id"))
        except (TypeError, ValueError):
            raise ValidationError("category_id must be a valid category") from None
        if not self._category_exists(category_id):
            raise ValidationError("category_id must reference an existing category")

        return {
            "description": _clean_text(data.get("description"), "description", 120),
            "amount": _validate_amount(data.get("amount")),
            "expense_date": _validate_iso_date(data.get("expense_date")),
            "category_id": category_id,
            "notes": _clean_text(data.get("notes", ""), "notes", 500, required=False),
        }

    def create_expense(self, data: dict[str, Any]) -> dict[str, Any]:
        payload = self._normalize_payload(data)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO expenses(description, amount, expense_date, category_id, notes)
                VALUES (:description, :amount, :expense_date, :category_id, :notes)
                """,
                payload,
            )
            expense_id = int(cursor.lastrowid)
        return self.get_expense(expense_id)

    def get_expense(self, expense_id: int) -> dict[str, Any]:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT e.id, e.description, e.amount, e.expense_date, e.category_id,
                       c.name AS category, e.notes, e.created_at, e.updated_at
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.id = ?
                """,
                (expense_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("expense not found")
        return dict(row)

    def list_expenses(
        self,
        category_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if category_id is not None:
            clauses.append("e.category_id = ?")
            params.append(int(category_id))
        if start_date:
            clauses.append("e.expense_date >= ?")
            params.append(_validate_iso_date(start_date))
        if end_date:
            clauses.append("e.expense_date <= ?")
            params.append(_validate_iso_date(end_date))
        if start_date and end_date and date.fromisoformat(start_date) > date.fromisoformat(end_date):
            raise ValidationError("start_date cannot be after end_date")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT e.id, e.description, e.amount, e.expense_date, e.category_id,
                   c.name AS category, e.notes, e.created_at, e.updated_at
            FROM expenses e
            JOIN categories c ON c.id = e.category_id
            {where}
            ORDER BY e.expense_date DESC, e.id DESC
        """
        with connect(self.db_path) as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def update_expense(self, expense_id: int, data: dict[str, Any]) -> dict[str, Any]:
        self.get_expense(expense_id)
        payload = self._normalize_payload(data)
        payload["expense_id"] = expense_id
        payload["updated_at"] = datetime.now(UTC).replace(microsecond=0).isoformat(sep=" ")
        with connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE expenses
                SET description = :description,
                    amount = :amount,
                    expense_date = :expense_date,
                    category_id = :category_id,
                    notes = :notes,
                    updated_at = :updated_at
                WHERE id = :expense_id
                """,
                payload,
            )
        return self.get_expense(expense_id)

    def delete_expense(self, expense_id: int) -> None:
        with connect(self.db_path) as connection:
            cursor = connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            if cursor.rowcount == 0:
                raise NotFoundError("expense not found")

    def summary(self) -> dict[str, Any]:
        with connect(self.db_path) as connection:
            totals = connection.execute(
                """
                SELECT COUNT(*) AS expense_count,
                       COALESCE(SUM(amount), 0) AS total_spending,
                       COALESCE(AVG(amount), 0) AS average_expense
                FROM expenses
                """
            ).fetchone()
            by_category = connection.execute(
                """
                SELECT c.name AS category, ROUND(SUM(e.amount), 2) AS total
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                GROUP BY c.id, c.name
                ORDER BY total DESC, c.name
                """
            ).fetchall()

        return {
            "expense_count": int(totals["expense_count"]),
            "total_spending": round(float(totals["total_spending"]), 2),
            "average_expense": round(float(totals["average_expense"]), 2),
            "by_category": [dict(row) for row in by_category],
        }
