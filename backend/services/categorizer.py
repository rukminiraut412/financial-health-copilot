"""
Rule-based transaction categorizer matching merchant names and descriptions.
"""

import re
from typing import Dict, List, Optional
import pandas as pd
from backend.schemas.transaction import TransactionCategory, TransactionType


# Categorization keyword dictionary
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    TransactionCategory.INCOME.value: [
        "salary", "payroll", "paycheck", "freelance", "dividend", "interest",
        "stipend", "bonus", "commission", "wage", "refund", "reimbursement",
        "cashback", "consulting income", "direct deposit"
    ],
    TransactionCategory.HOUSING_RENT.value: [
        "rent", "mortgage", "apartment", "lease", "property tax", "hoa",
        "maintenance fee", "housing", "landlord", "condo"
    ],
    TransactionCategory.GROCERIES.value: [
        "grocery", "groceries", "supermarket", "whole foods", "trader joe",
        "walmart", "costco", "safeway", "aldi", "kroger", "fresh produce",
        "fresh mart", "food mart", "butcher", "produce market", "sprouts"
    ],
    TransactionCategory.DINING_FOOD.value: [
        "restaurant", "cafe", "coffee", "starbucks", "mcdonald", "burger",
        "pizza", "bistro", "diner", "bakery", "subway sandwich", "takeout",
        "ubereats", "doordash", "zomato", "swiggy", "grill", "bar & grill",
        "taco", "chipotle", "dunkin", "panera", "sushi", "trattoria"
    ],
    TransactionCategory.TRANSPORTATION.value: [
        "uber", "lyft", "taxi", "gas station", "shell", "chevron", "bp gas",
        "exxon", "fuel", "petrol", "metro", "subway pass", "transit pass",
        "train ticket", "bus fare", "parking", "toll", "speedway"
    ],
    TransactionCategory.UTILITIES.value: [
        "electric", "power co", "water utility", "gas bill", "utility",
        "internet", "wifi", "broadband", "at&t", "verizon", "t-mobile",
        "telecom", "comcast", "xfinity", "sewage", "trash"
    ],
    TransactionCategory.ENTERTAINMENT.value: [
        "netflix", "spotify", "hulu", "disney", "hbo", "cinema", "movie theater",
        "steam", "playstation", "xbox", "nintendo", "twitch", "concert",
        "tickets", "game purchase", "audible"
    ],
    TransactionCategory.SHOPPING.value: [
        "amazon", "ebay", "target", "clothing", "apparel", "zara", "h&m",
        "nike", "adidas", "best buy", "electronics", "department store",
        "shoes", "fashion", "ikea", "home depot"
    ],
    TransactionCategory.HEALTHCARE.value: [
        "pharmacy", "prescription", "doctor", "hospital", "clinic", "dental",
        "dentist", "medical", "medicine", "health", "cvs", "walgreens",
        "laboratory", "optometry", "vision care"
    ],
    TransactionCategory.SUBSCRIPTIONS.value: [
        "gym", "fitness", "membership", "icloud", "cloud storage", "dropbox",
        "google one", "prime membership", "patreon", "subscription"
    ],
    TransactionCategory.INVESTMENTS_SAVINGS.value: [
        "investment", "401k", "roth", "ira", "vanguard", "fidelity",
        "charles schwab", "stocks", "mutual fund", "crypto", "robinhood",
        "emergency fund", "savings deposit"
    ],
    TransactionCategory.PERSONAL_CARE.value: [
        "salon", "haircut", "barber", "spa", "cosmetics", "skincare", "beauty"
    ],
    TransactionCategory.EDUCATION.value: [
        "tuition", "course", "udemy", "coursera", "school", "university",
        "college", "textbook", "books"
    ],
    TransactionCategory.TRAVEL.value: [
        "airline", "flight", "hotel", "airbnb", "booking.com", "expedia",
        "hostel", "car rental", "delta", "united airlines", "american airlines"
    ],
}


def categorize_transaction(description: str, tx_type: str = "expense") -> str:
    """
    Categorizes a transaction based on description keywords and transaction type.
    """
    cleaned_desc = description.strip().lower() if description else ""

    # If marked as income, default to Income unless a specific investment keyword applies
    if tx_type.strip().lower() in [TransactionType.INCOME.value, "credit", "deposit", "inflow"]:
        for kw in CATEGORY_KEYWORDS[TransactionCategory.INVESTMENTS_SAVINGS.value]:
            if kw in cleaned_desc:
                return TransactionCategory.INVESTMENTS_SAVINGS.value
        return TransactionCategory.INCOME.value

    # Evaluate categories based on priority
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == TransactionCategory.INCOME.value:
            continue

        for kw in keywords:
            # Word boundary regex matching to avoid false positives on small words
            if len(kw) <= 4:
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, cleaned_desc):
                    return category
            else:
                if kw in cleaned_desc:
                    return category

    return TransactionCategory.MISCELLANEOUS.value


def categorize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches a transaction DataFrame with a 'category' column if not present or empty.
    """
    df_copy = df.copy()

    if "category" not in df_copy.columns:
        df_copy["category"] = None

    categories = []
    for _, row in df_copy.iterrows():
        existing_cat = row.get("category")
        if pd.notna(existing_cat) and str(existing_cat).strip() != "":
            categories.append(str(existing_cat).strip())
        else:
            desc = str(row.get("description", ""))
            tx_type = str(row.get("type", "expense"))
            cat = categorize_transaction(desc, tx_type)
            categories.append(cat)

    df_copy["category"] = categories
    return df_copy


def get_all_categories() -> List[str]:
    """
    Returns list of all recognized categories.
    """
    return [c.value for c in TransactionCategory]


def get_category_rules() -> Dict[str, List[str]]:
    """
    Returns the keyword rules dictionary.
    """
    return CATEGORY_KEYWORDS
