"""
Agent 7 — Business Automation Agent
Translates final audit verdicts and human reviews into ready-to-dispatch department action drafts:
Production Planning, Quality Control, and Purchasing.
"""

from typing import List, Dict, Any, Optional
from orchestration.state import AuditState


class BusinessAutomationAgent:
    """
    Business Automation Agent.
    Generates actionable, cross-department drafts tailored to the specific risk outcome.
    Never executes real external side-effects (safe simulated drafts only).
    """

    def generate_department_actions(self, state: AuditState) -> List[Dict[str, Any]]:
        """
        Synthesizes department drafts based on final verdict and human-in-the-loop decisions.
        """
        # Blocked runs produce zero department actions
        if state.verdict == "BLOCKED" or state.security_status.get("is_blocked", False):
            state.log_event(
                agent_name="Business Automation Agent",
                event_type="SECURITY_ALERT",
                message="Workflow BLOCKED: No department actions generated due to security incident.",
                status="BLOCKED"
            )
            state.department_actions = []
            return []

        # If awaiting human review, block premature generation
        if state.awaiting_human_review and state.human_review is None:
            state.log_event(
                agent_name="Business Automation Agent",
                event_type="OBSERVATION",
                message="Workflow paused: Department action generation awaits mandatory human review.",
                status="RUNNING"
            )
            return []

        vendor = state.vendor_name
        vendor_data = state.vendor_data
        open_pos = vendor_data.get("open_pos", [])
        parts = vendor_data.get("parts_supplied", ["Parts"])
        alternate = vendor_data.get("alternate_supplier", "Approved Secondary Sourcing")
        pos_str = ", ".join(open_pos) if open_pos else "None"
        parts_str = ", ".join(parts)

        effective_verdict = state.verdict
        # If escalated, check human decision
        if state.verdict == "ESCALATE" and state.human_review:
            effective_verdict = f"ESCALATE_{state.human_review.get('decision', 'REJECT')}"

        actions = []

        # =====================================================================
        # 1. PRODUCTION PLANNING
        # =====================================================================
        if effective_verdict == "APPROVE":
            prod_action = {
                "department": "Production Planning",
                "action_type": "NORMAL_SCHEDULING",
                "title": "Standard Production Allocation",
                "description": f"Authorize scheduled production allocations for {vendor}. Open orders ({pos_str}) confirmed for manufacturing lines.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": None,
                "status": "DRAFT"
            }
        elif effective_verdict == "ESCALATE_APPROVE":
            prod_action = {
                "department": "Production Planning",
                "action_type": "LEAD_TIME_BUFFER",
                "title": "Apply Production Lead-Time Buffer",
                "description": f"Add 5-day lead-time safety buffer on open orders ({pos_str}) for {parts_str} to absorb delivery delay risks.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": alternate,
                "status": "DRAFT"
            }
        else:  # REJECT or ESCALATE_REJECT
            prod_action = {
                "department": "Production Planning",
                "action_type": "SUPPLY_DISRUPTION_ALERT",
                "title": "Flag Open Orders & Emergency Re-routing",
                "description": f"CRITICAL ALERT: Open purchase orders ({pos_str}) at risk for {parts_str}. Freeze production line staging and transfer demand to alternate supplier: {alternate}.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": alternate,
                "status": "DRAFT"
            }
        actions.append(prod_action)

        # =====================================================================
        # 2. QUALITY CONTROL
        # =====================================================================
        if effective_verdict == "APPROVE":
            qc_action = {
                "department": "Quality Control",
                "action_type": "NORMAL_INSPECTION",
                "title": "Standard Incoming Inspection (Level II)",
                "description": f"Maintain standard statistical sampling (MIL-STD-105E / AQL 1.0) on all incoming consignments from {vendor}.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": None,
                "status": "DRAFT"
            }
        elif effective_verdict == "ESCALATE_APPROVE":
            qc_action = {
                "department": "Quality Control",
                "action_type": "ENHANCED_100_PERCENT_INSPECTION",
                "title": "Mandatory 100% Inspection on First 3 Lots",
                "description": f"Enforce 100% receiving inspection for the next three consecutive shipment lots of {parts_str}. Mandatory Certificate of Analysis (CoA) sign-off required prior to stock release.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": None,
                "status": "DRAFT"
            }
        else:  # REJECT or ESCALATE_REJECT
            qc_action = {
                "department": "Quality Control",
                "action_type": "QUARANTINE_HOLD",
                "title": "Immediate Quarantine & Inventory Hold",
                "description": f"Place all received or transit inventory of {parts_str} from {vendor} on immediate quality quarantine hold. Block warehouse issue slips pending Return-to-Vendor (RTV) disposal.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": None,
                "status": "DRAFT"
            }
        actions.append(qc_action)

        # =====================================================================
        # 3. PURCHASING
        # =====================================================================
        if effective_verdict == "APPROVE":
            purch_action = {
                "department": "Purchasing",
                "action_type": "AVL_APPROVAL",
                "title": "Confirm Approved Vendor List (AVL) Status",
                "description": f"Confirm {vendor} on active Approved Vendor List (AVL). Proceed with standard master service agreement and scheduled releases.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": None,
                "status": "DRAFT"
            }
        elif effective_verdict == "ESCALATE_APPROVE":
            # Check if ISO reminder is relevant
            r4_fired = any(f["rule_id"] == "R4" for f in state.critic_findings)
            r4_note = " Issue mandatory ISO 9001 certificate renewal reminder." if r4_fired else ""
            purch_action = {
                "department": "Purchasing",
                "action_type": "CONDITIONAL_AVL_AND_CAPA",
                "title": "Probationary AVL Entry & Corrective Action Request",
                "description": f"Grant conditional 90-day probationary AVL entry for {vendor}. Issue formal Corrective Action Request (CAPA-2026-MED) with mandatory 30-day remediation timeline.{r4_note}",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": alternate,
                "status": "DRAFT"
            }
        else:  # REJECT or ESCALATE_REJECT
            purch_action = {
                "department": "Purchasing",
                "action_type": "PROCUREMENT_HOLD_AND_RFQ",
                "title": "Vendor Procurement Hold & Alternate Supplier RFQ",
                "description": f"Place {vendor} on IMMEDIATE PROCUREMENT HOLD. Terminate pending purchase requisitions. Draft emergency Request for Quotation (RFQ-2026-ALT) to alternate supplier: {alternate}.",
                "affected_pos": open_pos,
                "parts": parts,
                "suggested_alternate": alternate,
                "status": "DRAFT"
            }
        actions.append(purch_action)

        state.department_actions = actions
        state.outbox_status = "PENDING_CONFIRMATION"

        state.log_event(
            agent_name="Business Automation Agent",
            event_type="ACTION_DRAFT",
            message=f"Generated {len(actions)} department action drafts for Production Planning, Quality Control, and Purchasing.",
            payload={"actions": actions}
        )
        return actions
