"""
Tool: check_credit_history
Queries credit_risk.csv for applicant financial profile.
Falls back to synthetic data if the CSV is unavailable.
"""

import logging
import os
import random
from typing import Any, Dict, Optional

import pandas as pd

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Cache the DataFrame in memory
_df_cache: Optional[pd.DataFrame] = None


def _load_df() -> Optional[pd.DataFrame]:
    global _df_cache
    if _df_cache is not None:
        return _df_cache
    data_path = settings.CREDIT_DATA_PATH
    if os.path.exists(data_path):
        try:
            if data_path.lower().endswith(('.xlsx', '.xls')):
                _df_cache = pd.read_excel(data_path)
            else:
                _df_cache = pd.read_csv(data_path)
            logger.info(f"[CreditTool] Loaded {len(_df_cache)} records from {data_path}")
            return _df_cache
        except Exception as e:
            logger.warning(f"[CreditTool] Failed to load data file: {e}")
    return None


def _synthetic_profile(applicant_id: str) -> Dict[str, Any]:
    """Generate a deterministic synthetic profile when CSV is unavailable."""
    rng = random.Random(hash(applicant_id) % 10000)
    income = rng.randint(300000, 2500000)
    existing_debt = rng.randint(0, int(income * 0.6))
    credit_score = rng.randint(480, 820)
    defaults = rng.randint(0, 3)
    return {
        "applicant_id": applicant_id,
        "annual_income": income,
        "existing_debt": existing_debt,
        "credit_score": credit_score,
        "previous_defaults": defaults,
        "employment_status": rng.choice(["employed", "self-employed", "unemployed"]),
        "employment_years": rng.randint(0, 25),
        "loan_count": rng.randint(0, 5),
        "on_time_payments_pct": rng.randint(60, 100),
        "data_source": "synthetic (CSV not found)",
    }


def _normalize_columns(row: pd.Series) -> Dict[str, Any]:
    """Try to map common Kaggle credit-risk CSV columns to our schema."""
    d = row.to_dict()

    # Common column name mappings across Kaggle datasets
    col_map = {
        "person_income": "annual_income",
        "income": "annual_income",
        "annual_income": "annual_income",
        "loan_int_rate": "interest_rate",
        "cb_person_default_on_file": "previous_defaults",
        "default": "previous_defaults",
        "credit_score": "credit_score",
        "fico_score": "credit_score",
        "loan_amnt": "existing_debt",
        "loan_amount": "existing_debt",
        "person_emp_length": "employment_years",
        "emp_length": "employment_years",
        "person_home_ownership": "home_ownership",
        "loan_intent": "loan_purpose",
        "loan_grade": "loan_grade",
        "cb_person_cred_hist_length": "credit_history_years",
        "person_age": "age",
        "loan_status": "loan_status",
    }
    normalised = {}
    for src, dst in col_map.items():
        if src in d:
            normalised[dst] = d[src]

    # Defaults for missing fields
    normalised.setdefault("credit_score", d.get("fico", d.get("score", 650)))
    normalised.setdefault("annual_income", d.get("income_annum", 500000))
    normalised.setdefault("existing_debt", d.get("loan_amount", d.get("cibil_score", 0)))
    normalised.setdefault("previous_defaults", 1 if str(d.get("previous_defaults", "N")).upper() == "Y" else 0)
    normalised.setdefault("employment_years", d.get("no_of_months_employed", 24) / 12)
    normalised.setdefault("employment_status", "employed")

    return normalised


def check_credit_history(applicant_id: str, include_full_profile: bool = True) -> Dict[str, Any]:
    """
    Main tool function. Returns a structured dict with the applicant's financial profile.
    """
    df = _load_df()

    if df is not None:
        # Attempt to find the applicant
        # Check if there's an ID column
        id_cols = [c for c in df.columns if "id" in c.lower()]
        found_row = None

        if id_cols:
            for id_col in id_cols:
                mask = df[id_col].astype(str).str.upper() == applicant_id.upper()
                if mask.any():
                    found_row = df[mask].iloc[0]
                    break

        if found_row is None:
            # Fall back to using the applicant_id as a row index seed
            idx = abs(hash(applicant_id)) % len(df)
            found_row = df.iloc[idx]
            logger.info(f"[CreditTool] ID '{applicant_id}' not found; using row {idx} as proxy.")

        profile = _normalize_columns(found_row)
        profile["applicant_id"] = applicant_id
        profile["data_source"] = f"credit_risk.csv (row {df.index.get_loc(found_row.name) if hasattr(found_row, 'name') else 'n/a'})"

        if not include_full_profile:
            # Return just the essentials
            return {k: profile[k] for k in
                    ["applicant_id", "annual_income", "credit_score", "previous_defaults", "data_source"]
                    if k in profile}
        return profile

    else:
        logger.warning("[CreditTool] CSV not found; using synthetic profile.")
        return _synthetic_profile(applicant_id)


def format_profile_for_llm(profile: Dict[str, Any]) -> str:
    """Render profile as a readable string for LLM context."""
    lines = [f"=== CREDIT PROFILE: {profile.get('applicant_id', 'Unknown')} ==="]
    field_labels = {
        "annual_income": "Annual Income (₹)",
        "existing_debt": "Existing Debt (₹)",
        "credit_score": "Credit Score",
        "previous_defaults": "Previous Defaults",
        "employment_status": "Employment Status",
        "employment_years": "Years Employed",
        "loan_count": "Active Loans",
        "on_time_payments_pct": "On-Time Payments %",
        "loan_grade": "Loan Grade",
        "home_ownership": "Home Ownership",
        "credit_history_years": "Credit History (Years)",
        "data_source": "Data Source",
    }
    for key, label in field_labels.items():
        if key in profile:
            val = profile[key]
            if key == "annual_income" and isinstance(val, (int, float)):
                val = f"₹{val:,.0f}"
            elif key == "existing_debt" and isinstance(val, (int, float)):
                val = f"₹{val:,.0f}"
            lines.append(f"  {label}: {val}")
    return "\n".join(lines)
