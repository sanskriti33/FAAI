"""
Shared typed state model for the Enterprise Agentic Auditor.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
from .events import ExecutionEvent


@dataclass
class AuditState:
    """
    Central shared state carried across all seven agents and the human-in-the-loop review.
    Ensures complete traceability, isolation, and deterministic execution.
    """
    vendor_name: str
    user_query: str
    audit_id: str = field(default_factory=lambda: f"AUD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Raw Vendor Profile
    vendor_data: Dict[str, Any] = field(default_factory=dict)
    
    # SecOps Guardrail State
    security_status: Dict[str, Any] = field(default_factory=lambda: {
        "checkpoint_1_passed": False,
        "checkpoint_2_passed": False,
        "is_blocked": False,
        "blocked_reason": None,
        "blocked_checkpoint": None,
        "quarantined_chunks": []
    })
    
    # Task Planner State (ReAct)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    initial_task_count: int = 2
    expanded_task_count: int = 2
    
    # Worker Results
    research_results: List[Dict[str, Any]] = field(default_factory=list)
    executor_results: Dict[str, Any] = field(default_factory=dict)
    
    # Software Dev Agent
    monitoring_script: Optional[str] = None
    monitoring_test_result: Optional[Dict[str, Any]] = None
    
    # Critic Verification & Decision
    critic_findings: List[Dict[str, Any]] = field(default_factory=list)
    verdict: Optional[str] = None  # APPROVE, REJECT, ESCALATE, BLOCKED, REVISE
    verdict_summary: Optional[str] = None
    
    # Human Review Workflow
    awaiting_human_review: bool = False
    human_review: Optional[Dict[str, Any]] = None
    
    # Business Automation Drafts
    department_actions: List[Dict[str, Any]] = field(default_factory=list)
    outbox_status: str = "PENDING_CONFIRMATION"  # PENDING_CONFIRMATION, DISPATCHED_TO_SIMULATED_OUTBOX
    
    # Orchestration Tracking
    revision_count: int = 0
    events: List[ExecutionEvent] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def log_event(self, agent_name: str, event_type: str, message: str, status: str = "COMPLETED", payload: Optional[Dict[str, Any]] = None):
        """Helper to append structured event to the state timeline."""
        evt = ExecutionEvent(
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            status=status,
            payload=payload or {}
        )
        self.events.append(evt)
        return evt

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to serializable dictionary for logs and UI."""
        return {
            "audit_id": self.audit_id,
            "vendor_name": self.vendor_name,
            "user_query": self.user_query,
            "timestamp": self.timestamp,
            "security_status": self.security_status,
            "tasks": self.tasks,
            "initial_task_count": self.initial_task_count,
            "expanded_task_count": self.expanded_task_count,
            "research_results": self.research_results,
            "executor_results": self.executor_results,
            "monitoring_script": self.monitoring_script,
            "monitoring_test_result": self.monitoring_test_result,
            "critic_findings": self.critic_findings,
            "verdict": self.verdict,
            "verdict_summary": self.verdict_summary,
            "awaiting_human_review": self.awaiting_human_review,
            "human_review": self.human_review,
            "department_actions": self.department_actions,
            "outbox_status": self.outbox_status,
            "revision_count": self.revision_count,
            "events": [e.to_dict() for e in self.events],
            "errors": self.errors
        }
