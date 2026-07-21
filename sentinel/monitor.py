"""
Q-RAKSHA SENTINEL — Edge Crypto Sentinel (Step 7 — Real-Time Monitoring)
Passively monitors the crypto posture of all NFs:
  - Passive TLS observation (version, cipher inventory)
  - Certificate drift detection (expiry, algorithm changes)
  - Cipher score computation
  - TPM-backed telemetry simulation
  - Live alerts for compliance violations
"""
from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# TLS version scores (higher = better)
TLS_SCORES = {
    "TLS1.3": 100,
    "TLS1.2": 70,
    "TLS1.1": 20,
    "TLS1.0": 5,
    "SSLv3": 0,
}

# Cipher suite scores
CIPHER_SCORES = {
    "TLS_AES_256_GCM_SHA384": 100,
    "TLS_AES_128_GCM_SHA256": 95,
    "TLS_CHACHA20_POLY1305_SHA256": 98,
    "TLS_ECDHE_RSA_AES256_GCM": 70,
    "TLS_ECDHE_RSA_AES128_GCM": 65,
    "TLS_RSA_AES256_CBC": 35,
    "TLS_RSA_AES128_CBC": 30,
    "TLS_RSA_3DES": 5,
    "TLS_NULL_WITH_NULL_NULL": 0,
}

# Alert severity thresholds
CERT_EXPIRY_WARNING_DAYS = 90
CERT_EXPIRY_CRITICAL_DAYS = 30


@dataclass
class TLSObservation:
    """A single TLS connection observation."""
    nf_id: str
    connection_id: str
    timestamp: float
    tls_version: str
    cipher_suite: str
    cert_algorithm: str
    cert_expiry_days: int
    sha_usage: str            # SHA-256 / SHA-384 / SHA-1
    tls_score: int
    cipher_score: int
    overall_posture_score: float
    is_pqc_cipher: bool


@dataclass
class CertDriftAlert:
    """Certificate drift detection alert."""
    alert_id: str
    nf_id: str
    alert_type: str         # EXPIRY_WARNING / EXPIRY_CRITICAL / ALGO_CHANGE / DOWNGRADE
    severity: str           # INFO / WARNING / CRITICAL
    message: str
    timestamp: float
    cert_expiry_days: int
    current_algo: str


@dataclass
class TPMTelemetry:
    """Simulated TPM 2.0 telemetry from edge node."""
    nf_id: str
    tpm_present: bool
    pcr_valid: bool           # Platform Configuration Register integrity
    measured_boot_ok: bool
    attestation_quote: str    # Hex quote (simulated)
    tpm_score: float          # 0–100


@dataclass
class SentinelReport:
    """Full Edge Crypto Sentinel report."""
    report_id: str
    timestamp: str
    observations: List[TLSObservation] = field(default_factory=list)
    alerts: List[CertDriftAlert] = field(default_factory=list)
    tpm_telemetry: List[TPMTelemetry] = field(default_factory=list)
    avg_posture_score: float = 0.0
    critical_alerts: int = 0
    warning_alerts: int = 0
    cipher_inventory: Dict[str, int] = field(default_factory=dict)
    tls_version_inventory: Dict[str, int] = field(default_factory=dict)
    pqc_cipher_count: int = 0
    summary: str = ""


class EdgeCryptoSentinel:
    """
    Edge Crypto Sentinel — passive TLS observation and certificate monitoring.
    Simulates the passive observation capability described in the architecture,
    generating realistic TLS/cert telemetry for each NF.
    """

    def __init__(self, seed: int = 77):
        self._rng = random.Random(seed)
        self._alert_counter = 0

    def monitor_all(
        self,
        nf_nodes: list,      # List[NFNode]
        edges: list,         # List[GraphEdge]
    ) -> SentinelReport:

        report_id = "SNT-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        observations: List[TLSObservation] = []
        alerts: List[CertDriftAlert] = []
        tpm_data: List[TPMTelemetry] = []
        cipher_inv: Dict[str, int] = {}
        tls_inv: Dict[str, int] = {}

        for nf in nf_nodes:
            # Generate 1–3 TLS observations per NF (passive traffic sample)
            for _ in range(self._rng.randint(1, 3)):
                obs = self._observe_nf(nf, edges)
                observations.append(obs)
                cipher_inv[obs.cipher_suite] = cipher_inv.get(obs.cipher_suite, 0) + 1
                tls_inv[obs.tls_version] = tls_inv.get(obs.tls_version, 0) + 1

            # Check for cert drift alerts
            nf_alerts = self._check_cert_drift(nf)
            alerts.extend(nf_alerts)

            # TPM telemetry
            tpm = self._get_tpm_telemetry(nf)
            tpm_data.append(tpm)

        # Compute overall posture
        avg_posture = sum(o.overall_posture_score for o in observations) / max(len(observations), 1)
        crit = sum(1 for a in alerts if a.severity == "CRITICAL")
        warn = sum(1 for a in alerts if a.severity == "WARNING")
        pqc_count = sum(1 for o in observations if o.is_pqc_cipher)

        return SentinelReport(
            report_id=report_id,
            timestamp=timestamp,
            observations=observations,
            alerts=alerts,
            tpm_telemetry=tpm_data,
            avg_posture_score=round(avg_posture, 1),
            critical_alerts=crit,
            warning_alerts=warn,
            cipher_inventory=cipher_inv,
            tls_version_inventory=tls_inv,
            pqc_cipher_count=pqc_count,
            summary=(
                f"Edge Crypto Sentinel: {len(observations)} TLS observations, "
                f"{len(alerts)} alerts ({crit} CRITICAL, {warn} WARNING). "
                f"Avg posture score: {avg_posture:.0f}/100. "
                f"PQC-capable connections: {pqc_count}/{len(observations)}."
            ),
        )

    def _observe_nf(self, nf, edges: list) -> TLSObservation:
        """Simulate passive TLS observation for one NF."""
        # Determine observed TLS version from edge topology
        nf_edges = [e for e in edges if e.source == nf.node_id or e.target == nf.node_id]
        if nf_edges:
            edge = self._rng.choice(nf_edges)
            tls_ver = edge.tls_version
            cipher = edge.cipher_suite
        else:
            tls_ver = self._rng.choice(["TLS1.3", "TLS1.2"])
            cipher = "TLS_AES_256_GCM_SHA384"

        # SHA usage
        sha = "SHA-384" if "SHA384" in cipher else "SHA-256" if "SHA256" in cipher else "SHA-1"

        tls_s = TLS_SCORES.get(tls_ver, 30)
        cip_s = CIPHER_SCORES.get(cipher, 40)
        is_pqc = nf.cert_algorithm in ["ML-KEM-768", "ML-DSA-65", "SLH-DSA-128f", "FN-DSA-512"]

        # Cert expiry jitter
        expiry = max(1, nf.cert_expiry_days + self._rng.randint(-5, 5))

        # Overall posture
        expiry_score = min(100, expiry / 365 * 100)
        pqc_bonus = 15.0 if is_pqc else 0.0
        posture = (tls_s * 0.35 + cip_s * 0.35 + expiry_score * 0.20 + pqc_bonus + 0.10 * 100) / 1.1
        posture = min(100.0, posture)

        conn_id = "CONN-" + hashlib.sha256(f"{nf.node_id}{time.time()}{self._rng.random()}".encode()).hexdigest()[:8].upper()

        return TLSObservation(
            nf_id=nf.node_id,
            connection_id=conn_id,
            timestamp=time.time(),
            tls_version=tls_ver,
            cipher_suite=cipher,
            cert_algorithm=nf.cert_algorithm,
            cert_expiry_days=expiry,
            sha_usage=sha,
            tls_score=tls_s,
            cipher_score=cip_s,
            overall_posture_score=round(posture, 1),
            is_pqc_cipher=is_pqc,
        )

    def _check_cert_drift(self, nf) -> List[CertDriftAlert]:
        """Check for certificate expiry, downgrade, and algorithm drift alerts."""
        alerts: List[CertDriftAlert] = []
        self._alert_counter += 1
        aid_base = f"ALT-{self._alert_counter:04d}"

        # Expiry alerts
        if nf.cert_expiry_days <= CERT_EXPIRY_CRITICAL_DAYS:
            alerts.append(CertDriftAlert(
                alert_id=aid_base + "-EXP",
                nf_id=nf.node_id,
                alert_type="EXPIRY_CRITICAL",
                severity="CRITICAL",
                message=f"{nf.node_id} certificate expires in {nf.cert_expiry_days} days! Immediate renewal required.",
                timestamp=time.time(),
                cert_expiry_days=nf.cert_expiry_days,
                current_algo=nf.cert_algorithm,
            ))
        elif nf.cert_expiry_days <= CERT_EXPIRY_WARNING_DAYS:
            alerts.append(CertDriftAlert(
                alert_id=aid_base + "-WARN",
                nf_id=nf.node_id,
                alert_type="EXPIRY_WARNING",
                severity="WARNING",
                message=f"{nf.node_id} certificate expires in {nf.cert_expiry_days} days. Schedule renewal.",
                timestamp=time.time(),
                cert_expiry_days=nf.cert_expiry_days,
                current_algo=nf.cert_algorithm,
            ))

        # Algorithm vulnerability alert
        from qmie.risk_scorer import ALGO_VULN_SCORE
        if ALGO_VULN_SCORE.get(nf.cert_algorithm, 0) >= 70:
            alerts.append(CertDriftAlert(
                alert_id=aid_base + "-ALGO",
                nf_id=nf.node_id,
                alert_type="ALGO_VULNERABLE",
                severity="CRITICAL" if ALGO_VULN_SCORE[nf.cert_algorithm] >= 85 else "WARNING",
                message=f"{nf.node_id} uses quantum-vulnerable '{nf.cert_algorithm}'. HNDL risk active.",
                timestamp=time.time(),
                cert_expiry_days=nf.cert_expiry_days,
                current_algo=nf.cert_algorithm,
            ))

        return alerts

    def _get_tpm_telemetry(self, nf) -> TPMTelemetry:
        """Simulate TPM 2.0 telemetry from edge node."""
        # High-criticality NFs are more likely to have TPM
        tpm_present = self._rng.random() > 0.25
        pcr_valid = tpm_present and self._rng.random() > 0.05
        boot_ok = pcr_valid and self._rng.random() > 0.02
        quote = hashlib.sha256(f"{nf.node_id}{time.time()}".encode()).hexdigest()[:32] if tpm_present else ""
        score = (100 if boot_ok else 60 if pcr_valid else 30 if tpm_present else 0)

        return TPMTelemetry(
            nf_id=nf.node_id,
            tpm_present=tpm_present,
            pcr_valid=pcr_valid,
            measured_boot_ok=boot_ok,
            attestation_quote=quote,
            tpm_score=float(score),
        )
