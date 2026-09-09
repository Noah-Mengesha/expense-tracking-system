from pathlib import Path
import sys

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from repository import ExpenseRepository, NotFoundError, ValidationError


@pytest.fixture()
def repo(tmp_path):
    return ExpenseRepository(tmp_path / "test.db")


def category_id(repo, name="Food"):
    return next(c["id"] for c in repo.list_categories() if c["name"] == name)


def valid_payload(repo):
    return {
        "description": "Lunch",
        "amount": 14.75,
        "expense_date": "2026-09-08",
        "category_id": category_id(repo),
        "notes": "Campus cafe",
    }


def test_default_categories_created(repo):
    names = {item["name"] for item in repo.list_categories()}
    assert {"Food", "Transportation", "Housing", "Other"}.issubset(names)


def test_create_and_get_expense(repo):
    created = repo.create_expense(valid_payload(repo))
    fetched = repo.get_expense(created["id"])
    assert fetched["description"] == "Lunch"
    assert fetched["amount"] == 14.75
    assert fetched["category"] == "Food"


def test_update_expense(repo):
    created = repo.create_expense(valid_payload(repo))
    payload = valid_payload(repo)
    payload["description"] = "Dinner"
    payload["amount"] = 22.50
    updated = repo.update_expense(created["id"], payload)
    assert updated["description"] == "Dinner"
    assert updated["amount"] == 22.5


def test_delete_expense(repo):
    created = repo.create_expense(valid_payload(repo))
    repo.delete_expense(created["id"])
    with pytest.raises(NotFoundError):
        repo.get_expense(created["id"])


def test_filters(repo):
    first = valid_payload(repo)
    repo.create_expense(first)
    second = valid_payload(repo)
    second.update({
        "description": "Train",
        "amount": 30,
        "expense_date": "2026-09-01",
        "category_id": category_id(repo, "Transportation"),
    })
    repo.create_expense(second)

    food = repo.list_expenses(category_id=category_id(repo, "Food"))
    assert len(food) == 1
    assert food[0]["description"] == "Lunch"

    recent = repo.list_expenses(start_date="2026-09-05", end_date="2026-09-10")
    assert len(recent) == 1
    assert recent[0]["description"] == "Lunch"


def test_summary(repo):
    first = valid_payload(repo)
    repo.create_expense(first)
    second = valid_payload(repo)
    second["amount"] = 5.25
    second["description"] = "Snack"
    repo.create_expense(second)

    summary = repo.summary()
    assert summary["expense_count"] == 2
    assert summary["total_spending"] == 20.0
    assert summary["average_expense"] == 10.0
    assert summary["by_category"][0]["category"] == "Food"


@pytest.mark.parametrize(
    "field,value",
    [
        ("description", ""),
        ("amount", 0),
        ("amount", -3),
        ("amount", "not-a-number"),
        ("expense_date", "09/08/2026"),
        ("category_id", 99999),
    ],
)
def test_validation_rejects_bad_input(repo, field, value):
    payload = valid_payload(repo)
    payload[field] = value
    with pytest.raises(ValidationError):
        repo.create_expense(payload)


def test_rejects_reversed_date_filter(repo):
    with pytest.raises(ValidationError):
        repo.list_expenses(start_date="2026-09-10", end_date="2026-09-01")
