"""
Deterministic financial tools for Executor and Critic Auditor agents.
"""

from typing import Dict, Any
from config import POLICY_THRESHOLDS


def compute_debt_to_revenue(debt: float, revenue: float) -> Dict[str, Any]:
    """
    Computes exact Debt-to-Revenue ratio and benchmarks against R1 policy thresholds.
    """
    if revenue <= 0:
        raise ValueError("Revenue must be greater than zero.")
    
    ratio = round(debt / revenue, 4)
    med_threshold = POLICY_THRESHOLDS["R1_DEBT_RATIO_MED"]
    high_threshold = POLICY_THRESHOLDS["R1_DEBT_RATIO_HIGH"]

    if ratio > high_threshold:
        status = "HIGH"
        explanation = f"Critical debt ratio of {ratio:.2f} exceeds high risk limit (> {high_threshold:.2f})."
    elif ratio > med_threshold:
        status = "MED"
        explanation = f"Elevated debt ratio of {ratio:.2f} exceeds medium risk threshold (> {med_threshold:.2f})."
    else:
        status = "LOW"
        explanation = f"Healthy debt ratio of {ratio:.2f} is within acceptable limits (<= {med_threshold:.2f})."

    return {
        "debt": debt,
        "revenue": revenue,
        "ratio": ratio,
        "threshold_med": med_threshold,
        "threshold_high": high_threshold,
        "status": status,
        "explanation": explanation
    }


def compute_payment_delay(avg_delay_days: int) -> Dict[str, Any]:
    """
    Evaluates average supplier payment delay against R3 policy thresholds.
    """
    med_threshold = POLICY_THRESHOLDS["R3_PAYMENT_DELAY_MED"]
    high_threshold = POLICY_THRESHOLDS["R3_PAYMENT_DELAY_HIGH"]

    if avg_delay_days > high_threshold:
        status = "HIGH"
        explanation = f"Average payment delay of {avg_delay_days} days indicates severe working capital distress (> {high_threshold} days)."
    elif avg_delay_days > med_threshold:
        status = "MED"
        explanation = f"Average payment delay of {avg_delay_days} days exceeds operational target (> {med_threshold} days)."
    else:
        status = "LOW"
        explanation = f"Prompt payment history of {avg_delay_days} days conforms to standard terms (<= {med_threshold} days)."

    return {
        "avg_delay_days": avg_delay_days,
        "threshold_med": med_threshold,
        "threshold_high": high_threshold,
        "status": status,
        "explanation": explanation
    }


def compute_peer_benchmark(ratio: float, peer_median: float) -> Dict[str, Any]:
    """
    Compares vendor financial leverage against industry peer median.
    """
    variance = round(ratio - peer_median, 4)
    if variance > 0.10:
        status = "SIGNIFICANTLY_ABOVE_PEER"
        explanation = f"Ratio {ratio:.2f} is {variance:+.2f} higher than industry peer median ({peer_median:.2f}). High leverage alert."
    elif variance > 0:
        status = "SLIGHTLY_ABOVE_PEER"
        explanation = f"Ratio {ratio:.2f} is slightly elevated ({variance:+.2f}) above industry peer median ({peer_median:.2f})."
    else:
        status = "AT_OR_BELOW_PEER"
        explanation = f"Ratio {ratio:.2f} is favorable or in line with industry peer median ({peer_median:.2f})."

    return {
        "ratio": ratio,
        "peer_median": peer_median,
        "variance": variance,
        "status": status,
        "explanation": explanation
    }
