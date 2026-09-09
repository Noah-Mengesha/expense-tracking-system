from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from repository import ExpenseRepository, NotFoundError, ValidationError


def create_app(db_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    repository = ExpenseRepository(db_path or os.getenv("EXPENSE_DB_PATH") or None) if (db_path or os.getenv("EXPENSE_DB_PATH")) else ExpenseRepository()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/categories")
    def categories():
        return jsonify(repository.list_categories())

    @app.get("/api/expenses")
    def list_expenses():
        category_id = request.args.get("category_id", type=int)
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        return jsonify(repository.list_expenses(category_id, start_date, end_date))

    @app.post("/api/expenses")
    def create_expense():
        payload = request.get_json(silent=True) or {}
        expense = repository.create_expense(payload)
        return jsonify(expense), 201

    @app.get("/api/expenses/<int:expense_id>")
    def get_expense(expense_id: int):
        return jsonify(repository.get_expense(expense_id))

    @app.put("/api/expenses/<int:expense_id>")
    def update_expense(expense_id: int):
        payload = request.get_json(silent=True) or {}
        return jsonify(repository.update_expense(expense_id, payload))

    @app.delete("/api/expenses/<int:expense_id>")
    def delete_expense(expense_id: int):
        repository.delete_expense(expense_id)
        return "", 204

    @app.get("/api/summary")
    def summary():
        return jsonify(repository.summary())

    @app.errorhandler(ValidationError)
    def handle_validation(error: ValidationError):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(error: NotFoundError):
        return jsonify({"error": str(error)}), 404

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
