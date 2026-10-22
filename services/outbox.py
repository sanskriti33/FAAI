"""
Simulated Department Outbox Service.
Persists and manages confirmed action drafts across Production, QC, and Purchasing.
Clearly demarcates simulated local actions from real external ERP/email systems.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from config import DATA_DIR


class OutboxService:
    """
    Simulated Enterprise Outbox Service.
    Stores and manages action drafts confirmed by the user.
    """

    def __init__(self, outbox_file: Optional[Path] = None):
        self.outbox_file = outbox_file or (DATA_DIR / "department_outbox.json")
        self._ensure_file()

    def _ensure_file(self):
        if not self.outbox_file.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.outbox_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def dispatch_actions(self, audit_id: str, vendor_name: str, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Confirms drafts and records them into the simulated outbox table.
        """
        all_entries = self.get_all_entries()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        confirmed_entries = []
        for action in actions:
            entry = {
                "dispatch_id": f"DSP-{str(uuid.uuid4())[:8].upper()}",
                "audit_id": audit_id,
                "vendor_name": vendor_name,
                "timestamp": now_str,
                "department": action.get("department", "General"),
                "action_type": action.get("action_type", "ACTION"),
                "title": action.get("title", ""),
                "description": action.get("description", ""),
                "affected_pos": action.get("affected_pos", []),
                "parts": action.get("parts", []),
                "suggested_alternate": action.get("suggested_alternate"),
                "status": "DISPATCHED_TO_SIMULATED_OUTBOX"
            }
            confirmed_entries.append(entry)
            all_entries.insert(0, entry)

        with open(self.outbox_file, "w", encoding="utf-8") as f:
            json.dump(all_entries, f, indent=2)

        return confirmed_entries

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Retrieves all confirmed outbox entries."""
        try:
            with open(self.outbox_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def clear_outbox(self):
        """Resets the simulated outbox."""
        with open(self.outbox_file, "w", encoding="utf-8") as f:
            json.dump([], f)
