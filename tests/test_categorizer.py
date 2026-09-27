"""
Tests for categorizer service and standard category mapping.
Covers Food, Shopping, Transport, Entertainment, Bills & Utilities, Education,
Healthcare, Rent, Investment/Savings, Other, and fallback handling.
"""

import pytest
from backend.services.categorizer import (
    categorize_transaction,
    get_all_categories,
    get_category_rules,
)
from backend.services.analytics import map_category_to_standard


def test_categorize_food():
    cat1 = categorize_transaction("Trader Joes Groceries", "expense")
    assert map_category_to_standard(cat1) == "Food"

    cat2 = categorize_transaction("Starbucks Morning Coffee", "expense")
    assert map_category_to_standard(cat2) == "Food"

    cat3 = categorize_transaction("McDonalds Lunch Meal", "expense")
    assert map_category_to_standard(cat3) == "Food"


def test_categorize_shopping():
    cat1 = categorize_transaction("Amazon Online Shopping Order", "expense")
    assert map_category_to_standard(cat1) == "Shopping"

    cat2 = categorize_transaction("Nike Running Shoes Store", "expense")
    assert map_category_to_standard(cat2) == "Shopping"


def test_categorize_transport():
    cat1 = categorize_transaction("Uber Ride to Airport", "expense")
    assert map_category_to_standard(cat1) == "Transport"

    cat2 = categorize_transaction("Shell Gas Station Fuel", "expense")
    assert map_category_to_standard(cat2) == "Transport"

    cat3 = categorize_transaction("City Metro Transit Pass", "expense")
    assert map_category_to_standard(cat3) == "Transport"


def test_categorize_entertainment():
    cat1 = categorize_transaction("Netflix Monthly Streaming", "expense")
    assert map_category_to_standard(cat1) == "Entertainment"

    cat2 = categorize_transaction("Movie Theater Cinema Tickets", "expense")
    assert map_category_to_standard(cat2) == "Entertainment"

    cat3 = categorize_transaction("Steam PC Video Game", "expense")
    assert map_category_to_standard(cat3) == "Entertainment"


def test_categorize_bills_and_utilities():
    cat1 = categorize_transaction("Electric & Power Co Utility", "expense")
    assert map_category_to_standard(cat1) == "Bills & Utilities"

    cat2 = categorize_transaction("High Speed Internet Wifi Bill", "expense")
    assert map_category_to_standard(cat2) == "Bills & Utilities"

    cat3 = categorize_transaction("City Water Utility", "expense")
    assert map_category_to_standard(cat3) == "Bills & Utilities"


def test_categorize_education():
    cat1 = categorize_transaction("University College Tuition Payment", "expense")
    assert map_category_to_standard(cat1) == "Education"

    cat2 = categorize_transaction("Udemy Programming Course", "expense")
    assert map_category_to_standard(cat2) == "Education"


def test_categorize_healthcare():
    cat1 = categorize_transaction("City Pharmacy Prescription Medicine", "expense")
    assert map_category_to_standard(cat1) == "Healthcare"

    cat2 = categorize_transaction("Dental Checkup and Cleaning Clinic", "expense")
    assert map_category_to_standard(cat2) == "Healthcare"


def test_categorize_rent():
    cat1 = categorize_transaction("Apartment Monthly Rent", "expense")
    assert map_category_to_standard(cat1) == "Rent"

    cat2 = categorize_transaction("Residential Lease Payment", "expense")
    assert map_category_to_standard(cat2) == "Rent"


def test_categorize_investment_savings():
    cat1 = categorize_transaction("Mutual Fund Investment Deposit", "expense")
    assert map_category_to_standard(cat1) == "Investment/Savings"

    cat2 = categorize_transaction("Vanguard Stocks Purchase", "expense")
    assert map_category_to_standard(cat2) == "Investment/Savings"


def test_categorize_other_and_fallback():
    cat1 = categorize_transaction("Haircut Salon Spa Service", "expense")
    assert map_category_to_standard(cat1) == "Other"

    # Complete unknown fallback
    unknown_cat = categorize_transaction("XYZ98765 Nonexistent Merchant", "expense")
    assert unknown_cat == "Miscellaneous"
    assert map_category_to_standard(unknown_cat) == "Other"


def test_category_rules_and_categories_catalog():
    categories = get_all_categories()
    assert len(categories) > 0
    assert "Income" in categories

    rules = get_category_rules()
    assert isinstance(rules, dict)
    assert len(rules) > 0
