"""
Deterministic compliance evidence evaluation tool.
Performs negation-aware matching for regulatory, environmental, and safety breaches in vendor texts.
"""

import re
from typing import List, Dict, Any
from config import POLICY_THRESHOLDS


def evaluate_compliance_evidence(chunk_texts: List[str]) -> Dict[str, Any]:
    """
    Evaluates evidence text chunks for regulatory fines, environmental breaches,
    and compliance failures using negation-aware pattern detection.
    """
    breach_terms = POLICY_THRESHOLDS["R2_BREACH_KEYWORDS"]
    negation_terms = POLICY_THRESHOLDS["R2_NEGATION_KEYWORDS"]

    matched_quotes = []
    breach_detected = False

    for text in chunk_texts:
        t_lower = text.lower()
        
        # Check if text contains clear positive statements of compliance
        has_clear_pass = any(neg in t_lower for neg in [
            "zero non-conformance",
            "zero infractions",
            "passed with zero",
            "completed successfully",
            "operating within baseline"
        ])
        
        # Explicit check for active fines or failure
        for term in breach_terms:
            if term in t_lower:
                # Check if term is negated within proximity (e.g., "no regulatory fines", "not failed")
                negated_pattern = rf"(no|zero|without|not)\s+(any\s+)?{re.escape(term)}"
                if not re.search(negated_pattern, t_lower):
                    # Genuine breach detected
                    breach_detected = True
                    matched_quotes.append({
                        "matched_term": term,
                        "text": text
                    })
                    break

    if breach_detected:
        status = "HIGH"
        explanation = f"CRITICAL: Confirmed active regulatory fine or compliance violation in audited documents."
    else:
        status = "LOW"
        explanation = "Compliant: No active regulatory fines or critical compliance failures detected in retrieved evidence."

    return {
        "breach_detected": breach_detected,
        "matched_quotes": matched_quotes,
        "status": status,
        "explanation": explanation
    }
