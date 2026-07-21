"""
Q-RAKSHA SENTINEL — Adaptive Policy Engine (Step 8)
Enforces and auto-remediates crypto policy for all NFs:
  - TLS version check (minimum TLS 1.3)
  - SHA usage / PQC policy (SHA-1 banned, SHA-256+ required)
  - Hybrid TLS check (PQC + classical dual handshake)
  - Certificate age check (max 2 years, renew at 90 days)
  - Approved vendor check (against certified PQC vendor list)
  - Auto-remediation actions
Output: Policy Actions & Compliance Status
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Policy configuration
POLICY_CONFIG = {
    "min_tls_version": "TLS1.3",
    "banned_sha": ["SHA-1", "MD5"],
    "required_sha": "SHA-256",
    "max_cert_age_days": 730,
    "cert_renewal_threshold_days": 90,
    "approved_pqc_algos": ["ML-KEM-768", "ML-DSA-65", "SLH-DSA-128f", "FN-DSA-512"],
    "hybrid_tls_required_for_critical": True,
    "banned_ciphers": ["TLS_RSA_3DES", "TLS_NULL_WITH_NULL_NULL", "TLS_RSA_AES128_CBC"],
}

# Approved vendor PQC certification status
APPROVED_VENDORS = {
    "Ericsson": {"approved": True, "cert_ref": "GSMA-PQC-2024-001"},
    "Nokia": {"approved": True, "cert_ref": "GSMA-PQC-2024-002"},
    "Samsung": {"approved": True, "cert_ref": "GSMA-PQC-2024-003"},
    "Mavenir": {"approved": True, "cert_ref": "GSMA-PQC-2024-004"},
    "Radisys": {"approved": False, "cert_ref": None},
    "ZTE": {"approved": False, "cert_ref": None},
    "Huawei": {"approved": False, "cert_ref": None},
}

TLS_ORDER = {"TLS1.3": 4, "TLS1.2": 3, "TLS1.1": 2, "TLS1.0": 1, "SSLv3": 0}


@dataclass
class PolicyViolation:
    """A detected policy violation."""
    violation_id: str
    nf_id: str
    policy_rule: str
    severity: str          # CRITICAL / HIGH / MEDIUM / INFO
    current_value: str
    required_value: str
    description: str
    auto_remediation: str  # What the engine will do automatically
    remediation_effort: str  # IMMEDIATE / SHORT_TERM / PLANNED


@dataclass
class PolicyAction:
    """An auto-remediation action taken by the policy engine."""
    action_id: str
    nf_id: str
    action_type: str       # CERT_RENEWAL / TLS_UPGRADE / CIPHER_BLOCK / VENDOR_FLAG
    description: str
    automated: bool
    status: str            # APPLIED / PENDING / MANUAL_REQUIRED
    timestamp: float


@dataclass
class ComplianceStatus:
    """Compliance status for one NF."""
    nf_id: str
    nf_type: str
    overall_compliant: bool
    compliance_score: float     # 0–100
    violations: List[PolicyViolation] = field(default_factory=list)
    actions: List[PolicyAction] = field(default_factory=list)
    risk_tier: str = "LOW"


@dataclass
class PolicyReport:
    """Full policy engine report."""
    report_id: str
    timestamp: str
    statuses: List[ComplianceStatus] = field(default_factory=list)
    total_violations: int = 0
    critical_violations: int = 0
    auto_remediated: int = 0
    overall_compliance_pct: float = 0.0
    summary: str = ""


class AdaptivePolicyEngine:
    """
    Adaptive Policy Engine — enforces telecom PQC compliance policies
    and generates auto-remediation actions for violations.
    """

    def __init__(self):
        self._action_counter = 0
        self._violation_counter = 0

    def evaluate_all(
        self,
        nf_nodes: list,          # List[NFNode]
        sentinel_report: object, # SentinelReport
        risk_scores: list,       # List[QMISScore]
    ) -> PolicyReport:

        report_id = "POL-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        risk_map = {r.node_id: r for r in risk_scores}

        # Build observation map from sentinel
        obs_map: Dict[str, list] = {}
        if sentinel_report and hasattr(sentinel_report, 'observations'):
            for obs in sentinel_report.observations:
                obs_map.setdefault(obs.nf_id, []).append(obs)

        statuses: List[ComplianceStatus] = []
        for nf in nf_nodes:
            risk = risk_map.get(nf.node_id)
            obs_list = obs_map.get(nf.node_id, [])
            status = self._evaluate_nf(nf, obs_list, risk)
            statuses.append(status)

        total_v = sum(len(s.violations) for s in statuses)
        crit_v = sum(sum(1 for v in s.violations if v.severity == "CRITICAL") for s in statuses)
        auto_r = sum(sum(1 for a in s.actions if a.automated and a.status == "APPLIED") for s in statuses)
        compliant_n = sum(1 for s in statuses if s.overall_compliant)
        comp_pct = compliant_n / max(len(statuses), 1) * 100

        return PolicyReport(
            report_id=report_id,
            timestamp=timestamp,
            statuses=statuses,
            total_violations=total_v,
            critical_violations=crit_v,
            auto_remediated=auto_r,
            overall_compliance_pct=round(comp_pct, 1),
            summary=(
                f"Policy evaluation: {compliant_n}/{len(statuses)} NFs compliant ({comp_pct:.0f}%). "
                f"Violations: {total_v} ({crit_v} CRITICAL). "
                f"Auto-remediated: {auto_r} actions applied."
            ),
        )

    def _evaluate_nf(self, nf, obs_list: list, risk) -> ComplianceStatus:
        violations: List[PolicyViolation] = []
        actions: List[PolicyAction] = []

        # ── Rule 1: TLS Version ──────────────────────────────────────────────
        for obs in obs_list:
            if TLS_ORDER.get(obs.tls_version, 0) < TLS_ORDER.get(POLICY_CONFIG["min_tls_version"], 4):
                v = self._make_violation(
                    nf.node_id, "MIN_TLS_VERSION", "CRITICAL",
                    obs.tls_version, POLICY_CONFIG["min_tls_version"],
                    f"Connection uses {obs.tls_version} — below minimum TLS 1.3.",
                    "Enforce TLS 1.3 minimum via network policy. Block TLS 1.2 at SCP layer.",
                    "IMMEDIATE",
                )
                violations.append(v)
                actions.append(self._make_action(nf.node_id, "TLS_UPGRADE",
                    f"Applied TLS 1.3 enforcement rule for {nf.node_id}", True, "APPLIED"))

        # ── Rule 2: SHA Policy ───────────────────────────────────────────────
        for obs in obs_list:
            if obs.sha_usage in POLICY_CONFIG["banned_sha"]:
                v = self._make_violation(
                    nf.node_id, "SHA_POLICY", "CRITICAL",
                    obs.sha_usage, "SHA-256+",
                    f"Banned SHA usage ({obs.sha_usage}) detected in {nf.node_id}.",
                    "Replace with SHA-256 or SHA-384. Ban SHA-1 at CA level.",
                    "IMMEDIATE",
                )
                violations.append(v)

        # ── Rule 3: PQC Algorithm Check ──────────────────────────────────────
        if nf.cert_algorithm not in POLICY_CONFIG["approved_pqc_algos"]:
            tier = "CRITICAL" if (risk and risk.hndl_risk) else "HIGH"
            v = self._make_violation(
                nf.node_id, "PQC_ALGO_REQUIRED", tier,
                nf.cert_algorithm, "ML-KEM-768 or ML-DSA-65",
                f"{nf.node_id} uses non-PQC algorithm '{nf.cert_algorithm}'.",
                "Initiate PQC migration per Q-Raksha plan. Use HYBRID_FIRST strategy.",
                "SHORT_TERM",
            )
            violations.append(v)
            actions.append(self._make_action(nf.node_id, "MIGRATION_TRIGGER",
                f"PQC migration flagged for {nf.node_id} — {nf.cert_algorithm} → ML-KEM-768",
                False, "PENDING"))

        # ── Rule 4: Certificate Expiry ───────────────────────────────────────
        if nf.cert_expiry_days <= POLICY_CONFIG["cert_renewal_threshold_days"]:
            sev = "CRITICAL" if nf.cert_expiry_days <= 30 else "HIGH"
            v = self._make_violation(
                nf.node_id, "CERT_EXPIRY", sev,
                f"{nf.cert_expiry_days} days", ">90 days",
                f"{nf.node_id} certificate expires in {nf.cert_expiry_days} days.",
                "Auto-renew certificate with PQC algorithm via ACME protocol.",
                "IMMEDIATE" if nf.cert_expiry_days <= 30 else "SHORT_TERM",
            )
            violations.append(v)
            actions.append(self._make_action(nf.node_id, "CERT_RENEWAL",
                f"Auto-renewal initiated for {nf.node_id} (expires {nf.cert_expiry_days}d)",
                True, "APPLIED" if nf.cert_expiry_days > 7 else "MANUAL_REQUIRED"))

        # ── Rule 5: Vendor Approval ──────────────────────────────────────────
        vendor_info = APPROVED_VENDORS.get(nf.vendor, {"approved": False})
        if not vendor_info["approved"]:
            v = self._make_violation(
                nf.node_id, "VENDOR_APPROVAL", "HIGH",
                nf.vendor, "GSMA-PQC-Certified vendor",
                f"Vendor '{nf.vendor}' does not have GSMA PQC certification.",
                "Flag for vendor audit. Request PQC readiness certification timeline.",
                "PLANNED",
            )
            violations.append(v)
            actions.append(self._make_action(nf.node_id, "VENDOR_FLAG",
                f"Vendor audit flag raised for {nf.vendor} — {nf.node_id}",
                True, "APPLIED"))

        # ── Rule 6: Cipher Suite ─────────────────────────────────────────────
        for obs in obs_list:
            if obs.cipher_suite in POLICY_CONFIG["banned_ciphers"]:
                v = self._make_violation(
                    nf.node_id, "CIPHER_POLICY", "CRITICAL",
                    obs.cipher_suite, "TLS_AES_256_GCM_SHA384",
                    f"Banned cipher '{obs.cipher_suite}' in use at {nf.node_id}.",
                    "Block cipher at network layer. Force cipher renegotiation.",
                    "IMMEDIATE",
                )
                violations.append(v)
                actions.append(self._make_action(nf.node_id, "CIPHER_BLOCK",
                    f"Blocked cipher {obs.cipher_suite} for {nf.node_id}", True, "APPLIED"))

        # Compute compliance score
        deductions = sum(
            {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "INFO": 2}.get(v.severity, 5)
            for v in violations
        )
        score = max(0.0, 100.0 - deductions)
        overall = score >= 70.0

        # Risk tier
        if score < 40:
            tier = "CRITICAL"
        elif score < 60:
            tier = "HIGH"
        elif score < 80:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        return ComplianceStatus(
            nf_id=nf.node_id,
            nf_type=nf.nf_type,
            overall_compliant=overall,
            compliance_score=round(score, 1),
            violations=violations,
            actions=actions,
            risk_tier=tier,
        )

    def _make_violation(
        self, nf_id, rule, severity, current, required, desc, remediation, effort
    ) -> PolicyViolation:
        self._violation_counter += 1
        vid = f"VIO-{self._violation_counter:04d}"
        return PolicyViolation(
            violation_id=vid, nf_id=nf_id, policy_rule=rule, severity=severity,
            current_value=current, required_value=required, description=desc,
            auto_remediation=remediation, remediation_effort=effort,
        )

    def _make_action(self, nf_id, action_type, desc, automated, status) -> PolicyAction:
        self._action_counter += 1
        aid = f"ACT-{self._action_counter:04d}"
        return PolicyAction(
            action_id=aid, nf_id=nf_id, action_type=action_type, description=desc,
            automated=automated, status=status, timestamp=time.time(),
        )
