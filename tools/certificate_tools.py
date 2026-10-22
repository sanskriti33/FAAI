"""
Deterministic certificate validity checking tool.
Evaluates ISO 9001 certification against fixed enterprise audit date.
"""

from datetime import datetime, date
from typing import Dict, Any, Optional
from config import AUDIT_DATE, POLICY_THRESHOLDS


def check_iso9001_validity(expiry_date_str: str, audit_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Checks ISO 9001 certificate validity relative to configured audit date.
    """
    if audit_date is None:
        audit_date = AUDIT_DATE

    # Parse date strings (handles YYYY-MM-DD or Month YYYY)
    try:
        if len(expiry_date_str.split("-")) == 3:
            expiry_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        elif " " in expiry_date_str:
            # e.g., "March 2027" or "August 2026"
            parts = expiry_date_str.split()
            # Default to end of given month
            month_name = parts[0]
            year = int(parts[1])
            temp_dt = datetime.strptime(f"{month_name} {year}", "%B %Y")
            # Last day of month
            import calendar
            _, last_day = calendar.monthrange(year, temp_dt.month)
            expiry_dt = date(year, temp_dt.month, last_day)
        else:
            expiry_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except Exception as e:
        return {
            "expiry_date": expiry_date_str,
            "audit_date": audit_date.isoformat(),
            "days_remaining": -999,
            "status": "HIGH",
            "is_valid": False,
            "explanation": f"Failed to parse certificate date '{expiry_date_str}': {str(e)}"
        }

    days_remaining = (expiry_dt - audit_date).days
    med_warning_days = POLICY_THRESHOLDS["R4_EXPIRY_WARNING_DAYS_MED"]

    if days_remaining < 0:
        status = "HIGH"
        is_valid = False
        explanation = f"CRITICAL: ISO 9001 certificate expired on {expiry_dt.isoformat()} ({abs(days_remaining)} days before audit date)."
    elif days_remaining <= med_warning_days:
        status = "MED"
        is_valid = True
        explanation = f"WARNING: ISO 9001 certificate expires on {expiry_dt.isoformat()} (only {days_remaining} days remaining; renewal required)."
    else:
        status = "LOW"
        is_valid = True
        explanation = f"VALID: ISO 9001 certificate active through {expiry_dt.isoformat()} ({days_remaining} days remaining)."

    return {
        "expiry_date": expiry_dt.isoformat(),
        "audit_date": audit_date.isoformat(),
        "days_remaining": days_remaining,
        "status": status,
        "is_valid": is_valid,
        "explanation": explanation
    }
