"""
Q-RAKSHA SENTINEL — QMIE Explainability Engine (Step 4 — Explainability)
Generates human-readable explanations for:
  - "Why this order?" — migration sequence rationale
  - "Which dependency caused risk?" — dependency chain tracing
  - "What if analysis?" — counterfactual impact simulation
  - Rollback complexity explanation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Explanation:
    """Human-readable explanation for one NF migration decision."""
    node_id: str
    nf_type: str
    why_this_order: str
    dependency_risk_chain: List[str]
    what_if_delayed: str
    what_if_vendor_upgraded: str
    rollback_rationale: str
    plain_english_summary: str


@dataclass
class ExplainabilityReport:
    """Full explainability report."""
    report_id: str
    timestamp: str
    explanations: List[Explanation] = field(default_factory=list)
    global_summary: str = ""


class ExplainabilityEngine:
    """
    Generates natural-language explanations for QMIE decisions.
    Designed for network engineers and executive stakeholders who need
    to understand *why* migration order and strategy were chosen.
    """

    def explain_all(
        self,
        risk_scores: list,         # List[QMISScore]
        migration_plan: object,    # MigrationPlan
        failure_preds: list,       # List[FailurePrediction]
        nf_nodes: list,            # List[NFNode]
        edges: list,               # List[GraphEdge]
    ) -> ExplainabilityReport:
        import hashlib, time
        report_id = "EXP-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        nf_map = {n.node_id: n for n in nf_nodes}
        risk_map = {r.node_id: r for r in risk_scores}
        fp_map = {p.node_id: p for p in failure_preds}
        step_map = {}
        if migration_plan and hasattr(migration_plan, 'steps'):
            step_map = {s.node_id: s for s in migration_plan.steps}

        # Build dependency chains from edges
        dep_chains = self._build_dep_chains(edges, nf_map)

        explanations: List[Explanation] = []
        for step in (migration_plan.steps if migration_plan and hasattr(migration_plan, 'steps') else []):
            nf = nf_map.get(step.node_id)
            risk = risk_map.get(step.node_id)
            fp = fp_map.get(step.node_id)
            if not nf or not risk:
                continue

            exp = self._explain_nf(nf, risk, fp, step, dep_chains)
            explanations.append(exp)

        top3 = [e.node_id for e in explanations[:3]]
        global_summary = (
            f"Migration sequence explained for {len(explanations)} NFs. "
            f"Top-priority NFs: {', '.join(top3)}. "
            f"All decisions driven by QMIS composite score (crypto risk × centrality × subscriber impact)."
        )

        return ExplainabilityReport(
            report_id=report_id,
            timestamp=timestamp,
            explanations=explanations,
            global_summary=global_summary,
        )

    def _explain_nf(self, nf, risk, fp, step, dep_chains: dict) -> Explanation:
        from qmie.risk_scorer import VENDOR_PQC_READINESS

        vr = VENDOR_PQC_READINESS.get(nf.vendor, 0.5)

        # Why this order
        why_order = (
            f"Ranked #{step.step_number} because QMIS={risk.qmis:.1f}/100. "
            f"Algorithm '{nf.cert_algorithm}' is {'quantum-vulnerable (HNDL risk)' if risk.hndl_risk else 'transitional'}. "
            f"Centrality score {risk.centrality_impact:.0f} means {nf.nf_type} is on the critical path for "
            f"{nf.subscriber_count:,} subscribers on '{nf.slice_id}' slice."
        )

        # Dependency chain
        deps = dep_chains.get(nf.node_id, [])
        dep_chain = []
        for d_id in deps[:4]:
            d_nf = nf.node_id  # just reference
            dep_chain.append(f"{d_id} depends on {nf.node_id} — migrating {nf.node_id} first ensures {d_id} inherits PQC trust chain")
        if not dep_chain:
            dep_chain = [f"{nf.node_id} is a leaf node — no downstream NFs directly depend on it"]

        # What-if delayed
        hndl_str = "a Cryptographically Relevant Quantum Computer (CRQC) could decrypt intercepted traffic" if risk.hndl_risk else "quantum risk escalates"
        what_if_delayed = (
            f"Delaying {nf.node_id} migration beyond {step.rollback_window_min:.0f} days means {hndl_str}. "
            f"HNDL risk: {'⚠️ YES — data intercepted today may be decrypted in ~7 years' if risk.hndl_risk else 'Lower — algorithm not actively harvested'}. "
            f"Each month of delay increases exposure window by ~{risk.crypto_risk/12:.1f} risk points."
        )

        # What-if vendor upgraded
        new_vr = min(1.0, vr + 0.25)
        new_fp = round((fp.rollback_probability if fp else 0.15) * (vr / new_vr), 3)
        what_if_vendor = (
            f"If {nf.vendor} upgrades PQC readiness from {vr*100:.0f}% to {new_vr*100:.0f}%, "
            f"rollback probability drops from {fp.rollback_probability if fp else 'N/A'} to {new_fp}. "
            f"Recommend requesting PQC certification roadmap from {nf.vendor} before migration."
        )

        # Rollback rationale
        rollback = (
            f"Strategy '{step.migration_strategy}' chosen because rollback complexity={risk.rollback_complexity:.0f}/100. "
            f"{'HYBRID_FIRST runs PQC alongside classical — zero-downtime rollback possible.' if step.migration_strategy=='HYBRID_FIRST' else 'PARALLEL validates both stacks simultaneously — rollback window ' + str(step.rollback_window_min) + ' min.'}"
        )

        # Plain English
        plain = (
            f"{nf.nf_type} {nf.node_id} uses '{nf.cert_algorithm}' which is breakable by quantum computers. "
            f"It serves {nf.subscriber_count:,} users on the {nf.slice_id} slice. "
            f"We migrate it {'first' if step.step_number <= 3 else 'in order'} because it has the "
            f"{'highest' if step.step_number == 1 else 'significant'} risk score. "
            f"Expected success: {fp.registration_success_pct if fp else 97:.1f}% with {step.migration_strategy} strategy."
        )

        return Explanation(
            node_id=nf.node_id,
            nf_type=nf.nf_type,
            why_this_order=why_order,
            dependency_risk_chain=dep_chain,
            what_if_delayed=what_if_delayed,
            what_if_vendor_upgraded=what_if_vendor,
            rollback_rationale=rollback,
            plain_english_summary=plain,
        )

    def _build_dep_chains(self, edges: list, nf_map: dict) -> Dict[str, List[str]]:
        """Build reverse dependency map: for each NF, which NFs depend on it."""
        rev: Dict[str, List[str]] = {nid: [] for nid in nf_map}
        for e in edges:
            if e.source in nf_map and e.target in nf_map:
                rev[e.target].append(e.source)
        return rev
