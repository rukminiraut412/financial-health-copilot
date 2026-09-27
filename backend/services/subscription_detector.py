"""
Subscription Detector Service (Foundation / Scaffold).
Identifies recurring payments, digital subscriptions, and memberships.
"""

from typing import List, Dict, Any
from backend.schemas.transaction import Transaction


def detect_subscriptions(transactions: List[Transaction]) -> List[Dict[str, Any]]:
    """
    Identifies recurring subscriptions based on categorized patterns and frequencies.
    Foundation stub for subsequent tasks.
    """
    subscription_txs = [
        t for t in transactions
        if t.category in ["Subscriptions", "Entertainment"]
        and t.type == "expense"
    ]

    detected = []
    seen = set()
    for t in subscription_txs:
        key = (t.description.lower(), t.amount)
        if key not in seen:
            seen.add(key)
            detected.append({
                "merchant": t.description,
                "amount": t.amount,
                "category": t.category,
                "estimated_frequency": "Monthly",
                "annual_cost": round(t.amount * 12, 2),
            })

    return detected
