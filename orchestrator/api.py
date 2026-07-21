"""
Q-RAKSHA SENTINEL — FastAPI Orchestrator (Step 10 — CI/CD Automation Loop)
Full REST API exposing the complete 10-step workflow pipeline.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── Core modules ────────────────────────────────────────────────────────────
from cbom.scanner import CBOMScanner
from pqc.engine import PQCEngine
from qkd.bb84_sim import BB84DecoySimulator, QKDChannelParams
from ai.predictor import predictor as global_predictor
from orchestrator.state_machine import ModeStateMachine, ChannelMetrics, Mode
from ledger.chain import EvidenceLedger

# ─── Q-RAKSHA modules ────────────────────────────────────────────────────────
from graph.telecom_graph import TelecomKnowledgeGraph, get_knowledge_graph
from graph.centrality import CentralityEngine, get_centrality_engine
from qmie.risk_scorer import RiskScorer
from qmie.optimizer import MigrationOptimizer
from qmie.failure_predictor import FailurePredictor
from qmie.explainer import ExplainabilityEngine
from twin.validator import DigitalTwinValidator
from sentinel.monitor import EdgeCryptoSentinel
from policy.engine import AdaptivePolicyEngine


# ─── Global singletons ────────────────────────────────────────────────────────

pqc_engine   = PQCEngine()
qkd_sim      = BB84DecoySimulator()
ai_pred      = global_predictor
sm           = ModeStateMachine(pqc_engine)
ledger       = EvidenceLedger()
cbom_scanner = CBOMScanner()

kg_builder       = get_knowledge_graph()
centrality_eng   = get_centrality_engine()
risk_scorer      = RiskScorer()
optimizer        = MigrationOptimizer()
failure_pred     = FailurePredictor()
explainer        = ExplainabilityEngine()
twin_validator   = DigitalTwinValidator()
sentinel         = EdgeCryptoSentinel()
policy_engine    = AdaptivePolicyEngine()

# Register mode change → ledger
sm.on_mode_change(lambda t: ledger.log_mode_switch(
    {"from": t.from_mode, "to": t.to_mode, "trigger": t.trigger,
     "qber": t.qber_at_switch, "skr_kbps": t.skr_at_switch, "rekey_ms": t.rekey_time_ms}
))

# Pipeline cache — stores latest run of each step
_pipeline: Dict[str, Any] = {
    "step": 0,          # current completed step
    "running": False,
    "cbom": None,       # Step 1
    "graph": None,      # Step 2
    "centrality": None, # Step 3
    "risk": None,       # Step 4a
    "plan": None,       # Step 4b
    "failures": None,   # Step 4c
    "explanations": None, # Step 4d
    "twin": None,       # Step 5
    "pqc": None,        # Step 6
    "sentinel": None,   # Step 7
    "policy": None,     # Step 8
    "report": None,     # Step 9
}

# QKD live state
_qkd_state = {"distance_km": 50.0, "cn2": 1e-15, "cloud_cover": 0.1, "is_free_space": False, "running": True}
_ws_clients: List[WebSocket] = []


# ─── Background loops ────────────────────────────────────────────────────────

async def qkd_simulation_loop():
    """Continuous QKD monitoring for the hybrid PQC step."""
    params = QKDChannelParams()
    hour = 14.0
    while _qkd_state["running"]:
        params.distance_km = _qkd_state["distance_km"]
        params.cn2 = _qkd_state["cn2"]
        params.is_free_space = _qkd_state["is_free_space"]
        params.cn2 = max(1e-18, min(1e-12, params.cn2 * (1 + random.gauss(0, 0.05))))
        _qkd_state["cn2"] = params.cn2

        result = qkd_sim.simulate(params)
        if result.secret_key_rate_bps > 1000:
            sm.buffer_qkd_key(os.urandom(min(int(result.secret_key_rate_bps / 8), 64)))

        import math
        loss_db = min(result.total_loss_db if not math.isinf(result.total_loss_db) else 99.9, 99.9)
        pred = ai_pred.predict(
            cn2_log=math.log10(max(params.cn2, 1e-18)),
            wind_ms=5.0, cloud_cover=_qkd_state["cloud_cover"], temp_k=295.0,
            humidity=0.6, hour_of_day=hour % 24,
            qber_current=result.qber, skr_current_kbps=result.secret_key_rate_bps / 1e3,
            loss_db=loss_db,
        )
        hour += 1 / 3600

        metrics = ChannelMetrics(
            qber=result.qber, skr_kbps=result.secret_key_rate_bps / 1e3,
            predicted_skr_kbps=pred.skr_predicted_kbps, distance_km=params.distance_km,
            loss_db=loss_db, ai_predicted_mode=pred.predicted_mode,
        )
        sm.update(metrics)

        payload = {
            "ts": time.time(),
            "qber": round(result.qber * 100, 3),
            "skr_kbps": round(result.secret_key_rate_bps / 1e3, 2),
            "predicted_skr_kbps": round(pred.skr_predicted_kbps, 2),
            "loss_db": round(loss_db, 1),
            "mode": sm.current_mode.value,
            "session_id": sm.current_session.session_id if sm.current_session else "",
            "key_buffer_bytes": len(sm.key_buffer),
            "transitions": len(sm.transitions),
        }
        dead = []
        for ws in _ws_clients:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            _ws_clients.remove(ws)

        await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(qkd_simulation_loop())
    yield
    _qkd_state["running"] = False
    task.cancel()


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Q-RAKSHA SENTINEL — Orchestrator API",
    description="Autonomous Telecom Quantum Migration Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── Pydantic models ─────────────────────────────────────────────────────────

class CBOMRequest(BaseModel):
    target_path: str
    data_sensitivity: str = "CONFIDENTIAL"
    years_secret: int = 10

class QKDChannelUpdate(BaseModel):
    distance_km: Optional[float] = None
    cn2: Optional[float] = None
    cloud_cover: Optional[float] = None
    is_free_space: Optional[bool] = None

class WorkflowRunRequest(BaseModel):
    target_path: str = "workspace/scan_target"
    num_nfs: int = 24
    data_sensitivity: str = "CONFIDENTIAL"


def _safe_asdict(obj) -> dict:
    """Convert dataclass to dict, handling nested objects."""
    try:
        return asdict(obj)
    except Exception:
        return {"error": str(obj)}


# ─── Status ──────────────────────────────────────────────────────────────────

@app.get("/status")
async def status():
    return {
        "service": "Q-RAKSHA SENTINEL",
        "version": "2.0.0",
        "pipeline_step": _pipeline["step"],
        "pipeline_running": _pipeline["running"],
        "pqc": pqc_engine.status(),
        "qkd_mode": sm.current_mode.value,
        "ledger": ledger.stats(),
    }



# ─── File Uploads for Scanning ───────────────────────────────────────────────

@app.post("/workflow/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "scan_target")
    os.makedirs(target_dir, exist_ok=True)
    
    # Clean previous uploads
    for f in os.listdir(target_dir):
        os.remove(os.path.join(target_dir, f))
        
    saved_files = []
    for file in files:
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(target_dir, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(safe_filename)
        
    return {"status": "success", "saved_files": saved_files, "target_path": target_dir}


# ─── Step 1: Discovery & Telecom CBOM ────────────────────────────────────────

@app.post("/workflow/step1/cbom")
async def run_cbom(req: CBOMRequest):
    scanner = CBOMScanner(
        data_sensitivity=req.data_sensitivity,
        years_data_must_stay_secret=req.years_secret,
    )
    report = scanner.scan_path(req.target_path)
    ledger.log_cbom_scan({
        "scan_id": report.scan_id, "path": req.target_path,
        "findings": report.total_findings, "critical": report.critical_count,
    })
    result = json.loads(scanner.to_json(report))
    _pipeline["cbom"] = result
    _pipeline["step"] = max(_pipeline["step"], 1)
    return result


# ─── Step 2: Knowledge Graph Construction ────────────────────────────────────

@app.post("/workflow/step2/graph")
async def build_graph(num_nfs: int = 24):
    graph = kg_builder.build(num_nfs=num_nfs)
    result = {
        "graph_id": graph.graph_id,
        "timestamp": graph.timestamp,
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "summary": graph.summary,
        "nf_nodes": [_safe_asdict(n) for n in graph.nf_nodes],
        "edges": [_safe_asdict(e) for e in graph.edges[:50]],  # limit for API
    }
    _pipeline["graph"] = result
    _pipeline["step"] = max(_pipeline["step"], 2)
    return result


# ─── Step 3: Dependency Centrality ───────────────────────────────────────────

@app.post("/workflow/step3/centrality")
async def compute_centrality():
    if not kg_builder._built:
        kg_builder.build()
    nf_nodes = kg_builder.get_nf_nodes()
    edges = kg_builder._edges
    nx_graph = kg_builder.get_nx_graph()
    report = centrality_eng.compute(nf_nodes, edges, nx_graph)
    result = {
        "report_id": report.report_id,
        "timestamp": report.timestamp,
        "top_critical_nfs": report.top_critical_nfs,
        "summary": report.summary,
        "scores": [_safe_asdict(s) for s in report.scores],
    }
    _pipeline["centrality"] = result
    _pipeline["step"] = max(_pipeline["step"], 3)
    return result


# ─── Step 4: QMIE ────────────────────────────────────────────────────────────

@app.post("/workflow/step4/qmie")
async def run_qmie():
    """Run all 4 QMIE sub-engines: Risk, Optimize, Predict, Explain."""
    if not kg_builder._built:
        kg_builder.build()

    nf_nodes = kg_builder.get_nf_nodes()
    edges = kg_builder._edges

    # Centrality
    cent_report = centrality_eng.compute(nf_nodes, edges, kg_builder.get_nx_graph())
    cent_map = {s.node_id: s for s in cent_report.scores}

    # Risk
    risk_report = risk_scorer.score_all(nf_nodes, cent_map)

    # Optimize
    plan = optimizer.optimize(risk_report.scores, nf_nodes)

    # Failure predict
    fp_report = failure_pred.predict_all(risk_report.scores, nf_nodes, plan)

    # Explain
    exp_report = explainer.explain_all(
        risk_report.scores, plan, fp_report.predictions, nf_nodes, edges
    )

    result = {
        "risk": {
            "report_id": risk_report.report_id,
            "critical": risk_report.critical_count,
            "high": risk_report.high_count,
            "medium": risk_report.medium_count,
            "low": risk_report.low_count,
            "avg_qmis": risk_report.avg_qmis,
            "summary": risk_report.summary,
            "scores": [_safe_asdict(s) for s in risk_report.scores[:20]],
        },
        "plan": {
            "plan_id": plan.plan_id,
            "total_nfs": plan.total_nfs,
            "total_downtime_min": plan.total_estimated_downtime_min,
            "avg_failure_probability": plan.avg_failure_probability,
            "summary": plan.summary,
            "steps": [_safe_asdict(s) for s in plan.steps[:10]],
        },
        "failures": {
            "report_id": fp_report.report_id,
            "red": fp_report.red_flags,
            "yellow": fp_report.yellow_flags,
            "green": fp_report.green_flags,
            "summary": fp_report.summary,
            "predictions": [_safe_asdict(p) for p in fp_report.predictions[:15]],
        },
        "explanations": {
            "report_id": exp_report.report_id,
            "global_summary": exp_report.global_summary,
            "items": [_safe_asdict(e) for e in exp_report.explanations[:10]],
        },
    }
    _pipeline["risk"]         = result["risk"]
    _pipeline["plan"]         = result["plan"]
    _pipeline["failures"]     = result["failures"]
    _pipeline["explanations"] = result["explanations"]
    _pipeline["step"] = max(_pipeline["step"], 4)
    return result


# ─── Step 5: Digital Twin Validation ─────────────────────────────────────────

@app.post("/workflow/step5/twin")
async def run_twin_validation():
    if not kg_builder._built:
        kg_builder.build()
    nf_nodes = kg_builder.get_nf_nodes()
    risk_scores = risk_scorer.score_all(
        nf_nodes,
        {s.node_id: s for s in centrality_eng.compute(nf_nodes, kg_builder._edges, kg_builder.get_nx_graph()).scores},
    ).scores
    plan = optimizer.optimize(risk_scores, nf_nodes)
    twin_summary = twin_validator.validate_all(nf_nodes, plan, risk_scores)

    result = {
        "summary_id": twin_summary.summary_id,
        "passed": twin_summary.passed_count,
        "failed": twin_summary.failed_count,
        "confidence": twin_summary.overall_confidence,
        "summary": twin_summary.summary,
        "reports": [_safe_asdict(r) for r in twin_summary.reports[:12]],
    }
    _pipeline["twin"] = result
    _pipeline["step"] = max(_pipeline["step"], 5)
    return result


# ─── Step 6: Hybrid PQC Validation ───────────────────────────────────────────

@app.post("/workflow/step6/pqc")
async def run_pqc_validation():
    pk, sk, keygen = pqc_engine.kem_keygen()
    ct, ss_b, encap = pqc_engine.kem_encapsulate(pk)
    ss_a, decap = pqc_engine.kem_decapsulate(sk, ct)
    spk, ssk, smeta = pqc_engine.sig_keygen()
    sig, signmeta = pqc_engine.sign(ss_a, ssk)
    valid, vmeta = pqc_engine.verify(ss_a, sig, spk)

    result = {
        "algorithm": "ML-KEM-768 + ML-DSA-65",
        "is_real_pqc": pqc_engine.liboqs_available,
        "kem_match": ss_a == ss_b,
        "signature_valid": valid,
        "shared_secret_hex": ss_a.hex()[:32] + "...",
        "keygen_ms": keygen["keygen_ms"],
        "encap_ms": encap["encap_ms"],
        "decap_ms": decap["decap_ms"],
        "sign_ms": signmeta["sign_ms"],
        "verify_ms": vmeta["verify_ms"],
        "pk_bytes": len(pk), "ct_bytes": len(ct), "sig_bytes": len(sig),
        "qkd_mode": sm.current_mode.value,
        "key_buffer_bytes": len(sm.key_buffer),
    }
    ledger.log_pqc_handshake(result)
    _pipeline["pqc"] = result
    _pipeline["step"] = max(_pipeline["step"], 6)
    return result


# ─── Step 7: Edge Crypto Sentinel ────────────────────────────────────────────

@app.get("/workflow/step7/sentinel")
async def run_sentinel():
    if not kg_builder._built:
        kg_builder.build()
    nf_nodes = kg_builder.get_nf_nodes()
    edges = kg_builder._edges
    sent_report = sentinel.monitor_all(nf_nodes, edges)

    result = {
        "report_id": sent_report.report_id,
        "avg_posture_score": sent_report.avg_posture_score,
        "critical_alerts": sent_report.critical_alerts,
        "warning_alerts": sent_report.warning_alerts,
        "pqc_cipher_count": sent_report.pqc_cipher_count,
        "total_observations": len(sent_report.observations),
        "cipher_inventory": sent_report.cipher_inventory,
        "tls_version_inventory": sent_report.tls_version_inventory,
        "summary": sent_report.summary,
        "alerts": [_safe_asdict(a) for a in sent_report.alerts[:20]],
        "tpm": [_safe_asdict(t) for t in sent_report.tpm_telemetry[:10]],
    }
    _pipeline["sentinel"] = result
    _pipeline["step"] = max(_pipeline["step"], 7)
    return result


# ─── Step 8: Adaptive Policy Engine ──────────────────────────────────────────

@app.get("/workflow/step8/policy")
async def run_policy():
    if not kg_builder._built:
        kg_builder.build()
    nf_nodes = kg_builder.get_nf_nodes()
    edges = kg_builder._edges
    sent_report = sentinel.monitor_all(nf_nodes, edges)
    risk_scores = risk_scorer.score_all(
        nf_nodes,
        {s.node_id: s for s in centrality_eng.compute(nf_nodes, edges, kg_builder.get_nx_graph()).scores},
    ).scores
    pol_report = policy_engine.evaluate_all(nf_nodes, sent_report, risk_scores)

    result = {
        "report_id": pol_report.report_id,
        "compliance_pct": pol_report.overall_compliance_pct,
        "total_violations": pol_report.total_violations,
        "critical_violations": pol_report.critical_violations,
        "auto_remediated": pol_report.auto_remediated,
        "summary": pol_report.summary,
        "statuses": [_safe_asdict(s) for s in pol_report.statuses[:15]],
    }
    _pipeline["policy"] = result
    _pipeline["step"] = max(_pipeline["step"], 8)
    return result


# ─── Step 9: Executive Report ─────────────────────────────────────────────────

@app.get("/workflow/step9/report")
async def generate_report():
    report = {
        "report_type": "Q-RAKSHA SENTINEL Executive Report",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pipeline_summary": {
            "steps_completed": _pipeline["step"],
            "cbom": _pipeline.get("cbom", {}).get("statistics") if _pipeline.get("cbom") else None,
            "graph": {"node_count": _pipeline.get("graph", {}).get("node_count"),
                      "edge_count": _pipeline.get("graph", {}).get("edge_count")} if _pipeline.get("graph") else None,
            "risk": {"avg_qmis": _pipeline.get("risk", {}).get("avg_qmis"),
                     "critical": _pipeline.get("risk", {}).get("critical")} if _pipeline.get("risk") else None,
            "plan": {"total_nfs": _pipeline.get("plan", {}).get("total_nfs"),
                     "total_downtime": _pipeline.get("plan", {}).get("total_downtime_min")} if _pipeline.get("plan") else None,
            "twin": {"passed": _pipeline.get("twin", {}).get("passed"),
                     "confidence": _pipeline.get("twin", {}).get("confidence")} if _pipeline.get("twin") else None,
            "pqc": {"is_real_pqc": _pipeline.get("pqc", {}).get("is_real_pqc")} if _pipeline.get("pqc") else None,
            "sentinel": {"posture": _pipeline.get("sentinel", {}).get("avg_posture_score"),
                         "critical_alerts": _pipeline.get("sentinel", {}).get("critical_alerts")} if _pipeline.get("sentinel") else None,
            "policy": {"compliance_pct": _pipeline.get("policy", {}).get("compliance_pct")} if _pipeline.get("policy") else None,
        },
        "ledger": ledger.export_report(),
    }
    _pipeline["report"] = report
    _pipeline["step"] = max(_pipeline["step"], 9)
    return report


# ─── Step 10: CI/CD Full Pipeline Run ────────────────────────────────────────

@app.post("/workflow/run")
async def run_full_workflow(req: WorkflowRunRequest, background_tasks: BackgroundTasks):
    """Kick off the full 10-step pipeline in the background."""
    if _pipeline["running"]:
        return {"status": "already_running", "step": _pipeline["step"]}

    async def _run():
        _pipeline["running"] = True
        _pipeline["step"] = 0
        try:
            # Resolve target path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_path = req.target_path if os.path.isabs(req.target_path) else os.path.join(base_dir, req.target_path)
            if not os.path.exists(target_path):
                target_path = base_dir # fallback to project root if scan_target doesn't exist
                
            # Step 1 — CBOM
            scanner = CBOMScanner(data_sensitivity=req.data_sensitivity, years_data_must_stay_secret=10)
            report = scanner.scan_path(target_path)
            _pipeline["cbom"] = json.loads(scanner.to_json(report))
            _pipeline["step"] = 1
            await asyncio.sleep(0.5)

            # Step 2 — Graph
            graph = kg_builder.build(num_nfs=req.num_nfs)
            _pipeline["graph"] = {"graph_id": graph.graph_id, "node_count": graph.node_count,
                                   "edge_count": graph.edge_count, "summary": graph.summary,
                                   "nf_nodes": [asdict(n) for n in graph.nf_nodes]}
            _pipeline["step"] = 2
            await asyncio.sleep(0.3)

            # Step 3 — Centrality
            nf_nodes = kg_builder.get_nf_nodes()
            edges = kg_builder._edges
            cent = centrality_eng.compute(nf_nodes, edges, kg_builder.get_nx_graph())
            cent_map = {s.node_id: s for s in cent.scores}
            _pipeline["centrality"] = {"report_id": cent.report_id, "summary": cent.summary,
                                        "scores": [asdict(s) for s in cent.scores]}
            _pipeline["step"] = 3
            await asyncio.sleep(0.3)

            # Step 4 — QMIE
            risk_rpt = risk_scorer.score_all(nf_nodes, cent_map)
            plan = optimizer.optimize(risk_rpt.scores, nf_nodes)
            fp_rpt = failure_pred.predict_all(risk_rpt.scores, nf_nodes, plan)
            exp_rpt = explainer.explain_all(risk_rpt.scores, plan, fp_rpt.predictions, nf_nodes, edges)
            _pipeline["risk"] = {"report_id": risk_rpt.report_id, "critical": risk_rpt.critical_count,
                                   "high": risk_rpt.high_count, "avg_qmis": risk_rpt.avg_qmis,
                                   "summary": risk_rpt.summary, "scores": [asdict(s) for s in risk_rpt.scores]}
            _pipeline["plan"] = {"plan_id": plan.plan_id, "total_nfs": plan.total_nfs,
                                   "total_downtime_min": plan.total_estimated_downtime_min,
                                   "summary": plan.summary, "steps": [asdict(s) for s in plan.steps]}
            _pipeline["failures"] = {"report_id": fp_rpt.report_id, "red": fp_rpt.red_flags,
                                      "green": fp_rpt.green_flags, "summary": fp_rpt.summary,
                                      "predictions": [asdict(p) for p in fp_rpt.predictions]}
            _pipeline["explanations"] = {"report_id": exp_rpt.report_id,
                                          "global_summary": exp_rpt.global_summary,
                                          "items": [asdict(e) for e in exp_rpt.explanations]}
            _pipeline["step"] = 4
            await asyncio.sleep(0.5)

            # Step 5 — Twin
            twin_sum = twin_validator.validate_all(nf_nodes, plan, risk_rpt.scores)
            _pipeline["twin"] = {"passed": twin_sum.passed_count, "failed": twin_sum.failed_count,
                                   "confidence": twin_sum.overall_confidence, "summary": twin_sum.summary,
                                   "reports": [asdict(r) for r in twin_sum.reports]}
            _pipeline["step"] = 5
            await asyncio.sleep(0.3)

            # Step 6 — PQC
            pk, sk, km = pqc_engine.kem_keygen()
            ct, ss_b, em = pqc_engine.kem_encapsulate(pk)
            ss_a, dm = pqc_engine.kem_decapsulate(sk, ct)
            _pipeline["pqc"] = {"is_real_pqc": pqc_engine.liboqs_available, "kem_match": ss_a == ss_b,
                                  "keygen_ms": km["keygen_ms"], "encap_ms": em["encap_ms"],
                                  "decap_ms": dm["decap_ms"], "qkd_mode": sm.current_mode.value}
            _pipeline["step"] = 6
            await asyncio.sleep(0.3)

            # Step 7 — Sentinel
            sent_rpt = sentinel.monitor_all(nf_nodes, edges)
            _pipeline["sentinel"] = {"avg_posture_score": sent_rpt.avg_posture_score,
                                      "critical_alerts": sent_rpt.critical_alerts,
                                      "pqc_cipher_count": sent_rpt.pqc_cipher_count,
                                      "summary": sent_rpt.summary,
                                      "alerts": [asdict(a) for a in sent_rpt.alerts],
                                      "tpm": [asdict(t) for t in sent_rpt.tpm_telemetry]}
            _pipeline["step"] = 7
            await asyncio.sleep(0.3)

            # Step 8 — Policy
            pol_rpt = policy_engine.evaluate_all(nf_nodes, sent_rpt, risk_rpt.scores)
            _pipeline["policy"] = {"compliance_pct": pol_rpt.overall_compliance_pct,
                                    "total_violations": pol_rpt.total_violations,
                                    "auto_remediated": pol_rpt.auto_remediated,
                                    "summary": pol_rpt.summary,
                                    "statuses": [asdict(s) for s in pol_rpt.statuses]}
            _pipeline["step"] = 8
            await asyncio.sleep(0.3)


            # Step 8.5 — Physical File Remediation
            # If target_path is scan_target, we generate safe versions
            safe_dir = os.path.join(base_dir, "workspace", "safe_versions")
            os.makedirs(safe_dir, exist_ok=True)
            if True:
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, "r", encoding="utf-8") as rf:
                                f_content = rf.read()
                            # Basic auto-remediation logic for python/config
                            f_content = re.sub(r'(?i)RSA', 'ML-KEM-768', f_content)
                            f_content = re.sub(r'(?i)MD5|SHA-?1', 'SHA-256', f_content)
                            f_content = re.sub(r'(?i)TLSv1\.2|TLSv1\.1|TLSv1', 'TLSv1.3', f_content)
                            
                            safe_filepath = os.path.join(safe_dir, file)
                            with open(safe_filepath, "w", encoding="utf-8") as wf:
                                wf.write(f_content)
                        except Exception:
                            pass # skip binary files or errors
                            
            # Step 9 — Report
            _pipeline["report"] = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "ledger": ledger.export_report()}
            _pipeline["step"] = 9

        except Exception as e:
            _pipeline["error"] = str(e)
        finally:
            _pipeline["running"] = False

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Full Q-RAKSHA workflow initiated. Poll /workflow/status."}


@app.get("/workflow/status")
async def workflow_status():
    return {
        "step": _pipeline["step"],
        "running": _pipeline["running"],
        "step_name": [
            "Idle", "CBOM Discovery", "Knowledge Graph", "Centrality",
            "QMIE Engine", "Digital Twin", "PQC Validation",
            "Edge Sentinel", "Policy Engine", "Executive Report",
        ][min(_pipeline["step"], 9)],
        "has_cbom": _pipeline["cbom"] is not None,
        "has_graph": _pipeline["graph"] is not None,
        "has_risk":  _pipeline["risk"] is not None,
        "has_twin":  _pipeline["twin"] is not None,
        "has_pqc":   _pipeline["pqc"] is not None,
        "has_sentinel": _pipeline["sentinel"] is not None,
        "has_policy": _pipeline["policy"] is not None,
        "has_report": _pipeline["report"] is not None,
    }


@app.get("/workflow/data/{step}")
async def get_step_data(step: str):
    """Get cached data for a specific pipeline step."""
    data = _pipeline.get(step)
    if data is None:
        raise HTTPException(404, detail=f"Step '{step}' not yet computed. Run the workflow first.")
    return data


# ─── Legacy endpoints (preserved for compatibility) ───────────────────────────

@app.get("/ledger/entries")
async def get_ledger(limit: int = 50, event_type: Optional[str] = None):
    return {"entries": ledger.get_entries(limit=limit, event_type=event_type)}

@app.get("/ledger/verify")
async def verify_ledger():
    valid, errors = ledger.verify_chain()
    return {"chain_valid": valid, "errors": errors, "total_entries": len(ledger._entries)}

@app.put("/channel")
async def update_channel(update: QKDChannelUpdate):
    if update.distance_km is not None: _qkd_state["distance_km"] = update.distance_km
    if update.cn2 is not None:         _qkd_state["cn2"] = update.cn2
    if update.cloud_cover is not None: _qkd_state["cloud_cover"] = update.cloud_cover
    if update.is_free_space is not None: _qkd_state["is_free_space"] = update.is_free_space
    return {"status": "updated"}

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
