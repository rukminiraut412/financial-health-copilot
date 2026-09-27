"""
Budget Engine Service (Foundation / Scaffold).
Provides 50/30/20 budgeting and category limit recommendations.
"""

from typing import List, Dict, Any
from backend.schemas.transaction import Transaction


def generate_budget_recommendations(transactions: List[Transaction]) -> Dict[str, Any]:
    """
    Computes standard 50/30/20 budget framework guidelines against actual spending.
    Foundation stub for subsequent tasks.
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
