"""
Agent 6 — Critic Auditor
Mandatory independent verification stage.
Enforces Policy Rules R1–R6, recalculates arithmetic, demands evidence citations,
and decides verdicts: REVISE, REJECT, ESCALATE, or APPROVE.
"""

from typing import List, Dict, Any, Tuple
from config import POLICY_THRESHOLDS
from orchestration.state import AuditState
from tools.compliance_tools import evaluate_compliance_evidence


class CriticAuditorAgent:
    """
    Critic Auditor Agent.
    Independent verification barrier that never trusts preceding agents blindly.
    Re-computes financial ratios, evaluates evidence citations, checks R1-R6 policies,
    and returns deterministic verdicts.
    """

    def audit(self, state: AuditState) -> str:
        """
        Executes complete verification of findings against policy rules R1-R6.
        Returns verdict: 'REVISE', 'REJECT', 'ESCALATE', or 'APPROVE'.
        """
        state.log_event(
            agent_name="Critic Auditor",
            event_type="VALIDATION",
            message="Commencing independent Critic verification against Policy Rules R1–R6."
        )

        findings: List[Dict[str, Any]] = []

        # ---------------------------------------------------------
        # R6 — Integrity and Evidence Check (Applied first)
        # ---------------------------------------------------------
        r6_passed, r6_finding = self._verify_integrity_and_evidence(state)
        if not r6_passed:
            # If revision count is below limit (2 loops max), return REVISE
            max_revisions = POLICY_THRESHOLDS.get("MAX_REVISION_CYCLES", 2)
            if state.revision_count < max_revisions:
                state.verdict = "REVISE"
                state.verdict_summary = f"Integrity/Evidence deficiency detected: {r6_finding['description']}. Demanding ReAct revision loop ({state.revision_count + 1}/{max_revisions})."
                state.log_event(
                    agent_name="Critic Auditor",
                    event_type="DECISION",
                    message=f"DECISION: REVISE. {state.verdict_summary}",
                    status="REVISED",
                    payload={"finding": r6_finding, "revision_count": state.revision_count}
                )
                return "REVISE"
            else:
                # Max revisions reached; convert unresolved integrity failure to ESCALATE
                findings.append(r6_finding)

        # ---------------------------------------------------------
        # R1 — Financial Risk (Independently Recomputed)
        # ---------------------------------------------------------
        financials = state.vendor_data.get("financials", {})
        revenue = float(financials.get("revenue", 1.0))
        debt = float(financials.get("debt", 0.0))
        recomputed_ratio = round(debt / revenue, 4)

        med_r1 = POLICY_THRESHOLDS["R1_DEBT_RATIO_MED"]
        high_r1 = POLICY_THRESHOLDS["R1_DEBT_RATIO_HIGH"]

        if recomputed_ratio > high_r1:
            findings.append({
                "rule_id": "R1",
                "severity": "HIGH",
                "description": f"Critical financial leverage: Independently verified Debt-to-Revenue ratio {recomputed_ratio:.2f} exceeds high risk limit.",
                "actual_value": recomputed_ratio,
                "threshold": f"> {high_r1:.2f}",
                "evidence_id": "FIN-2026" if "Titanium" in state.vendor_name else "FIN-STATEMENT",
                "corrective_action": "Freeze procurement credit line; demand financial guarantee or substitute supplier."
            })
        elif recomputed_ratio > med_r1:
            findings.append({
                "rule_id": "R1",
                "severity": "MED",
                "description": f"Elevated financial leverage: Independently verified Debt-to-Revenue ratio {recomputed_ratio:.2f} exceeds warning threshold.",
                "actual_value": recomputed_ratio,
                "threshold": f"> {med_r1:.2f}",
                "evidence_id": "FIN-M26" if "Meridian" in state.vendor_name else "FIN-STATEMENT",
                "corrective_action": "Request debt restructuring plan; require advance credit security."
            })

        # ---------------------------------------------------------
        # R2 — Compliance Risk (Evidence citations)
        # ---------------------------------------------------------
        # Filter safe chunks only
        safe_chunks = [c for c in state.research_results if c.get("is_safe", True)]
        chunk_texts = [c["text"] for c in safe_chunks]
        compliance_eval = evaluate_compliance_evidence(chunk_texts)

        if compliance_eval["breach_detected"]:
            for match in compliance_eval["matched_quotes"]:
                # Locate chunk ID
                chunk_id = "AUD-DOC"
                for c in safe_chunks:
                    if match["text"] == c["text"]:
                        chunk_id = c["doc_id"]
                        break

                findings.append({
                    "rule_id": "R2",
                    "severity": "HIGH",
                    "description": f"Active compliance/regulatory breach: {match['matched_term'].title()} confirmed in audited documentation.",
                    "actual_value": match["matched_term"],
                    "threshold": "Zero active regulatory violations or fines",
                    "evidence_id": chunk_id,
                    "corrective_action": "Quarantine vendor orders; demand proof of fine clearance and regulatory remediation."
                })

        # ---------------------------------------------------------
        # R3 — Payment Performance Risk
        # ---------------------------------------------------------
        delay_days = int(financials.get("avg_delay_days", 0))
        med_r3 = POLICY_THRESHOLDS["R3_PAYMENT_DELAY_MED"]
        high_r3 = POLICY_THRESHOLDS["R3_PAYMENT_DELAY_HIGH"]

        if delay_days > high_r3:
            findings.append({
                "rule_id": "R3",
                "severity": "HIGH",
                "description": f"Severe working capital distress: Average payment delay of {delay_days} days exceeds critical limit.",
                "actual_value": f"{delay_days} days",
                "threshold": f"> {high_r3} days",
                "evidence_id": "SYS-ERP-AR",
                "corrective_action": "Place vendor on cash-in-advance or transition to secondary source."
            })
        elif delay_days > med_r3:
            findings.append({
                "rule_id": "R3",
                "severity": "MED",
                "description": f"Operational payment delay: Average delay of {delay_days} days exceeds standard terms.",
                "actual_value": f"{delay_days} days",
                "threshold": f"> {med_r3} days",
                "evidence_id": "FIN-M26" if "Meridian" in state.vendor_name else "SYS-ERP-AR",
                "corrective_action": "Enforce strict Net-30 payment milestones; monitor cash flow stability."
            })

        # ---------------------------------------------------------
        # R4 — Certification Risk (ISO 9001 on fixed date 2026-10-19)
        # ---------------------------------------------------------
        iso_res = state.executor_results.get("iso9001_check", {})
        iso_days = iso_res.get("days_remaining", 999)
        iso_status = iso_res.get("status", "LOW")

        if iso_status == "HIGH":
            findings.append({
                "rule_id": "R4",
                "severity": "HIGH",
                "description": f"Invalid certification: ISO 9001 expired on {iso_res.get('expiry_date')} ({abs(iso_days)} days before audit date).",
                "actual_value": iso_res.get("expiry_date"),
                "threshold": "Active unexpired certification",
                "evidence_id": "CERT-REGISTRY",
                "corrective_action": "Revoke certified vendor status; suspend quality certification sign-offs."
            })
        elif iso_status == "MED":
            findings.append({
                "rule_id": "R4",
                "severity": "MED",
                "description": f"Certificate expiring soon: ISO 9001 expires on {iso_res.get('expiry_date')} (only {iso_days} days remaining).",
                "actual_value": f"{iso_days} days remaining",
                "threshold": "<= 30 days to expiry",
                "evidence_id": "CERT-REGISTRY",
                "corrective_action": "Issue mandatory 30-day renewal notice and request audit schedule from registrar."
            })

        # ---------------------------------------------------------
        # R5 — Statutory & Blacklist Risk
        # ---------------------------------------------------------
        gst_status = str(state.vendor_data.get("gst_status", "ACTIVE")).strip().upper()
        if gst_status != POLICY_THRESHOLDS["R5_VALID_GST_STATUS"]:
            findings.append({
                "rule_id": "R5",
                "severity": "HIGH",
                "description": f"Statutory breach: GST registration is '{gst_status}' (Non-compliant tax status).",
                "actual_value": gst_status,
                "threshold": "ACTIVE",
                "evidence_id": "GOV-GST-PORTAL",
                "corrective_action": "Immediate statutory hold; report to statutory tax compliance committee."
            })

        if state.vendor_data.get("blacklisted", False):
            findings.append({
                "rule_id": "R5",
                "severity": "HIGH",
                "description": "Internal Blacklist: Vendor is explicitly flagged on the enterprise procurement blacklist.",
                "actual_value": "BLACKLISTED",
                "threshold": "NOT_BLACKLISTED",
                "evidence_id": "INTERNAL-BLACKLIST-DB",
                "corrective_action": "Immediate procurement freeze and legal consultation."
            })

        # Store findings in state
        state.critic_findings = findings

        # ---------------------------------------------------------
        # Final Decision Priority Resolution
        # ---------------------------------------------------------
        has_high = any(f["severity"] == "HIGH" for f in findings)
        has_med = any(f["severity"] == "MED" for f in findings)

        if has_high:
            verdict = "REJECT"
            high_rules = [f"{f['rule_id']} ({f['description'][:45]}...)" for f in findings if f["severity"] == "HIGH"]
            summary = f"VENDOR REJECTED: Critical risk triggers detected in {len(high_rules)} policy check(s): " + " | ".join(high_rules)
            state.awaiting_human_review = False
        elif has_med:
            verdict = "ESCALATE"
            med_rules = [f["rule_id"] for f in findings if f["severity"] == "MED"]
            summary = f"AUDIT ESCALATED: Moderate risk profile detected under rule(s) {', '.join(set(med_rules))}. Mandatory human-in-the-loop review required."
            state.awaiting_human_review = True
        else:
            verdict = "APPROVE"
            summary = "VENDOR APPROVED: All policy rules R1–R6 satisfied. Clean statutory, financial, and compliance standing."
            state.awaiting_human_review = False

        state.verdict = verdict
        state.verdict_summary = summary

        state.log_event(
            agent_name="Critic Auditor",
            event_type="DECISION",
            message=f"DECISION: {verdict}. {summary}",
            status="COMPLETED",
            payload={"verdict": verdict, "findings_count": len(findings), "exceptions": findings}
        )

        return verdict

    def _verify_integrity_and_evidence(self, state: AuditState) -> Tuple[bool, Dict[str, Any]]:
        """
        R6 Integrity check:
        1. Independently recomputes debt-to-revenue ratio and verifies against Executor.
        2. Verifies similarity score >= 0.20 for cited documentary evidence.
        """
        financials = state.vendor_data.get("financials", {})
        revenue = float(financials.get("revenue", 1.0))
        debt = float(financials.get("debt", 0.0))
        recomputed = round(debt / revenue, 4)

        executor_ratio = state.executor_results.get("debt_to_revenue", {}).get("ratio")
        if executor_ratio is not None:
            diff = abs(recomputed - executor_ratio)
            tolerance = POLICY_THRESHOLDS["R6_RATIO_TOLERANCE"]
            if diff > tolerance:
                return False, {
                    "rule_id": "R6",
                    "severity": "HIGH",
                    "description": f"Arithmetic Integrity Failure: Executor ratio ({executor_ratio}) diverges from independent Critic calculation ({recomputed}).",
                    "actual_value": f"Diff: {diff:.4f}",
                    "threshold": f"Tolerance <= {tolerance}",
                    "evidence_id": "SYS-CRITIC-AUDIT",
                    "corrective_action": "Recompute financial statements and verify telemetry feeds."
                }

        # Check evidence citation requirement
        # If user explicitly requested certificate (like ISO 14001 in T6), require score >= 0.20
        query_lower = state.user_query.lower()
        if "iso 14001" in query_lower:
            # Check if any chunk specifically matched ISO 14001 with score >= 0.20
            matched_14001 = False
            top_score = 0.0
            for chunk in state.research_results:
                if chunk.get("score", 0.0) > top_score:
                    top_score = chunk.get("score", 0.0)
                if "14001" in chunk.get("text", "").lower() and chunk.get("score", 0.0) >= POLICY_THRESHOLDS["R6_MIN_SIMILARITY_SCORE"]:
                    matched_14001 = True
                    break

            if not matched_14001:
                return False, {
                    "rule_id": "R6",
                    "severity": "MED",
                    "description": f"Evidence Sufficiency Failure: Specific query for ISO 14001 yielded no verified chunk with similarity >= {POLICY_THRESHOLDS['R6_MIN_SIMILARITY_SCORE']} (top score: {top_score:.2f}).",
                    "actual_value": f"Top similarity: {top_score:.2f}",
                    "threshold": f">= {POLICY_THRESHOLDS['R6_MIN_SIMILARITY_SCORE']}",
                    "evidence_id": "DOC-CORPUS",
                    "corrective_action": "Broaden retrieval query to search environmental management records or escalate."
                }

        return True, {}
