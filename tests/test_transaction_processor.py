"""
Tests for transaction processor service.
Covers CSV ingestion, validation, row cleaning, date/amount handling, and financial metrics derivation.
"""

import pytest
from backend.services.transaction_processor import (
    parse_csv_file,
    transactions_to_dataframe,
    dataframe_to_transactions,
)
from backend.services.analytics import (
    calculate_total_income,
    calculate_total_expenses,
    calculate_savings,
    calculate_savings_rate,
)
from backend.schemas.transaction import Transaction, TransactionType


def test_parse_valid_csv():
    csv_data = (
        "date,description,amount,type\n"
        "2026-09-01,Salary,45000,income\n"
        "2026-09-02,Apartment Rent,15000,expense\n"
        "2026-09-03,Grocery Store,1200,expense\n"
    )
    transactions, errors = parse_csv_file(csv_data)

    assert len(errors) == 0
    assert len(transactions) == 3
    assert transactions[0].amount == 45000.0
    assert transactions[0].type == TransactionType.INCOME.value
    assert transactions[1].amount == 15000.0
    assert transactions[1].type == TransactionType.EXPENSE.value
    assert transactions[2].amount == 1200.0


def test_income_and_expense_calculation_from_processed_csv():
    csv_data = (
        "date,description,amount,type\n"
        "2026-09-01,Monthly Salary,50000,income\n"
        "2026-09-05,Freelance Work,10000,income\n"
        "2026-09-02,Rent,20000,expense\n"
        "2026-09-10,Groceries,5000,expense\n"
    )
    transactions, errors = parse_csv_file(csv_data)
    assert len(errors) == 0

    income = calculate_total_income(transactions)
    assert income == 60000.0

    expenses = calculate_total_expenses(transactions)
    assert expenses == 25000.0


def test_savings_and_savings_rate_from_processed_csv():
    csv_data = (
        "date,description,amount,type\n"
        "2026-09-01,Salary,50000,income\n"
        "2026-09-02,Living Expenses,30000,expense\n"
    )
    transactions, errors = parse_csv_file(csv_data)
    assert len(errors) == 0

    savings = calculate_savings(transactions)
    assert savings == 20000.0

    savings_rate = calculate_savings_rate(transactions)
    assert savings_rate == 40.0


def test_invalid_or_missing_required_columns():
    # Missing 'amount' and 'type'
    csv_missing_cols = (
        "date,description\n"
        "2026-09-01,Salary\n"
    )
    transactions, errors = parse_csv_file(csv_missing_cols)
    assert len(transactions) == 0
    assert len(errors) > 0
    assert any("Missing required columns" in err for err in errors)


def test_invalid_date_handling():
    csv_invalid_date = (
        "date,description,amount,type\n"
        "2026-09-01,Valid Transaction,1000,income\n"
        "not-a-date,Broken Date Transaction,500,expense\n"
    )
    transactions, errors = parse_csv_file(csv_invalid_date)

    # Valid transaction is parsed, invalid row is recorded as an error
    assert len(transactions) == 1
    assert transactions[0].description == "Valid Transaction"
    assert len(errors) == 1
    assert "Invalid or missing date" in errors[0]


def test_invalid_amount_handling():
    csv_invalid_amount = (
        "date,description,amount,type\n"
        "2026-09-01,Valid Transaction,1000,income\n"
        "2026-09-02,Broken Amount,not_a_number,expense\n"
    )
    transactions, errors = parse_csv_file(csv_invalid_amount)

    assert len(transactions) == 1
    assert len(errors) == 1
    assert "Invalid amount" in errors[0]


def test_empty_csv_handling():
    transactions, errors = parse_csv_file("")
    assert len(transactions) == 0
    assert len(errors) > 0
    assert "empty" in errors[0].lower()


def test_dataframe_conversion_roundtrip():
    txs = [
        Transaction(id="txn_1", date="2026-09-01", description="Salary", amount=4000.0, type="income", category="Income"),
        Transaction(id="txn_2", date="2026-09-02", description="Rent", amount=1200.0, type="expense", category="Rent"),
    ]
    df = transactions_to_dataframe(txs)
    assert len(df) == 2
    assert "amount" in df.columns

    restored_txs = dataframe_to_transactions(df)
    assert len(restored_txs) == 2
    assert restored_txs[0].amount == 4000.0
    assert restored_txs[1].description == "Rent"
