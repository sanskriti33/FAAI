"""
Agent 1 — SecOps Guardrail
Implements dual security checkpoints for prompt-injection defense and vendor allowlist verification.
"""

import re
from typing import List, Dict, Any, Tuple
from config import INJECTION_PATTERNS, KNOWN_VENDORS
from orchestration.state import AuditState


class SecOpsGuardrailAgent:
    """
    Security Operations Guardrail Agent.
    Enforces fail-closed security at two distinct checkpoints:
    1. Checkpoint 1: Pre-audit validation of user request and vendor allowlist.
    2. Checkpoint 2: Post-retrieval quarantine scanning of vendor document chunks.
    """

    def __init__(self, patterns: List[str] = None, allowlist: List[str] = None):
        self.patterns = patterns or INJECTION_PATTERNS
        self.allowlist = allowlist or KNOWN_VENDORS

    def is_safe_text(self, text: str) -> Tuple[bool, str]:
        """
        Scans text for prompt injection patterns.
        Returns (is_safe, matched_pattern).
        """
        t_clean = text.lower()
        for p in self.patterns:
            match = re.search(p, t_clean, re.IGNORECASE)
            if match:
                return False, match.group(0)
        return True, ""

    def validate_checkpoint_1(self, state: AuditState) -> bool:
        """
        Checkpoint 1: Validates vendor existence and user query safety.
        Returns True if passed, False if blocked.
        """
        state.log_event(
            agent_name="SecOps Guardrail",
            event_type="VALIDATION",
            message=f"Checkpoint 1: Verifying query safety and vendor allowlist for '{state.vendor_name}'."
        )

        # 1. Allowlist verification
        if state.vendor_name not in self.allowlist:
            reason = f"Access Denied: Vendor '{state.vendor_name}' is not in the enterprise approved allowlist."
            state.security_status.update({
                "checkpoint_1_passed": False,
                "is_blocked": True,
                "blocked_reason": reason,
                "blocked_checkpoint": 1
            })
            state.verdict = "BLOCKED"
            state.verdict_summary = reason
            state.log_event(
                agent_name="SecOps Guardrail",
                event_type="SECURITY_ALERT",
                message=reason,
                status="BLOCKED",
                payload={"checkpoint": 1, "vendor": state.vendor_name}
            )
            return False

        # 2. Query injection detection
        is_safe, matched_term = self.is_safe_text(state.user_query)
        if not is_safe:
            reason = f"Security Violation: Malicious prompt injection pattern detected in user query: '{matched_term}'."
            state.security_status.update({
                "checkpoint_1_passed": False,
                "is_blocked": True,
                "blocked_reason": reason,
                "blocked_checkpoint": 1
            })
            state.verdict = "BLOCKED"
            state.verdict_summary = reason
            state.log_event(
                agent_name="SecOps Guardrail",
                event_type="SECURITY_ALERT",
                message=reason,
                status="BLOCKED",
                payload={"checkpoint": 1, "matched_pattern": matched_term}
            )
            return False

        state.security_status["checkpoint_1_passed"] = True
        state.log_event(
            agent_name="SecOps Guardrail",
            event_type="OBSERVATION",
            message="Checkpoint 1 Passed: Vendor verified on allowlist and user query is clean.",
            status="COMPLETED"
        )
        return True

    def validate_checkpoint_2(self, state: AuditState) -> bool:
        """
        Checkpoint 2: Scans all retrieved document chunks for embedded prompt injections.
        Quarantines malicious chunks and fails closed if poisoned content is detected.
        """
        state.log_event(
            agent_name="SecOps Guardrail",
            event_type="VALIDATION",
            message=f"Checkpoint 2: Scanning {len(state.research_results)} retrieved document chunks for indirect prompt injection."
        )

        quarantined = []
        for chunk in state.research_results:
            is_safe, matched_term = self.is_safe_text(chunk.get("text", ""))
            if not is_safe:
                quarantine_record = {
                    "doc_id": chunk.get("doc_id"),
                    "title": chunk.get("title"),
                    "text": chunk.get("text"),
                    "matched_pattern": matched_term,
                    "vendor": state.vendor_name
                }
                quarantined.append(quarantine_record)
                chunk["is_safe"] = False
                chunk["quarantine_reason"] = f"Embedded injection pattern: '{matched_term}'"
            else:
                chunk["is_safe"] = True

        if quarantined:
            state.security_status.update({
                "checkpoint_2_passed": False,
                "is_blocked": True,
                "blocked_reason": f"Indirect Prompt Injection Quarantined: Found {len(quarantined)} poisoned document(s) in {state.vendor_name} corpus.",
                "blocked_checkpoint": 2,
                "quarantined_chunks": quarantined
            })
            state.verdict = "BLOCKED"
            state.verdict_summary = f"Audit halted: Document {quarantined[0]['doc_id']} contains malicious instructions ('{quarantined[0]['matched_pattern']}'). Fail-closed activated."
            state.log_event(
                agent_name="SecOps Guardrail",
                event_type="SECURITY_ALERT",
                message=f"Checkpoint 2 FAILED: Quarantined poisoned document {quarantined[0]['doc_id']}.",
                status="BLOCKED",
                payload={"checkpoint": 2, "quarantined_docs": quarantined}
            )
            return False

        state.security_status["checkpoint_2_passed"] = True
        state.log_event(
            agent_name="SecOps Guardrail",
            event_type="OBSERVATION",
            message="Checkpoint 2 Passed: All retrieved document chunks verified safe and unpoisoned.",
            status="COMPLETED"
        )
        return True
