"""
Q-RAKSHA SENTINEL — QMIE Failure Predictor (Step 4 — Failure Prediction)
Predicts post-migration failure probability for each NF:
  - Registration success rate
  - Authentication delay impact
  - PDU session delay
  - Rollback probability
  - Failure impact score
Uses gradient boosting trained on synthetic 5G KPI data.
"""
from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

try:
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class FailurePrediction:
    """Failure prediction for one NF migration."""
    node_id: str
    nf_type: str
    # KPI predictions (post-migration)
    registration_success_pct: float   # Expected UE registration success %
    auth_delay_ms: float              # Expected auth delay increase (ms)
    pdu_session_delay_ms: float       # Expected PDU session setup delay increase (ms)
    rollback_probability: float       # Probability migration will need rollback (0–1)
    failure_impact_score: float       # 0–100 (higher = worse impact if it fails)
    # Classification
    risk_flag: str                    # GREEN / YELLOW / RED
    recommended_action: str


@dataclass
class FailurePredictionReport:
    """All failure predictions."""
    report_id: str
    timestamp: str
    predictions: List[FailurePrediction] = field(default_factory=list)
    red_flags: int = 0
    yellow_flags: int = 0
    green_flags: int = 0
    summary: str = ""


class FailurePredictor:
    """
    Predicts migration failure likelihood and KPI impact.
    Uses a lightweight GBM model trained on synthetic 5G migration data.
    Falls back to physics-based heuristics when sklearn unavailable.
    """

    def __init__(self):
        self._model_trained = False
        self._reg_model = None   # Regressor for KPI metrics
        self._cls_model = None   # Classifier for rollback flag
        self._scaler = None
        if SKLEARN_AVAILABLE:
            self._train()

    def _train(self):
        """Train on synthetic 5G migration outcome data."""
        rng = np.random.default_rng(42)
        n = 5_000

        # Features: [vendor_readiness, qmis, centrality, subscriber_M, cert_expiry_d,
        #            strategy_num, api_count, connection_count]
        vendor_rd  = rng.uniform(0.2, 0.9, n)
        qmis       = rng.uniform(20, 95, n)
        centrality = rng.uniform(10, 90, n)
        subs_m     = rng.uniform(0.001, 10, n)
        cert_exp   = rng.integers(30, 730, n).astype(float)
        strategy   = rng.integers(0, 3, n).astype(float)
        api_count  = rng.integers(3, 25, n).astype(float)
        conn_count = rng.integers(1, 20, n).astype(float)

        X = np.column_stack([vendor_rd, qmis, centrality, subs_m,
                             cert_exp, strategy, api_count, conn_count])

        # Targets — synthetic KPI degradation
        reg_success = 99.5 - (qmis * 0.05) - (1 - vendor_rd) * 5 + rng.normal(0, 0.5, n)
        reg_success = np.clip(reg_success, 85, 100)

        rollback_p  = (qmis / 100) * (1 - vendor_rd) * 0.4 + rng.normal(0, 0.02, n)
        rollback_p  = np.clip(rollback_p, 0, 0.6)
        rollback_flag = (rollback_p > 0.15).astype(int)

        self._scaler = StandardScaler()
        Xs = self._scaler.fit_transform(X)

        self._reg_model = GradientBoostingRegressor(n_estimators=80, max_depth=3, random_state=42)
        self._reg_model.fit(Xs, reg_success)

        self._cls_model = GradientBoostingClassifier(n_estimators=80, max_depth=3, random_state=42)
        self._cls_model.fit(Xs, rollback_flag)
        self._model_trained = True

    def predict_all(
        self,
        risk_scores: list,   # List[QMISScore]
        nf_nodes: list,      # List[NFNode]
        migration_plan: object,  # MigrationPlan
    ) -> FailurePredictionReport:

        report_id = "FP-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        nf_map = {n.node_id: n for n in nf_nodes}
        risk_map = {r.node_id: r for r in risk_scores}
        step_map = {}
        if migration_plan and hasattr(migration_plan, 'steps'):
            step_map = {s.node_id: s for s in migration_plan.steps}

        from qmie.risk_scorer import VENDOR_PQC_READINESS

        predictions: List[FailurePrediction] = []
        for nf in nf_nodes:
            risk = risk_map.get(nf.node_id)
            step = step_map.get(nf.node_id)
            if not risk:
                continue

            vr = VENDOR_PQC_READINESS.get(nf.vendor, 0.5)
            strategy_num = {"HYBRID_FIRST": 0, "PARALLEL": 1, "CUTOVER": 2}.get(
                step.migration_strategy if step else "PARALLEL", 1)

            feat = np.array([[
                vr, risk.qmis, risk.centrality_impact,
                nf.subscriber_count / 1e6, nf.cert_expiry_days,
                float(strategy_num), float(nf.api_count),
                float(risk.rollback_complexity / 8),
            ]])

            if self._model_trained and self._scaler is not None:
                Xf = self._scaler.transform(feat)
                reg_succ = float(self._reg_model.predict(Xf)[0])
                rb_prob_cls = float(self._cls_model.predict_proba(Xf)[0][1])
            else:
                # Heuristic fallback
                reg_succ = 99.5 - (risk.qmis * 0.05) - (1 - vr) * 3
                reg_succ = max(85.0, min(100.0, reg_succ))
                rb_prob_cls = (risk.qmis / 100) * (1 - vr) * 0.35

            # KPI impact heuristics
            auth_delay = (1 - vr) * 20.0 + (risk.centrality_impact / 100) * 15.0
            pdu_delay  = (1 - vr) * 35.0 + (risk.qmis / 100) * 20.0
            impact_score = (risk.centrality_impact * 0.5 + risk.subscriber_risk * 0.3 +
                            rb_prob_cls * 100 * 0.2)

            # Flag
            if rb_prob_cls > 0.25 or reg_succ < 92:
                flag = "RED"
                action = f"Defer {nf.nf_type} — high rollback risk. Require vendor PQC cert before proceeding."
            elif rb_prob_cls > 0.12 or reg_succ < 96:
                flag = "YELLOW"
                action = f"Proceed with caution. Use HYBRID_FIRST strategy, extended validation window."
            else:
                flag = "GREEN"
                action = f"Proceed as planned. Standard HYBRID_FIRST migration with 72h observation."

            predictions.append(FailurePrediction(
                node_id=nf.node_id,
                nf_type=nf.nf_type,
                registration_success_pct=round(reg_succ, 2),
                auth_delay_ms=round(auth_delay, 1),
                pdu_session_delay_ms=round(pdu_delay, 1),
                rollback_probability=round(rb_prob_cls, 3),
                failure_impact_score=round(impact_score, 1),
                risk_flag=flag,
                recommended_action=action,
            ))

        red  = sum(1 for p in predictions if p.risk_flag == "RED")
        yel  = sum(1 for p in predictions if p.risk_flag == "YELLOW")
        grn  = sum(1 for p in predictions if p.risk_flag == "GREEN")

        return FailurePredictionReport(
            report_id=report_id,
            timestamp=timestamp,
            predictions=predictions,
            red_flags=red,
            yellow_flags=yel,
            green_flags=grn,
            summary=(
                f"Failure predictions for {len(predictions)} NFs. "
                f"🔴 RED: {red}, 🟡 YELLOW: {yel}, 🟢 GREEN: {grn}. "
                f"Avg registration success: "
                f"{sum(p.registration_success_pct for p in predictions)/max(len(predictions),1):.1f}%."
            ),
        )
