"""
Tests for AI Financial Copilot service and endpoint.
Validates explainability, deterministic intent matching, validation, and privacy.
"""

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.main import app, get_current_analysis, set_current_analysis
from backend.schemas.analysis import (
    ActionItem,
    AnalysisResponse,
    AnomalyItem,
    CategoryBudgetStatus,
    BudgetSummary,
    CashFlowSummary,
    CategoryBreakdown,
    CopilotRequest,
    CopilotResponse,
    DateRange,
    EssentialVsNonEssential,
    HealthScoreBreakdown,
    HealthScoreMetrics,
    HealthScoreResponse,
    MonthlyTrend,
    SubscriptionItem,
)
from backend.schemas.transaction import Transaction, TransactionType
from backend.services.ai_copilot import generate_copilot_response, ask_copilot
from backend.services.analytics import generate_basic_analysis


@pytest.fixture
def synthetic_analysis() -> AnalysisResponse:
    """Creates a deterministic synthetic AnalysisResponse for testing."""
    return AnalysisResponse(
        summary=CashFlowSummary(
            total_income=5000.0,
            total_expenses=3200.0,
            net_savings=1800.0,
            savings_rate=36.0,
        ),
        category_spending={
            "Rent": 1500.0,
            "Food": 800.0,
            "Shopping": 400.0,
            "Entertainment": 300.0,
            "Bills & Utilities": 200.0,
        },
        category_percentages={
            "Rent": 46.9,
            "Food": 25.0,
            "Shopping": 12.5,
            "Entertainment": 9.4,
            "Bills & Utilities": 6.2,
        },
        category_breakdown=[
            CategoryBreakdown(category="Rent", total_amount=1500.0, percentage=46.9, transaction_count=1),
            CategoryBreakdown(category="Food", total_amount=800.0, percentage=25.0, transaction_count=5),
            CategoryBreakdown(category="Shopping", total_amount=400.0, percentage=12.5, transaction_count=2),
            CategoryBreakdown(category="Entertainment", total_amount=300.0, percentage=9.4, transaction_count=3),
            CategoryBreakdown(category="Bills & Utilities", total_amount=200.0, percentage=6.2, transaction_count=1),
        ],
        top_spending_categories=[
            CategoryBreakdown(category="Rent", total_amount=1500.0, percentage=46.9, transaction_count=1),
            CategoryBreakdown(category="Food", total_amount=800.0, percentage=25.0, transaction_count=5),
            CategoryBreakdown(category="Shopping", total_amount=400.0, percentage=12.5, transaction_count=2),
        ],
        monthly_trends=[
            MonthlyTrend(month="2026-01", income=5000.0, expenses=3200.0, savings=1800.0)
        ],
        essential_vs_non_essential=EssentialVsNonEssential(
            essential_spending=2000.0,
            non_essential_spending=1200.0,
            essential_percentage=62.5,
            non_essential_percentage=37.5,
            essential_categories={"Rent": 1500.0, "Bills & Utilities": 200.0},
            non_essential_categories={"Food": 800.0, "Shopping": 400.0, "Entertainment": 300.0},
        ),
        health_score=HealthScoreResponse(
            score=82,
            grade="B",
            status="Good",
            breakdown=HealthScoreBreakdown(
                savings_score=40.0,
                essential_spending_score=25.0,
                living_within_means_score=17.0,
            ),
            metrics=HealthScoreMetrics(
                savings_rate=36.0,
                essential_ratio=40.0,
                non_essential_ratio=24.0,
                expense_to_income_ratio=64.0,
            ),
            insights=["Strong savings rate above 20%."],
        ),
        anomalies=[
            AnomalyItem(
                date="2026-01-15",
                description="Luxury Watch Store",
                amount=350.0,
                category="Shopping",
                reason="Expense of $350.00 is 2.5x higher than average",
                severity="medium",
            )
        ],
        subscriptions=[
            SubscriptionItem(
                description="Netflix Subscription",
                amount=15.99,
                category="Entertainment",
                frequency="Monthly",
                occurrences=3,
                estimated_monthly_cost=15.99,
            )
        ],
        budget_summary=BudgetSummary(
            total_budget=3000.0,
            total_actual=3200.0,
            overall_utilization_percentage=106.7,
            overspent_categories=["Food"],
            categories=[
                CategoryBudgetStatus(
                    category="Food",
                    budget=600.0,
                    actual=800.0,
                    remaining=-200.0,
                    utilization_percentage=133.3,
                    status="over_budget",
                )
            ],
        ),
        actions=[
            ActionItem(
                title="Review Food Spending",
                description="Trimming Food expenses could save $120.00 monthly.",
                reason="Food spending at $800.00 exceeds 25% of total expenses.",
                category="Food",
                priority="high",
                estimated_monthly_impact=120.0,
                action_type="reduce_category_spending",
            ),
            ActionItem(
                title="Audit Recurring Subscriptions",
                description="Review Netflix Subscription ($15.99/mo).",
                reason="Active subscription detected: Netflix Subscription.",
                category="Entertainment",
                priority="low",
                estimated_monthly_impact=15.99,
                action_type="review_subscription",
            ),
            ActionItem(
                title="Review Unusual Spending Flag",
                description="Verify Luxury Watch Store ($350.00).",
                reason="Transaction flagged as anomaly (medium severity).",
                category="Shopping",
                priority="medium",
                estimated_monthly_impact=350.0,
                action_type="review_anomaly",
            ),
        ],
        total_transactions=12,
        date_range=DateRange(start_date="2026-01-01", end_date="2026-01-31"),
    )


# 1. Empty message validation
def test_empty_message_validation(synthetic_analysis: AnalysisResponse):
    with pytest.raises(ValidationError):
        CopilotRequest(message="")

    with pytest.raises(ValidationError):
        CopilotRequest(message="   ")

    with pytest.raises(ValidationError):
        CopilotRequest(message="a" * 501)

    # Empty string directly to generate_copilot_response
    res = generate_copilot_response("", synthetic_analysis)
    assert "valid" in res.response.lower()
    assert res.actions == []


# 2. Highest spending category question
def test_highest_spending_category_question(synthetic_analysis: AnalysisResponse):
    queries = [
        "Where am I spending the most?",
        "where am i spending",
        "highest spending category",
        "what is my top spending",
    ]
    for q in queries:
        res = generate_copilot_response(q, synthetic_analysis)
        assert "Rent" in res.response
        assert "$1,500.00" in res.response
        assert "category_spending" in res.sources
        assert isinstance(res.actions, list)


# 3. Savings improvement question
def test_savings_improvement_question(synthetic_analysis: AnalysisResponse):
    queries = [
        "How can I save more?",
        "how to save money",
        "increase my savings",
        "ways to save",
    ]
    for q in queries:
        res = generate_copilot_response(q, synthetic_analysis)
        assert "savings" in res.response.lower()
        assert "summary" in res.sources
        assert len(res.actions) > 0


# 4. Anomaly question
def test_anomaly_question(synthetic_analysis: AnalysisResponse):
    res = generate_copilot_response("What unusual spending did you detect?", synthetic_analysis)
    assert "Luxury Watch Store" in res.response
    assert "$350.00" in res.response
    assert "anomalies" in res.sources
    assert any(a.action_type == "review_anomaly" for a in res.actions)

    # When no anomalies exist
    synthetic_analysis.anomalies = []
    res_none = generate_copilot_response("What unusual spending did you detect?", synthetic_analysis)
    assert "no unusual" in res_none.response.lower()
    assert "anomalies" in res_none.sources


# 5. Subscription question
def test_subscription_question(synthetic_analysis: AnalysisResponse):
    res = generate_copilot_response("Which subscriptions should I review?", synthetic_analysis)
    assert "Netflix Subscription" in res.response
    assert "$15.99" in res.response
    assert "subscriptions" in res.sources
    assert any(a.action_type == "review_subscription" for a in res.actions)

    # When no subscriptions exist
    synthetic_analysis.subscriptions = []
    res_none = generate_copilot_response("Which subscriptions should I review?", synthetic_analysis)
    assert "no recurring subscriptions" in res_none.response.lower()


# 6. Health score explanation & why score is low
def test_health_score_explanation(synthetic_analysis: AnalysisResponse):
    # Score calculation breakdown
    res_calc = generate_copilot_response("How is my financial health score calculated?", synthetic_analysis)
    assert "82/100" in res_calc.response
    assert "Savings Rate" in res_calc.response
    assert "Needs vs. Wants" in res_calc.response
    assert "Living Within Means" in res_calc.response
    assert "health_score" in res_calc.sources

    # Why score is low
    res_low = generate_copilot_response("Why is my financial health score low?", synthetic_analysis)
    assert "82/100" in res_low.response
    assert "health_score" in res_low.sources


# 7. Budget question
def test_budget_question(synthetic_analysis: AnalysisResponse):
    res = generate_copilot_response("Am I within my budget?", synthetic_analysis)
    assert "Food" in res.response
    assert "budget_summary" in res.sources

    # When no budget configured
    synthetic_analysis.budget_summary = BudgetSummary()
    res_none = generate_copilot_response("Am I within my budget?", synthetic_analysis)
    assert "not configured" in res_none.response.lower()


# 8. Action-related question
def test_action_related_question(synthetic_analysis: AnalysisResponse):
    queries = [
        "What should I do this month?",
        "what should i do",
        "what actions do you recommend",
    ]
    for q in queries:
        res = generate_copilot_response(q, synthetic_analysis)
        assert len(res.actions) > 0
        assert "actions" in res.sources
        assert "recommended actions" in res.response.lower()


# 9. Unknown question
def test_unknown_question(synthetic_analysis: AnalysisResponse):
    res = generate_copilot_response("What is the capital of France?", synthetic_analysis)
    assert "I can help you understand your spending" in res.response
    assert res.actions == []
    assert res.sources == []


# 10. Missing analysis data
def test_missing_analysis_data():
    res = generate_copilot_response("Where am I spending the most?", analysis=None)
    assert "unavailable" in res.response.lower()
    assert res.actions == []
    assert res.sources == []

    # Empty analysis with 0 transactions
    empty_analysis = AnalysisResponse(
        summary=CashFlowSummary(
            total_income=0.0,
            total_expenses=0.0,
            net_savings=0.0,
            savings_rate=0.0,
        ),
        category_spending={},
        category_percentages={},
        category_breakdown=[],
        top_spending_categories=[],
        monthly_trends=[],
        essential_vs_non_essential=EssentialVsNonEssential(
            essential_spending=0.0,
            non_essential_spending=0.0,
            essential_percentage=0.0,
            non_essential_percentage=0.0,
        ),
        health_score=HealthScoreResponse(
            score=0,
            grade="N/A",
            status="Insufficient Data",
            breakdown=HealthScoreBreakdown(
                savings_score=0.0,
                essential_spending_score=0.0,
                living_within_means_score=0.0,
            ),
            metrics=HealthScoreMetrics(
                savings_rate=0.0,
                essential_ratio=0.0,
                non_essential_ratio=0.0,
                expense_to_income_ratio=0.0,
            ),
            insights=[],
        ),
        total_transactions=0,
        date_range=DateRange(),
    )
    res_empty = generate_copilot_response("Where am I spending the most?", empty_analysis)
    assert "unavailable" in res_empty.response.lower()


# 11. API endpoint success
def test_api_endpoint_success(synthetic_analysis: AnalysisResponse):
    client = TestClient(app)
    response = client.post(
        "/api/copilot/chat",
        json={
            "message": "Where am I spending the most?",
            "analysis": synthetic_analysis.model_dump(),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "actions" in data
    assert "sources" in data
    assert isinstance(data["actions"], list)
    assert isinstance(data["sources"], list)
    assert len(data["response"]) > 0
    assert "Rent" in data["response"]


# 11b. Context flow across analyze endpoints and copilot chat
def test_copilot_context_flow(synthetic_analysis: AnalysisResponse):
    client = TestClient(app)

    # A. Missing context gives a safe response
    set_current_analysis(None)
    res_missing = client.post("/api/copilot/chat", json={"message": "Where am I spending the most?"})
    assert res_missing.status_code == 200
    data_missing = res_missing.json()
    assert "unavailable" in data_missing["response"].lower()
    assert data_missing["actions"] == []
    assert data_missing["sources"] == []

    # B. /api/sample/analyze updates the latest analysis context
    res_sample = client.get("/api/sample/analyze")
    assert res_sample.status_code == 200
    sample_analysis = get_current_analysis()
    assert sample_analysis is not None
    assert sample_analysis.total_transactions > 0

    # Copilot chat without explicit payload uses the latest analysis
    res_sample_chat = client.post("/api/copilot/chat", json={"message": "Where am I spending the most?"})
    assert res_sample_chat.status_code == 200
    data_sample_chat = res_sample_chat.json()
    assert "Rent" in data_sample_chat["response"]
    assert "category_spending" in data_sample_chat["sources"]

    # C. /api/analyze updates the latest analysis context
    analyze_payload = {
        "transactions": [
            {"date": "2026-03-01", "description": "Salary", "amount": 10000.0, "type": "income", "category": "Income"},
            {"date": "2026-03-02", "description": "Tuition Fee", "amount": 4000.0, "type": "expense", "category": "Education"},
        ]
    }
    res_analyze = client.post("/api/analyze", json=analyze_payload)
    assert res_analyze.status_code == 200
    updated_analysis = get_current_analysis()
    assert updated_analysis is not None
    assert "Education" in updated_analysis.category_spending

    res_analyze_chat = client.post("/api/copilot/chat", json={"message": "Where am I spending the most?"})
    assert res_analyze_chat.status_code == 200
    assert "Education" in res_analyze_chat.json()["response"]

    # D. /api/analyze-csv updates the latest analysis context
    csv_bytes = (
        b"date,description,amount,type\n"
        b"2026-04-01,Monthly Salary,8000,income\n"
        b"2026-04-05,Medical Clinic,3500,expense\n"
    )
    files = {"file": ("clinic.csv", csv_bytes, "text/csv")}
    res_csv = client.post("/api/analyze-csv", files=files)
    assert res_csv.status_code == 200
    csv_analysis = get_current_analysis()
    assert csv_analysis is not None
    assert "Healthcare" in csv_analysis.category_spending

    res_csv_chat = client.post("/api/copilot/chat", json={"message": "Where am I spending the most?"})
    assert res_csv_chat.status_code == 200
    assert "Healthcare" in res_csv_chat.json()["response"]

    # E. Explicit analysis payload takes priority over cached analysis
    res_explicit = client.post(
        "/api/copilot/chat",
        json={
            "message": "Where am I spending the most?",
            "analysis": synthetic_analysis.model_dump(),
        },
    )
    assert res_explicit.status_code == 200
    # In synthetic_analysis, top category is Rent (overrides Healthcare)
    assert "Rent" in res_explicit.json()["response"]


# 12. API endpoint validation and error handling
def test_api_endpoint_validation_and_error_handling():
    client = TestClient(app)

    # Empty string
    res_empty = client.post("/api/copilot/chat", json={"message": ""})
    assert res_empty.status_code == 422

    # Whitespace only
    res_spaces = client.post("/api/copilot/chat", json={"message": "   "})
    assert res_spaces.status_code == 422

    # Missing message field
    res_missing = client.post("/api/copilot/chat", json={})
    assert res_missing.status_code == 422

    # Exceeding maximum length (501 characters)
    res_too_long = client.post("/api/copilot/chat", json={"message": "x" * 501})
    assert res_too_long.status_code == 422


# Backward-compatible helper test
def test_ask_copilot_backward_compatibility():
    txs = [
        Transaction(date="2026-01-10", description="Salary", amount=4000.0, type=TransactionType.INCOME),
        Transaction(date="2026-01-12", description="Groceries Store", amount=250.0, type=TransactionType.EXPENSE),
    ]
    res = ask_copilot("Where am I spending the most?", txs)
    assert res["status"] == "success"
    assert "response" in res
    assert "actions" in res
    assert "sources" in res
