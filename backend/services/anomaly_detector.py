"""
Anomaly Detector Service (Foundation / Scaffold).
Flags unusually large or atypical transactions for user review.
"""

from typing import List, Dict, Any
from backend.schemas.transaction import Transaction


def detect_anomalies(transactions: List[Transaction], threshold_factor: float = 2.5) -> List[Dict[str, Any]]:
    """
    Detects anomalous expenses that deviate substantially from average spending.
    Foundation stub for subsequent tasks.
    """
    expenses = [t for t in transactions if t.type == "expense"]
    if len(expenses) < 3:
        return []

    amounts = [t.amount for t in expenses]
    avg_expense = sum(amounts) / len(amounts)

    anomalies = []
    for t in expenses:
        if t.amount > avg_expense * threshold_factor:
            anomalies.append({
                "transaction_id": t.id,
                "description": t.description,
                "amount": t.amount,
                "date": t.date,
                "category": t.category,
                "average_amount": round(avg_expense, 2),
                "reason": f"Amount is significantly higher than your average expense of ${avg_expense:.2f}",
            })

    return anomalies
