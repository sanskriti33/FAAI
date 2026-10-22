"""
Execution event definitions for traceable ReAct workflows.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


@dataclass
class ExecutionEvent:
    """
    Represents an atomic, observable event within the agentic workflow.
    Provides complete transparency for audit trails and faculty evaluation.
    """
    agent_name: str
    event_type: str  # PLAN, ACTION, OBSERVATION, PLAN_UPDATE, VALIDATION, DECISION, HUMAN_REVIEW, ACTION_DRAFT, SECURITY_ALERT
    message: str
    status: str = "COMPLETED"  # RUNNING, COMPLETED, REVISED, BLOCKED, FAILED
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3])
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "agent_name": self.agent_name,
            "event_type": self.event_type,
            "message": self.message,
            "status": self.status,
            "payload": self.payload
        }
