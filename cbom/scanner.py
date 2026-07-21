"""
CBOM Scanner — Cryptographic Bill of Materials Generator
Scans source code for weak/quantum-vulnerable cryptographic usages.
Supports: Python (AST + regex), Java, C/C++, JavaScript/TypeScript (regex)
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cbom.patterns import LANGUAGE_MAP, RISK_ORDER
from cbom.risk_model import DataSensitivity, compute_risk


@dataclass
class CBOMEntry:
    id: str
    file: str
    line: int
    language: str
    algorithm: str
    pattern_matched: str
    risk_level: str          # CRITICAL / HIGH / MEDIUM / LOW
    risk_score: float
    harvest_now_decrypt_later: bool
    years_until_vulnerable: int
    recommendation: str
    nqm_mapping: str
    data_sensitivity: str
    code_snippet: str


@dataclass
class CBOMReport:
    scan_id: str
    timestamp: str
    target_path: str
    total_files_scanned: int
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    hndl_risk_count: int
    entries: list[CBOMEntry] = field(default_factory=list)
    summary: str = ""


def _generate_id(file: str, line: int, algo: str) -> str:
    raw = f"{file}:{line}:{algo}"
    return "CBOM-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()


def _get_snippet(lines: list[str], lineno: int, context: int = 1) -> str:
    start = max(0, lineno - 1 - context)
    end = min(len(lines), lineno + context)
    snippet_lines = []
    for i, l in enumerate(lines[start:end], start=start + 1):
        marker = ">>>" if i == lineno else "   "
        snippet_lines.append(f"{marker} {i:4d}: {l.rstrip()}")
    return "\n".join(snippet_lines)


class CBOMScanner:
    def __init__(
        self,
        data_sensitivity: DataSensitivity = "CONFIDENTIAL",
        years_data_must_stay_secret: int = 10,
        exclude_dirs: list[str] | None = None,
    ):
        self.data_sensitivity = data_sensitivity
        self.years_data_must_stay_secret = years_data_must_stay_secret
        self.exclude_dirs = set(exclude_dirs or [
            ".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build",
        ])

    def scan_path(self, target: str | Path) -> CBOMReport:
        target = Path(target)
        scan_id = "SCAN-" + hashlib.sha256(str(target).encode()).hexdigest()[:6].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        entries: list[CBOMEntry] = []
        files_scanned = 0

        if target.is_file():
            files_scanned = 1
            entries = self._scan_file(target)
        else:
            for root, dirs, files in os.walk(target):
                dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
                for fname in files:
                    fp = Path(root) / fname
                    if fp.suffix in LANGUAGE_MAP:
                        files_scanned += 1
                        entries.extend(self._scan_file(fp))

        # Deduplicate by id
        seen = set()
        unique_entries: list[CBOMEntry] = []
        for e in entries:
            if e.id not in seen:
                seen.add(e.id)
                unique_entries.append(e)

        # Sort by risk
        unique_entries.sort(key=lambda e: RISK_ORDER.get(e.risk_level, 99))

        critical = sum(1 for e in unique_entries if e.risk_level == "CRITICAL")
        high = sum(1 for e in unique_entries if e.risk_level == "HIGH")
        medium = sum(1 for e in unique_entries if e.risk_level == "MEDIUM")
        low = sum(1 for e in unique_entries if e.risk_level == "LOW")
        hndl = sum(1 for e in unique_entries if e.harvest_now_decrypt_later)

        summary = (
            f"Scanned {files_scanned} files. Found {len(unique_entries)} cryptographic findings. "
            f"CRITICAL: {critical}, HIGH: {high}, MEDIUM: {medium}, LOW: {low}. "
            f"HNDL risk (harvest-now-decrypt-later) findings: {hndl}."
        )

        return CBOMReport(
            scan_id=scan_id,
            timestamp=timestamp,
            target_path=str(target),
            total_files_scanned=files_scanned,
            total_findings=len(unique_entries),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            hndl_risk_count=hndl,
            entries=unique_entries,
            summary=summary,
        )

    def _scan_file(self, filepath: Path) -> list[CBOMEntry]:
        ext = filepath.suffix.lower()
        if ext not in LANGUAGE_MAP:
            return []

        language, patterns = LANGUAGE_MAP[ext]

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        lines = content.splitlines()
        entries: list[CBOMEntry] = []

        for pat_def in patterns:
            regex = re.compile(pat_def["pattern"], re.IGNORECASE)
            for lineno, line in enumerate(lines, start=1):
                if regex.search(line):
                    algo = pat_def["algorithm"]
                    ra = compute_risk(
                        algo,
                        self.data_sensitivity,
                        self.years_data_must_stay_secret,
                    )
                    eid = _generate_id(str(filepath), lineno, algo)
                    snippet = _get_snippet(lines, lineno)
                    entries.append(CBOMEntry(
                        id=eid,
                        file=str(filepath),
                        line=lineno,
                        language=language,
                        algorithm=algo,
                        pattern_matched=pat_def["pattern"],
                        risk_level=ra.risk_tier,
                        risk_score=ra.risk_score,
                        harvest_now_decrypt_later=ra.harvest_now_decrypt_later,
                        years_until_vulnerable=ra.years_until_vulnerable,
                        recommendation=ra.recommendation,
                        nqm_mapping=ra.nqm_mapping,
                        data_sensitivity=self.data_sensitivity,
                        code_snippet=snippet,
                    ))

        return entries

    def to_json(self, report: CBOMReport, indent: int = 2) -> str:
        def _serial(obj: Any) -> Any:
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        data = {
            "cbom_version": "1.0",
            "scan_id": report.scan_id,
            "timestamp": report.timestamp,
            "target_path": report.target_path,
            "statistics": {
                "files_scanned": report.total_files_scanned,
                "total_findings": report.total_findings,
                "by_risk": {
                    "CRITICAL": report.critical_count,
                    "HIGH": report.high_count,
                    "MEDIUM": report.medium_count,
                    "LOW": report.low_count,
                },
                "hndl_risk_count": report.hndl_risk_count,
            },
            "summary": report.summary,
            "findings": [asdict(e) for e in report.entries],
        }
        return json.dumps(data, indent=indent, default=_serial)


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    scanner = CBOMScanner(data_sensitivity="CONFIDENTIAL", years_data_must_stay_secret=10)
    report = scanner.scan_path(target)
    print(scanner.to_json(report))
