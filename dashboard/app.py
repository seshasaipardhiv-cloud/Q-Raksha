"""
Q-RAKSHA SENTINEL — Executive Dashboard
10-step Telecom Quantum Migration Intelligence Platform
"""
import json
import math
import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import requests

# Page config — must be first
st.set_page_config(
    page_title="Q-RAKSHA SENTINEL",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:    #0a0e1a;
    --bg-card:       #0f1629;
    --bg-card2:      #141d35;
    --border:        #1e2d4d;
    --accent-blue:   #3b82f6;
    --accent-cyan:   #06b6d4;
    --accent-purple: #8b5cf6;
    --accent-green:  #10b981;
    --accent-orange: #f59e0b;
    --accent-red:    #ef4444;
    --text-primary:  #e2e8f0;
    --text-secondary:#94a3b8;
    --text-dim:      #475569;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stApp { background-color: var(--bg-primary); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1226 0%, #0a0e1a 100%) !important;
    border-right: 1px solid var(--border);
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card2) 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
}
.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-card .metric-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}
.metric-card .metric-sub {
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-top: 6px;
    font-family: 'JetBrains Mono', monospace;
}

/* Section headers */
.section-header {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin-bottom: 16px;
    margin-top: 24px;
}

/* Alert boxes */
.alert-critical { background: rgba(239,68,68,0.1); border-left: 4px solid #ef4444; border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 6px 0; font-size: 0.85rem; }
.alert-high { background: rgba(245,158,11,0.1); border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 6px 0; font-size: 0.85rem; }
.alert-ok { background: rgba(16,185,129,0.1); border-left: 4px solid #10b981; border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 6px 0; font-size: 0.85rem; }

/* Logo */
.logo-text {
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
}
.logo-sub {
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1e293b, #0f172a) !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important;
}
.primary-btn > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    border: none !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 500;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    color: #60a5fa !important;
    border-bottom-color: #60a5fa !important;
}

/* Step Pipeline Flow */
.step-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
    padding: 12px;
    background: #0d1226;
    border-radius: 8px;
    border: 1px solid #1e2d4d;
}
.step-box {
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #1e293b;
    color: #64748b;
    border: 1px solid #334155;
}
.step-box.active {
    background: rgba(59,130,246,0.1);
    color: #60a5fa;
    border-color: #3b82f6;
    box-shadow: 0 0 10px rgba(59,130,246,0.2);
}
.step-box.done {
    background: rgba(16,185,129,0.1);
    color: #10b981;
    border-color: #10b981;
}
</style>
""", unsafe_allow_html=True)


# ─── Initialization ─────────────────────────────────────────────────────────

API_URL = "https://q-raksha-api.onrender.com"


if "workflow_step" not in st.session_state:
    st.session_state.workflow_step = 0
if "workflow_running" not in st.session_state:
    st.session_state.workflow_running = False

def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=2.0)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def api_post(endpoint, json_data=None):
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=json_data, timeout=5.0)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# Fetch latest status
status = api_get("/workflow/status")
if status:
    st.session_state.workflow_step = status.get("step", 0)
    st.session_state.workflow_running = status.get("running", False)


# ─── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="logo-text">Q-RAKSHA SENTINEL</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Telecom Quantum Migration Platform</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown('<div class="section-header">TCOE Demo Flow</div>', unsafe_allow_html=True)
    
    if st.button("🚀 Launch Open5GS", help="Step 1: Start 5G Core emulation"):
        st.success("Open5GS Emulation Started")
    
    # Run full workflow button
    st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
    if st.button("▶️ Run Full Migration Workflow", disabled=st.session_state.workflow_running):
        res = api_post("/workflow/run", {"target_path": ".", "num_nfs": 24})
        if res:
            st.session_state.workflow_running = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.workflow_running:
        st.info(f"⏳ Workflow running (Step {st.session_state.workflow_step}/9)...")
        time.sleep(1)
        st.rerun()
        
    st.markdown("---")
    st.caption("From Discovery to Quantum-Safe Continuity — Intelligent, Predictive, Autonomous.")


# ─── Pipeline Header ────────────────────────────────────────────────────────

st.markdown('<h1 style="font-size:1.8rem;font-weight:800;margin-bottom:4px;">Q-RAKSHA SENTINEL Dashboard</h1>', unsafe_allow_html=True)

steps_def = [
    (1, "Discovery & CBOM"),
    (2, "Knowledge Graph"),
    (3, "Centrality"),
    (4, "QMIE (Risk & Plan)"),
    (5, "Digital Twin"),
    (6, "PQC Validation"),
    (7, "Edge Sentinel"),
    (8, "Policy Engine"),
    (9, "Executive Report")
]

curr_step = st.session_state.workflow_step
html = '<div class="step-container">'
for s_num, s_name in steps_def:
    cls = "step-box"
    if s_num < curr_step: cls += " done"
    elif s_num == curr_step: cls += " active"
    html += f'<div class="{cls}">Step {s_num}: {s_name}</div>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)


# ─── Main Tabs ──────────────────────────────────────────────────────────────

tabs = st.tabs([
    "1️⃣ CBOM", "2️⃣ Graph", "3️⃣ Centrality", "4️⃣ QMIE", 
    "5️⃣ Twin", "6️⃣ PQC", "7️⃣ Sentinel", "8️⃣ Policy", "9️⃣ Report"
])

# ─── Tab 1: Discovery & CBOM ────────────────────────────────────────────────
with tabs[0]:
    data = api_get("/workflow/data/cbom")
    if not data:
        st.info("Run the workflow to see Discovery & CBOM data.")
        if st.button("Run Discovery"): api_post("/workflow/step1/cbom", {"target_path": ".", "years_secret": 10}); st.rerun()
    else:
        stats = data.get("statistics", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("files_scanned", 0)}</div><div class="metric-label">Files Scanned</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#ef4444;">{stats.get("total_findings", 0)}</div><div class="metric-label">Crypto Findings</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#f59e0b;">{stats.get("by_risk",{}).get("CRITICAL",0)}</div><div class="metric-label">Critical Risk</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#06b6d4;">{stats.get("hndl_risk_count", 0)}</div><div class="metric-label">HNDL Exposed</div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Telecom CBOM Findings</div>', unsafe_allow_html=True)
        findings = data.get("findings", [])
        if findings:
            df = pd.DataFrame(findings)
            st.dataframe(df[["file", "algorithm", "risk_level", "harvest_now_decrypt_later", "recommendation"]], use_container_width=True)


# ─── Tab 2: Knowledge Graph ─────────────────────────────────────────────────
with tabs[1]:
    data = api_get("/workflow/data/graph")
    if not data:
        st.info("Run the workflow to see Knowledge Graph.")
        if st.button("Build Graph"): api_post("/workflow/step2/graph"); st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("node_count", 0)}</div><div class="metric-label">Total Nodes</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("edge_count", 0)}</div><div class="metric-label">Total Edges</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#10b981;">{len([n for n in data.get("nf_nodes",[]) if n.get("pqc_ready")])}</div><div class="metric-label">PQC Ready NFs</div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">NF Inventory</div>', unsafe_allow_html=True)
        nfs = data.get("nf_nodes", [])
        if nfs:
            df = pd.DataFrame(nfs)
            st.dataframe(df[["node_id", "nf_type", "vendor", "cert_algorithm", "pqc_ready", "subscriber_count"]], use_container_width=True)


# ─── Tab 3: Centrality ──────────────────────────────────────────────────────
with tabs[2]:
    data = api_get("/workflow/data/centrality")
    if not data:
        st.info("Run the workflow to see Centrality scores.")
        if st.button("Compute Centrality"): api_post("/workflow/step3/centrality"); st.rerun()
    else:
        st.success(data.get("summary", ""))
        scores = data.get("scores", [])
        if scores:
            df = pd.DataFrame(scores)
            
            # Bar chart for centrality
            fig = px.bar(df.head(10), x="node_id", y="centrality_score", color="centrality_score", 
                         title="Top 10 NFs by Centrality Score", color_continuous_scale="Viridis")
            fig.update_layout(plot_bgcolor="#0f1629", paper_bgcolor="#0f1629", font=dict(color="#94a3b8"))
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df[["migration_priority", "node_id", "nf_type", "centrality_score", "connection_count", "subscriber_reach"]], use_container_width=True)


# ─── Tab 4: QMIE ────────────────────────────────────────────────────────────
with tabs[3]:
    has_risk = api_get("/workflow/data/risk")
    has_plan = api_get("/workflow/data/plan")
    has_fail = api_get("/workflow/data/failures")
    has_exp  = api_get("/workflow/data/explanations")
    
    if not has_risk:
        st.info("Run the workflow to see QMIE results.")
        if st.button("Run QMIE"): api_post("/workflow/step4/qmie"); st.rerun()
    else:
        qt1, qt2, qt3, qt4 = st.tabs(["Risk Scorer", "Optimizer Plan", "Failure Predictor", "Explainability"])
        
        with qt1:
            st.markdown('<div class="section-header">Quantum Migration Impact Score (QMIS)</div>', unsafe_allow_html=True)
            scores = has_risk.get("scores", [])
            df = pd.DataFrame(scores)
            st.dataframe(df[["node_id", "nf_type", "qmis", "risk_tier", "crypto_risk", "centrality_impact", "hndl_risk"]], use_container_width=True)
            
        with qt2:
            st.markdown('<div class="section-header">Optimized Migration Plan</div>', unsafe_allow_html=True)
            steps = has_plan.get("steps", [])
            df = pd.DataFrame(steps)
            st.dataframe(df[["step_number", "node_id", "migration_strategy", "target_algo", "estimated_downtime_min", "maintenance_window"]], use_container_width=True)
            
        with qt3:
            st.markdown('<div class="section-header">Failure Prediction (AI)</div>', unsafe_allow_html=True)
            preds = has_fail.get("predictions", [])
            df = pd.DataFrame(preds)
            st.dataframe(df[["node_id", "risk_flag", "registration_success_pct", "rollback_probability", "recommended_action"]], use_container_width=True)
            
        with qt4:
            st.markdown('<div class="section-header">Explainability Engine</div>', unsafe_allow_html=True)
            exps = has_exp.get("items", [])
            for e in exps[:3]:
                with st.expander(f"Explain Migration Decision: {e['node_id']} ({e['nf_type']})", expanded=True):
                    st.write("**Plain English:**", e["plain_english_summary"])
                    st.write("**Why this order?**", e["why_this_order"])
                    st.write("**What if delayed?**", e["what_if_delayed"])


# ─── Tab 5: Digital Twin ────────────────────────────────────────────────────
with tabs[4]:
    data = api_get("/workflow/data/twin")
    if not data:
        st.info("Run the workflow to see Digital Twin Validation.")
        if st.button("Run Twin"): api_post("/workflow/step5/twin"); st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#10b981;">{data.get("passed",0)}</div><div class="metric-label">NFs Passed</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#ef4444;">{data.get("failed",0)}</div><div class="metric-label">NFs Failed</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("confidence",0)}%</div><div class="metric-label">Twin Confidence</div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Twin Validation Reports</div>', unsafe_allow_html=True)
        reports = data.get("reports", [])
        for r in reports[:5]:
            color = "#10b981" if r["overall_passed"] else "#ef4444"
            with st.expander(f"Twin Report: {r['nf_id']} - {'PASSED' if r['overall_passed'] else 'FAILED'}"):
                st.write("**Recommendation:**", r["recommendation"])
                st.write(f"**Pass Rate:** {r['pass_rate_pct']}% | **Confidence:** {r['twin_confidence_score']}%")
                df_kpi = pd.DataFrame(r.get("kpi_deltas", []))
                if not df_kpi.empty:
                    st.dataframe(df_kpi[["metric_name", "before", "after", "delta_pct", "within_sla"]], use_container_width=True)


# ─── Tab 6: PQC Validation ──────────────────────────────────────────────────
with tabs[5]:
    data = api_get("/workflow/data/pqc")
    if not data:
        st.info("Run the workflow to see Hybrid PQC Validation.")
        if st.button("Run PQC Demo"): api_post("/workflow/step6/pqc"); st.rerun()
    else:
        st.markdown('<div class="section-header">Hybrid PQC Validation (Kyber + Dilithium)</div>', unsafe_allow_html=True)
        is_real = data.get("is_real_pqc", False)
        if is_real:
            st.markdown('<div class="alert-ok">✅ <b>liboqs detected</b> — Running REAL NIST PQC (ML-KEM-768 + ML-DSA-65)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-high">⚠️ <b>liboqs not installed</b> — Running simulated PQC stubs.</div>', unsafe_allow_html=True)
            
        c1, c2 = st.columns(2)
        with c1:
            st.write("### KEM Handshake")
            st.write(f"**Match:** {'✅' if data.get('kem_match') else '❌'}")
            st.write(f"**Keygen:** {data.get('keygen_ms', 0):.2f} ms")
            st.write(f"**Encap:** {data.get('encap_ms', 0):.2f} ms")
            st.write(f"**Decap:** {data.get('decap_ms', 0):.2f} ms")
        with c2:
            st.write("### Digital Signature")
            st.write(f"**Valid:** {'✅' if data.get('signature_valid') else '❌'}")
            st.write(f"**Sign:** {data.get('sign_ms', 0):.2f} ms")
            st.write(f"**Verify:** {data.get('verify_ms', 0):.2f} ms")
            

# ─── Tab 7: Edge Sentinel ───────────────────────────────────────────────────
with tabs[6]:
    data = api_get("/workflow/data/sentinel")
    if not data:
        st.info("Run the workflow to see Edge Crypto Sentinel data.")
        if st.button("Run Sentinel"): api_get("/workflow/step7/sentinel"); st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("avg_posture_score",0):.1f}</div><div class="metric-label">Avg Posture</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#ef4444;">{data.get("critical_alerts",0)}</div><div class="metric-label">Critical Alerts</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#60a5fa;">{data.get("pqc_cipher_count",0)}</div><div class="metric-label">PQC Connections</div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Live Alerts</div>', unsafe_allow_html=True)
        alerts = data.get("alerts", [])
        if alerts:
            df = pd.DataFrame(alerts)
            st.dataframe(df[["nf_id", "alert_type", "severity", "message"]], use_container_width=True)


# ─── Tab 8: Policy Engine ───────────────────────────────────────────────────
with tabs[7]:
    data = api_get("/workflow/data/policy")
    if not data:
        st.info("Run the workflow to see Policy Engine actions.")
        if st.button("Run Policy Engine"): api_get("/workflow/step8/policy"); st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("compliance_pct",0):.1f}%</div><div class="metric-label">Compliance</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("total_violations",0)}</div><div class="metric-label">Total Violations</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#10b981;">{data.get("auto_remediated",0)}</div><div class="metric-label">Auto-Remediated</div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Compliance Status per NF</div>', unsafe_allow_html=True)
        statuses = data.get("statuses", [])
        if statuses:
            for s in statuses[:5]:
                with st.expander(f"{s['nf_id']} - Score: {s['compliance_score']} - {'✅ Compliant' if s['overall_compliant'] else '❌ Non-Compliant'}"):
                    if s.get("violations"):
                        st.write("**Violations:**")
                        st.dataframe(pd.DataFrame(s["violations"])[["policy_rule", "severity", "description", "auto_remediation"]])
                    if s.get("actions"):
                        st.write("**Auto-Remediation Actions Taken:**")
                        st.dataframe(pd.DataFrame(s["actions"])[["action_type", "description", "status"]])


# ─── Tab 9: Executive Report ────────────────────────────────────────────────
with tabs[8]:
    data = api_get("/workflow/data/report")
    if not data:
        st.info("Run the full workflow to generate the Executive Report.")
    else:
        st.markdown(f"### 📄 Executive Summary Report")
        st.caption(f"Generated at: `{data.get('generated_at')}` | Classification: **TOP SECRET // NCIIPC**")
        st.markdown("---")
        
        # Pipeline Summary Cards
        pipe = data.get("pipeline_summary", {})
        st.markdown('<div class="section-header">PIPELINE EXECUTION SUMMARY</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{pipe.get("steps_completed", 0)}/9</div><div class="metric-label">Steps Completed</div></div>', unsafe_allow_html=True)
        with col2:
            qmis = pipe.get("risk", {}).get("avg_qmis", 0) if pipe.get("risk") else 0
            color = "#ef4444" if qmis > 70 else "#f59e0b" if qmis > 40 else "#10b981"
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:{color};">{qmis:.1f}</div><div class="metric-label">Avg QMIS Risk</div></div>', unsafe_allow_html=True)
        with col3:
            comp = pipe.get("policy", {}).get("compliance_pct", 0) if pipe.get("policy") else 0
            color = "#10b981" if comp > 80 else "#f59e0b"
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:{color};">{comp:.0f}%</div><div class="metric-label">Policy Compliance</div></div>', unsafe_allow_html=True)
        with col4:
            tw = pipe.get("twin", {}).get("confidence", 0) if pipe.get("twin") else 0
            color = "#10b981" if tw > 80 else "#ef4444"
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:{color};">{tw:.1f}%</div><div class="metric-label">Twin Confidence</div></div>', unsafe_allow_html=True)
        
        # Tamper-Evident Ledger Section
        st.markdown('<div class="section-header" style="margin-top: 40px;">TAMPER-EVIDENT EVIDENCE LEDGER</div>', unsafe_allow_html=True)
        
        ledger_data = data.get("ledger", {})
        is_valid = ledger_data.get('chain_valid', False)
        
        lc1, lc2 = st.columns([1, 3])
        with lc1:
            if is_valid:
                st.markdown('<div style="padding:20px; border-radius:12px; background:rgba(16,185,129,0.1); border:1px solid #10b981; text-align:center;"><h1 style="margin:0;color:#10b981;">🛡️ VALID</h1><p style="margin:0;color:#a7f3d0;font-size:0.8rem;">Cryptographic Chain Intact</p></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="padding:20px; border-radius:12px; background:rgba(239,68,68,0.1); border:1px solid #ef4444; text-align:center;"><h1 style="margin:0;color:#ef4444;">⚠️ BROKEN</h1><p style="margin:0;color:#fca5a5;font-size:0.8rem;">Tampering Detected</p></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.write(f"**Events Logged:** {ledger_data.get('total_entries', 0)}")
            
            st.markdown("<br><p style='font-size:0.75rem; color:#64748b; margin-bottom:0;'>ROOT HASH</p>", unsafe_allow_html=True)
            st.code(ledger_data.get("ledger_root_hash", "N/A"), language="text")
            
        with lc2:
            st.write("### 📜 Immutable Event Log")
            entries = ledger_data.get("entries", [])
            if entries:
                df_ledger = pd.DataFrame(entries)
                # Format timestamp
                df_ledger['timestamp'] = pd.to_datetime(df_ledger['timestamp']).dt.strftime('%H:%M:%S.%f')
                
                # Show nicely formatted dataframe
                st.dataframe(
                    df_ledger[["sequence", "timestamp", "event_type", "entry_id", "previous_hash"]],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Expandable raw data for auditors
                with st.expander("🔍 View Raw Cryptographic Ledger JSON (Auditor View)"):
                    st.json(ledger_data)
            else:
                st.info("No ledger entries found.")

