"""
Analytics service computing cash flow, category breakdowns, savings rates,
monthly trends, essential vs non-essential spending, and financial health scores.
"""

from typing import Dict, List, Optional
import pandas as pd

from backend.schemas.analysis import (
    AnalysisResponse,
    CashFlowSummary,
    CategoryBreakdown,
    DateRange,
    EssentialVsNonEssential,
    MonthlyTrend,
)
from backend.schemas.transaction import Transaction, TransactionType
from backend.services.transaction_processor import transactions_to_dataframe


# Standard 10 frontend display categories
STANDARD_CATEGORIES: List[str] = [
    "Food",
    "Shopping",
    "Transport",
    "Entertainment",
    "Bills & Utilities",
    "Education",
    "Healthcare",
    "Rent",
    "Investment/Savings",
    "Other",
]

# Canonical category mapping from various classifier tags
CATEGORY_MAPPING: Dict[str, str] = {
    "food": "Food",
    "groceries": "Food",
    "dining & food": "Food",
    "dining": "Food",
    "restaurant": "Food",
    "shopping": "Shopping",
    "retail": "Shopping",
    "transport": "Transport",
    "transportation": "Transport",
    "travel": "Transport",
    "entertainment": "Entertainment",
    "bills & utilities": "Bills & Utilities",
    "utilities": "Bills & Utilities",
    "bills": "Bills & Utilities",
    "subscriptions": "Bills & Utilities",
    "education": "Education",
    "healthcare": "Healthcare",
    "medical": "Healthcare",
    "rent": "Rent",
    "housing & rent": "Rent",
    "housing": "Rent",
    "investment/savings": "Investment/Savings",
    "investments & savings": "Investment/Savings",
    "investment": "Investment/Savings",
    "savings": "Investment/Savings",
    "other": "Other",
    "miscellaneous": "Other",
    "personal care": "Other",
}

# Essential categories for financial health classification
ESSENTIAL_CATEGORIES = {"Rent", "Bills & Utilities", "Healthcare", "Education", "Transport"}
# Non-essential categories for financial health classification
NON_ESSENTIAL_CATEGORIES = {"Food", "Shopping", "Entertainment", "Other"}


def map_category_to_standard(raw_category: Optional[str]) -> str:
    """
    Maps any raw or sub-category string to one of the 10 standard display categories.
    """
    if not raw_category:
        return "Other"
    cleaned = raw_category.strip().lower()
    return CATEGORY_MAPPING.get(cleaned, "Other")


def calculate_total_income(transactions: List[Transaction]) -> float:
    """Calculates total aggregated income."""
    income_txs = [t for t in transactions if t.type == TransactionType.INCOME.value]
    return round(sum(t.amount for t in income_txs), 2)


def calculate_total_expenses(transactions: List[Transaction], exclude_investments: bool = False) -> float:
    """
    Calculates total aggregated expenses.
    If exclude_investments is True, excludes transfers categorized as Investment/Savings.
    """
    expense_txs = [t for t in transactions if t.type == TransactionType.EXPENSE.value]
    if exclude_investments:
        expense_txs = [
            t for t in expense_txs
            if map_category_to_standard(t.category) != "Investment/Savings"
        ]
    return round(sum(t.amount for t in expense_txs), 2)


def calculate_savings(transactions: List[Transaction]) -> float:
    """Calculates net savings (total income minus total expenses)."""
    income = calculate_total_income(transactions)
    expenses = calculate_total_expenses(transactions)
    return round(income - expenses, 2)


def calculate_savings_rate(transactions: List[Transaction]) -> float:
    """Calculates savings rate as a percentage of income (0.0 if income <= 0)."""
    income = calculate_total_income(transactions)
    savings = calculate_savings(transactions)
    if income > 0:
        return round((savings / income) * 100.0, 2)
    return 0.0


def calculate_cash_flow(transactions: List[Transaction]) -> CashFlowSummary:
    """Computes cash flow overview."""
    income = calculate_total_income(transactions)
    expenses = calculate_total_expenses(transactions)
    savings = round(income - expenses, 2)
    savings_rate = round((savings / income) * 100.0, 2) if income > 0 else 0.0

    return CashFlowSummary(
        total_income=income,
        total_expenses=expenses,
        net_savings=savings,
        savings_rate=savings_rate,
    )


def calculate_category_spending(transactions: List[Transaction]) -> Dict[str, float]:
    """
    Calculates spending aggregated by standard category for expense transactions.
    Returns clean dictionary format: { "Food": 5000.0, "Shopping": 3000.0, ... }
    """
    expense_txs = [t for t in transactions if t.type == TransactionType.EXPENSE.value]
    category_totals: Dict[str, float] = {cat: 0.0 for cat in STANDARD_CATEGORIES}

    for t in expense_txs:
        std_cat = map_category_to_standard(t.category)
        category_totals[std_cat] = round(category_totals.get(std_cat, 0.0) + t.amount, 2)

    # Return only categories with spending > 0, sorted descending
    active_categories = {k: v for k, v in category_totals.items() if v > 0}
    return dict(sorted(active_categories.items(), key=lambda item: item[1], reverse=True))


def calculate_category_percentages(transactions: List[Transaction]) -> Dict[str, float]:
    """
    Calculates category spending percentages of total expenses.
    Returns clean dictionary format: { "Food": 50.0, "Shopping": 30.0, ... }
    """
    spending = calculate_category_spending(transactions)
    total_spent = sum(spending.values())
    if total_spent <= 0:
        return {}

    return {
        cat: round((amt / total_spent) * 100.0, 2)
        for cat, amt in spending.items()
    }


def calculate_category_breakdown(transactions: List[Transaction]) -> List[CategoryBreakdown]:
    """
    Computes spending breakdown aggregated by category for expense transactions.
    """
    expense_txs = [t for t in transactions if t.type == TransactionType.EXPENSE.value]
    if not expense_txs:
        return []

    total_expense = sum(t.amount for t in expense_txs)
    category_totals: Dict[str, float] = {}
    category_counts: Dict[str, int] = {}

    for t in expense_txs:
        cat = map_category_to_standard(t.category)
        category_totals[cat] = category_totals.get(cat, 0.0) + t.amount
        category_counts[cat] = category_counts.get(cat, 0) + 1

    breakdowns: List[CategoryBreakdown] = []
    for cat, total in category_totals.items():
        pct = (total / total_expense * 100.0) if total_expense > 0 else 0.0
        breakdowns.append(
            CategoryBreakdown(
                category=cat,
                total_amount=round(total, 2),
                percentage=round(pct, 2),
                transaction_count=category_counts[cat],
            )
        )

    breakdowns.sort(key=lambda x: x.total_amount, reverse=True)
    return breakdowns


def calculate_monthly_income(transactions: List[Transaction]) -> Dict[str, float]:
    """Computes total income per month (YYYY-MM)."""
    if not transactions:
        return {}
    df = transactions_to_dataframe(transactions)
    df["month"] = df["date"].dt.strftime("%Y-%m")
    income_df = df[df["type"] == TransactionType.INCOME.value]
    return income_df.groupby("month")["amount"].sum().round(2).to_dict()


def calculate_monthly_expenses(transactions: List[Transaction]) -> Dict[str, float]:
    """Computes total expenses per month (YYYY-MM)."""
    if not transactions:
        return {}
    df = transactions_to_dataframe(transactions)
    df["month"] = df["date"].dt.strftime("%Y-%m")
    expense_df = df[df["type"] == TransactionType.EXPENSE.value]
    return expense_df.groupby("month")["amount"].sum().round(2).to_dict()


def calculate_monthly_savings(transactions: List[Transaction]) -> Dict[str, float]:
    """Computes net savings per month (YYYY-MM)."""
    m_inc = calculate_monthly_income(transactions)
    m_exp = calculate_monthly_expenses(transactions)
    all_months = sorted(set(m_inc.keys()) | set(m_exp.keys()))
    return {
        m: round(m_inc.get(m, 0.0) - m_exp.get(m, 0.0), 2)
        for m in all_months
    }


def calculate_monthly_trends(transactions: List[Transaction]) -> List[MonthlyTrend]:
    """
    Computes monthly income, expenses, and savings chronologically.
    Output directly matches frontend chart requirements.
    """
    if not transactions:
        return []

    df = transactions_to_dataframe(transactions)
    df["month"] = df["date"].dt.strftime("%Y-%m")

    grouped = df.groupby(["month", "type"])["amount"].sum().unstack(fill_value=0.0)

    if TransactionType.INCOME.value not in grouped.columns:
        grouped[TransactionType.INCOME.value] = 0.0
    if TransactionType.EXPENSE.value not in grouped.columns:
        grouped[TransactionType.EXPENSE.value] = 0.0

    trends: List[MonthlyTrend] = []
    for month_str, row in grouped.sort_index().iterrows():
        inc = round(float(row[TransactionType.INCOME.value]), 2)
        exp = round(float(row[TransactionType.EXPENSE.value]), 2)
        sav = round(inc - exp, 2)
        trends.append(
            MonthlyTrend(
                month=str(month_str),
                income=inc,
                expenses=exp,
                savings=sav,
                expense=exp,
                net=sav,
            )
        )

    return trends


def calculate_essential_vs_non_essential(transactions: List[Transaction]) -> EssentialVsNonEssential:
    """
    Simple, transparent classification of expenses into Essential and Non-Essential.
    Investment/Savings is excluded from expense metrics for this classification.
    """
    expense_txs = [t for t in transactions if t.type == TransactionType.EXPENSE.value]

    essential_breakdown: Dict[str, float] = {}
    non_essential_breakdown: Dict[str, float] = {}

    essential_total = 0.0
    non_essential_total = 0.0

    for t in expense_txs:
        std_cat = map_category_to_standard(t.category)

        # Investment/Savings is not treated as an expense for this metric
        if std_cat == "Investment/Savings":
            continue

        if std_cat in ESSENTIAL_CATEGORIES:
            essential_total += t.amount
            essential_breakdown[std_cat] = round(essential_breakdown.get(std_cat, 0.0) + t.amount, 2)
        else:
            non_essential_total += t.amount
            non_essential_breakdown[std_cat] = round(non_essential_breakdown.get(std_cat, 0.0) + t.amount, 2)

    total_classified = essential_total + non_essential_total
    if total_classified > 0:
        essential_pct = round((essential_total / total_classified) * 100.0, 2)
        non_essential_pct = round((non_essential_total / total_classified) * 100.0, 2)
    else:
        essential_pct = 0.0
        non_essential_pct = 0.0

    return EssentialVsNonEssential(
        essential_spending=round(essential_total, 2),
        non_essential_spending=round(non_essential_total, 2),
        essential_percentage=essential_pct,
        non_essential_percentage=non_essential_pct,
        essential_categories=essential_breakdown,
        non_essential_categories=non_essential_breakdown,
    )


def get_date_range(transactions: List[Transaction]) -> DateRange:
    """Identifies the earliest and latest transaction date."""
    if not transactions:
        return DateRange(start_date=None, end_date=None)

    dates = sorted([t.date for t in transactions if t.date])
    if not dates:
        return DateRange(start_date=None, end_date=None)

    return DateRange(start_date=dates[0], end_date=dates[-1])


def generate_basic_analysis(
    transactions: List[Transaction],
    budgets: Optional[Dict[str, float]] = None,
) -> AnalysisResponse:
    """
    Aggregates cash flow, category breakdowns, monthly trends, essential vs non-essential,
    Financial Health Score, anomaly detection, subscription detection, and budget comparison.
    """
    from backend.services.health_score import calculate_health_score
    from backend.services.anomaly_detector import detect_anomalies
    from backend.services.subscription_detector import detect_subscriptions
    from backend.services.budget_engine import evaluate_budget
    from backend.services.action_engine import generate_actions

    summary = calculate_cash_flow(transactions)
    category_spending = calculate_category_spending(transactions)
    category_percentages = calculate_category_percentages(transactions)
    category_breakdown = calculate_category_breakdown(transactions)
    top_categories = category_breakdown[:5]
    monthly_trends = calculate_monthly_trends(transactions)
    essential_vs_non_essential = calculate_essential_vs_non_essential(transactions)
    health_score = calculate_health_score(transactions)
    anomalies = detect_anomalies(transactions)
    subscriptions = detect_subscriptions(transactions)
    budget_summary = evaluate_budget(transactions, budgets=budgets)
    actions = generate_actions(
        summary=summary,
        category_spending=category_spending,
        category_percentages=category_percentages,
        essential_vs_non_essential=essential_vs_non_essential,
        health_score=health_score,
        anomalies=anomalies,
        subscriptions=subscriptions,
        budget_summary=budget_summary,
    )
    date_range = get_date_range(transactions)

    return AnalysisResponse(
        summary=summary,
        category_spending=category_spending,
        category_percentages=category_percentages,
        category_breakdown=category_breakdown,
        top_spending_categories=top_categories,
        monthly_trends=monthly_trends,
        essential_vs_non_essential=essential_vs_non_essential,
        health_score=health_score,
        anomalies=anomalies,
        subscriptions=subscriptions,
        budget_summary=budget_summary,
        actions=actions,
        total_transactions=len(transactions),
        date_range=date_range,
    )
