"""
Configuration settings for Enterprise Agentic Procurement & Vendor Risk Auditor.
Academic Project CA-3: Swayam Singh (24070126181) & Sanskriti Soni (24070126162)
Department of AIML, Symbiosis Institute of Technology (SIT), Pune.
"""

from datetime import date
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Fixed audit date for reproducible certificate calculations
AUDIT_DATE = date(2026, 10, 19)

# Policy Rule Thresholds (Critic Auditor)
POLICY_THRESHOLDS = {
    # R1: Financial Risk (Debt-to-Revenue Ratio)
    "R1_DEBT_RATIO_MED": 0.50,
    "R1_DEBT_RATIO_HIGH": 0.70,
    
    # R2: Compliance Risk Keywords
    "R2_BREACH_KEYWORDS": [
        "failed",
        "violation",
        "fines active",
        "regulatory fines",
        "non-compliance",
        "hazardous material storage compliance checks in q3",
        "environmental fine"
    ],
    "R2_NEGATION_KEYWORDS": [
        "no violation",
        "no fines",
        "passed",
        "zero non-conformance",
        "zero infractions",
        "not failed",
        "compliant"
    ],
    
    # R3: Payment Delay Risk (Days)
    "R3_PAYMENT_DELAY_MED": 30,
    "R3_PAYMENT_DELAY_HIGH": 60,
    
    # R4: ISO 9001 Certification Risk (Days to expiry relative to AUDIT_DATE)
    "R4_EXPIRY_WARNING_DAYS_MED": 30,
    "R4_EXPIRED_DAYS_HIGH": 0,
    
    # R5: Statutory Risk
    "R5_VALID_GST_STATUS": "ACTIVE",
    
    # R6: Integrity & Evidence
    "R6_MIN_SIMILARITY_SCORE": 0.20,
    "R6_RATIO_TOLERANCE": 0.005,
    "MAX_REVISION_CYCLES": 2
}

# Retrieval settings
DEFAULT_TOP_K = 2

# SecOps Guardrail Injection Attack Patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all|previous|safety|checks|rules|alerts|instructions)",
    r"disregard\s+.*(alert|check|rule|safety|instructions)",
    r"(skip|bypass|override)\s+(the\s+)?(check|audit|safety|rules|guardrail)",
    r"(approve|mark)\s+.*regardless",
    r"system\s*:\s*override",
    r"forget\s+all\s+(previous\s+)?instructions",
    r"do\s+not\s+apply\s+(any\s+)?(policy|rule|check)",
    r"elevate\s+privilege"
]

# Allowlist of Known Enterprise Vendors
KNOWN_VENDORS = [
    "Titanium Machinery Spares",
    "Apex Fasteners",
    "Meridian Castings",
    "Orion Polymers",
    "Kestrel Forgings"
]
