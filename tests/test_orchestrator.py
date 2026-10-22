"""
Orchestrator pipeline and lifecycle integration tests.
"""

import pytest
from orchestration.workflow import AuditOrchestrator
from services.audit_history import AuditHistoryService
from services.outbox import OutboxService


def test_orchestrator_initialization():
    orch = AuditOrchestrator()
    assert len(orch.vendors_db) == 5
    assert "Titanium Machinery Spares" in orch.vendors_db


def test_outbox_service_dispatch(tmp_path):
    outbox = OutboxService(tmp_path / "department_outbox.json")
    test_actions = [
        {
            "department": "Production Planning",
            "action_type": "SUPPLY_DISRUPTION_ALERT",
            "title": "Flag Open Orders",
            "description": "Alert PO-1042",
            "affected_pos": ["PO-1042"],
            "parts": ["Shaft Sleeves"],
            "suggested_alternate": "Vega Precision Components"
        }
    ]
    dispatched = outbox.dispatch_actions(
        audit_id="AUD-TEST-001",
        vendor_name="Titanium Machinery Spares",
        actions=test_actions
    )
    assert len(dispatched) == 1
    assert dispatched[0]["status"] == "DISPATCHED_TO_SIMULATED_OUTBOX"
    assert dispatched[0]["department"] == "Production Planning"


def test_audit_history_service_stats(tmp_path):
    history = AuditHistoryService(tmp_path / "audit_history.json")
    stats = history.get_stats()
    assert "total_audits" in stats
    assert "approved" in stats
    assert "rejected" in stats
    assert "escalated" in stats
    assert "blocked" in stats
