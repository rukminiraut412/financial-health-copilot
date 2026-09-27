"""
Subscription Detector Service.
Detects likely recurring monthly expenses, digital subscriptions, and memberships.
"""

import re
from typing import Dict, List
import numpy as np

from backend.schemas.analysis import SubscriptionItem
from backend.schemas.transaction import Transaction, TransactionType
from backend.services.analytics import map_category_to_standard


# Well-known subscription keywords
SUBSCRIPTION_KEYWORDS = {
    "netflix", "spotify", "hulu", "disney", "prime", "gym", "fitness",
    "icloud", "dropbox", "google one", "internet", "broadband", "wifi",
    "audible", "youtube", "chatgpt", "apple music", "subscription",
    "membership", "patreon", "subway pass", "transit pass", "phone bill",
}

# Words to strip when normalizing merchant identity
STRIP_WORDS = {
    "monthly", "subscription", "recurring", "fee", "bill", "membership",
    "premium", "payment", "charge", "auto-renew", "online", "service",
}


def normalize_merchant_name(desc: str) -> str:
    """Extracts a normalized core merchant key from a description."""
    cleaned = re.sub(r"[^\w\s]", " ", desc.lower())
    words = [w for w in cleaned.split() if w not in STRIP_WORDS]
    return " ".join(words) if words else cleaned.strip()


def clean_display_name(desc: str) -> str:
    """Returns a clean presentation name for the subscription."""
    return desc.strip().title()


def detect_subscriptions(transactions: List[Transaction]) -> List[SubscriptionItem]:
    """
    Identifies recurring subscriptions based on recurring occurrences and known subscription merchants.
    One-time variable purchases are excluded.
    """
    expense_txs = [t for t in transactions if t.type == TransactionType.EXPENSE.value]
    if not expense_txs:
        return []

    # Exclude inherently large non-subscription categories like Rent and Investment
    candidate_txs = [
        t for t in expense_txs
        if map_category_to_standard(t.category) not in {"Rent", "Investment/Savings"}
    ]

    # Group transactions by normalized merchant
    merchant_groups: Dict[str, List[Transaction]] = {}
    for t in candidate_txs:
        key = normalize_merchant_name(t.description)
        if key not in merchant_groups:
            merchant_groups[key] = []
        merchant_groups[key].append(t)

    subscriptions: List[SubscriptionItem] = []
    seen_merchants = set()

    for key, tx_list in merchant_groups.items():
        amounts = [t.amount for t in tx_list]
        first_tx = tx_list[0]
        desc_lower = first_tx.description.lower()

        # Case 1: Multiple occurrences with consistent pricing (<= 15% variation)
        if len(tx_list) >= 2:
            min_amt = min(amounts)
            max_amt = max(amounts)
            diff = max_amt - min_amt

            if diff <= max(10.0, min_amt * 0.15):
                avg_amount = float(np.mean(amounts))
                display_name = clean_display_name(first_tx.description)
                if display_name not in seen_merchants:
                    seen_merchants.add(display_name)
                    subscriptions.append(
                        SubscriptionItem(
                            description=display_name,
                            category=map_category_to_standard(first_tx.category),
                            amount=round(avg_amount, 2),
                            frequency="Monthly",
                            occurrences=len(tx_list),
                            estimated_monthly_cost=round(avg_amount, 2),
                        )
                    )
                continue

        # Case 2: Single occurrence matching recognized subscription keyword
        is_known_sub = any(kw in desc_lower for kw in SUBSCRIPTION_KEYWORDS)
        if is_known_sub and first_tx.amount < 5000.0:
            display_name = clean_display_name(first_tx.description)
            if display_name not in seen_merchants:
                seen_merchants.add(display_name)
                subscriptions.append(
                    SubscriptionItem(
                        description=display_name,
                        category=map_category_to_standard(first_tx.category),
                        amount=round(first_tx.amount, 2),
                        frequency="Monthly",
                        occurrences=1,
                        estimated_monthly_cost=round(first_tx.amount, 2),
                    )
                )

    # Sort descending by estimated monthly cost
    subscriptions.sort(key=lambda s: s.estimated_monthly_cost, reverse=True)
    return subscriptions
