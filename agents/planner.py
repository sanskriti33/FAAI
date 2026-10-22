"""
Agent 2 — Master Planner
Implements ReAct-style planning, dynamic task expansion, and revision loops.
"""

from typing import List, Dict, Any
from orchestration.state import AuditState


class MasterPlannerAgent:
    """
    Master Planner Agent using Chain-of-Thought (CoT) and ReAct principles.
    1. Creates initial 2 base tasks.
    2. Inspects worker observations (ratios, compliance alerts).
    3. Dynamically expands task plan (e.g. 2 -> 5 tasks for Titanium).
    4. Handles REVISE loops from Critic Auditor (up to max 2 replanning cycles).
    """

    def create_initial_plan(self, state: AuditState) -> List[Dict[str, Any]]:
        """
        Generates the two fundamental base audit tasks.
        """
        initial_tasks = [
            {
                "task_id": "T1",
                "title": "Retrieve compliance & audit documentation",
                "agent": "Research Agent",
                "status": "PENDING",
                "description": f"Query document corpus for {state.vendor_name} to find safety, compliance, and financial records.",
                "reason": "Base audit requirement: Document evidence extraction."
            },
            {
                "task_id": "T2",
                "title": "Execute deterministic financial and statutory checks",
                "agent": "Executor Agent",
                "status": "PENDING",
                "description": f"Compute debt-to-revenue ratio, payment delay, ISO 9001 validity, and GST status for {state.vendor_name}.",
                "reason": "Base audit requirement: Quantitative policy verification."
            }
        ]

        state.tasks = initial_tasks
        state.initial_task_count = 2
        state.expanded_task_count = 2

        state.log_event(
            agent_name="Master Planner",
            event_type="PLAN",
            message=f"THOUGHT 1: Audit initiated for {state.vendor_name} ({state.vendor_data.get('industry', 'General')}). Generated 2 base tasks.",
            payload={"tasks": initial_tasks}
        )
        return initial_tasks

    def evaluate_and_expand_plan(self, state: AuditState) -> List[Dict[str, Any]]:
        """
        Inspects observations from Tasks 1 and 2 and dynamically expands the task plan.
        For Titanium Machinery Spares, expands from 2 to 5 tasks based on risk findings.
        """
        state.log_event(
            agent_name="Master Planner",
            event_type="OBSERVATION",
            message="Evaluating worker observations from Research (T1) and Executor (T2)."
        )

        debt_ratio_info = state.executor_results.get("debt_to_revenue", {})
        ratio = debt_ratio_info.get("ratio", 0.0)
        
        # Check if compliance breach was observed in retrieved docs
        compliance_breach = False
        breach_text = ""
        for chunk in state.research_results:
            t = chunk.get("text", "").lower()
            if "failed" in t or "fines active" in t or "regulatory fines" in t:
                compliance_breach = True
                breach_text = chunk.get("doc_id", "DOC")
                break

        added_tasks = []

        # Expansion Rule 1: High leverage detected (> 0.50) -> Run Peer Benchmarking
        if ratio > 0.50:
            t3 = {
                "task_id": "T3",
                "title": "Run industry peer benchmark analysis",
                "agent": "Executor Agent",
                "status": "PENDING",
                "description": f"Benchmark leverage ratio {ratio:.2f} against {state.vendor_data.get('industry', 'sector')} median.",
                "reason": f"High financial leverage ({ratio:.2f} > 0.50) requires comparative peer risk analysis."
            }
            state.tasks.append(t3)
            added_tasks.append(t3)

        # Expansion Rule 2: Active regulatory fine or breach -> Targeted search for corrective action
        if compliance_breach:
            t4 = {
                "task_id": "T4",
                "title": "Retrieve regulatory fine status and corrective action history",
                "agent": "Research Agent",
                "status": "PENDING",
                "description": f"Perform targeted search on {breach_text} to check for remedial filings, settlement receipts, or CAPA.",
                "reason": f"Active compliance breach ({breach_text}) requires verification of remediation history."
            }
            state.tasks.append(t4)
            added_tasks.append(t4)

        # Task 5: Software Development Monitoring Script
        t5 = {
            "task_id": f"T{len(state.tasks) + 1}",
            "title": "Generate and self-test vendor monitoring script",
            "agent": "Software Development Agent",
            "status": "PENDING",
            "description": f"Synthesize all financial, certification, and compliance findings into a verified Python monitoring script.",
            "reason": "Enterprise monitoring requirement: Automated continuous risk tracking."
        }
        state.tasks.append(t5)
        added_tasks.append(t5)

        state.expanded_task_count = len(state.tasks)

        if len(added_tasks) > 1:
            state.log_event(
                agent_name="Master Planner",
                event_type="PLAN_UPDATE",
                message=f"THOUGHT 2: Risk observations trigger dynamic plan expansion! Plan expanded from 2 to {len(state.tasks)} tasks.",
                payload={"added_tasks": added_tasks, "total_tasks": len(state.tasks)}
            )
        else:
            state.log_event(
                agent_name="Master Planner",
                event_type="PLAN_UPDATE",
                message=f"THOUGHT 2: Standard audit progression. Plan finalized with {len(state.tasks)} tasks.",
                payload={"total_tasks": len(state.tasks)}
            )

        return state.tasks

    def replan_for_revision(self, state: AuditState, broaden_query: bool = True) -> str:
        """
        Handles Critic REVISE instructions by broadening search queries or adding verification tasks.
        """
        state.revision_count += 1
        new_query = f"{state.user_query} environmental management quality certificates and compliance records"
        
        state.log_event(
            agent_name="Master Planner",
            event_type="PLAN",
            message=f"REPLAN (Cycle {state.revision_count}/2): Critic requested revision due to insufficient evidence. Broadening retrieval scope.",
            payload={"old_query": state.user_query, "revised_query": new_query}
        )
        return new_query
