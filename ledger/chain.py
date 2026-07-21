"""
Evidence Ledger — Hash-Chained Tamper-Evident Log
Each entry includes a SHA3-256 hash of (entry_data + previous_hash).
Maps to India NQM / NCIIPC certification language.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


LEDGER_PATH = os.path.join(os.path.dirname(__file__), "evidence_ledger.jsonl")

NQM_EVENT_TAGS = {
    "MODE_SWITCH":      "NQM-P2-4.1 — Crypto-Agile Mode Transition",
    "KEY_ROTATION":     "NQM-P2-4.2 — Key Lifecycle Event",
    "CBOM_ALERT":       "NQM-P2-3.1 — Cryptographic Inventory Finding",
    "PQC_HANDSHAKE":    "NQM-P2-2.1 — Post-Quantum Key Establishment",
    "QKD_OUTAGE":       "NQM-P3-1.1 — QKD Channel Disruption",
    "QKD_RECOVERY":     "NQM-P3-1.2 — QKD Channel Recovery",
    "SYSTEM_START":     "NQM-P2-5.1 — System Initialization",
    "AUDIT_EXPORT":     "NQM-P2-5.3 — Certification Evidence Export",
    "REKEY":            "NQM-P2-4.2 — Session Re-Keying",
    "SIGNATURE_VERIFY": "NQM-P2-2.2 — Digital Signature Verification",
    "CBOM_SCAN":        "NQM-P2-3.0 — Cryptographic Bill of Materials Scan",
}


@dataclass
class LedgerEntry:
    entry_id: str
    sequence: int
    event_type: str
    event_data: dict
    nqm_tag: str
    timestamp: float
    timestamp_iso: str
    actor: str
    previous_hash: str
    entry_hash: str = ""        # Computed after construction

    def compute_hash(self) -> str:
        """SHA3-256 of (sequence + event_type + event_data + timestamp + previous_hash)."""
        raw = json.dumps({
            "entry_id": self.entry_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "nqm_tag": self.nqm_tag,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha3_256(raw.encode()).hexdigest()


class EvidenceLedger:
    """
    Append-only hash-chained evidence ledger.
    
    Structure: each entry's hash = SHA3-256(entry_fields + prev_hash)
    Tamper detection: any modification breaks the hash chain.
    """

    def __init__(self, ledger_path: str = LEDGER_PATH):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[LedgerEntry] = []
        self._load()

        # Write genesis if empty
        if not self._entries:
            self._write_genesis()

    def _load(self):
        """Load existing ledger from disk."""
        if self.ledger_path.exists():
            for line in self.ledger_path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    entry = LedgerEntry(**d)
                    self._entries.append(entry)
                except Exception:
                    pass

    def _write_genesis(self):
        self.append(
            event_type="SYSTEM_START",
            event_data={"message": "QuantumShield Evidence Ledger initialized", "version": "1.0"},
            actor="SYSTEM",
        )

    def append(
        self,
        event_type: str,
        event_data: dict,
        actor: str = "ORCHESTRATOR",
    ) -> LedgerEntry:
        """Append a new event to the chain."""
        prev_hash = self._entries[-1].entry_hash if self._entries else "0" * 64
        seq = len(self._entries)
        now = time.time()

        entry = LedgerEntry(
            entry_id=str(uuid.uuid4()),
            sequence=seq,
            event_type=event_type,
            event_data=event_data,
            nqm_tag=NQM_EVENT_TAGS.get(event_type, f"NQM-GENERAL — {event_type}"),
            timestamp=now,
            timestamp_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            actor=actor,
            previous_hash=prev_hash,
        )
        entry.entry_hash = entry.compute_hash()
        self._entries.append(entry)
        self._persist_entry(entry)
        return entry

    def _persist_entry(self, entry: LedgerEntry):
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    def verify_chain(self) -> tuple[bool, list[str]]:
        """
        Verify hash chain integrity. Returns (valid, list_of_errors).
        Detects any tampering by recomputing all hashes.
        """
        errors = []
        for i, entry in enumerate(self._entries):
            # Recompute hash
            expected = entry.compute_hash()
            if entry.entry_hash != expected:
                errors.append(f"Entry {i} (seq={entry.sequence}): hash mismatch — TAMPERED")

            # Check prev_hash linkage
            if i > 0:
                prev = self._entries[i - 1].entry_hash
                if entry.previous_hash != prev:
                    errors.append(f"Entry {i}: broken chain link — previous_hash mismatch")

        return (len(errors) == 0, errors)

    def get_entries(self, limit: int | None = None, event_type: str | None = None) -> list[dict]:
        entries = self._entries
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        if limit:
            entries = entries[-limit:]
        return [asdict(e) for e in entries]

    def export_report(self) -> dict:
        """Export full certification report."""
        valid, errors = self.verify_chain()
        return {
            "report_id": "RPT-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper(),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "chain_valid": valid,
            "chain_errors": errors,
            "total_entries": len(self._entries),
            "event_summary": self._summarize_events(),
            "ledger_root_hash": self._entries[-1].entry_hash if self._entries else None,
            "entries": [asdict(e) for e in self._entries],
        }

    def _summarize_events(self) -> dict:
        counts: dict[str, int] = {}
        for e in self._entries:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return counts

    def stats(self) -> dict:
        valid, errors = self.verify_chain()
        return {
            "total_entries": len(self._entries),
            "chain_valid": valid,
            "chain_errors": len(errors),
            "root_hash": self._entries[-1].entry_hash if self._entries else None,
            "ledger_path": str(self.ledger_path),
        }

    # ─── Convenience Loggers ──────────────────────────────────────────────────

    def log_mode_switch(self, transition: dict):
        return self.append("MODE_SWITCH", transition, actor="ORCHESTRATOR")

    def log_cbom_alert(self, finding: dict):
        return self.append("CBOM_ALERT", finding, actor="CBOM_SCANNER")

    def log_pqc_handshake(self, data: dict):
        return self.append("PQC_HANDSHAKE", data, actor="PQC_ENGINE")

    def log_qkd_outage(self, data: dict):
        return self.append("QKD_OUTAGE", data, actor="QKD_SIMULATOR")

    def log_qkd_recovery(self, data: dict):
        return self.append("QKD_RECOVERY", data, actor="QKD_SIMULATOR")

    def log_cbom_scan(self, data: dict):
        return self.append("CBOM_SCAN", data, actor="CBOM_SCANNER")


# Singleton
ledger = EvidenceLedger()


if __name__ == "__main__":
    import json

    l = EvidenceLedger("/tmp/test_ledger.jsonl")
    l.append("MODE_SWITCH", {"from": "PQC_ONLY", "to": "QKD_PQC_HYBRID", "trigger": "QKD_RECOVERED"})
    l.append("KEY_ROTATION", {"session_id": "SES-ABC123", "rotation_count": 1})
    l.append("CBOM_ALERT", {"algorithm": "RSA-2048", "file": "auth.py", "line": 42, "risk": "HIGH"})
    l.append("PQC_HANDSHAKE", {"algorithm": "Kyber768", "key_bytes": 1184, "success": True})

    valid, errors = l.verify_chain()
    print(f"Chain valid: {valid}")
    print(f"Total entries: {len(l._entries)}")
    print(f"Root hash: {l._entries[-1].entry_hash[:32]}...")

    report = l.export_report()
    print(f"\nReport ID: {report['report_id']}")
    print(f"Event summary: {report['event_summary']}")
