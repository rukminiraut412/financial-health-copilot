"""
Tests for FastAPI API endpoints.
Tests GET /health, POST /api/analyze (including anomalies, subscriptions, and budgets),
POST /api/analyze-csv, and GET /api/sample/analyze.
"""

import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "financial-health-copilot"

    # API alias check
    api_health = client.get("/api/health")
    assert api_health.status_code == 200
    assert api_health.json()["status"] == "healthy"


def test_post_analyze_endpoint_with_new_mvp_features(client):
    payload = {
        "transactions": [
            {"date": "2026-07-01", "description": "Salary", "amount": 40000, "type": "income", "category": "Income"},
            {"date": "2026-07-02", "description": "Rent", "amount": 15000, "type": "expense", "category": "Rent"},
            {"date": "2026-07-05", "description": "Food Groceries", "amount": 5000, "type": "expense", "category": "Food"},
            {"date": "2026-07-10", "description": "Netflix Subscription", "amount": 15.99, "type": "expense", "category": "Entertainment"},
            {"date": "2026-08-01", "description": "Salary", "amount": 45000, "type": "income", "category": "Income"},
            {"date": "2026-08-02", "description": "Rent", "amount": 15000, "type": "expense", "category": "Rent"},
            {"date": "2026-08-10", "description": "Netflix Subscription", "amount": 15.99, "type": "expense", "category": "Entertainment"},
            {"date": "2026-08-15", "description": "Surprise Luxury Feast", "amount": 4500, "type": "expense", "category": "Food"},
        ],
        "budgets": {
            "Food": 8000.0,
            "Rent": 35000.0,
            "Entertainment": 100.0,
        }
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Cash flow summary
    assert data["summary"]["total_income"] == 85000.0
    assert "total_expenses" in data["summary"]
    assert "net_savings" in data["summary"]

    # Category spending and percentages
    assert "category_spending" in data
    assert data["category_spending"]["Rent"] == 30000.0
    assert "category_percentages" in data

    # Monthly trends
    assert len(data["monthly_trends"]) == 2
    assert data["monthly_trends"][0]["month"] == "2026-07"
    assert "expenses" in data["monthly_trends"][0]
    assert "savings" in data["monthly_trends"][0]

    # Essential vs non-essential
    assert "essential_vs_non_essential" in data
    assert "essential_spending" in data["essential_vs_non_essential"]

    # Financial health score
    assert "health_score" in data
    assert 0 <= data["health_score"]["score"] <= 100

    # Anomalies
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)

    # Subscriptions
    assert "subscriptions" in data
    assert isinstance(data["subscriptions"], list)
    assert any("netflix" in s["description"].lower() for s in data["subscriptions"])

    # Budget summary
    assert "budget_summary" in data
    bs = data["budget_summary"]
    assert bs["total_budget"] == 43100.0
    assert len(bs["categories"]) == 3
    cat_names = [c["category"] for c in bs["categories"]]
    assert "Food" in cat_names
    assert "Rent" in cat_names
    assert "Entertainment" in cat_names


def test_post_analyze_empty_transactions(client):
    response = client.post("/api/analyze", json={"transactions": []})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_post_analyze_csv_endpoint(client):
    csv_bytes = (
        b"date,description,amount,type\n"
        b"2026-09-01,Monthly Salary,50000,income\n"
        b"2026-09-02,Apartment Rent,15000,expense\n"
        b"2026-09-05,Whole Foods Groceries,1200,expense\n"
        b"2026-09-08,Netflix Monthly Subscription,15.99,expense\n"
    )
    files = {"file": ("test_transactions.csv", io.BytesIO(csv_bytes), "text/csv")}
    response = client.post("/api/analyze-csv", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["summary"]["total_income"] == 50000.0
    assert "Rent" in data["category_spending"]
    assert "health_score" in data
    assert "anomalies" in data
    assert "subscriptions" in data
    assert "budget_summary" in data


def test_post_analyze_csv_invalid_file(client):
    files = {"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")}
    response = client.post("/api/analyze-csv", files=files)
    assert response.status_code == 400
    assert "valid csv" in response.json()["detail"].lower()


def test_get_sample_analyze_endpoint(client):
    response = client.get("/api/sample/analyze")
    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    assert data["summary"]["total_income"] > 0
    assert data["summary"]["total_expenses"] > 0
    assert "category_spending" in data
    assert "monthly_trends" in data
    assert "essential_vs_non_essential" in data
    assert "health_score" in data
    assert 0 <= data["health_score"]["score"] <= 100
    assert "anomalies" in data
    assert "subscriptions" in data
    assert "budget_summary" in data
