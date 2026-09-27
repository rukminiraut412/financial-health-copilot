"""
Financial Health Score Service.
Computes a comprehensive 0-100 financial health score based on savings rate,
essential vs non-essential spending ratio, and living-within-means metrics.
"""

from typing import List, Optional
from backend.schemas.analysis import (
    HealthScoreBreakdown,
    HealthScoreMetrics,
    HealthScoreResponse,
)
from backend.schemas.transaction import Transaction


def calculate_health_score(transactions: List[Transaction]) -> HealthScoreResponse:
    """
    Computes an objective 0-100 Financial Health Score and returns grade,
    component breakdown, metrics, and targeted insights.
    """
    if not transactions:
        return HealthScoreResponse(
            score=50,
            grade="N/A",
            status="Insufficient Data",
            breakdown=HealthScoreBreakdown(
                savings_score=20.0,
                essential_spending_score=17.5,
                living_within_means_score=12.5,
            ),
            metrics=HealthScoreMetrics(
                savings_rate=0.0,
                essential_ratio=0.0,
                non_essential_ratio=0.0,
                expense_to_income_ratio=0.0,
            ),
            insights=["No transactions provided. Upload your CSV to evaluate your Financial Health Score."],
        )

    # Avoid circular imports by importing locally
    from backend.services.analytics import (
        calculate_total_income,
        calculate_total_expenses,
        calculate_savings,
        calculate_savings_rate,
        calculate_essential_vs_non_essential,
    )

    total_income = calculate_total_income(transactions)
    # Exclude Investment/Savings from expense metric for health score
    total_expenses = calculate_total_expenses(transactions, exclude_investments=True)
    net_savings = calculate_savings(transactions)
    savings_rate = calculate_savings_rate(transactions)

    essential_data = calculate_essential_vs_non_essential(transactions)
    essential_spent = essential_data.essential_spending
    non_essential_spent = essential_data.non_essential_spending

    if total_income > 0:
        essential_ratio = round((essential_spent / total_income) * 100.0, 2)
        non_essential_ratio = round((non_essential_spent / total_income) * 100.0, 2)
        expense_ratio = round((total_expenses / total_income) * 100.0, 2)
    else:
        essential_ratio = 100.0 if essential_spent > 0 else 0.0
        non_essential_ratio = 100.0 if non_essential_spent > 0 else 0.0
        expense_ratio = 100.0 if total_expenses > 0 else 0.0

    # 1. Savings Rate Score (Max 40 points)
    if savings_rate >= 20.0:
        savings_score = 40.0
    elif savings_rate >= 10.0:
        savings_score = 25.0 + ((savings_rate - 10.0) / 10.0) * 15.0
    elif savings_rate >= 0.0:
        savings_score = 10.0 + (savings_rate / 10.0) * 15.0
    else:
        # Negative savings rate penalizes down to 0
        savings_score = max(0.0, 10.0 + (savings_rate / 10.0) * 5.0)

    # 2. Essential Spending Score (Max 35 points) - 50% benchmark
    if essential_ratio <= 50.0:
        essential_score = 35.0
    elif essential_ratio <= 70.0:
        essential_score = 35.0 - ((essential_ratio - 50.0) / 20.0) * 15.0
    elif essential_ratio <= 90.0:
        essential_score = 20.0 - ((essential_ratio - 70.0) / 20.0) * 15.0
    else:
        essential_score = max(0.0, 5.0 - ((essential_ratio - 90.0) / 10.0) * 5.0)

    # 3. Living Within Means Score (Max 25 points) - <= 70% benchmark
    if expense_ratio <= 70.0:
        living_score = 25.0
    elif expense_ratio <= 90.0:
        living_score = 25.0 - ((expense_ratio - 70.0) / 20.0) * 10.0
    elif expense_ratio <= 100.0:
        living_score = 15.0 - ((expense_ratio - 90.0) / 10.0) * 10.0
    else:
        living_score = max(0.0, 5.0 - ((expense_ratio - 100.0) / 20.0) * 5.0)

    total_score = int(round(savings_score + essential_score + living_score))
    total_score = min(100, max(0, total_score))

    # Determine Grade and Status
    if total_score >= 85:
        grade = "A"
        status = "Excellent"
    elif total_score >= 70:
        grade = "B"
        status = "Good"
    elif total_score >= 50:
        grade = "C"
        status = "Fair"
    elif total_score >= 35:
        grade = "D"
        status = "Needs Attention"
    else:
        grade = "F"
        status = "Critical"

    # Generate Targeted Actionable Insights
    insights = []
    if savings_rate >= 20.0:
        insights.append(f"Outstanding savings rate of {savings_rate:.1f}%, beating the 20% healthy threshold.")
    elif savings_rate >= 10.0:
        insights.append(f"Solid savings rate of {savings_rate:.1f}%. Boosting it above 20% will accelerate your financial goals.")
    elif savings_rate > 0.0:
        insights.append(f"Savings rate is modest at {savings_rate:.1f}%. Aim to save at least 15-20% to build an emergency fund.")
    else:
        deficit = abs(net_savings)
        insights.append(f"Spending exceeds income with a net cash deficit of ₹{deficit:,.2f}. Immediate expense trimming recommended.")

    if essential_ratio <= 50.0:
        insights.append(f"Essential living costs are well-controlled at {essential_ratio:.1f}% of income (target: ≤50%).")
    else:
        insights.append(f"Essential expenses take up {essential_ratio:.1f}% of income, exceeding the 50% guideline. Consider optimizing fixed bills.")

    if non_essential_ratio <= 30.0:
        insights.append(f"Discretionary spending is balanced at {non_essential_ratio:.1f}% of income (target: ≤30%).")
    else:
        insights.append(f"Discretionary spending is elevated at {non_essential_ratio:.1f}% of income. Review dining and shopping to reclaim savings.")

    return HealthScoreResponse(
        score=total_score,
        grade=grade,
        status=status,
        breakdown=HealthScoreBreakdown(
            savings_score=round(savings_score, 1),
            essential_spending_score=round(essential_score, 1),
            living_within_means_score=round(living_score, 1),
        ),
        metrics=HealthScoreMetrics(
            savings_rate=round(savings_rate, 2),
            essential_ratio=round(essential_ratio, 2),
            non_essential_ratio=round(non_essential_ratio, 2),
            expense_to_income_ratio=round(expense_ratio, 2),
        ),
        insights=insights,
    )
