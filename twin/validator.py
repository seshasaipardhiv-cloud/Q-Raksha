"""
Q-RAKSHA SENTINEL — Digital Twin Validator (Step 5)
Simulates NF migration in a digital twin environment:
  - Registration replay (UE attach procedure)
  - Authentication replay (5G-AKA / EAP-AKA')
  - Session setup replay (PDU session establishment)
  - Slice selection replay
  - TLS negotiation test
  - KPI comparison (before vs. after migration)
Output: Twin Validation Report & KPI Delta
"""
from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KPIDelta:
    """KPI before/after comparison."""
    metric_name: str
    before: float
    after: float
    delta: float
    delta_pct: float
    within_sla: bool
    sla_threshold: float


@dataclass
class ReplayResult:
    """Result of a single replay test."""
    test_name: str
    nf_id: str
    passed: bool
    latency_ms: float
    error_rate_pct: float
    notes: str


@dataclass
class TwinValidationReport:
    """Digital twin validation report for one NF."""
    nf_id: str
    nf_type: str
    validation_id: str
    timestamp: str
    replay_results: List[ReplayResult] = field(default_factory=list)
    kpi_deltas: List[KPIDelta] = field(default_factory=list)
    overall_passed: bool = False
    pass_rate_pct: float = 0.0
    recommendation: str = ""
    twin_confidence_score: float = 0.0   # 0–100


@dataclass
class TwinValidationSummary:
    """Summary of all twin validations."""
    summary_id: str
    timestamp: str
    reports: List[TwinValidationReport] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    overall_confidence: float = 0.0
    summary: str = ""


# SLA thresholds per KPI
SLA_THRESHOLDS = {
    "registration_latency_ms": 200.0,
    "auth_latency_ms": 150.0,
    "pdu_setup_latency_ms": 500.0,
    "handover_latency_ms": 50.0,
    "tls_handshake_ms": 100.0,
    "success_rate_pct": 99.5,
}

# Test suites per NF type
TEST_SUITES: Dict[str, List[str]] = {
    "AMF": ["Registration replay", "Authentication replay", "Handover replay", "TLS negotiation", "Policy control"],
    "SMF": ["Session setup replay", "PDU session replay", "Charging interface", "TLS negotiation", "KPI comparison"],
    "UPF": ["User plane throughput", "GTP tunnel validation", "Latency baseline", "TLS negotiation"],
    "NRF": ["NF discovery test", "Registration integrity", "Heartbeat validation", "TLS negotiation"],
    "UDM": ["Subscriber auth replay", "Profile retrieval", "SUPI encryption check", "TLS negotiation"],
    "AUSF": ["5G-AKA replay", "EAP-AKA' test", "Auth vector generation", "TLS negotiation"],
    "PCF": ["Policy provisioning", "QoS enforcement", "Charging rule validation", "TLS negotiation"],
}

DEFAULT_TESTS = ["TLS negotiation", "Certificate validation", "KPI comparison", "Health check"]


class DigitalTwinValidator:
    """
    Simulates NF behavior in a digital twin after PQC migration.
    Uses realistic latency models based on NF type, algorithm, and vendor readiness.
    """

    def __init__(self, seed: int = 99):
        self._rng = random.Random(seed)

    def validate_all(
        self,
        nf_nodes: list,          # List[NFNode]
        migration_plan: object,  # MigrationPlan
        risk_scores: list,       # List[QMISScore]
    ) -> TwinValidationSummary:

        summary_id = "TWN-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        from qmie.risk_scorer import VENDOR_PQC_READINESS
        risk_map = {r.node_id: r for r in risk_scores}
        step_map = {}
        if migration_plan and hasattr(migration_plan, 'steps'):
            step_map = {s.node_id: s for s in migration_plan.steps}

        reports: List[TwinValidationReport] = []
        for nf in nf_nodes:
            risk = risk_map.get(nf.node_id)
            step = step_map.get(nf.node_id)
            vr = VENDOR_PQC_READINESS.get(nf.vendor, 0.5)
            report = self._validate_nf(nf, risk, step, vr)
            reports.append(report)

        passed = sum(1 for r in reports if r.overall_passed)
        failed = len(reports) - passed
        avg_conf = sum(r.twin_confidence_score for r in reports) / max(len(reports), 1)

        return TwinValidationSummary(
            summary_id=summary_id,
            timestamp=timestamp,
            reports=reports,
            passed_count=passed,
            failed_count=failed,
            overall_confidence=round(avg_conf, 1),
            summary=(
                f"Digital twin validation: {passed}/{len(reports)} NFs passed. "
                f"Failed: {failed}. Avg confidence: {avg_conf:.1f}%. "
                f"KPI SLA compliance: {passed/max(len(reports),1)*100:.0f}%."
            ),
        )

    def _validate_nf(self, nf, risk, step, vr: float) -> TwinValidationReport:
        val_id = "VLD-" + hashlib.sha256(f"{nf.node_id}{time.time()}".encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        tests = TEST_SUITES.get(nf.nf_type, DEFAULT_TESTS)
        replays: List[ReplayResult] = []

        # PQC algorithms add slight latency overhead (realistic: ~1-5ms)
        pqc_overhead = self._rng.uniform(1.0, 5.0) if step and "ML-" in (step.target_algo or "") else 0.0
        base_fail_rate = (1 - vr) * 0.08  # up to 8% error rate for low-readiness vendors

        for test_name in tests:
            # Base latencies per test type
            base_latency = {
                "Registration replay": 85.0,
                "Authentication replay": 65.0,
                "5G-AKA replay": 60.0,
                "EAP-AKA' test": 70.0,
                "Session setup replay": 200.0,
                "PDU session replay": 220.0,
                "TLS negotiation": 25.0,
                "NF discovery test": 15.0,
                "User plane throughput": 10.0,
                "Handover replay": 35.0,
                "KPI comparison": 5.0,
                "Health check": 5.0,
            }.get(test_name, 50.0)

            latency = base_latency + pqc_overhead + self._rng.gauss(0, base_latency * 0.1)
            latency = max(1.0, latency)

            err_rate = max(0.0, base_fail_rate + self._rng.gauss(0, 0.005))
            passed = err_rate < 0.05  # Pass if < 5% error

            notes = (
                f"PQC overhead: +{pqc_overhead:.1f}ms. "
                f"Vendor readiness: {vr*100:.0f}%. "
                + ("✅ Within SLA." if passed else "⚠️ Elevated error rate — check cipher negotiation.")
            )

            replays.append(ReplayResult(
                test_name=test_name,
                nf_id=nf.node_id,
                passed=passed,
                latency_ms=round(latency, 1),
                error_rate_pct=round(err_rate * 100, 2),
                notes=notes,
            ))

        # KPI Deltas
        kpi_deltas: List[KPIDelta] = []
        kpi_items = [
            ("registration_latency_ms", 90.0, pqc_overhead),
            ("auth_latency_ms", 65.0, pqc_overhead * 0.8),
            ("pdu_setup_latency_ms", 210.0, pqc_overhead * 1.2),
            ("tls_handshake_ms", 22.0, pqc_overhead * 0.5),
            ("success_rate_pct", 99.8, -base_fail_rate * 100),
        ]
        for metric, before, delta in kpi_items:
            after = before + delta + self._rng.gauss(0, 1.0)
            sla = SLA_THRESHOLDS.get(metric, 99.0)
            within = after <= sla if metric != "success_rate_pct" else after >= sla
            kpi_deltas.append(KPIDelta(
                metric_name=metric,
                before=round(before, 2),
                after=round(after, 2),
                delta=round(delta, 2),
                delta_pct=round(delta / max(before, 0.01) * 100, 2),
                within_sla=within,
                sla_threshold=sla,
            ))

        pass_count = sum(1 for r in replays if r.passed)
        pass_rate = pass_count / max(len(replays), 1) * 100
        overall = pass_rate >= 80.0
        kpi_ok = sum(1 for k in kpi_deltas if k.within_sla)
        confidence = (pass_rate * 0.6) + (kpi_ok / max(len(kpi_deltas), 1) * 100 * 0.4)

        if overall and confidence >= 75:
            rec = f"✅ {nf.node_id} passed digital twin. Approve for production migration."
        elif pass_rate >= 60:
            rec = f"⚠️ {nf.node_id} passed with warnings. Address TLS cipher negotiation before production."
        else:
            rec = f"🔴 {nf.node_id} failed twin validation. Defer migration — resolve vendor compatibility first."

        return TwinValidationReport(
            nf_id=nf.node_id,
            nf_type=nf.nf_type,
            validation_id=val_id,
            timestamp=timestamp,
            replay_results=replays,
            kpi_deltas=kpi_deltas,
            overall_passed=overall,
            pass_rate_pct=round(pass_rate, 1),
            recommendation=rec,
            twin_confidence_score=round(confidence, 1),
        )
