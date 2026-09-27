"""
Action Engine Service (Foundation / Scaffold).
Converts financial analytics and insights into discrete, high-impact action items.
"""

from typing import List, Dict, Any
from backend.schemas.transaction import Transaction


def generate_action_items(transactions: List[Transaction]) -> List[Dict[str, Any]]:
    """
    Produces actionable recommendations from transactions.
    Starter foundation stub for subsequent tasks.
    """
    actions = []
    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")

    if expenses > income:
        actions.append({
            "id": "act_reduce_burn",
            "priority": "HIGH",
            "title": "Reduce Discretionary Spending",
            "description": "Your expenses exceed your current income. Review dining and entertainment to stabilize cash flow.",
            "impact": "High Cash Flow Protection",
        })
    else:
        actions.append({
            "id": "act_boost_savings",
            "priority": "MEDIUM",
            "title": "Automate Surplus to Savings",
            "description": "You have positive net cash flow. Consider routing 20% to an emergency or index fund.",
            "impact": "Wealth Accumulation",
        })

    return actions
