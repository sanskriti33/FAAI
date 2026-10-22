"""
Orchestrator Workflow Engine.
Coordinates seven specialized agents using ReAct orchestration,
concurrent worker execution, dual security checkpoints, and human-in-the-loop gates.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from config import DATA_DIR, POLICY_THRESHOLDS
from .state import AuditState
from agents.guardrail import SecOpsGuardrailAgent
from agents.planner import MasterPlannerAgent
from agents.research import ResearchAgent
from agents.executor import ExecutorAgent
from agents.software_development import SoftwareDevelopmentAgent
from agents.critic import CriticAuditorAgent
from agents.business_automation import BusinessAutomationAgent
from services.audit_history import AuditHistoryService


class AuditOrchestrator:
    """
    Central Orchestrator coordinating all seven agents.
    Enforces the complete ReAct pipeline:
    PLAN -> ACTION -> OBSERVATION -> PLAN UPDATE -> VALIDATION -> DECISION -> HUMAN-IN-THE-LOOP -> ACTION DRAFTS
    """

    def __init__(
        self,
        vendors_path: Optional[Path] = None,
        history_service: Optional[AuditHistoryService] = None
    ):
        self.vendors_path = vendors_path or (DATA_DIR / "vendors.json")
        self.history_service = history_service or AuditHistoryService()
        self.vendors_db = self._load_vendors()

        # Initialize agents
        self.guardrail = SecOpsGuardrailAgent()
        self.planner = MasterPlannerAgent()
        self.research = ResearchAgent()
        self.executor = ExecutorAgent()
        self.dev_agent = SoftwareDevelopmentAgent()
        self.critic = CriticAuditorAgent()
        self.automation = BusinessAutomationAgent()

    def _load_vendors(self) -> Dict[str, Any]:
        if not self.vendors_path.exists():
            return {}
        with open(self.vendors_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_audit(self, vendor_name: str, query: str, state: Optional[AuditState] = None) -> AuditState:
        """
        Executes end-to-end multi-agent vendor audit workflow.
        """
        # 1. Initialize State
        if state is None:
            state = AuditState(vendor_name=vendor_name, user_query=query)

        vendor_profile = self.vendors_db.get(vendor_name, {})
        state.vendor_data = vendor_profile

        state.log_event(
            agent_name="Audit Orchestrator",
            event_type="PLAN",
            message=f"Received audit request for vendor '{vendor_name}': '{query}'."
        )

        # -------------------------------------------------------------
        # STEP 1: SecOps Guardrail — Checkpoint 1 (Fail-Closed)
        # -------------------------------------------------------------
        cp1_ok = self.guardrail.validate_checkpoint_1(state)
        if not cp1_ok:
            self.history_service.record_audit(state)
            return state

        # -------------------------------------------------------------
        # STEP 2: Master Planner — Initial 2 Base Tasks
        # -------------------------------------------------------------
        self.planner.create_initial_plan(state)

        # -------------------------------------------------------------
        # STEP 3 & 4: Worker Tier (Agents 3 & 4 in Parallel) + Replanning Loop
        # -------------------------------------------------------------
        max_loops = POLICY_THRESHOLDS.get("MAX_REVISION_CYCLES", 2) + 1
        active_query = state.user_query

        for loop_idx in range(max_loops):
            # Parallel execution of Research (A3) and Executor (A4)
            with ThreadPoolExecutor(max_workers=2) as executor_pool:
                f3 = executor_pool.submit(self.research.execute_research, state, active_query)
                f4 = executor_pool.submit(self.executor.execute_tools, state)
                f3.result()
                f4.result()

            # Mark Tasks 1 and 2 as COMPLETED
            for t in state.tasks:
                if t["task_id"] in ["T1", "T2"]:
                    t["status"] = "COMPLETED"

            # ---------------------------------------------------------
            # STEP 4: SecOps Guardrail — Checkpoint 2 (Fail-Closed)
            # ---------------------------------------------------------
            cp2_ok = self.guardrail.validate_checkpoint_2(state)
            if not cp2_ok:
                self.history_service.record_audit(state)
                return state

            # ---------------------------------------------------------
            # STEP 5: Dynamic Plan Expansion (Planner ReAct)
            # ---------------------------------------------------------
            if loop_idx == 0:
                self.planner.evaluate_and_expand_plan(state)

                # Execute dynamically added tasks if any
                for task in state.tasks:
                    if task["task_id"] == "T3" and task["status"] == "PENDING":
                        self.executor.execute_peer_benchmark(state)
                        task["status"] = "COMPLETED"
                    elif task["task_id"] == "T4" and task["status"] == "PENDING":
                        # Targeted search for compliance breach remediation
                        self.research.targeted_followup_search(state, "hazardous material corrective action fine settlement")
                        task["status"] = "COMPLETED"

            # ---------------------------------------------------------
            # STEP 6: Software Development Agent — Monitoring Script & Test
            # ---------------------------------------------------------
            self.dev_agent.generate_and_test_script(state)
            for task in state.tasks:
                if "Software Development" in task.get("agent", ""):
                    task["status"] = "COMPLETED"

            # ---------------------------------------------------------
            # STEP 7: Critic Auditor Verification
            # ---------------------------------------------------------
            verdict = self.critic.audit(state)
            if verdict != "REVISE":
                break

            # If REVISE, Planner reformulates query and loops
            active_query = self.planner.replan_for_revision(state, broaden_query=True)

        # -------------------------------------------------------------
        # STEP 8: Decision Handling & Business Automation
        # -------------------------------------------------------------
        if state.verdict == "ESCALATE":
            # Human review required before department actions
            state.awaiting_human_review = True
            state.log_event(
                agent_name="Audit Orchestrator",
                event_type="OBSERVATION",
                message="Workflow paused for human decision. Department drafts on hold until review submitted."
            )
        else:
            # Generate department action drafts directly
            self.automation.generate_department_actions(state)

        # Persist audit state
        self.history_service.record_audit(state)
        return state

    def resume_after_human_review(
        self,
        state: AuditState,
        human_decision: str,
        reason: str,
        reviewer_name: str = "Procurement Review Board"
    ) -> AuditState:
        """
        Resumes workflow after human decision is submitted for an ESCALATED audit.
        """
        clean_reason = reason.strip()
        if not clean_reason:
            raise ValueError("A mandatory non-empty business rationale must be provided for human review.")

        valid_decisions = ["APPROVE", "REJECT"]
        norm_decision = human_decision.strip().upper()
        if norm_decision not in valid_decisions:
            raise ValueError(f"Invalid human decision '{human_decision}'. Must be 'APPROVE' or 'REJECT'.")

        review_record = {
            "reviewed_by": reviewer_name,
            "decision": norm_decision,
            "reason": clean_reason,
            "timestamp": state.timestamp
        }
        state.human_review = review_record
        state.awaiting_human_review = False

        state.log_event(
            agent_name="Human Reviewer",
            event_type="HUMAN_REVIEW",
            message=f"Human Decision recorded: {norm_decision}. Rationale: '{clean_reason}'.",
            payload=review_record
        )

        # Generate department actions using human review outcome
        self.automation.generate_department_actions(state)

        # Update audit history
        self.history_service.record_audit(state)
        return state
