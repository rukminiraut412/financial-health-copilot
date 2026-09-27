"""
Transaction schemas and data models using Pydantic.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionCategory(str, Enum):
    INCOME = "Income"
    HOUSING_RENT = "Housing & Rent"
    GROCERIES = "Groceries"
    DINING_FOOD = "Dining & Food"
    TRANSPORTATION = "Transportation"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    HEALTHCARE = "Healthcare"
    SUBSCRIPTIONS = "Subscriptions"
    INVESTMENTS_SAVINGS = "Investments & Savings"
    PERSONAL_CARE = "Personal Care"
    EDUCATION = "Education"
    TRAVEL = "Travel"
    MISCELLANEOUS = "Miscellaneous"


class TransactionBase(BaseModel):
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format", examples=["2026-09-01"])
    description: str = Field(..., description="Merchant or transaction description", examples=["Trader Joes Groceries"])
    amount: float = Field(..., ge=0.0, description="Transaction amount (positive value)", examples=[124.50])
    type: str = Field(..., description="Transaction type: 'income' or 'expense'", examples=["expense"])

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ["income", "credit", "deposit", "inflow"]:
                return TransactionType.INCOME.value
            return TransactionType.EXPENSE.value
        return TransactionType.EXPENSE.value


class TransactionCreate(TransactionBase):
    category: Optional[str] = Field(None, description="Optional pre-assigned category")


class Transaction(TransactionBase):
    id: Optional[str] = Field(None, description="Unique transaction identifier")
    category: str = Field(default=TransactionCategory.MISCELLANEOUS.value, description="Categorized bucket")
    is_recurring: Optional[bool] = Field(default=False, description="Flag for recurring/subscription charge")


class TransactionUploadResponse(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int
    transactions: List[Transaction]
    errors: List[str] = Field(default_factory=list)
