"""
Tool: regulatory_compliance_check
Tool: score_risk_matrix

Rule-based compliance engine and composite risk scoring.
"""

import logging
from typing import Any, Dict

from app.config import get_settings
from app.tools.credit_history import check_credit_history

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Regulatory Compliance ─────────────────────────────────────────────────────

POVERTY_LINE_ANNUAL = 180000  # ₹1.8 lakh (approx. India poverty threshold)
MAX_ACTIVE_BANKRUPTCIES = 0
MAX_RECENT_DEFAULTS_FOR_APPROVAL = 1  # 0 defaults = clean; 1 = borderline


def regulatory_compliance_check(
    applicant_id: str,
    loan_amount: float,
    loan_purpose: str = "General",
) -> Dict[str, Any]:
    """
    Check loan application against NeoStats compliance ruleset.
    Returns a structured compliance report.
    """
    profile = check_credit_history(applicant_id, include_full_profile=True)
    annual_income = float(profile.get("annual_income", 0))
    previous_defaults = int(profile.get("previous_defaults", 0))
    employment_status = str(profile.get("employment_status", "unknown")).lower()

    violations = []
    warnings = []
    passed = []

    # Rule 1: Loan-to-Income ratio (40% cap)
    max_allowed = annual_income * settings.COMPLIANCE_INCOME_RATIO
    lti_ratio = (loan_amount / annual_income) if annual_income > 0 else float("inf")

    if loan_amount > max_allowed:
        violations.append(
            f"LOAN_TO_INCOME_BREACH: Loan ₹{loan_amount:,.0f} exceeds 40% of "
            f"annual income ₹{annual_income:,.0f} (max allowed: ₹{max_allowed:,.0f})"
        )
    else:
        passed.append(
            f"LOAN_TO_INCOME_OK: ₹{loan_amount:,.0f} is {lti_ratio:.1%} of annual income "
            f"(limit: 40%)"
        )

    # Rule 2: Minimum income above poverty line
    if annual_income < POVERTY_LINE_ANNUAL:
        violations.append(
            f"INCOME_BELOW_THRESHOLD: Annual income ₹{annual_income:,.0f} is below "
            f"the minimum threshold ₹{POVERTY_LINE_ANNUAL:,.0f}"
        )
    else:
        passed.append(f"INCOME_THRESHOLD_OK: ₹{annual_income:,.0f} above minimum.")

    # Rule 3: Employment status
    if employment_status == "unemployed":
        violations.append("EMPLOYMENT_STATUS: Applicant is currently unemployed.")
    elif employment_status == "self-employed":
        warnings.append("SELF_EMPLOYED: Enhanced income verification recommended.")
        passed.append("EMPLOYMENT_STATUS_BORDERLINE: Self-employed — additional docs needed.")
    else:
        passed.append(f"EMPLOYMENT_STATUS_OK: {employment_status}")

    # Rule 4: Previous defaults warning
    if previous_defaults >= 2:
        violations.append(
            f"PREVIOUS_DEFAULTS_BREACH: {previous_defaults} previous defaults exceed the maximum of 1."
        )
    elif previous_defaults == 1:
        warnings.append(
            "PREVIOUS_DEFAULT_WARNING: 1 prior default on record. Enhanced scrutiny required."
        )
    else:
        passed.append("NO_PREVIOUS_DEFAULTS: Clean repayment history.")

    # Rule 5: Loan purpose special checks
    high_risk_purposes = ["speculation", "gambling", "crypto"]
    if any(p in loan_purpose.lower() for p in high_risk_purposes):
        violations.append(f"HIGH_RISK_PURPOSE: Loan purpose '{loan_purpose}' is prohibited.")
    else:
        passed.append(f"LOAN_PURPOSE_OK: '{loan_purpose}' is an eligible purpose.")

    # Overall compliance status
    if violations:
        status = "NON_COMPLIANT"
    elif warnings:
        status = "CONDITIONALLY_COMPLIANT"
    else:
        status = "COMPLIANT"

    return {
        "applicant_id": applicant_id,
        "loan_amount": loan_amount,
        "annual_income": annual_income,
        "loan_to_income_ratio": round(lti_ratio, 4),
        "max_allowed_loan": round(max_allowed, 2),
        "compliance_status": status,
        "violations": violations,
        "warnings": warnings,
        "passed_checks": passed,
        "total_checks": len(violations) + len(warnings) + len(passed),
    }


def format_compliance_for_llm(result: Dict[str, Any]) -> str:
    lines = [
        f"=== COMPLIANCE REPORT: {result['applicant_id']} ===",
        f"Status: {result['compliance_status']}",
        f"Loan/Income Ratio: {result['loan_to_income_ratio']:.1%} (limit: 40%)",
        f"Annual Income: ₹{result['annual_income']:,.0f}",
        f"Max Allowed Loan: ₹{result['max_allowed_loan']:,.0f}",
        "",
    ]
    if result["violations"]:
        lines.append("❌ VIOLATIONS:")
        for v in result["violations"]:
            lines.append(f"  • {v}")
    if result["warnings"]:
        lines.append("⚠️  WARNINGS:")
        for w in result["warnings"]:
            lines.append(f"  • {w}")
    if result["passed_checks"]:
        lines.append("✅ PASSED:")
        for p in result["passed_checks"]:
            lines.append(f"  • {p}")
    return "\n".join(lines)


# ── Risk Matrix Scoring ────────────────────────────────────────────────────────

RISK_WEIGHTS = {
    "credit_score": 0.30,
    "debt_to_income": 0.25,
    "previous_defaults": 0.20,
    "employment_stability": 0.15,
    "sector_risk": 0.10,
}

SECTOR_RISK_SCORES = {
    "low": 90,
    "medium": 60,
    "high": 30,
    "critical": 10,
}


def _score_credit_score(cs: float) -> float:
    """Maps credit score (300-900) to 0-100."""
    cs = max(300, min(900, cs))
    return (cs - 300) / 600 * 100


def _score_debt_to_income(dti: float) -> float:
    """Maps DTI ratio (0-1+) to 0-100 (lower DTI = higher score)."""
    dti = max(0, dti)
    if dti <= 0.20:
        return 100
    elif dti <= 0.40:
        return 80
    elif dti <= 0.60:
        return 50
    elif dti <= 0.80:
        return 25
    else:
        return 5


def _score_defaults(defaults: int) -> float:
    return {0: 100, 1: 50, 2: 20}.get(defaults, 0)


def _score_employment(status: str, years: float) -> float:
    base = {"employed": 80, "self-employed": 60, "unemployed": 10}.get(status.lower(), 40)
    stability_bonus = min(20, years * 2)
    return min(100, base + stability_bonus)


def score_risk_matrix(applicant_id: str, sector_risk_level: str = "medium") -> Dict[str, Any]:
    """Compute composite risk score (0-100, higher = safer)."""
    profile = check_credit_history(applicant_id, include_full_profile=True)

    annual_income = float(profile.get("annual_income", 500000))
    existing_debt = float(profile.get("existing_debt", 0))
    credit_score = float(profile.get("credit_score", 600))
    previous_defaults = int(profile.get("previous_defaults", 0))
    employment_status = str(profile.get("employment_status", "employed"))
    employment_years = float(profile.get("employment_years", 3))

    dti = existing_debt / annual_income if annual_income > 0 else 1.0

    sub_scores = {
        "credit_score": round(_score_credit_score(credit_score), 1),
        "debt_to_income": round(_score_debt_to_income(dti), 1),
        "previous_defaults": round(_score_defaults(previous_defaults), 1),
        "employment_stability": round(_score_employment(employment_status, employment_years), 1),
        "sector_risk": SECTOR_RISK_SCORES.get(sector_risk_level.lower(), 60),
    }

    composite = sum(sub_scores[k] * RISK_WEIGHTS[k] for k in sub_scores)
    composite = round(composite, 1)

    if composite >= 75:
        risk_rating = "LOW"
        recommendation = "APPROVE"
    elif composite >= 55:
        risk_rating = "MEDIUM"
        recommendation = "APPROVE_WITH_CONDITIONS"
    elif composite >= 35:
        risk_rating = "HIGH"
        recommendation = "MANUAL_REVIEW"
    else:
        risk_rating = "CRITICAL"
        recommendation = "REJECT"

    return {
        "applicant_id": applicant_id,
        "composite_score": composite,
        "risk_rating": risk_rating,
        "recommendation": recommendation,
        "sub_scores": sub_scores,
        "weights_used": RISK_WEIGHTS,
        "inputs": {
            "credit_score": credit_score,
            "debt_to_income_ratio": round(dti, 4),
            "previous_defaults": previous_defaults,
            "employment_status": employment_status,
            "employment_years": employment_years,
            "sector_risk_level": sector_risk_level,
        },
    }


def format_risk_matrix_for_llm(result: Dict[str, Any]) -> str:
    lines = [
        f"=== RISK MATRIX SCORE: {result['applicant_id']} ===",
        f"Composite Score    : {result['composite_score']}/100",
        f"Risk Rating        : {result['risk_rating']}",
        f"Initial Recommendation: {result['recommendation']}",
        "",
        "Sub-Scores (weighted):",
    ]
    for k, v in result["sub_scores"].items():
        weight_pct = int(result["weights_used"][k] * 100)
        lines.append(f"  • {k.replace('_', ' ').title():25s}: {v:5.1f}/100 (weight: {weight_pct}%)")
    lines.append("")
    lines.append("Input Parameters:")
    for k, v in result["inputs"].items():
        lines.append(f"  • {k.replace('_', ' ').title():25s}: {v}")
    return "\n".join(lines)
