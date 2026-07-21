"""
Q-RAKSHA SENTINEL — QMIE Risk Scorer (Step 4 — Risk Scoring)
Computes a Quantum Migration Impact Score (QMIS) for each NF:
  - Crypto risk (algorithm vulnerability + HNDL)
  - NF criticality (from centrality)
  - Subscriber reach impact
  - Vendor PQC readiness
  - Rollback complexity
  - Validation confidence
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Crypto vulnerability scores (higher = more quantum-vulnerable)
ALGO_VULN_SCORE: Dict[str, float] = {
    # Fully vulnerable (Harvest Now Decrypt Later threat)
    "RSA-2048": 95.0,
    "RSA-4096": 85.0,
    "ECDSA-P256": 90.0,
    "ECDH-P384": 88.0,
    "DH-2048": 92.0,
    # Transition algorithms (partially safe)
    "RSA-4096+Kyber768": 45.0,
    "ECDSA+Dilithium3": 40.0,
    # PQC-ready (NIST-approved)
    "ML-KEM-768": 5.0,
    "ML-DSA-65": 5.0,
    "SLH-DSA-128f": 5.0,
    "FN-DSA-512": 5.0,
}

# Vendor PQC readiness (1.0 = fully PQC-certified, 0 = no roadmap)
VENDOR_PQC_READINESS: Dict[str, float] = {
    "Ericsson": 0.85,
    "Nokia": 0.80,
    "Samsung": 0.75,
    "Mavenir": 0.70,
    "Radisys": 0.65,
    "ZTE": 0.35,
    "Huawei": 0.30,
}


@dataclass
class QMISScore:
    """Quantum Migration Impact Score for one NF."""
    node_id: str
    nf_type: str
    # Risk components
    crypto_risk: float         # 0–100 (higher = worse)
    centrality_impact: float   # 0–100
    subscriber_risk: float     # 0–100
    vendor_readiness: float    # 0–100 (higher = more ready)
    rollback_complexity: float # 0–100 (higher = harder to rollback)
    validation_confidence: float  # 0–100 (higher = more confident migration will succeed)
    hndl_risk: bool            # Harvest Now Decrypt Later threat
    # Composite
    qmis: float                # 0–100 (higher = migrate sooner)
    risk_tier: str             # CRITICAL / HIGH / MEDIUM / LOW
    migration_window_days: int # Recommended migration window
    estimated_downtime_min: float


@dataclass
class RiskReport:
    """Full QMIS report for all NFs."""
    report_id: str
    timestamp: str
    scores: List[QMISScore] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    avg_qmis: float = 0.0
    summary: str = ""


class RiskScorer:
    """
    Computes QMIS for each NF node.
    Integrates crypto vulnerability, centrality, subscriber exposure,
    vendor readiness, and HNDL risk horizon.
    """

    YEARS_TO_CRQC = 7   # Estimated years until Cryptographically Relevant Quantum Computer

    def score_all(
        self,
        nf_nodes: list,          # List[NFNode]
        centrality_scores: dict,  # node_id → CentralityScore
        data_retention_years: int = 10,
    ) -> RiskReport:

        report_id = "RISK-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        max_subs = max((n.subscriber_count for n in nf_nodes), default=1)
        scores: List[QMISScore] = []

        for nf in nf_nodes:
            score = self._score_nf(nf, centrality_scores, max_subs, data_retention_years)
            scores.append(score)

        # Sort by QMIS descending
        scores.sort(key=lambda s: s.qmis, reverse=True)

        crit = sum(1 for s in scores if s.risk_tier == "CRITICAL")
        high = sum(1 for s in scores if s.risk_tier == "HIGH")
        med  = sum(1 for s in scores if s.risk_tier == "MEDIUM")
        low  = sum(1 for s in scores if s.risk_tier == "LOW")
        avg  = sum(s.qmis for s in scores) / max(len(scores), 1)

        return RiskReport(
            report_id=report_id,
            timestamp=timestamp,
            scores=scores,
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            avg_qmis=round(avg, 2),
            summary=(
                f"QMIS computed for {len(scores)} NFs. "
                f"CRITICAL: {crit}, HIGH: {high}, MEDIUM: {med}, LOW: {low}. "
                f"Avg QMIS: {avg:.1f}/100. "
                f"HNDL-exposed: {sum(1 for s in scores if s.hndl_risk)} NFs."
            ),
        )

    def _score_nf(
        self, nf, centrality_scores: dict, max_subs: int, retention_years: int
    ) -> QMISScore:
        # Crypto risk
        crypto_vuln = ALGO_VULN_SCORE.get(nf.cert_algorithm, 70.0)
        hndl = (crypto_vuln >= 70.0) and (retention_years > self.YEARS_TO_CRQC)

        # Centrality impact
        cent_obj = centrality_scores.get(nf.node_id)
        centrality_impact = cent_obj.centrality_score if cent_obj else 50.0

        # Subscriber risk
        subscriber_risk = (nf.subscriber_count / max_subs) * 100.0

        # Vendor readiness (invert — low readiness = higher risk)
        vendor_rd = VENDOR_PQC_READINESS.get(nf.vendor, 0.5)
        vendor_readiness = vendor_rd * 100.0

        # Rollback complexity (more connections = harder rollback)
        conn = (cent_obj.connection_count if cent_obj else 5)
        rollback_complexity = min(100.0, conn * 8.0)

        # Validation confidence (based on vendor readiness + cert expiry)
        val_conf = (vendor_rd * 50.0) + (min(nf.cert_expiry_days, 365) / 365.0 * 50.0)

        # Composite QMIS: higher = more urgent to migrate
        qmis = (
            crypto_vuln        * 0.30 +
            centrality_impact  * 0.25 +
            subscriber_risk    * 0.20 +
            (100 - vendor_readiness) * 0.15 +   # low readiness = higher urgency
            rollback_complexity * 0.10
        )
        qmis = min(100.0, qmis)

        # Risk tier
        if qmis >= 75:
            tier = "CRITICAL"
            window = 30
        elif qmis >= 55:
            tier = "HIGH"
            window = 90
        elif qmis >= 35:
            tier = "MEDIUM"
            window = 180
        else:
            tier = "LOW"
            window = 365

        # Estimated downtime (minutes) — based on NF type + rollback complexity
        from graph.centrality import NF_CRITICALITY
        base_dt = NF_CRITICALITY.get(nf.nf_type, 0.5) * 120.0   # 0–120 min
        downtime = base_dt * (rollback_complexity / 100.0 + 0.5)

        return QMISScore(
            node_id=nf.node_id,
            nf_type=nf.nf_type,
            crypto_risk=round(crypto_vuln, 1),
            centrality_impact=round(centrality_impact, 1),
            subscriber_risk=round(subscriber_risk, 1),
            vendor_readiness=round(vendor_readiness, 1),
            rollback_complexity=round(rollback_complexity, 1),
            validation_confidence=round(val_conf, 1),
            hndl_risk=hndl,
            qmis=round(qmis, 2),
            risk_tier=tier,
            migration_window_days=window,
            estimated_downtime_min=round(downtime, 1),
        )
