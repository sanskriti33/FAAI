"""
Unit tests for individual deterministic tools and specialized agents.
"""

import pytest
from datetime import date
from tools.financial_tools import compute_debt_to_revenue, compute_payment_delay, compute_peer_benchmark
from tools.certificate_tools import check_iso9001_validity
from tools.compliance_tools import evaluate_compliance_evidence
from tools.vendor_tools import check_gst_status, check_blacklist_status
from agents.software_development import SoftwareDevelopmentAgent
from orchestration.state import AuditState


def test_financial_tools_exact_calculation():
    # Titanium ratio: 2.0M / 2.5M = 0.80 -> HIGH
    res = compute_debt_to_revenue(debt=2000000, revenue=2500000)
    assert res["ratio"] == 0.80
    assert res["status"] == "HIGH"

    # Apex ratio: 450k / 1.5M = 0.30 -> LOW
    res = compute_debt_to_revenue(debt=450000, revenue=1500000)
    assert res["ratio"] == 0.30
    assert res["status"] == "LOW"

    # Meridian ratio: 990k / 1.8M = 0.55 -> MED
    res = compute_debt_to_revenue(debt=990000, revenue=1800000)
    assert res["ratio"] == 0.55
    assert res["status"] == "MED"


def test_payment_delay_tool():
    assert compute_payment_delay(8)["status"] == "LOW"
    assert compute_payment_delay(38)["status"] == "MED"
    assert compute_payment_delay(65)["status"] == "HIGH"


def test_certificate_tool_fixed_audit_date():
    audit_date = date(2026, 10, 19)

    # Titanium: 2027-06-30 -> > 30 days -> LOW (VALID)
    res = check_iso9001_validity("2027-06-30", audit_date=audit_date)
    assert res["is_valid"] is True
    assert res["status"] == "LOW"
    assert res["days_remaining"] > 200

    # Meridian: 2026-11-08 -> 20 days remaining -> MED (EXPIRING SOON)
    res = check_iso9001_validity("2026-11-08", audit_date=audit_date)
    assert res["is_valid"] is True
    assert res["status"] == "MED"
    assert res["days_remaining"] == 20

    # Kestrel: 2026-08-15 -> Expired before audit date -> HIGH (EXPIRED)
    res = check_iso9001_validity("2026-08-15", audit_date=audit_date)
    assert res["is_valid"] is False
    assert res["status"] == "HIGH"
    assert res["days_remaining"] < 0


def test_compliance_tool_negation_awareness():
    # Genuine breach: "Critical alert: Failed workplace hazardous material storage compliance checks in Q3. Regulatory fines active."
    breach_text = ["Critical alert: Failed workplace hazardous material storage compliance checks in Q3. Regulatory fines active."]
    res = evaluate_compliance_evidence(breach_text)
    assert res["breach_detected"] is True
    assert res["status"] == "HIGH"

    # Negated / clean: "Comprehensive metal forging inspection passed with zero non-conformances."
    clean_text = ["Comprehensive metal forging inspection passed with zero non-conformances."]
    res2 = evaluate_compliance_evidence(clean_text)
    assert res2["breach_detected"] is False
    assert res2["status"] == "LOW"


def test_gst_and_blacklist_tools():
    assert check_gst_status("ACTIVE")["status"] == "LOW"
    assert check_gst_status("CANCELLED")["status"] == "HIGH"
    assert check_blacklist_status("Apex", is_blacklisted=False)["status"] == "LOW"
    assert check_blacklist_status("Rogue Supplier", is_blacklisted=True)["status"] == "HIGH"


def test_software_dev_agent_sandboxed_self_test():
    dev = SoftwareDevelopmentAgent()
    state = AuditState(vendor_name="Titanium Machinery Spares", user_query="Audit Titanium")
    state.executor_results = {
        "debt_to_revenue": {"ratio": 0.80},
        "payment_delay": {"avg_delay_days": 12},
        "iso9001_check": {"days_remaining": 250},
        "gst_check": {"gst_status": "ACTIVE"}
    }
    result = dev.generate_and_test_script(state)
    assert result["test_passed"] is True
    assert "Self-test SUCCESS" in result["test_output"]
    assert "class VendorRiskMonitor" in result["script_code"]
