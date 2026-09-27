"""
Tests for transaction anomaly detector service.
Verifies that normal transactions are not incorrectly flagged, unusually large transactions are detected,
severity levels are correctly determined, and empty data is handled gracefully.
"""

import pytest
from backend.schemas.transaction import Transaction
from backend.services.anomaly_detector import detect_anomalies


def test_empty_transactions_returns_empty_anomalies():
    assert detect_anomalies([]) == []


def test_normal_transactions_not_incorrectly_flagged():
    # Normal consistent food & transport transactions
    txs = [
        Transaction(date="2026-09-01", description="Trader Joes Groceries", amount=120.0, type="expense", category="Food"),
        Transaction(date="2026-09-03", description="Starbucks Coffee", amount=15.0, type="expense", category="Food"),
        Transaction(date="2026-09-05", description="Local Market", amount=110.0, type="expense", category="Food"),
        Transaction(date="2026-09-08", description="Whole Foods", amount=130.0, type="expense", category="Food"),
        Transaction(date="2026-09-02", description="Uber Ride", amount=25.0, type="expense", category="Transport"),
        Transaction(date="2026-09-04", description="Shell Gas", amount=45.0, type="expense", category="Transport"),
        Transaction(date="2026-09-01", description="Monthly Rent", amount=15000.0, type="expense", category="Rent"),
    ]
    anomalies = detect_anomalies(txs)
    # None of these routine charges or expected rent should be flagged
    assert len(anomalies) == 0


def test_unusually_large_transaction_detected():
    # Typical food is ~100-150, but one food charge is 1500 (10x typical)
    txs = [
        Transaction(date="2026-09-01", description="Trader Joes Groceries", amount=120.0, type="expense", category="Food"),
        Transaction(date="2026-09-05", description="Local Supermarket", amount=110.0, type="expense", category="Food"),
        Transaction(date="2026-09-10", description="Whole Foods Market", amount=130.0, type="expense", category="Food"),
        Transaction(date="2026-09-15", description="Luxury Feast Banquet", amount=1500.0, type="expense", category="Food"),
    ]
    anomalies = detect_anomalies(txs)

    assert len(anomalies) == 1
    detected = anomalies[0]
    assert detected.description == "Luxury Feast Banquet"
    assert detected.amount == 1500.0
    assert detected.category == "Food"
    assert "higher than typical" in detected.reason.lower()


def test_anomaly_severity_levels():
    # Baseline food is ~100
    # Low anomaly: 250 (2.5x)
    # Medium anomaly: 350 (3.5x)
    # High anomaly: 650 (6.5x)
    txs = [
        Transaction(date="2026-09-01", description="Groceries 1", amount=100.0, type="expense", category="Food"),
        Transaction(date="2026-09-02", description="Groceries 2", amount=105.0, type="expense", category="Food"),
        Transaction(date="2026-09-03", description="Groceries 3", amount=95.0, type="expense", category="Food"),
        Transaction(date="2026-09-04", description="Groceries 4", amount=100.0, type="expense", category="Food"),
        Transaction(date="2026-09-05", description="Groceries 5", amount=102.0, type="expense", category="Food"),
        Transaction(date="2026-09-06", description="Groceries 6", amount=98.0, type="expense", category="Food"),
        Transaction(date="2026-09-10", description="Dinner Out", amount=250.0, type="expense", category="Food"),
        Transaction(date="2026-09-15", description="Party Catering", amount=350.0, type="expense", category="Food"),
        Transaction(date="2026-09-20", description="VIP Banquet", amount=650.0, type="expense", category="Food"),
    ]
    anomalies = detect_anomalies(txs)
    severity_map = {a.description: a.severity for a in anomalies}

    assert severity_map.get("VIP Banquet") == "high"
    assert severity_map.get("Party Catering") == "medium"
    assert severity_map.get("Dinner Out") == "low"


def test_income_not_flagged_as_anomaly():
    # Large salary should not be flagged as an expense anomaly
    txs = [
        Transaction(date="2026-09-01", description="Huge Bonus", amount=100000.0, type="income", category="Income"),
        Transaction(date="2026-09-02", description="Regular Salary", amount=45000.0, type="income", category="Income"),
        Transaction(date="2026-09-05", description="Coffee", amount=5.0, type="expense", category="Food"),
    ]
    anomalies = detect_anomalies(txs)
    assert len(anomalies) == 0
