"""
Audit History Service.
Persists and retrieves audit runs, outcome statistics, and security incident logs.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import DATA_DIR
from orchestration.state import AuditState


class AuditHistoryService:
    """
    Manages persistent local history of audit sessions and security events.
    """

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or (DATA_DIR / "audit_history.json")
        self._ensure_file()

    def _ensure_file(self):
        if not self.history_file.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def record_audit(self, state: AuditState) -> Dict[str, Any]:
        """
        Extracts summary record from AuditState and appends to persistent history.
        """
        history = self.get_all_audits()
        
        record = {
            "audit_id": state.audit_id,
            "timestamp": state.timestamp,
            "vendor_name": state.vendor_name,
            "query": state.user_query,
            "verdict": state.verdict or "IN_PROGRESS",
            "verdict_summary": state.verdict_summary,
            "is_blocked": state.security_status.get("is_blocked", False),
            "blocked_checkpoint": state.security_status.get("blocked_checkpoint"),
            "blocked_reason": state.security_status.get("blocked_reason"),
            "findings_count": len(state.critic_findings),
            "findings": state.critic_findings,
            "initial_tasks": state.initial_task_count,
            "expanded_tasks": state.expanded_task_count,
            "human_reviewed": state.human_review is not None,
            "human_decision": state.human_review.get("decision") if state.human_review else None,
            "department_actions_count": len(state.department_actions)
        }

        # Avoid duplicate audit IDs
        history = [r for r in history if r["audit_id"] != state.audit_id]
        history.insert(0, record)

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        return record

    def get_all_audits(self) -> List[Dict[str, Any]]:
        """Returns all recorded audits."""
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Calculates dashboard summary statistics."""
        audits = self.get_all_audits()
        total = len(audits)
        approved = sum(1 for a in audits if a.get("verdict") == "APPROVE")
        rejected = sum(1 for a in audits if a.get("verdict") == "REJECT")
        escalated = sum(1 for a in audits if a.get("verdict") == "ESCALATE")
        blocked = sum(1 for a in audits if a.get("verdict") == "BLOCKED" or a.get("is_blocked"))
        incidents = [a for a in audits if a.get("is_blocked")]

        return {
            "total_audits": total,
            "approved": approved,
            "rejected": rejected,
            "escalated": escalated,
            "blocked": blocked,
            "security_incidents": incidents
        }

    def clear_history(self):
        """Resets audit history file."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump([], f)
