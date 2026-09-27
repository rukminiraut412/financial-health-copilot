"""
AI Copilot Service (Foundation / Scaffold).
Handles natural language queries and generative insights. Full LLM logic to be integrated in future phase.
"""

from typing import Dict, Any, List
from backend.schemas.transaction import Transaction


def ask_copilot(query: str, transactions: List[Transaction]) -> Dict[str, Any]:
    """
    Answers user financial queries or provides tailored feedback.
    Starter foundation stub returning structured insights.
    """
    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")
    net = income - expenses

    return {
        "query": query,
        "response": (
            f"Based on your {len(transactions)} transactions, your total income is ${income:,.2f} "
            f"and total expenses are ${expenses:,.2f}, resulting in a net cash flow of ${net:,.2f}."
        ),
        "status": "success",
        "mode": "basic_rule_engine",
    }
