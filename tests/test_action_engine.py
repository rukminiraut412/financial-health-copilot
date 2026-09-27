"""
Tests for Action Engine service.
Verifies recommendation generation based on high category spending, budget overruns,
subscriptions, anomalies, low savings rate, non-essential spending, deduplication,
action capping at 5, and schema integrity.
"""

import pytest
from backend.schemas.analysis import (
    ActionItem,
    AnomalyItem,
    BudgetSummary,
    CashFlowSummary,
    CategoryBudgetStatus,
    EssentialVsNonEssential,
    HealthScoreResponse,
    SubscriptionItem,
)
from backend.schemas.transaction import Transaction
from backend.services.action_engine import generate_actions, generate_action_items


def test_empty_analysis_produces_safe_output():
    # Empty inputs should produce empty action list without failing
    actions = generate_actions(summary=None)
    assert actions == []

    zero_summary = CashFlowSummary(
        total_income=0.0,
        total_expenses=0.0,
        net_savings=0.0,
        savings_rate=0.0,
    )
    actions_zero = generate_actions(summary=zero_summary)
    assert actions_zero == []


def test_high_category_spending_generates_action():
    summary = CashFlowSummary(total_income=50000.0, total_expenses=25000.0, net_savings=25000.0, savings_rate=50.0)
    category_spending = {"Food": 8000.0, "Rent": 15000.0, "Transport": 2000.0}
    category_percentages = {"Food": 32.0, "Rent": 60.0, "Transport": 8.0}

    actions = generate_actions(
        summary=summary,
        category_spending=category_spending,
        category_percentages=category_percentages,
    )

    food_actions = [a for a in actions if a.action_type == "reduce_category_spending" and a.category == "Food"]
    assert len(food_actions) == 1
    action = food_actions[0]
    assert "Food" in action.title
    assert action.estimated_monthly_impact is not None
    assert action.estimated_monthly_impact > 0
    assert "Food is one of your largest" in action.reason


def test_over_budget_category_generates_action():
    summary = CashFlowSummary(total_income=50000.0, total_expenses=25000.0, net_savings=25000.0, savings_rate=50.0)
    budget_summary = BudgetSummary(
        categories=[
            CategoryBudgetStatus(
                category="Shopping",
                budget=2000.0,
                actual=3500.0,
                remaining=-1500.0,
                utilization_percentage=175.0,
                status="over_budget",
            )
        ],
        total_budget=2000.0,
        total_actual=3500.0,
        total_remaining=-1500.0,
        overall_utilization_percentage=175.0,
        overspent_categories=["Shopping"],
    )

    actions = generate_actions(summary=summary, budget_summary=budget_summary)
    budget_actions = [a for a in actions if a.action_type == "set_or_adjust_budget" and a.category == "Shopping"]
    assert len(budget_actions) == 1
    action = budget_actions[0]
    assert "Shopping" in action.title
    assert action.priority == "high"  # utilization >= 120%
    assert action.estimated_monthly_impact == 1500.0


def test_subscription_generates_action():
    summary = CashFlowSummary(total_income=50000.0, total_expenses=20000.0, net_savings=30000.0, savings_rate=60.0)
    subscriptions = [
        SubscriptionItem(
            description="Netflix Premium",
            category="Entertainment",
            amount=19.99,
            frequency="Monthly",
            occurrences=3,
            estimated_monthly_cost=19.99,
        ),
        SubscriptionItem(
            description="Gym Fitness Club",
            category="Bills & Utilities",
            amount=50.00,
            frequency="Monthly",
            occurrences=2,
            estimated_monthly_cost=50.00,
        ),
    ]

    actions = generate_actions(summary=summary, subscriptions=subscriptions)
    sub_actions = [a for a in actions if a.action_type == "review_subscription"]
    assert len(sub_actions) == 1
    action = sub_actions[0]
    assert "recurring subscriptions" in action.title.lower()
    assert action.estimated_monthly_impact is not None
    assert action.estimated_monthly_impact > 0


def test_anomaly_generates_action():
    summary = CashFlowSummary(total_income=50000.0, total_expenses=20000.0, net_savings=30000.0, savings_rate=60.0)
    anomalies = [
        AnomalyItem(
            date="2026-09-15",
            description="VIP Luxury Banquet",
            amount=2500.0,
            category="Food",
            reason="Amount is 8.5x higher than typical Food spending",
            severity="high",
        )
    ]

    actions = generate_actions(summary=summary, anomalies=anomalies)
    anomaly_actions = [a for a in actions if a.action_type == "review_anomaly"]
    assert len(anomaly_actions) == 1
    action = anomaly_actions[0]
    assert "VIP Luxury Banquet" in action.title
    assert action.priority == "high"
    # Anomaly impact should be conservative (None)
    assert action.estimated_monthly_impact is None


def test_low_savings_rate_generates_action():
    # Savings rate 8% (below 15% threshold)
    summary = CashFlowSummary(total_income=40000.0, total_expenses=36800.0, net_savings=3200.0, savings_rate=8.0)

    actions = generate_actions(summary=summary)
    savings_actions = [a for a in actions if a.action_type == "increase_savings"]
    assert len(savings_actions) == 1
    action = savings_actions[0]
    assert "savings rate" in action.title.lower()
    assert action.estimated_monthly_impact is not None
    assert action.estimated_monthly_impact > 0


def test_deficit_spending_generates_high_priority_action():
    # Expenses exceed income
    summary = CashFlowSummary(total_income=30000.0, total_expenses=35000.0, net_savings=-5000.0, savings_rate=0.0)

    actions = generate_actions(summary=summary)
    savings_actions = [a for a in actions if a.action_type == "increase_savings"]
    assert len(savings_actions) == 1
    action = savings_actions[0]
    assert "deficit" in action.title.lower()
    assert action.priority == "high"
    assert action.estimated_monthly_impact == 5000.0


def test_non_essential_spending_generates_action():
    summary = CashFlowSummary(total_income=50000.0, total_expenses=30000.0, net_savings=20000.0, savings_rate=40.0)
    evn = EssentialVsNonEssential(
        essential_spending=12000.0,
        non_essential_spending=18000.0,
        essential_percentage=40.0,
        non_essential_percentage=60.0,
    )

    actions = generate_actions(summary=summary, essential_vs_non_essential=evn)
    discretionary_actions = [a for a in actions if a.action_type == "reduce_non_essential_spending"]
    assert len(discretionary_actions) == 1
    action = discretionary_actions[0]
    assert "discretionary" in action.title.lower() or "non-essential" in action.title.lower()
    assert action.priority == "high"  # > 50% non-essential


def test_maximum_five_actions_returned_and_no_duplicates():
    summary = CashFlowSummary(total_income=30000.0, total_expenses=35000.0, net_savings=-5000.0, savings_rate=0.0)
    category_spending = {"Food": 8000.0, "Shopping": 6000.0, "Entertainment": 4000.0}
    category_percentages = {"Food": 22.8, "Shopping": 17.1, "Entertainment": 11.4}
    evn = EssentialVsNonEssential(
        essential_spending=15000.0,
        non_essential_spending=20000.0,
        essential_percentage=42.8,
        non_essential_percentage=57.2,
    )
    anomalies = [
        AnomalyItem(date="2026-09-01", description="Spike", amount=3000.0, category="Shopping", reason="Outlier", severity="high"),
    ]
    subscriptions = [
        SubscriptionItem(description="Club", category="Bills & Utilities", amount=100.0, occurrences=2, estimated_monthly_cost=100.0),
    ]
    budget_summary = BudgetSummary(
        categories=[
            CategoryBudgetStatus(category="Food", budget=4000.0, actual=8000.0, remaining=-4000.0, utilization_percentage=200.0, status="over_budget"),
        ],
        total_budget=4000.0,
        total_actual=8000.0,
        total_remaining=-4000.0,
        overall_utilization_percentage=200.0,
        overspent_categories=["Food"],
    )

    actions = generate_actions(
        summary=summary,
        category_spending=category_spending,
        category_percentages=category_percentages,
        essential_vs_non_essential=evn,
        anomalies=anomalies,
        subscriptions=subscriptions,
        budget_summary=budget_summary,
    )

    # Must return at most 5 actions
    assert len(actions) <= 5
    assert len(actions) >= 3

    # Must contain no duplicates by (action_type, category)
    keys = [(a.action_type, a.category) for a in actions]
    assert len(keys) == len(set(keys))


def test_action_schema_fields_present_and_non_negative_impact():
    summary = CashFlowSummary(total_income=45000.0, total_expenses=20000.0, net_savings=25000.0, savings_rate=55.5)
    category_spending = {"Food": 6000.0}
    category_percentages = {"Food": 30.0}

    actions = generate_actions(
        summary=summary,
        category_spending=category_spending,
        category_percentages=category_percentages,
    )

    for action in actions:
        assert isinstance(action.title, str) and len(action.title) > 0
        assert isinstance(action.description, str) and len(action.description) > 0
        assert isinstance(action.action_type, str) and len(action.action_type) > 0
        assert action.priority in ["high", "medium", "low"]
        assert isinstance(action.reason, str) and len(action.reason) > 0
        if action.estimated_monthly_impact is not None:
            assert action.estimated_monthly_impact >= 0.0


def test_generate_action_items_from_transactions_helper():
    txs = [
        Transaction(date="2026-09-01", description="Salary", amount=45000.0, type="income", category="Income"),
        Transaction(date="2026-09-02", description="Rent", amount=15000.0, type="expense", category="Rent"),
        Transaction(date="2026-09-05", description="Groceries", amount=3500.0, type="expense", category="Food"),
    ]
    actions = generate_action_items(txs)
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, ActionItem) for a in actions)
