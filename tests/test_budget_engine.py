"""
Tests for budget engine service.
Verifies category budget comparison, remaining funds, utilization percentages,
status classifications (under_budget, near_limit, over_budget), and empty handling.
"""

import pytest
from backend.schemas.transaction import Transaction
from backend.services.budget_engine import evaluate_budget, generate_budget_recommendations


def test_empty_budget_handling():
    txs = [
        Transaction(date="2026-09-01", description="Groceries", amount=200.0, type="expense", category="Food"),
    ]
    summary_none = evaluate_budget(txs, budgets=None)
    assert summary_none.total_budget == 0.0
    assert summary_none.categories == []
    assert summary_none.overspent_categories == []

    summary_empty = evaluate_budget(txs, budgets={})
    assert summary_empty.total_budget == 0.0
    assert summary_empty.categories == []


def test_under_budget_category():
    # Budget 5000, Actual 2000 -> Utilization 40% (under_budget)
    txs = [
        Transaction(date="2026-09-01", description="Supermarket Groceries", amount=1200.0, type="expense", category="Food"),
        Transaction(date="2026-09-05", description="Local Market", amount=800.0, type="expense", category="Food"),
    ]
    budgets = {"Food": 5000.0}
    summary = evaluate_budget(txs, budgets=budgets)

    assert len(summary.categories) == 1
    food_status = summary.categories[0]
    assert food_status.category == "Food"
    assert food_status.budget == 5000.0
    assert food_status.actual == 2000.0
    assert food_status.remaining == 3000.0
    assert food_status.utilization_percentage == 40.0
    assert food_status.status == "under_budget"
    assert "Food" not in summary.overspent_categories


def test_near_limit_category():
    # Budget 2000, Actual 1800 -> Utilization 90% (near_limit)
    txs = [
        Transaction(date="2026-09-02", description="Uber Rides", amount=1800.0, type="expense", category="Transport"),
    ]
    budgets = {"Transport": 2000.0}
    summary = evaluate_budget(txs, budgets=budgets)

    assert len(summary.categories) == 1
    transport_status = summary.categories[0]
    assert transport_status.utilization_percentage == 90.0
    assert transport_status.remaining == 200.0
    assert transport_status.status == "near_limit"
    assert "Transport" not in summary.overspent_categories


def test_over_budget_category():
    # Budget 3000, Actual 4200 -> Utilization 140% (over_budget)
    txs = [
        Transaction(date="2026-09-10", description="Amazon Order", amount=2500.0, type="expense", category="Shopping"),
        Transaction(date="2026-09-15", description="Clothing Store", amount=1700.0, type="expense", category="Shopping"),
    ]
    budgets = {"Shopping": 3000.0}
    summary = evaluate_budget(txs, budgets=budgets)

    assert len(summary.categories) == 1
    shopping_status = summary.categories[0]
    assert shopping_status.actual == 4200.0
    assert shopping_status.remaining == -1200.0
    assert shopping_status.utilization_percentage == 140.0
    assert shopping_status.status == "over_budget"
    assert "Shopping" in summary.overspent_categories


def test_multi_category_budget_totals():
    txs = [
        Transaction(date="2026-09-01", description="Groceries", amount=2000.0, type="expense", category="Food"),
        Transaction(date="2026-09-02", description="Uber", amount=1800.0, type="expense", category="Transport"),
        Transaction(date="2026-09-03", description="Clothes", amount=4000.0, type="expense", category="Shopping"),
    ]
    budgets = {
        "Food": 4000.0,        # actual 2000 (50%, under_budget)
        "Transport": 2000.0,   # actual 1800 (90%, near_limit)
        "Shopping": 3000.0,    # actual 4000 (133.33%, over_budget)
    }
    summary = evaluate_budget(txs, budgets=budgets)

    assert summary.total_budget == 9000.0
    assert summary.total_actual == 7800.0
    assert summary.total_remaining == 1200.0
    assert summary.overall_utilization_percentage == round((7800 / 9000) * 100.0, 2)
    assert summary.overspent_categories == ["Shopping"]


def test_budget_recommendations_compatibility():
    txs = [
        Transaction(date="2026-09-01", description="Salary", amount=50000.0, type="income", category="Income"),
        Transaction(date="2026-09-02", description="Expenses", amount=20000.0, type="expense", category="Other"),
    ]
    recs = generate_budget_recommendations(txs)
    assert recs["monthly_income"] == 50000.0
    assert recs["targets"]["needs_target"] == 25000.0
    assert recs["status"] == "On Track"
