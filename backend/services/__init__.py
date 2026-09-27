"""
Services package exporting core business logic and analysis engines.
"""

from backend.services.transaction_processor import (
    parse_csv_file,
    transactions_to_dataframe,
    dataframe_to_transactions,
)
from backend.services.categorizer import (
    categorize_transaction,
    categorize_dataframe,
    get_all_categories,
    get_category_rules,
)
from backend.services.analytics import (
    calculate_total_income,
    calculate_total_expenses,
    calculate_savings,
    calculate_savings_rate,
    calculate_cash_flow,
    calculate_category_spending,
    calculate_category_percentages,
    calculate_category_breakdown,
    calculate_monthly_income,
    calculate_monthly_expenses,
    calculate_monthly_savings,
    calculate_monthly_trends,
    calculate_essential_vs_non_essential,
    map_category_to_standard,
    get_date_range,
    generate_basic_analysis,
    STANDARD_CATEGORIES,
    ESSENTIAL_CATEGORIES,
    NON_ESSENTIAL_CATEGORIES,
)
from backend.services.health_score import calculate_health_score
from backend.services.anomaly_detector import detect_anomalies
from backend.services.subscription_detector import detect_subscriptions
from backend.services.budget_engine import evaluate_budget, generate_budget_recommendations
from backend.services.ai_copilot import ask_copilot
from backend.services.action_engine import generate_action_items

__all__ = [
    "evaluate_budget",
    "parse_csv_file",
    "transactions_to_dataframe",
    "dataframe_to_transactions",
    "categorize_transaction",
    "categorize_dataframe",
    "get_all_categories",
    "get_category_rules",
    "calculate_total_income",
    "calculate_total_expenses",
    "calculate_savings",
    "calculate_savings_rate",
    "calculate_cash_flow",
    "calculate_category_spending",
    "calculate_category_percentages",
    "calculate_category_breakdown",
    "calculate_monthly_income",
    "calculate_monthly_expenses",
    "calculate_monthly_savings",
    "calculate_monthly_trends",
    "calculate_essential_vs_non_essential",
    "map_category_to_standard",
    "get_date_range",
    "generate_basic_analysis",
    "calculate_health_score",
    "detect_anomalies",
    "detect_subscriptions",
    "generate_budget_recommendations",
    "ask_copilot",
    "generate_action_items",
    "STANDARD_CATEGORIES",
    "ESSENTIAL_CATEGORIES",
    "NON_ESSENTIAL_CATEGORIES",
]
