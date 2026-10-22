"""
Deterministic tools for statutory GST verification and internal vendor blacklist lookup.
"""

from typing import Dict, Any
from config import POLICY_THRESHOLDS


def check_gst_status(gst_status: str) -> Dict[str, Any]:
    """
    Validates GST status against statutory requirements (R5).
    """
    valid_status = POLICY_THRESHOLDS["R5_VALID_GST_STATUS"]
    is_valid = (gst_status.strip().upper() == valid_status)

    if not is_valid:
        status = "HIGH"
        explanation = f"CRITICAL: Statutory GST status is '{gst_status}' (Expected: '{valid_status}'). Tax compliance breach."
    else:
        status = "LOW"
        explanation = f"VALID: GST status is active and verified against national portal records."

    return {
        "gst_status": gst_status,
        "is_valid": is_valid,
        "status": status,
        "explanation": explanation
    }


def check_blacklist_status(vendor_name: str, is_blacklisted: bool = False) -> Dict[str, Any]:
    """
    Checks internal enterprise procurement blacklist (R5).
    """
    if is_blacklisted:
        status = "HIGH"
        explanation = f"CRITICAL: Vendor '{vendor_name}' is currently flagged on the enterprise blacklist."
    else:
        status = "LOW"
        explanation = f"CLEAN: Vendor '{vendor_name}' is in good standing with no internal blacklist records."

    return {
        "vendor_name": vendor_name,
        "is_blacklisted": is_blacklisted,
        "status": status,
        "explanation": explanation
    }
