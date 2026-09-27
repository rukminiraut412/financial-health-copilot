"""
Helper functions for transaction data cleaning, date parsing, and formatting.
"""

import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
import pandas as pd


def clean_amount(val: Any) -> float:
    """
    Cleans and converts any amount value to a positive float.
    Handles currency symbols, commas, negative signs, and whitespace.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0

    if isinstance(val, (int, float)):
        return abs(float(val))

    s = str(val).strip()
    if not s:
        return 0.0

    # Remove currency symbols and common decorative characters
    cleaned = re.sub(r"[^\d.-]", "", s)

    try:
        num = float(cleaned)
        return abs(num)
    except (ValueError, TypeError):
        return 0.0


def parse_date_safe(val: Any) -> Optional[str]:
    """
    Safely parses diverse date inputs into ISO format 'YYYY-MM-DD'.
    Returns None if date parsing fails.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None

    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")

    if isinstance(val, date):
        return val.isoformat()

    s = str(val).strip()
    if not s:
        return None

    # Common date formats to try
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(s, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Attempt pandas date parsing as fallback
    try:
        ts = pd.to_datetime(s, errors="coerce")
        if pd.notna(ts):
            return ts.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None


def format_currency(amount: Union[int, float], currency_symbol: str = "₹") -> str:
    """
    Formats a numeric amount to a standard currency representation (e.g. '₹1,250.00').
    """
    try:
        val = float(amount)
        return f"{currency_symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"


def normalize_text(text: Any) -> str:
    """
    Normalizes string by lowering case and stripping whitespace.
    """
    if text is None:
        return ""
    return str(text).strip().lower()


def normalize_column_names(columns: List[str]) -> Dict[str, str]:
    """
    Maps various common column name variations to canonical names:
    'date', 'description', 'amount', 'type'.
    """
    mapping = {}
    canonical_patterns = {
        "date": [r"^date.*", r"^transaction[_\s]?date.*", r"^timestamp.*", r"^posted[_\s]?date.*"],
        "description": [r"^description.*", r"^desc.*", r"^narrative.*", r"^particulars.*", r"^merchant.*", r"^title.*"],
        "amount": [r"^amount.*", r"^transaction[_\s]?amount.*", r"^val.*", r"^value.*", r"^amt.*"],
        "type": [r"^type.*", r"^transaction[_\s]?type.*", r"^txn[_\s]?type.*", r"^flow.*"],
    }

    for col in columns:
        # Strip parenthesis, symbols, and extra spaces
        clean_key = re.sub(r"[^\w\s]", "", str(col).strip().lower())
        clean_key = re.sub(r"\s+", " ", clean_key).strip()

        matched = False
        for canon, patterns in canonical_patterns.items():
            for pat in patterns:
                if re.match(pat, clean_key):
                    mapping[col] = canon
                    matched = True
                    break
            if matched:
                break
        if not matched:
            mapping[col] = str(col).strip().lower()

    return mapping
