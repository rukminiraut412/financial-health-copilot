"""
Transaction processor service: CSV ingestion, cleaning, validation, and normalization.
"""

import io
import uuid
from typing import List, Tuple, Union
import pandas as pd

from backend.schemas.transaction import Transaction, TransactionType
from backend.services.categorizer import categorize_transaction
from backend.utils.helpers import clean_amount, parse_date_safe, normalize_column_names


REQUIRED_COLUMNS = {"date", "description", "amount", "type"}


def parse_csv_file(file_content: Union[str, bytes]) -> Tuple[List[Transaction], List[str]]:
    """
    Parses raw CSV content into a list of validated Transaction models.
    Returns:
        (List[Transaction], List[str] errors)
    """
    errors: List[str] = []
    transactions: List[Transaction] = []

    # Decode bytes if needed
    if isinstance(file_content, bytes):
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = file_content.decode("latin-1")
            except Exception as e:
                return [], [f"Failed to decode file encoding: {str(e)}"]
    else:
        text = str(file_content)

    if not text.strip():
        return [], ["Uploaded CSV file is empty."]

    # Read CSV with pandas
    try:
        df = pd.read_csv(io.StringIO(text), skipinitialspace=True)
    except Exception as e:
        return [], [f"Failed to parse CSV: {str(e)}"]

    if df.empty:
        return [], ["CSV contains headers but no data rows."]

    # Normalize column names
    col_map = normalize_column_names(list(df.columns))
    df = df.rename(columns=col_map)

    # Check for missing required columns
    present_cols = set(df.columns)
    missing_cols = REQUIRED_COLUMNS - present_cols
    if missing_cols:
        return [], [f"Missing required columns in CSV: {', '.join(sorted(list(missing_cols)))}. Found columns: {list(df.columns)}"]

    # Process each row
    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed including header
        raw_date = row.get("date")
        raw_desc = row.get("description")
        raw_amount = row.get("amount")
        raw_type = row.get("type")

        # Validate date
        parsed_date = parse_date_safe(raw_date)
        if not parsed_date:
            errors.append(f"Row {row_num}: Invalid or missing date '{raw_date}'")
            continue

        # Validate description
        if pd.isna(raw_desc) or not str(raw_desc).strip():
            errors.append(f"Row {row_num}: Description cannot be empty")
            continue
        description = str(raw_desc).strip()

        # Validate amount
        amount = clean_amount(raw_amount)
        if amount <= 0:
            errors.append(f"Row {row_num}: Invalid amount '{raw_amount}'. Amount must be greater than zero")
            continue

        # Validate and normalize type
        t_str = str(raw_type).strip().lower() if pd.notna(raw_type) else "expense"
        if t_str in ["income", "credit", "deposit", "inflow"]:
            tx_type = TransactionType.INCOME.value
        else:
            tx_type = TransactionType.EXPENSE.value

        # Category
        raw_category = row.get("category") if "category" in df.columns else None
        if pd.notna(raw_category) and str(raw_category).strip():
            category = str(raw_category).strip()
        else:
            category = categorize_transaction(description, tx_type)

        tx_id = f"txn_{uuid.uuid4().hex[:8]}"

        transactions.append(
            Transaction(
                id=tx_id,
                date=parsed_date,
                description=description,
                amount=round(amount, 2),
                type=tx_type,
                category=category,
                is_recurring=False,
            )
        )

    return transactions, errors


def transactions_to_dataframe(transactions: List[Transaction]) -> pd.DataFrame:
    """
    Converts a list of Transaction models into a pandas DataFrame.
    """
    if not transactions:
        return pd.DataFrame(columns=["id", "date", "description", "amount", "type", "category", "is_recurring"])

    data = [t.model_dump() for t in transactions]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)
    return df


def dataframe_to_transactions(df: pd.DataFrame) -> List[Transaction]:
    """
    Converts a DataFrame back to a list of Transaction models.
    """
    transactions: List[Transaction] = []
    if df.empty:
        return transactions

    for idx, row in df.iterrows():
        date_val = str(row.get("date"))[:10]
        desc = str(row.get("description", ""))
        amount = float(row.get("amount", 0.0))
        tx_type = str(row.get("type", "expense"))
        category = str(row.get("category", "Miscellaneous"))
        tx_id = str(row.get("id", f"txn_{idx}"))

        transactions.append(
            Transaction(
                id=tx_id,
                date=date_val,
                description=desc,
                amount=amount,
                type=tx_type,
                category=category,
                is_recurring=bool(row.get("is_recurring", False)),
            )
        )

    return transactions
