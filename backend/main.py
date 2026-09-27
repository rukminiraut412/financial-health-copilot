"""
Financial Health Copilot - Main FastAPI Application.
Handles transaction ingestion, automated categorization, and cash flow analysis.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is present in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    CopilotRequest,
    CopilotResponse,
)
from backend.schemas.transaction import (
    Transaction,
    TransactionCategory,
    TransactionUploadResponse,
)
from backend.services.ai_copilot import generate_copilot_response
from backend.services.analytics import generate_basic_analysis
from backend.services.categorizer import get_all_categories, get_category_rules
from backend.services.transaction_processor import parse_csv_file


app = FastAPI(
    title="Financial Health Copilot API",
    description="API for transforming raw financial transactions into categorized analytics and actionable health insights.",
    version="1.0.0",
)

# CORS configuration for seamless frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for latest financial analysis context
LATEST_ANALYSIS: Optional[AnalysisResponse] = None


def get_current_analysis() -> Optional[AnalysisResponse]:
    """Retrieves the latest analysis context stored in memory."""
    global LATEST_ANALYSIS
    return LATEST_ANALYSIS


def set_current_analysis(analysis: Optional[AnalysisResponse]) -> None:
    """Sets or clears the current analysis context stored in memory."""
    global LATEST_ANALYSIS
    LATEST_ANALYSIS = analysis


@app.get("/", summary="Root Health & Overview")
def root() -> Dict[str, Any]:
    """Root status endpoint providing API metadata."""
    return {
        "name": "Financial Health Copilot API",
        "status": "online",
        "version": "1.0.0",
        "description": "From Transaction to Action",
        "docs_url": "/docs",
        "endpoints": {
            "health": "GET /api/health",
            "upload_csv": "POST /api/upload",
            "analyze": "POST /api/analyze",
            "analyze_csv": "POST /api/analyze-csv",
            "categories": "GET /api/categories",
            "sample_data": "GET /api/sample",
            "sample_analysis": "GET /api/sample/analyze",
            "copilot_chat": "POST /api/copilot/chat",
        },
    }


@app.get("/health", summary="Service Health Check")
@app.get("/api/health", summary="API Health Check")
def health_check() -> Dict[str, str]:
    """Health check endpoint for container and uptime probes."""
    return {
        "status": "healthy",
        "service": "financial-health-copilot",
        "version": "1.0.0",
    }


@app.post(
    "/api/upload",
    response_model=TransactionUploadResponse,
    summary="Upload and Parse CSV Transactions",
)
async def upload_transactions(file: UploadFile = File(...)) -> TransactionUploadResponse:
    """
    Accepts a CSV file containing columns: date, description, amount, type.
    Parses, validates, and automatically categorizes transactions.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a CSV file with '.csv' extension.",
        )

    try:
        content = await file.read()
        transactions, errors = parse_csv_file(content)

        total_records = len(transactions) + len(errors)
        return TransactionUploadResponse(
            total_records=total_records,
            valid_records=len(transactions),
            invalid_records=len(errors),
            transactions=transactions,
            errors=errors,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the file: {str(e)}",
        )


@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    summary="Analyze Transactions JSON",
)
def analyze_transactions(payload: AnalysisRequest) -> AnalysisResponse:
    """
    Performs cash flow aggregation, spending breakdown, and trends
    from a list of transactions.
    """
    if not payload.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction list is empty. Provide at least one transaction for analysis.",
        )

    global LATEST_ANALYSIS
    result = generate_basic_analysis(payload.transactions, budgets=payload.budgets)
    LATEST_ANALYSIS = result
    return result


@app.post(
    "/api/analyze-csv",
    response_model=AnalysisResponse,
    summary="Upload CSV and Directly Return Full Analysis",
)
async def analyze_csv_direct(file: UploadFile = File(...)) -> AnalysisResponse:
    """
    Single-step convenience endpoint: uploads CSV, validates, categorizes,
    and returns full analytics response.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid CSV file.",
        )

    try:
        content = await file.read()
        transactions, errors = parse_csv_file(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred while reading or parsing the CSV file: {str(e)}",
        )

    if not transactions:
        detail = "No valid transactions could be processed from the CSV."
        if errors:
            detail += f" Errors encountered: {'; '.join(errors[:3])}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    global LATEST_ANALYSIS
    result = generate_basic_analysis(transactions)
    LATEST_ANALYSIS = result
    return result


@app.get("/api/categories", summary="List Available Categories")
def list_categories() -> Dict[str, Any]:
    """Returns all supported transaction categories and their keyword matchers."""
    return {
        "categories": get_all_categories(),
        "rules": get_category_rules(),
    }


@app.get("/api/sample", summary="Get Pre-loaded Sample Transactions")
def get_sample_transactions() -> Dict[str, Any]:
    """Returns sample transactions parsed from the bundled sample_transactions.csv."""
    sample_file = PROJECT_ROOT / "data" / "sample_transactions.csv"
    if not sample_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample data file not found.",
        )

    with open(sample_file, "rb") as f:
        transactions, errors = parse_csv_file(f.read())

    return {
        "total_records": len(transactions),
        "transactions": transactions,
        "errors": errors,
    }


@app.get("/api/sample/analyze", response_model=AnalysisResponse, summary="Get Sample Analysis")
def get_sample_analysis() -> AnalysisResponse:
    """Returns ready-to-render analytics computed on the sample dataset."""
    sample_file = PROJECT_ROOT / "data" / "sample_transactions.csv"
    if not sample_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample data file not found.",
        )

    with open(sample_file, "rb") as f:
        transactions, _ = parse_csv_file(f.read())

    global LATEST_ANALYSIS
    result = generate_basic_analysis(transactions)
    LATEST_ANALYSIS = result
    return result


@app.post(
    "/api/copilot/chat",
    response_model=CopilotResponse,
    summary="Ask AI Financial Copilot",
)
def copilot_chat(payload: CopilotRequest) -> CopilotResponse:
    """
    Accepts a user natural-language financial question and generates an
    explainable, deterministic response grounded in structured financial analysis.
    Uses explicitly provided analysis if present, or the latest cached analysis,
    or falls back to sample transaction analysis.
    """
    analysis = payload.analysis or get_current_analysis()
    return generate_copilot_response(payload.message, analysis)

