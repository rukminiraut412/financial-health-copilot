"""
AI Financial Copilot Service.
Provides an explainable, deterministic natural language copilot for user financial questions
grounded strictly in structured transaction analytics, anomalies, subscriptions, and budgets.
"""

import os
import re
from typing import Dict, List, Optional
from backend.schemas.analysis import (
    ActionItem,
    AnalysisResponse,
    CopilotResponse,
)
from backend.schemas.transaction import Transaction


def _clean_text(text: str) -> str:
    """Normalizes text for keyword and intent matching."""
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()


def _format_currency(val: float) -> str:
    return f"₹{val:,.2f}"


def _format_analysis_summary_for_llm(analysis: AnalysisResponse) -> str:
    """
    Formats structured analysis for an optional LLM prompt without exposing
    unnecessary raw transaction data (privacy-first).
    """
    top_cat = analysis.top_spending_categories[0].category if analysis.top_spending_categories else "None"
    return (
        f"Financial Summary:\n"
        f"- Total Income: {_format_currency(analysis.summary.total_income)}\n"
        f"- Total Expenses: {_format_currency(analysis.summary.total_expenses)}\n"
        f"- Net Savings: {_format_currency(analysis.summary.net_savings)} (Rate: {analysis.summary.savings_rate:.1f}%)\n"
        f"- Health Score: {analysis.health_score.score}/100 ({analysis.health_score.status})\n"
        f"- Top Spending Category: {top_cat}\n"
        f"- Discretionary Spending: {analysis.essential_vs_non_essential.non_essential_percentage:.1f}%\n"
        f"- Anomalies Detected: {len(analysis.anomalies)}\n"
        f"- Active Subscriptions: {len(analysis.subscriptions)}\n"
        f"- Over-budget Categories: {len(analysis.budget_summary.overspent_categories) if analysis.budget_summary else 0}\n"
    )


def _try_llm_generation(message: str, analysis: AnalysisResponse) -> Optional[str]:
    """
    Optional LLM generation hook. Checks environment variables for API key.
    Always preserves privacy by sending only high-level structured summaries.
    Returns None if no LLM provider is configured, ensuring seamless deterministic fallback.
    """
    api_key = os.getenv("COPILOT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    # An external provider can be invoked here; returns None on failure or missing dependency
    return None


def generate_copilot_response(
    message: str,
    analysis: Optional[AnalysisResponse] = None,
) -> CopilotResponse:
    """
    Analyzes user message and generates an explainable, deterministic response
    using structured financial analysis context.
    """
    if not message or not message.strip():
        return CopilotResponse(
            response="Please enter a valid financial question.",
            actions=[],
            sources=[],
        )

    # Missing or empty analysis context
    if not analysis or analysis.total_transactions == 0:
        return CopilotResponse(
            response=(
                "Financial analysis data is currently unavailable. "
                "Please upload a transaction CSV or analyze your transactions first so I can assist you."
            ),
            actions=[],
            sources=[],
        )

    query = _clean_text(message)

    # 1. Top Spending Category Intent
    if any(phrase in query for phrase in [
        "spending the most", "spend the most", "where am i spending",
        "highest spending", "top spending", "most expensive category",
        "biggest expense", "largest expense", "spend most", "where does my money go",
        "where did my money go", "most spent", "highest expense"
    ]):
        if analysis.category_spending:
            sorted_cats = sorted(analysis.category_spending.items(), key=lambda x: x[1], reverse=True)
            top_cat, top_amt = sorted_cats[0]
            top_pct = analysis.category_percentages.get(top_cat, 0.0)

            breakdown_parts = []
            for cat, amt in sorted_cats[:3]:
                pct = analysis.category_percentages.get(cat, 0.0)
                breakdown_parts.append(f"{cat}: {_format_currency(amt)} ({pct:.1f}%)")
            top_list_str = ", ".join(breakdown_parts)

            response_text = (
                f"You are spending the most on {top_cat}, totaling {_format_currency(top_amt)} "
                f"({top_pct:.1f}% of your total expenses). Your top spending categories are: {top_list_str}."
            )
            matching_actions = [
                a for a in analysis.actions
                if a.category == top_cat or a.action_type == "reduce_category_spending"
            ]
            return CopilotResponse(
                response=response_text,
                actions=matching_actions[:2],
                sources=["category_spending", "category_percentages"],
            )

    # 2. How to Save More Intent
    if any(phrase in query for phrase in [
        "how can i save more", "how to save", "save more", "increase savings",
        "boost savings", "increase my savings", "how to save money", "saving tips",
        "how can i save", "ways to save", "help me save"
    ]):
        savings_rate = analysis.summary.savings_rate
        net_savings = analysis.summary.net_savings
        tips = []

        if net_savings < 0:
            tips.append(f"Your expenses currently exceed income by {_format_currency(abs(net_savings))}.")
        else:
            tips.append(f"Your current savings rate is {savings_rate:.1f}% (net savings: {_format_currency(net_savings)}).")

        # Top discretionary category tip
        discretionary_cats = [
            (c, a) for c, a in analysis.category_spending.items()
            if c in {"Food", "Shopping", "Entertainment"}
        ]
        if discretionary_cats:
            top_disc_cat, top_disc_amt = sorted(discretionary_cats, key=lambda x: x[1], reverse=True)[0]
            potential_trim = top_disc_amt * 0.15
            tips.append(
                f"Trimming your {top_disc_cat} spending ({_format_currency(top_disc_amt)}) by 15% could free up approximately {_format_currency(potential_trim)} monthly."
            )

        # Subscriptions tip
        if analysis.subscriptions:
            total_subs = sum(s.estimated_monthly_cost for s in analysis.subscriptions)
            tips.append(
                f"Auditing your {len(analysis.subscriptions)} active subscription(s) ({_format_currency(total_subs)}/month) can quickly eliminate recurring leakage."
            )

        response_text = "Here is how you can boost your savings:\n• " + "\n• ".join(tips)
        relevant_actions = [
            a for a in analysis.actions
            if a.action_type in {"increase_savings", "reduce_non_essential_spending", "reduce_category_spending", "review_subscription"}
        ]
        return CopilotResponse(
            response=response_text,
            actions=relevant_actions[:3],
            sources=["summary", "category_spending", "subscriptions"],
        )

    # 3. Anomaly / Unusual Spending Intent
    if any(phrase in query for phrase in [
        "unusual spending", "anomaly", "anomalies", "unusual transaction",
        "irregular", "unusual charge", "spike in spending", "unexpected",
        "strange transaction", "flagged"
    ]):
        if analysis.anomalies:
            anomaly_lines = []
            for anom in analysis.anomalies[:3]:
                anomaly_lines.append(
                    f"• {anom.description} on {anom.date}: {_format_currency(anom.amount)} "
                    f"({anom.category}, {anom.severity} severity) — {anom.reason}"
                )
            response_text = (
                f"I detected {len(analysis.anomalies)} unusual transaction(s) in your statement:\n"
                + "\n".join(anomaly_lines)
            )
            relevant_actions = [a for a in analysis.actions if a.action_type == "review_anomaly"]
            return CopilotResponse(
                response=response_text,
                actions=relevant_actions,
                sources=["anomalies"],
            )
        else:
            return CopilotResponse(
                response="No unusual spending spikes or anomalous transactions were detected in your statement. Your expenses appear consistent with typical patterns.",
                actions=[],
                sources=["anomalies"],
            )

    # 4. Subscription Review Intent
    if any(phrase in query for phrase in [
        "subscription", "subscriptions", "recurring", "membership", "memberships",
        "recurring charge", "recurring bill", "monthly charges", "streaming"
    ]):
        if analysis.subscriptions:
            total_cost = sum(s.estimated_monthly_cost for s in analysis.subscriptions)
            sub_lines = []
            for s in analysis.subscriptions:
                sub_lines.append(
                    f"• {s.description}: {_format_currency(s.amount)}/{s.frequency.lower()} "
                    f"({s.category}, {s.occurrences} occurrence(s))"
                )
            response_text = (
                f"I identified {len(analysis.subscriptions)} recurring subscription(s) totaling {_format_currency(total_cost)} per month:\n"
                + "\n".join(sub_lines)
                + "\n\nConsider reviewing these to cancel any services you no longer actively use."
            )
            relevant_actions = [a for a in analysis.actions if a.action_type == "review_subscription"]
            return CopilotResponse(
                response=response_text,
                actions=relevant_actions,
                sources=["subscriptions"],
            )
        else:
            return CopilotResponse(
                response="No recurring subscriptions or digital memberships were identified in your transaction history.",
                actions=[],
                sources=["subscriptions"],
            )

    # 5. Financial Health Score Calculation Intent
    if any(phrase in query for phrase in [
        "what is my financial health score", "what is my health score", "financial health score",
        "my financial health score", "what is my score", "my score", "health score",
        "how is my financial health score calculated", "how is the score calculated",
        "how is health score calculated", "how is my score calculated",
        "explain score", "score breakdown", "how did you calculate my score",
        "scoring method", "formula"
    ]):
        hs = analysis.health_score
        bd = hs.breakdown
        metrics = hs.metrics

        response_text = (
            f"Your Financial Health Score is {hs.score}/100 (Grade {hs.grade}, '{hs.status}'). "
            "It is calculated deterministically using three objective factors:\n"
            f"1. Savings Rate (up to 40 pts, benchmark ≥20%): earned {bd.savings_score:.1f} pts (current savings rate: {metrics.savings_rate:.1f}%)\n"
            f"2. Needs vs. Wants Balance (up to 35 pts, essential living costs ≤50%): earned {bd.essential_spending_score:.1f} pts (essential ratio: {metrics.essential_ratio:.1f}%)\n"
            f"3. Living Within Means (up to 25 pts, total expenses ≤70% of income): earned {bd.living_within_means_score:.1f} pts (expense-to-income ratio: {metrics.expense_to_income_ratio:.1f}%)\n\n"
            f"Key takeaway: {' '.join(hs.insights)}"
        )
        return CopilotResponse(
            response=response_text,
            actions=[a for a in analysis.actions if a.priority == "high"],
            sources=["health_score"],
        )

    # 6. Why is my Financial Health Score Low?
    if any(phrase in query for phrase in [
        "why is my financial health score low", "why is my score low",
        "why is score low", "why low score", "score is low", "reasons for low score"
    ]):
        hs = analysis.health_score
        metrics = hs.metrics
        reasons = []

        if metrics.savings_rate < 15.0:
            reasons.append(f"Your savings rate is {metrics.savings_rate:.1f}%, which is below the healthy 20% target.")
        if metrics.essential_ratio > 50.0:
            reasons.append(f"Essential living costs consume {metrics.essential_ratio:.1f}% of income, exceeding the 50% guideline.")
        if metrics.non_essential_ratio > 30.0:
            reasons.append(f"Discretionary spending is elevated at {metrics.non_essential_ratio:.1f}% of income.")
        if metrics.expense_to_income_ratio > 90.0:
            reasons.append(f"Total expenses represent {metrics.expense_to_income_ratio:.1f}% of your income, leaving little financial cushion.")

        if not reasons:
            reasons.append("Your score is well-balanced across metrics with room for incremental savings optimization.")

        response_text = (
            f"Your score is {hs.score}/100 (Grade {hs.grade}, '{hs.status}'). The primary factor(s) impacting your score:\n• "
            + "\n• ".join(reasons)
        )
        return CopilotResponse(
            response=response_text,
            actions=analysis.actions[:3],
            sources=["health_score", "summary"],
        )

    # 7. Budget Status Intent
    if any(phrase in query for phrase in [
        "within my budget", "am i within budget", "budget status", "how is my budget",
        "over budget", "under budget", "budget summary", "check budget", "spending limit"
    ]):
        bs = analysis.budget_summary
        if bs and bs.categories:
            status_lines = []
            for c in bs.categories:
                status_lines.append(
                    f"• {c.category}: spent {_format_currency(c.actual)} of {_format_currency(c.budget)} "
                    f"({c.utilization_percentage:.1f}% - {c.status.replace('_', ' ')})"
                )
            overspent_str = (
                f" Over-budget categories: {', '.join(bs.overspent_categories)}."
                if bs.overspent_categories else " Great job! All budgeted categories are within limits."
            )
            response_text = (
                f"You have allocated a total budget of {_format_currency(bs.total_budget)}, "
                f"with {_format_currency(bs.total_actual)} spent so far ({bs.overall_utilization_percentage:.1f}% utilized).{overspent_str}\n\n"
                + "\n".join(status_lines)
            )
            relevant_actions = [a for a in analysis.actions if a.action_type == "set_or_adjust_budget"]
            return CopilotResponse(
                response=response_text,
                actions=relevant_actions,
                sources=["budget_summary"],
            )
        else:
            return CopilotResponse(
                response=(
                    "You have not configured any category budgets yet. "
                    "Setting monthly budgets for categories like Food, Shopping, and Transport will allow you to track utilization and prevent overspending."
                ),
                actions=[a for a in analysis.actions if a.action_type == "set_or_adjust_budget"],
                sources=["budget_summary"],
            )

    # 8. What Should I Do / Action Recommendations Intent
    if any(phrase in query for phrase in [
        "what should i do", "what actions", "how can i improve", "what should i fix",
        "what to do this month", "recommendations", "next steps", "action plan",
        "what should i do this month", "give me advice"
    ]):
        if analysis.actions:
            action_lines = []
            for idx, a in enumerate(analysis.actions, 1):
                impact_str = f" [est. monthly impact: {_format_currency(a.estimated_monthly_impact)}]" if a.estimated_monthly_impact else ""
                action_lines.append(f"{idx}. {a.title} ({a.priority.upper()} priority){impact_str}\n   {a.description}")
            response_text = (
                f"Based on your transaction analysis, here are your top {len(analysis.actions)} recommended actions:\n\n"
                + "\n\n".join(action_lines)
            )
            return CopilotResponse(
                response=response_text,
                actions=analysis.actions,
                sources=["actions"],
            )
        else:
            return CopilotResponse(
                response="Your finances look stable! Continue monitoring weekly spending to maintain healthy savings consistency.",
                actions=[],
                sources=["actions"],
            )

    # 9. What Increased My Spending / Spending Drivers Intent
    if any(phrase in query for phrase in [
        "what increased my spending", "why did my spending increase",
        "spending increase", "what drove my spending", "why are my expenses high",
        "where did my money go", "drivers of spending"
    ]):
        top_cats = sorted(analysis.category_spending.items(), key=lambda x: x[1], reverse=True)[:2]
        drivers = [f"{cat}: {_format_currency(amt)}" for cat, amt in top_cats]
        anomaly_note = ""
        if analysis.anomalies:
            top_anom = analysis.anomalies[0]
            anomaly_note = f" Additionally, an unusual spending spike was detected: {top_anom.description} ({_format_currency(top_anom.amount)})."

        response_text = (
            f"Your expenses were primarily driven by {', '.join(drivers)}.{anomaly_note} "
            f"Non-essential discretionary items account for {analysis.essential_vs_non_essential.non_essential_percentage:.1f}% of total spending."
        )
        return CopilotResponse(
            response=response_text,
            actions=[a for a in analysis.actions if a.action_type in {"reduce_category_spending", "review_anomaly"}],
            sources=["category_spending", "anomalies", "essential_vs_non_essential"],
        )

    # 10. How Much Am I Saving / Savings Status Intent
    if any(phrase in query for phrase in [
        "how much am i saving", "how much did i save", "what is my savings",
        "my savings rate", "current savings", "how much savings", "cash flow", "net savings"
    ]):
        s = analysis.summary
        response_text = (
            f"Over the analyzed period, your total income was {_format_currency(s.total_income)} "
            f"and total expenses were {_format_currency(s.total_expenses)}, resulting in net savings of {_format_currency(s.net_savings)} "
            f"(a savings rate of {s.savings_rate:.1f}%)."
        )
        relevant_actions = [a for a in analysis.actions if a.action_type == "increase_savings"]
        return CopilotResponse(
            response=response_text,
            actions=relevant_actions,
            sources=["summary"],
        )

    # Fallback for Unknown / Unsupported Questions
    return CopilotResponse(
        response=(
            "I can help you understand your spending, savings, financial health score, unusual transactions, subscriptions, budgets, and recommended actions. "
            "Try asking: 'Where am I spending the most?', 'How can I save more?', 'What unusual spending did you detect?', or 'Am I within my budget?'"
        ),
        actions=[],
        sources=[],
    )


def ask_copilot(query: str, transactions: List[Transaction]) -> Dict[str, Any]:
    """
    Backward-compatible entry point for asking the copilot with raw transactions.
    """
    from backend.services.analytics import generate_basic_analysis
    if not transactions:
        return {
            "query": query,
            "response": "No transactions provided. Please upload transactions to begin.",
            "status": "empty",
            "actions": [],
            "sources": [],
        }

    analysis = generate_basic_analysis(transactions)
    result = generate_copilot_response(query, analysis)
    return {
        "query": query,
        "response": result.response,
        "status": "success",
        "actions": [a.model_dump() for a in result.actions],
        "sources": result.sources,
    }
