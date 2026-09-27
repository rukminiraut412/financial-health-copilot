"""
Tests for subscription detector service.
Verifies detection of recurring monthly subscriptions, exclusion of one-time transactions,
validation of recurring information fields, and handling of empty datasets.
"""

import pytest
from backend.schemas.transaction import Transaction
from backend.services.subscription_detector import detect_subscriptions


def test_empty_transactions_returns_empty_subscriptions():
    assert detect_subscriptions([]) == []


def test_recurring_monthly_transactions_detected():
    # Multi-month recurring charges: Internet and Gym
    txs = [
        Transaction(date="2026-07-10", description="City Broadband Internet", amount=60.0, type="expense", category="Bills & Utilities"),
        Transaction(date="2026-08-10", description="City Broadband Internet", amount=60.0, type="expense", category="Bills & Utilities"),
        Transaction(date="2026-09-10", description="City Broadband Internet", amount=60.0, type="expense", category="Bills & Utilities"),
        Transaction(date="2026-07-15", description="Gold Gym Fitness", amount=45.0, type="expense", category="Bills & Utilities"),
        Transaction(date="2026-08-15", description="Gold Gym Fitness", amount=45.0, type="expense", category="Bills & Utilities"),
    ]
    subs = detect_subscriptions(txs)

    assert len(subs) == 2
    merchant_names = [s.description for s in subs]
    assert any("Broadband" in name or "Internet" in name for name in merchant_names)
    assert any("Gym" in name or "Fitness" in name for name in merchant_names)

    # Check recurring information fields
    internet_sub = next(s for s in subs if "Broadband" in s.description or "Internet" in s.description)
    assert internet_sub.amount == 60.0
    assert internet_sub.frequency == "Monthly"
    assert internet_sub.occurrences == 3
    assert internet_sub.estimated_monthly_cost == 60.0


def test_known_digital_subscription_keyword_detected():
    # Common subscriptions like Netflix, Spotify
    txs = [
        Transaction(date="2026-09-08", description="Netflix Monthly Subscription", amount=15.99, type="expense", category="Entertainment"),
        Transaction(date="2026-09-12", description="Spotify Premium", amount=10.99, type="expense", category="Entertainment"),
    ]
    subs = detect_subscriptions(txs)

    assert len(subs) == 2
    sub_names = [s.description.lower() for s in subs]
    assert any("netflix" in name for name in sub_names)
    assert any("spotify" in name for name in sub_names)


def test_one_time_transaction_not_treated_as_subscription():
    # Variable, single one-time transactions should NOT be flagged as subscriptions
    txs = [
        Transaction(date="2026-09-02", description="Italian Bistro Dinner", amount=68.0, type="expense", category="Food"),
        Transaction(date="2026-09-19", description="Nike Running Shoes Store", amount=110.0, type="expense", category="Shopping"),
        Transaction(date="2026-09-21", description="Delta Flight Ticket", amount=350.0, type="expense", category="Transport"),
        Transaction(date="2026-09-24", description="Zara Apparel Store", amount=89.5, type="expense", category="Shopping"),
    ]
    subs = detect_subscriptions(txs)
    # None of these should be recognized as subscriptions
    assert len(subs) == 0


def test_rent_not_flagged_as_subscription():
    # Rent is a major fixed expense, not a digital subscription/membership
    txs = [
        Transaction(date="2026-08-01", description="Apartment Monthly Rent", amount=15000.0, type="expense", category="Rent"),
        Transaction(date="2026-09-01", description="Apartment Monthly Rent", amount=15000.0, type="expense", category="Rent"),
    ]
    subs = detect_subscriptions(txs)
    assert len(subs) == 0
