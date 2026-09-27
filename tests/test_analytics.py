"""
Tests for analytics service.
Covers total income, total expenses, savings, savings rate, category spending,
category percentages, monthly trends, and essential vs non-essential breakdown.
"""

import pytest
from backend.schemas.transaction import Transaction
from backend.services.analytics import (
    calculate_total_income,
    calculate_total_expenses,
    calculate_savings,
    calculate_savings_rate,
    calculate_cash_flow,
    calculate_category_spending,
    calculate_category_percentages,
    calculate_category_breakdown,
    calculate_monthly_trends,
    calculate_essential_vs_non_essential,
    generate_basic_analysis,
)


@pytest.fixture
def sample_transactions():
    return [
        Transaction(date="2026-07-01", description="July Salary", amount=40000.0, type="income", category="Income"),
        Transaction(date="2026-07-02", description="July Rent", amount=15000.0, type="expense", category="Rent"),
        Transaction(date="2026-07-05", description="Groceries Food", amount=5000.0, type="expense", category="Food"),
        Transaction(date="2026-07-10", description="Uber Transport", amount=2000.0, type="expense", category="Transport"),
        Transaction(date="2026-07-15", description="Shopping Mall", amount=3000.0, type="expense", category="Shopping"),
        Transaction(date="2026-07-20", description="Electric Bill", amount=1500.0, type="expense", category="Bills & Utilities"),
        Transaction(date="2026-07-25", description="Mutual Fund", amount=2000.0, type="expense", category="Investment/Savings"),
        Transaction(date="2026-08-01", description="August Salary", amount=45000.0, type="income", category="Income"),
        Transaction(date="2026-08-02", description="August Rent", amount=15000.0, type="expense", category="Rent"),
        Transaction(date="2026-08-05", description="Restaurant Dining", amount=4000.0, type="expense", category="Food"),
    ]


def test_total_income(sample_transactions):
    income = calculate_total_income(sample_transactions)
    assert income == 85000.0


def test_total_expenses(sample_transactions):
    expenses = calculate_total_expenses(sample_transactions)
    assert expenses == 47500.0

    # With exclude_investments=True, excludes Investment/Savings (2000.0)
    expenses_no_inv = calculate_total_expenses(sample_transactions, exclude_investments=True)
    assert expenses_no_inv == 45500.0


def test_savings_and_savings_rate(sample_transactions):
    savings = calculate_savings(sample_transactions)
    assert savings == 37500.0

    savings_rate = calculate_savings_rate(sample_transactions)
    assert round(savings_rate, 2) == 44.12


def test_cash_flow_summary(sample_transactions):
    summary = calculate_cash_flow(sample_transactions)
    assert summary.total_income == 85000.0
    assert summary.total_expenses == 47500.0
    assert summary.net_savings == 37500.0
    assert round(summary.savings_rate, 2) == 44.12


def test_category_spending_clean_structure(sample_transactions):
    spending = calculate_category_spending(sample_transactions)

    assert isinstance(spending, dict)
    assert spending["Rent"] == 30000.0
    assert spending["Food"] == 9000.0
    assert spending["Shopping"] == 3000.0
    assert spending["Transport"] == 2000.0
    assert spending["Bills & Utilities"] == 1500.0
    assert spending["Investment/Savings"] == 2000.0
    # Income must not be included in expense spending
    assert "Income" not in spending


def test_category_percentages(sample_transactions):
    percentages = calculate_category_percentages(sample_transactions)

    assert isinstance(percentages, dict)
    assert "Rent" in percentages
    total_pct = sum(percentages.values())
    assert 99.9 <= total_pct <= 100.1


def test_monthly_trends_chronological(sample_transactions):
    trends = calculate_monthly_trends(sample_transactions)

    assert len(trends) == 2
    # Verify chronological order
    assert trends[0].month == "2026-07"
    assert trends[0].income == 40000.0
    assert trends[0].expenses == 28500.0
    assert trends[0].savings == 11500.0

    assert trends[1].month == "2026-08"
    assert trends[1].income == 45000.0
    assert trends[1].expenses == 19000.0
    assert trends[1].savings == 26000.0


def test_essential_vs_non_essential(sample_transactions):
    evn = calculate_essential_vs_non_essential(sample_transactions)

    # Essential: Rent (30000) + Transport (2000) + Bills & Utilities (1500) = 33500
    # Non-essential: Food (9000) + Shopping (3000) = 12000
    # Investment/Savings (2000) is excluded
    assert evn.essential_spending == 33500.0
    assert evn.non_essential_spending == 12000.0
    assert "Rent" in evn.essential_categories
    assert "Food" in evn.non_essential_categories
    assert "Investment/Savings" not in evn.essential_categories
    assert "Investment/Savings" not in evn.non_essential_categories
    assert round(evn.essential_percentage + evn.non_essential_percentage, 1) == 100.0


def test_generate_basic_analysis_aggregation(sample_transactions):
    analysis = generate_basic_analysis(sample_transactions)

    assert analysis.total_transactions == 10
    assert analysis.summary.total_income == 85000.0
    assert analysis.summary.total_expenses == 47500.0
    assert len(analysis.monthly_trends) == 2
    assert analysis.essential_vs_non_essential.essential_spending == 33500.0
    assert analysis.health_score.score > 0
    assert analysis.date_range.start_date == "2026-07-01"
    assert analysis.date_range.end_date == "2026-08-05"
