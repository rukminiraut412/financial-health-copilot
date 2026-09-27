"""
Budget Engine Service.
Compares actual category spending against user-defined budgets,
tracks utilization percentages, remaining funds, and identifies overspending.
"""

from typing import Dict, List, Optional
from backend.schemas.analysis import BudgetSummary, CategoryBudgetStatus
from backend.schemas.transaction import Transaction
from backend.services.analytics import (
    calculate_category_spending,
    map_category_to_standard,
)


def evaluate_budget(
    transactions: List[Transaction],
    budgets: Optional[Dict[str, float]] = None,
) -> BudgetSummary:
    """
    Compares category-wise expense spending against allocated budgets.
    Calculates remaining budget, utilization percentage, and status per category.
    """
    if not budgets:
        return BudgetSummary(
            categories=[],
            total_budget=0.0,
            total_actual=0.0,
            total_remaining=0.0,
            overall_utilization_percentage=0.0,
            overspent_categories=[],
        )

    # Actual spending aggregated by standard category
    actual_spending = calculate_category_spending(transactions)

    category_statuses: List[CategoryBudgetStatus] = []
    overspent: List[str] = []

    # Map budgets by standard category to merge any variations
    standardized_budgets: Dict[str, float] = {}
    for cat_name, b_val in budgets.items():
        std_cat = map_category_to_standard(cat_name)
        val = max(0.0, float(b_val))
        standardized_budgets[std_cat] = standardized_budgets.get(std_cat, 0.0) + val

    for cat, budget_val in standardized_budgets.items():
        actual_val = actual_spending.get(cat, 0.0)
        remaining = round(budget_val - actual_val, 2)

        if budget_val > 0:
            utilization = round((actual_val / budget_val) * 100.0, 2)
        else:
            utilization = 100.0 if actual_val > 0 else 0.0

        if utilization > 100.0:
            status = "over_budget"
            overspent.append(cat)
        elif utilization >= 80.0:
            status = "near_limit"
        else:
            status = "under_budget"

        category_statuses.append(
            CategoryBudgetStatus(
                category=cat,
                budget=round(budget_val, 2),
                actual=round(actual_val, 2),
                remaining=remaining,
                utilization_percentage=utilization,
                status=status,
            )
        )

    total_budget = round(sum(cs.budget for cs in category_statuses), 2)
    total_actual = round(sum(cs.actual for cs in category_statuses), 2)
    total_remaining = round(total_budget - total_actual, 2)
    overall_util = round((total_actual / total_budget) * 100.0, 2) if total_budget > 0 else 0.0

    return BudgetSummary(
        categories=category_statuses,
        total_budget=total_budget,
        total_actual=total_actual,
        total_remaining=total_remaining,
        overall_utilization_percentage=overall_util,
        overspent_categories=overspent,
    )


def generate_budget_recommendations(transactions: List[Transaction]) -> Dict[str, Any]:
    """
    Computes standard 50/30/20 budget framework guidelines against actual spending.
    Maintained for backward compatibility.
    """
    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")

    needs_target = round(income * 0.50, 2)
    wants_target = round(income * 0.30, 2)
    savings_target = round(income * 0.20, 2)

    return {
        "framework": "50/30/20 Rule",
        "monthly_income": round(income, 2),
        "actual_expenses": round(expenses, 2),
        "targets": {
            "needs_target": needs_target,
            "wants_target": wants_target,
            "savings_target": savings_target,
        },
        "status": "On Track" if expenses <= income else "Over Budget",
    }
