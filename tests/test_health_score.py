"""
Tests for Financial Health Score service.
Verifies score range (0-100), response structure, and currently implemented scoring logic.
"""

import pytest
from backend.schemas.transaction import Transaction
from backend.services.health_score import calculate_health_score


def test_health_score_range_and_structure():
    txs = [
        Transaction(date="2026-09-01", description="Monthly Salary", amount=50000.0, type="income", category="Income"),
        Transaction(date="2026-09-02", description="Apartment Rent", amount=15000.0, type="expense", category="Rent"),
        Transaction(date="2026-09-03", description="Groceries Food", amount=5000.0, type="expense", category="Food"),
        Transaction(date="2026-09-04", description="Utilities Bill", amount=2000.0, type="expense", category="Bills & Utilities"),
    ]
    result = calculate_health_score(txs)

    # 1. Score range check
    assert 0 <= result.score <= 100
    assert isinstance(result.score, int)

    # 2. Response structure check
    assert result.grade in ["A", "B", "C", "D", "F"]
    assert result.status in ["Excellent", "Good", "Fair", "Needs Attention", "Critical"]

    # Component breakdown
    assert result.breakdown is not None
    assert 0 <= result.breakdown.savings_score <= 40.0
    assert 0 <= result.breakdown.essential_spending_score <= 35.0
    assert 0 <= result.breakdown.living_within_means_score <= 25.0

    # Metrics
    assert result.metrics is not None
    assert result.metrics.savings_rate >= 0.0
    assert result.metrics.essential_ratio >= 0.0
    assert result.metrics.expense_to_income_ratio >= 0.0

    # Insights
    assert isinstance(result.insights, list)
    assert len(result.insights) > 0


def test_health_score_high_saver_profile():
    # 50k income, 15k expenses -> 70% savings rate, living within means
    txs = [
        Transaction(date="2026-09-01", description="Salary", amount=50000.0, type="income", category="Income"),
        Transaction(date="2026-09-02", description="Rent", amount=10000.0, type="expense", category="Rent"),
        Transaction(date="2026-09-03", description="Food", amount=5000.0, type="expense", category="Food"),
    ]
    result = calculate_health_score(txs)

    assert result.score >= 80
    assert result.grade in ["A", "B"]
    assert result.status in ["Excellent", "Good"]
    assert any("savings rate" in insight.lower() for insight in result.insights)


def test_health_score_deficit_profile():
    # 10k income, 25k expenses -> negative cash flow
    txs = [
        Transaction(date="2026-09-01", description="Salary", amount=10000.0, type="income", category="Income"),
        Transaction(date="2026-09-02", description="Rent", amount=12000.0, type="expense", category="Rent"),
        Transaction(date="2026-09-05", description="Shopping Spree", amount=13000.0, type="expense", category="Shopping"),
    ]
    result = calculate_health_score(txs)

    assert result.score <= 50
    assert result.grade in ["D", "F"]
    assert result.status in ["Needs Attention", "Critical"]
    assert any("deficit" in insight.lower() or "exceed" in insight.lower() for insight in result.insights)


def test_health_score_empty_transactions():
    result = calculate_health_score([])

    assert result.score == 50
    assert result.grade == "N/A"
    assert result.status == "Insufficient Data"
    assert len(result.insights) > 0
