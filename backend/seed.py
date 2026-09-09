from datetime import date, timedelta

from repository import ExpenseRepository


def main() -> None:
    repo = ExpenseRepository()
    if repo.list_expenses():
        print("Database already contains expenses; seed skipped.")
        return

    categories = {item["name"]: item["id"] for item in repo.list_categories()}
    today = date.today()
    samples = [
        {"description": "Groceries", "amount": 64.25, "expense_date": str(today), "category_id": categories["Food"], "notes": "Weekly groceries"},
        {"description": "Bus pass", "amount": 28.00, "expense_date": str(today - timedelta(days=1)), "category_id": categories["Transportation"], "notes": ""},
        {"description": "Streaming service", "amount": 12.99, "expense_date": str(today - timedelta(days=3)), "category_id": categories["Entertainment"], "notes": "Monthly subscription"},
    ]
    for sample in samples:
        repo.create_expense(sample)
    print("Added 3 sample expenses.")


if __name__ == "__main__":
    main()
