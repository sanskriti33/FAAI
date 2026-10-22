"""
Agent 4 — Executor Agent
Executes deterministic financial, statutory, certification, and benchmark checks.
"""

from typing import Dict, Any, Optional
from orchestration.state import AuditState
from tools.financial_tools import compute_debt_to_revenue, compute_payment_delay, compute_peer_benchmark
from tools.certificate_tools import check_iso9001_validity
from tools.vendor_tools import check_gst_status, check_blacklist_status


class ExecutorAgent:
    """
    Executor Agent responsible for deterministic quantitative checks.
    Runs exact arithmetic calculations and statutory verifications.
    """

    def execute_tools(self, state: AuditState) -> Dict[str, Any]:
        """
        Executes standard deterministic toolset for the given vendor.
        """
        vendor_data = state.vendor_data
        financials = vendor_data.get("financials", {})
        revenue = float(financials.get("revenue", 1.0))
        debt = float(financials.get("debt", 0.0))
        delay_days = int(financials.get("avg_delay_days", 0))
        iso_expiry = str(vendor_data.get("iso9001_expiry", "2026-01-01"))
        gst_status = str(vendor_data.get("gst_status", "ACTIVE"))
        is_blacklisted = bool(vendor_data.get("blacklisted", False))

        state.log_event(
            agent_name="Executor Agent",
            event_type="ACTION",
            message=f"ACTION 1: Executing deterministic checks (Debt Ratio, Payment Delay, ISO Expiry, GST, Blacklist) for '{state.vendor_name}'."
        )

        debt_ratio_res = compute_debt_to_revenue(debt=debt, revenue=revenue)
        delay_res = compute_payment_delay(avg_delay_days=delay_days)
        iso_res = check_iso9001_validity(expiry_date_str=iso_expiry)
        gst_res = check_gst_status(gst_status=gst_status)
        blacklist_res = check_blacklist_status(vendor_name=state.vendor_name, is_blacklisted=is_blacklisted)

        results = {
            "debt_to_revenue": debt_ratio_res,
            "payment_delay": delay_res,
            "iso9001_check": iso_res,
            "gst_check": gst_res,
            "blacklist_check": blacklist_res
        }

        state.executor_results = results

        obs_summary = (
            f"Debt Ratio: {debt_ratio_res['ratio']:.2f} ({debt_ratio_res['status']}) | "
            f"Delay: {delay_days}d ({delay_res['status']}) | "
            f"ISO 9001: {iso_res['days_remaining']}d left ({iso_res['status']}) | "
            f"GST: {gst_status} ({gst_res['status']})"
        )

        state.log_event(
            agent_name="Executor Agent",
            event_type="OBSERVATION",
            message=obs_summary,
            payload=results
        )
        return results

    def execute_peer_benchmark(self, state: AuditState) -> Dict[str, Any]:
        """
        Executes comparative peer benchmark analysis (Task 3).
        """
        vendor_data = state.vendor_data
        debt_res = state.executor_results.get("debt_to_revenue", {})
        ratio = debt_res.get("ratio", 0.0)
        peer_median = float(vendor_data.get("peer_median_debt_ratio", 0.45))

        state.log_event(
            agent_name="Executor Agent",
            event_type="ACTION",
            message=f"ACTION 2: Running industry peer benchmark against {vendor_data.get('industry', 'Sector')} median ({peer_median:.2f})."
        )

        peer_res = compute_peer_benchmark(ratio=ratio, peer_median=peer_median)
        state.executor_results["peer_benchmark"] = peer_res

        state.log_event(
            agent_name="Executor Agent",
            event_type="OBSERVATION",
            message=f"Peer Benchmark complete: Variance {peer_res['variance']:+.2f} vs median {peer_median:.2f} ({peer_res['status']}).",
            payload=peer_res
        )
        return peer_res
