"""
Anomaly Detector Service.
Provides explainable, statistical, and rule-based detection of unusual spending spikes.
"""

from typing import List
import numpy as np

from backend.schemas.analysis import AnomalyItem
from backend.schemas.transaction import Transaction, TransactionType
from backend.services.analytics import map_category_to_standard


def detect_anomalies(transactions: List[Transaction]) -> List[AnomalyItem]:
    """
    Detects unusually high spending compared with typical category and overall spending.
    Excludes income and inherently fixed expenses unless a severe outlier occurs.
    """
    expense_txs = [t for t in transactions if t.type == TransactionType.EXPENSE.value]
    if not expense_txs:
        return []

    # Group expenses by standard category
    category_txs = {}
    for t in expense_txs:
        std_cat = map_category_to_standard(t.category)
        if std_cat not in category_txs:
            category_txs[std_cat] = []
        category_txs[std_cat].append(t)

    # Calculate overall baseline for discretionary spending
    discretionary_txs = [
        t for t in expense_txs
        if map_category_to_standard(t.category) not in {"Rent", "Investment/Savings"}
    ]
    if discretionary_txs:
        overall_median = float(np.median([t.amount for t in discretionary_txs]))
    else:
        overall_median = float(np.median([t.amount for t in expense_txs]))

    anomalies: List[AnomalyItem] = []

    for cat, tx_list in category_txs.items():
        amounts = [t.amount for t in tx_list]
        cat_median = float(np.median(amounts))
        cat_mean = float(np.mean(amounts))
        baseline = cat_median if len(amounts) >= 3 else cat_mean

        # Inherently large fixed expense: Rent
        if cat in {"Rent", "Investment/Savings"}:
            for t in tx_list:
                if len(amounts) >= 2 and baseline > 0:
                    if t.amount >= baseline * 1.5 and (t.amount - baseline) >= 500.0:
                        ratio = t.amount / baseline
                        severity = "high" if ratio >= 2.0 else "medium"
                        anomalies.append(
                            AnomalyItem(
                                date=t.date,
                                description=t.description,
                                amount=round(t.amount, 2),
                                category=cat,
                                reason=f"Unusually high {cat} charge ({ratio:.1f}x typical of ${baseline:,.2f})",
                                severity=severity,
                            )
                        )
            continue

        # Variable/discretionary categories
        if len(tx_list) >= 2:
            for t in tx_list:
                # Flag if at least 2.2x baseline and difference is meaningful (>= 50)
                if baseline > 0 and t.amount >= baseline * 2.2 and (t.amount - baseline) >= 50.0:
                    ratio = t.amount / baseline
                    if ratio >= 4.5:
                        severity = "high"
                    elif ratio >= 3.0:
                        severity = "medium"
                    else:
                        severity = "low"

                    anomalies.append(
                        AnomalyItem(
                            date=t.date,
                            description=t.description,
                            amount=round(t.amount, 2),
                            category=cat,
                            reason=f"Amount (${t.amount:,.2f}) is {ratio:.1f}x higher than typical {cat} spending (avg: ${baseline:,.2f})",
                            severity=severity,
                        )
                    )
        else:
            # Single transaction in category: compare with overall median
            single_tx = tx_list[0]
            if overall_median > 0 and single_tx.amount >= overall_median * 3.0 and single_tx.amount >= 150.0:
                ratio = single_tx.amount / overall_median
                severity = "high" if ratio >= 5.0 else "medium"
                anomalies.append(
                    AnomalyItem(
                        date=single_tx.date,
                        description=single_tx.description,
                        amount=round(single_tx.amount, 2),
                        category=cat,
                        reason=f"Amount (${single_tx.amount:,.2f}) is {ratio:.1f}x higher than median discretionary spending (${overall_median:,.2f})",
                        severity=severity,
                    )
                )

    # Sort anomalies descending by amount
    anomalies.sort(key=lambda a: a.amount, reverse=True)
    return anomalies
