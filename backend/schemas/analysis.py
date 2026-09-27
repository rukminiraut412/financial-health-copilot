"""
Analysis schemas and data models using Pydantic.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from backend.schemas.transaction import Transaction


class CategoryBreakdown(BaseModel):
    category: str = Field(..., description="Category label")
    total_amount: float = Field(..., description="Total spent or allocated in category")
    percentage: float = Field(..., description="Percentage of total expense (0 - 100)")
    transaction_count: int = Field(..., description="Number of transactions in category")


class CashFlowSummary(BaseModel):
    total_income: float = Field(..., description="Total aggregated income")
    total_expenses: float = Field(..., description="Total aggregated expenses")
    net_savings: float = Field(..., description="Net savings (income minus expenses)")
    savings_rate: float = Field(..., description="Savings rate as percentage of income (0 - 100)")


class MonthlyTrend(BaseModel):
    month: str = Field(..., description="Year and month (YYYY-MM)")
    income: float = Field(..., description="Total income for the month")
    expenses: float = Field(..., description="Total expenses for the month")
    savings: float = Field(..., description="Net flow/savings for the month (income minus expenses)")
    # Backwards-compatible aliases
    expense: Optional[float] = Field(None, description="Alias for expenses")
    net: Optional[float] = Field(None, description="Alias for savings")


class EssentialVsNonEssential(BaseModel):
    essential_spending: float = Field(..., description="Total amount spent on essential categories")
    non_essential_spending: float = Field(..., description="Total amount spent on non-essential categories")
    essential_percentage: float = Field(..., description="Percentage of expenses allocated to essential needs")
    non_essential_percentage: float = Field(..., description="Percentage of expenses allocated to non-essential wants")
    essential_categories: Dict[str, float] = Field(default_factory=dict, description="Breakdown of essential spending by category")
    non_essential_categories: Dict[str, float] = Field(default_factory=dict, description="Breakdown of non-essential spending by category")


class HealthScoreBreakdown(BaseModel):
    savings_score: float = Field(..., description="Score component from savings rate (up to 40)")
    essential_spending_score: float = Field(..., description="Score component from needs/wants balance (up to 35)")
    living_within_means_score: float = Field(..., description="Score component from expense-to-income ratio (up to 25)")


class HealthScoreMetrics(BaseModel):
    savings_rate: float = Field(..., description="Net savings as percentage of income")
    essential_ratio: float = Field(..., description="Essential spending as percentage of income")
    non_essential_ratio: float = Field(..., description="Non-essential spending as percentage of income")
    expense_to_income_ratio: float = Field(..., description="Total expenses as percentage of income")


class HealthScoreResponse(BaseModel):
    score: int = Field(..., description="Overall health score (0 - 100)")
    grade: str = Field(..., description="Grade (A, B, C, D, or F)")
    status: str = Field(..., description="Status description (e.g. Excellent, Good, Fair, Needs Attention)")
    breakdown: Optional[HealthScoreBreakdown] = None
    metrics: Optional[HealthScoreMetrics] = None
    insights: List[str] = Field(default_factory=list, description="Actionable observations and tips")


class DateRange(BaseModel):
    start_date: Optional[str] = Field(None, description="Earliest transaction date")
    end_date: Optional[str] = Field(None, description="Latest transaction date")


class AnalysisRequest(BaseModel):
    transactions: List[Transaction] = Field(..., description="List of transactions to analyze")


class AnalysisResponse(BaseModel):
    summary: CashFlowSummary
    category_spending: Dict[str, float] = Field(default_factory=dict, description="Clean map of category to total spent")
    category_percentages: Dict[str, float] = Field(default_factory=dict, description="Clean map of category to percentage of total spent")
    category_breakdown: List[CategoryBreakdown]
    top_spending_categories: List[CategoryBreakdown]
    monthly_trends: List[MonthlyTrend]
    essential_vs_non_essential: EssentialVsNonEssential
    health_score: HealthScoreResponse
    total_transactions: int
    date_range: DateRange
