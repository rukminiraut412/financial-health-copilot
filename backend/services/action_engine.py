"""
Action Engine Service.
Converts financial analysis into 3–5 concrete, explainable, actionable recommendations.
Deterministic, rule-based, and non-LLM.
"""

from typing import Dict, List, Optional
from backend.schemas.analysis import (
    ActionItem,
    AnomalyItem,
    BudgetSummary,
    CashFlowSummary,
    EssentialVsNonEssential,
    HealthScoreResponse,
    SubscriptionItem,
)
from backend.schemas.transaction import Transaction


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def generate_actions(
    summary: Optional[CashFlowSummary] = None,
    category_spending: Optional[Dict[str, float]] = None,
    category_percentages: Optional[Dict[str, float]] = None,
    essential_vs_non_essential: Optional[EssentialVsNonEssential] = None,
    health_score: Optional[HealthScoreResponse] = None,
    anomalies: Optional[List[AnomalyItem]] = None,
    subscriptions: Optional[List[SubscriptionItem]] = None,
    budget_summary: Optional[BudgetSummary] = None,
) -> List[ActionItem]:
    """
    Generates 3 to 5 deterministic, explainable financial action recommendations
    based on comprehensive spending analytics, anomalies, subscriptions, and budgets.
    Returns an empty list if there is insufficient analysis data.
    """
    # Safe empty check
    if not summary or (summary.total_income == 0 and summary.total_expenses == 0):
        return []

    category_spending = category_spending or {}
    category_percentages = category_percentages or {}
    anomalies = anomalies or []
    subscriptions = subscriptions or []

    candidates: List[ActionItem] = []

    # Rule 1: High/Medium Anomaly Review
    notable_anomalies = [a for a in anomalies if a.severity in {"high", "medium"}]
    if notable_anomalies:
        # Pick the most severe/largest anomaly
        top_anomaly = sorted(
            notable_anomalies,
            key=lambda a: (0 if a.severity == "high" else 1, -a.amount),
        )[0]
        candidates.append(
            ActionItem(
                title=f"Review unusual charge: {top_anomaly.description}",
                description=(
                    f"A transaction of ${top_anomaly.amount:,.2f} on {top_anomaly.date} "
                    f"was flagged as atypical for {top_anomaly.category}. "
                    f"Confirm if this was an authorized, planned expense."
                ),
                action_type="review_anomaly",
                category=top_anomaly.category,
                priority=top_anomaly.severity,
                estimated_monthly_impact=None,  # Conservative: do not assume single anomaly is recurring saving
                reason=top_anomaly.reason,
            )
        )

    # Rule 2: Over-budget Category Correction
    if budget_summary and budget_summary.overspent_categories:
        overspent_items = [
            cs for cs in budget_summary.categories if cs.status == "over_budget"
        ]
        if overspent_items:
            # Sort by highest overrun amount
            top_overspent = sorted(overspent_items, key=lambda cs: cs.actual - cs.budget, reverse=True)[0]
            over_amount = round(top_overspent.actual - top_overspent.budget, 2)
            priority = "high" if top_overspent.utilization_percentage >= 120.0 else "medium"
            candidates.append(
                ActionItem(
                    title=f"Address budget overrun in {top_overspent.category}",
                    description=(
                        f"{top_overspent.category} spending (${top_overspent.actual:,.2f}) exceeded its "
                        f"${top_overspent.budget:,.2f} budget limit by ${over_amount:,.2f} "
                        f"({top_overspent.utilization_percentage:.1f}% utilized). Review recent purchases "
                        f"or adjust the budget allocation."
                    ),
                    action_type="set_or_adjust_budget",
                    category=top_overspent.category,
                    priority=priority,
                    estimated_monthly_impact=over_amount,
                    reason=f"Actual spending in {top_overspent.category} exceeded the allocated monthly budget.",
                )
            )

    # Rule 3: Low Savings Rate or Cash Deficit
    if summary.total_income > 0:
        if summary.net_savings < 0:
            deficit = round(abs(summary.net_savings), 2)
            candidates.append(
                ActionItem(
                    title="Eliminate monthly cash deficit",
                    description=(
                        f"Your monthly expenses exceed income by ${deficit:,.2f}. "
                        f"Focus on reducing non-essential spending to restore positive monthly cash flow."
                    ),
                    action_type="increase_savings",
                    category=None,
                    priority="high",
                    estimated_monthly_impact=deficit,
                    reason=f"Expenses currently exceed monthly income by ${deficit:,.2f}, creating a cash deficit.",
                )
            )
        elif summary.savings_rate < 15.0:
            target_diff = max(0.0, 20.0 - summary.savings_rate)
            target_savings = round(summary.total_income * (target_diff / 100.0), 2)
            priority = "high" if summary.savings_rate < 5.0 else "medium"
            candidates.append(
                ActionItem(
                    title="Increase monthly savings rate",
                    description=(
                        f"Your current savings rate is {summary.savings_rate:.1f}%. "
                        f"Saving an additional estimated ${target_savings:,.2f} monthly will help you "
                        f"reach the healthy 20% savings milestone."
                    ),
                    action_type="increase_savings",
                    category=None,
                    priority=priority,
                    estimated_monthly_impact=target_savings,
                    reason=f"Current savings rate of {summary.savings_rate:.1f}% is below the 20% benchmark.",
                )
            )

    # Rule 4: High Non-Essential Spending
    if essential_vs_non_essential and essential_vs_non_essential.non_essential_percentage > 35.0:
        non_ess_amount = essential_vs_non_essential.non_essential_spending
        trim_target = round(non_ess_amount * 0.15, 2)
        priority = "high" if essential_vs_non_essential.non_essential_percentage > 50.0 else "medium"
        candidates.append(
            ActionItem(
                title="Reduce non-essential discretionary spending",
                description=(
                    f"Non-essential wants represent {essential_vs_non_essential.non_essential_percentage:.1f}% "
                    f"of total expenses (${non_ess_amount:,.2f}). Trimming 15% across dining, shopping, "
                    f"and entertainment could free up an estimated ${trim_target:,.2f} monthly."
                ),
                action_type="reduce_non_essential_spending",
                category=None,
                priority=priority,
                estimated_monthly_impact=trim_target,
                reason=f"Discretionary spending is {essential_vs_non_essential.non_essential_percentage:.1f}% of expenses, exceeding the 30% guideline.",
            )
        )

    # Rule 5: High Spending in a Specific Discretionary Category
    discretionary_categories = ["Food", "Shopping", "Entertainment"]
    candidate_cats = [
        (cat, category_spending[cat], category_percentages.get(cat, 0.0))
        for cat in discretionary_categories
        if cat in category_spending and category_spending[cat] >= 200.0
    ]
    if candidate_cats:
        # Sort by highest spending
        candidate_cats.sort(key=lambda item: item[1], reverse=True)
        top_cat, top_spent, top_pct = candidate_cats[0]
        trim_est = round(top_spent * 0.15, 2)
        candidates.append(
            ActionItem(
                title=f"Reduce {top_cat} spending",
                description=(
                    f"{top_cat} spending is high compared with your overall expenses "
                    f"(${top_spent:,.2f}, representing {top_pct:.1f}% of expenses). "
                    f"Consider reducing it by about 15% to save an estimated ${trim_est:,.2f} monthly."
                ),
                action_type="reduce_category_spending",
                category=top_cat,
                priority="medium",
                estimated_monthly_impact=trim_est,
                reason=f"{top_cat} is one of your largest discretionary spending categories.",
            )
        )

    # Rule 6: Recurring Subscription Review
    if subscriptions:
        total_sub_cost = round(sum(s.estimated_monthly_cost for s in subscriptions), 2)
        sub_count = len(subscriptions)
        if total_sub_cost > 0:
            est_savings = round(total_sub_cost * 0.30, 2)  # conservative 30% optimization
            priority = "high" if total_sub_cost >= 150.0 or sub_count >= 5 else "medium"
            candidates.append(
                ActionItem(
                    title=f"Review recurring subscriptions ({sub_count} active)",
                    description=(
                        f"Detected {sub_count} recurring subscriptions totaling ${total_sub_cost:,.2f}/month. "
                        f"Auditing unused memberships could save an estimated ${est_savings:,.2f} monthly."
                    ),
                    action_type="review_subscription",
                    category="Bills & Utilities",
                    priority=priority,
                    estimated_monthly_impact=est_savings,
                    reason=f"Found {sub_count} recurring subscriptions totaling ${total_sub_cost:,.2f}/month.",
                )
            )

    # Rule 7: Proactive Budgeting Recommendation
    if len(candidates) < 3:
        if not budget_summary or not budget_summary.categories:
            candidates.append(
                ActionItem(
                    title="Set category spending budgets",
                    description=(
                        "Set monthly spending limits for key categories like Food, Shopping, "
                        "and Transport to proactively manage your cash flow."
                    ),
                    action_type="set_or_adjust_budget",
                    category=None,
                    priority="low",
                    estimated_monthly_impact=None,
                    reason="No category budgets currently configured. Setting limits helps prevent lifestyle creep.",
                )
            )

    # Rule 8: General Monitoring Recommendation
    if len(candidates) < 3:
        candidates.append(
            ActionItem(
                title="Monitor weekly spending trends",
                description=(
                    "Regularly review your categorized expenses to track changes against your income "
                    "and catch unexpected charges early."
                ),
                action_type="monitor_spending",
                category=None,
                priority="low",
                estimated_monthly_impact=None,
                reason="Routine tracking reinforces positive habits and protects long-term savings consistency.",
            )
        )

    # Deduplicate by (action_type, category)
    seen = set()
    unique_actions: List[ActionItem] = []
    for action in candidates:
        key = (action.action_type, action.category)
        if key not in seen:
            seen.add(key)
            unique_actions.append(action)

    # Sort deterministically by priority: high -> medium -> low
    unique_actions.sort(key=lambda a: PRIORITY_ORDER.get(a.priority, 3))

    # Return at most 5 actions
    return unique_actions[:5]


def generate_action_items(transactions: List[Transaction]) -> List[ActionItem]:
    """
    Convenience helper function for backward compatibility.
    Accepts transactions and generates structured action items.
    """
    from backend.services.analytics import generate_basic_analysis
    if not transactions:
        return []
    analysis = generate_basic_analysis(transactions)
    return analysis.actions
