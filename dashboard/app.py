"""
Q-RAKSHA SENTINEL — Executive Dashboard (Glassmorphism Edition)
"""
import base64
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import requests

# ── Load background image as base64 ─────────────────────────────────────────
_BG_PATH = Path(__file__).parent / "static" / "bg.png"
_BG_B64 = ""
if _BG_PATH.exists():
    with open(_BG_PATH, "rb") as _f:
        _BG_B64 = base64.b64encode(_f.read()).decode()

st.set_page_config(
    page_title="Q-RAKSHA SENTINEL",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: Quantum background + iOS glassmorphism ──────────────────────────────
_bg_css = f"url('data:image/png;base64,{_BG_B64}')" if _BG_B64 else "linear-gradient(135deg,#0d0221 0%,#1a0533 50%,#0d1a3a 100%)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Root Variables ── */
:root {{
    --glass-bg:       rgba(255,255,255,0.07);
    --glass-border:   rgba(255,255,255,0.18);
    --glass-shadow:   0 8px 32px rgba(0,0,0,0.4);
    --glass-blur:     backdrop-filter: blur(20px) saturate(180%);
    --accent-orange:  #f97316;
    --accent-amber:   #fbbf24;
    --accent-blue:    #60a5fa;
    --accent-cyan:    #22d3ee;
    --accent-purple:  #a78bfa;
    --accent-green:   #34d399;
    --accent-red:     #f87171;
    --text-primary:   rgba(255,255,255,0.95);
    --text-secondary: rgba(255,255,255,0.65);
    --text-dim:       rgba(255,255,255,0.35);
}}

/* ── Full-page quantum background ── */
html, body, .stApp {{
    font-family: 'Inter', sans-serif !important;
    background-image: {_bg_css} !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
    color: var(--text-primary) !important;
}}

/* Subtle dark veil for readability */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    background: rgba(8, 4, 20, 0.55);
    z-index: 0;
    pointer-events: none;
}}

/* ── Glassmorphism Sidebar ── */
[data-testid="stSidebar"] {{
    background: rgba(10, 5, 30, 0.65) !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
    border-right: 1px solid rgba(255,255,255,0.12) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.4) !important;
}}

/* ── Glass Card ── */
.glass-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    box-shadow: var(--glass-shadow), inset 0 1px 0 rgba(255,255,255,0.15);
    padding: 24px;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    position: relative;
    overflow: hidden;
}}
.glass-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
}}
.glass-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.2);
}}

/* ── Metric Cards ── */
.metric-card {{
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(20px) saturate(200%);
    -webkit-backdrop-filter: blur(20px) saturate(200%);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 18px;
    padding: 22px 18px;
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.12);
    position: relative;
    overflow: hidden;
}}
.metric-card::after {{
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at center, rgba(255,255,255,0.03) 0%, transparent 70%);
    pointer-events: none;
}}
.metric-card:hover {{
    transform: translateY(-4px) scale(1.02);
    border-color: rgba(255,255,255,0.28);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.2);
}}
.metric-card .metric-value {{
    font-size: 2.2rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    background: linear-gradient(135deg, #fbbf24 0%, #f97316 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}}
.metric-card .metric-label {{
    font-size: 0.72rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 600;
    margin-top: 6px;
}}

/* ── Logo ── */
.logo-text {{
    font-size: 1.5rem;
    font-weight: 900;
    background: linear-gradient(135deg, #fbbf24 0%, #f97316 40%, #a78bfa 80%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    text-shadow: none;
}}
.logo-sub {{
    font-size: 0.6rem;
    color: var(--text-dim);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 2px;
}}

/* ── Section headers ── */
.section-header {{
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
}}

/* ── Alert boxes ── */
.alert-critical {{
    background: rgba(248,113,113,0.12);
    border-left: 3px solid #f87171;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    margin: 6px 0;
    font-size: 0.83rem;
    backdrop-filter: blur(10px);
}}
.alert-ok {{
    background: rgba(52,211,153,0.12);
    border-left: 3px solid #34d399;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    margin: 6px 0;
    font-size: 0.83rem;
    backdrop-filter: blur(10px);
}}
.alert-high {{
    background: rgba(251,191,36,0.12);
    border-left: 3px solid #fbbf24;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    margin: 6px 0;
    font-size: 0.83rem;
    backdrop-filter: blur(10px);
}}

/* ── Pipeline Steps ── */
.step-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
    padding: 14px 16px;
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.1);
}}
.step-box {{
    padding: 6px 14px;
    border-radius: 30px;
    font-size: 0.72rem;
    font-weight: 600;
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.35);
    border: 1px solid rgba(255,255,255,0.1);
    letter-spacing: 0.03em;
    transition: all 0.2s;
}}
.step-box.done {{
    background: rgba(52,211,153,0.15);
    color: #34d399;
    border-color: rgba(52,211,153,0.4);
    box-shadow: 0 0 12px rgba(52,211,153,0.15);
}}
.step-box.active {{
    background: rgba(249,115,22,0.2);
    color: #fb923c;
    border-color: rgba(249,115,22,0.5);
    box-shadow: 0 0 16px rgba(249,115,22,0.25);
    animation: pulse-orange 2s infinite;
}}
@keyframes pulse-orange {{
    0%,100% {{ box-shadow: 0 0 16px rgba(249,115,22,0.25); }}
    50%      {{ box-shadow: 0 0 24px rgba(249,115,22,0.5); }}
}}

/* ── Buttons ── */
.stButton > button {{
    background: rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.9) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    backdrop-filter: blur(12px) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em !important;
}}
.stButton > button:hover {{
    background: rgba(249,115,22,0.2) !important;
    border-color: rgba(249,115,22,0.6) !important;
    box-shadow: 0 0 20px rgba(249,115,22,0.3) !important;
    transform: translateY(-1px) !important;
}}
.primary-btn > button {{
    background: linear-gradient(135deg, rgba(249,115,22,0.4), rgba(167,139,250,0.3)) !important;
    border-color: rgba(249,115,22,0.5) !important;
    box-shadow: 0 4px 20px rgba(249,115,22,0.25) !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: rgba(255,255,255,0.04) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    padding: 4px !important;
    gap: 2px !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    border-radius: 10px !important;
    padding: 6px 14px !important;
    transition: all 0.2s !important;
}}
.stTabs [aria-selected="true"] {{
    background: rgba(249,115,22,0.25) !important;
    color: #fb923c !important;
}}

/* ── Dataframe ── */
.stDataFrame {{
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    backdrop-filter: blur(12px) !important;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background: rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    backdrop-filter: blur(12px) !important;
    color: var(--text-primary) !important;
}}

/* ── Main page header ── */
h1, h2, h3 {{
    color: rgba(255,255,255,0.95) !important;
    font-family: 'Inter', sans-serif !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.03); }}
::-webkit-scrollbar-thumb {{ background: rgba(249,115,22,0.4); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(249,115,22,0.7); }}

/* Force plotly chart backgrounds transparent */
.js-plotly-plot .plotly {{ background: transparent !important; }}
</style>
""", unsafe_allow_html=True)


# ─── Initialization ──────────────────────────────────────────────────────────

API_URL = os.environ.get("API_URL", "http://localhost:8765")

if "workflow_step" not in st.session_state:
    st.session_state.workflow_step = 0
if "workflow_running" not in st.session_state:
    st.session_state.workflow_running = False

def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=4.0)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def api_post(endpoint, json_data=None):
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=json_data, timeout=8.0)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def _plot_layout():
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.75)", family="Inter"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.07)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.07)"),
        margin=dict(l=20, r=20, t=40, b=20),
    )

# Fetch latest pipeline status
status = api_get("/workflow/status")
if status:
    st.session_state.workflow_step = status.get("step", 0)
    st.session_state.workflow_running = status.get("running", False)


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="logo-text">🛡️ Q-RAKSHA</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Sentinel · Telecom Quantum Migration</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    api_ok = status is not None
    if api_ok:
        st.markdown('<div class="alert-ok">⚡ Backend API: Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-critical">🔴 Backend API: Offline</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Mission Control</div>', unsafe_allow_html=True)

    st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
    if st.button("▶️ Run Full Migration Workflow", disabled=st.session_state.workflow_running or not api_ok):
        res = api_post("/workflow/run", {"target_path": ".", "num_nfs": 24})
        if res:
            st.session_state.workflow_running = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.workflow_running:
        st.info(f"⏳ Step {st.session_state.workflow_step}/9 running...")
        time.sleep(1.5)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Quick Steps</div>', unsafe_allow_html=True)
    if st.button("Step 2: Build Graph"):
        api_post("/workflow/step2/graph"); st.rerun()
    if st.button("Step 4: Run QMIE"):
        api_post("/workflow/step4/qmie"); st.rerun()
    if st.button("Step 7: Run Sentinel"):
        api_get("/workflow/step7/sentinel"); st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("Q-RAKSHA SENTINEL v2.0 · NCIIPC Classified")


# ─── Pipeline Header ─────────────────────────────────────────────────────────

st.markdown("""
<div style="margin-bottom: 8px;">
  <span style="font-size:2rem;font-weight:900;background:linear-gradient(135deg,#fbbf24,#f97316,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Q-RAKSHA SENTINEL</span>
  <span style="font-size:0.8rem;color:rgba(255,255,255,0.4);margin-left:12px;font-family:JetBrains Mono,monospace;">AUTONOMOUS TELECOM QUANTUM MIGRATION PLATFORM</span>
</div>
""", unsafe_allow_html=True)

# Pipeline Step Tracker
steps_def = [(1,"CBOM"),(2,"Graph"),(3,"Centrality"),(4,"QMIE"),(5,"Twin"),(6,"PQC"),(7,"Sentinel"),(8,"Policy"),(9,"Report")]
curr_step = st.session_state.workflow_step
html = '<div class="step-container">'
for s_num, s_name in steps_def:
    cls = "step-box"
    if s_num < curr_step: cls += " done"
    elif s_num == curr_step and st.session_state.workflow_running: cls += " active"
    icon = "✓ " if s_num < curr_step else ""
    html += f'<div class="{cls}">{icon}Step {s_num}: {s_name}</div>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)


# ─── Tabs ────────────────────────────────────────────────────────────────────

tabs = st.tabs(["1️⃣ CBOM","2️⃣ Graph","3️⃣ Centrality","4️⃣ QMIE","5️⃣ Twin","6️⃣ PQC","7️⃣ Sentinel","8️⃣ Policy","9️⃣ Report"])


# ── Tab 1: CBOM ──────────────────────────────────────────────────────────────
with tabs[0]:
    data = api_get("/workflow/data/cbom")
    if not data:
        st.info("💡 Run the workflow or click **Step 1** to begin discovery.")
        if st.button("▶ Run Discovery"): api_post("/workflow/step1/cbom",{"target_path":".","years_secret":10}); st.rerun()
    else:
        stats = data.get("statistics", {})
        c1,c2,c3,c4 = st.columns(4)
        for col, val, label, color in [
            (c1, stats.get("files_scanned",0),      "Files Scanned",    None),
            (c2, stats.get("total_findings",0),     "Crypto Findings",  "#f87171"),
            (c3, stats.get("by_risk",{}).get("CRITICAL",0), "Critical", "#fbbf24"),
            (c4, stats.get("hndl_risk_count",0),    "HNDL Exposed",     "#22d3ee"),
        ]:
            style = f'style="-webkit-text-fill-color:{color};"' if color else ""
            col.markdown(f'<div class="metric-card"><div class="metric-value" {style}>{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Telecom CBOM Findings</div>', unsafe_allow_html=True)
        findings = data.get("findings", [])
        if findings:
            df = pd.DataFrame(findings)
            st.dataframe(df[["file","algorithm","risk_level","harvest_now_decrypt_later","recommendation"]], use_container_width=True, hide_index=True)


# ── Tab 2: Knowledge Graph ────────────────────────────────────────────────────
with tabs[1]:
    data = api_get("/workflow/data/graph")
    if not data:
        st.info("💡 Run the workflow to build the 5G Knowledge Graph.")
        if st.button("▶ Build Graph"): api_post("/workflow/step2/graph"); st.rerun()
    else:
        nfs = data.get("nf_nodes", [])
        pqc_ready = sum(1 for n in nfs if n.get("pqc_ready"))
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("node_count",0)}</div><div class="metric-label">Total Nodes</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("edge_count",0)}</div><div class="metric-label">SBA Edges</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#34d399;">{pqc_ready}</div><div class="metric-label">PQC Ready NFs</div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">NF Inventory</div>', unsafe_allow_html=True)
        if nfs:
            df = pd.DataFrame(nfs)
            
            # Donut chart — NF types
            type_counts = df["nf_type"].value_counts().reset_index()
            type_counts.columns = ["nf_type","count"]
            fig = go.Figure(go.Pie(
                labels=type_counts["nf_type"], values=type_counts["count"],
                hole=0.6, marker=dict(colors=px.colors.sequential.Plasma_r),
                textfont=dict(color="white")
            ))
            fig.update_layout(title="NF Type Distribution", **_plot_layout())
            fig.update_layout(legend=dict(font=dict(color="rgba(255,255,255,0.7)")))
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df[["node_id","nf_type","vendor","cert_algorithm","pqc_ready","subscriber_count"]], use_container_width=True, hide_index=True)


# ── Tab 3: Centrality ─────────────────────────────────────────────────────────
with tabs[2]:
    data = api_get("/workflow/data/centrality")
    if not data:
        st.info("💡 Compute dependency centrality to identify critical NFs.")
        if st.button("▶ Compute Centrality"): api_post("/workflow/step3/centrality"); st.rerun()
    else:
        st.markdown(f'<div class="alert-ok">{data.get("summary","")}</div>', unsafe_allow_html=True)
        scores = data.get("scores",[])
        if scores:
            df = pd.DataFrame(scores)
            top10 = df.head(10)
            fig = go.Figure(go.Bar(
                x=top10["node_id"], y=top10["centrality_score"],
                marker=dict(
                    color=top10["centrality_score"],
                    colorscale=[[0,"rgba(167,139,250,0.7)"],[1,"rgba(249,115,22,0.9)"]],
                    line=dict(color="rgba(255,255,255,0.2)", width=1)
                )
            ))
            fig.update_layout(title="Top 10 NFs by Centrality Score", **_plot_layout())
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[["migration_priority","node_id","nf_type","centrality_score","connection_count","subscriber_reach"]], use_container_width=True, hide_index=True)


# ── Tab 4: QMIE ──────────────────────────────────────────────────────────────
with tabs[3]:
    has_risk = api_get("/workflow/data/risk")
    has_plan = api_get("/workflow/data/plan")
    has_fail = api_get("/workflow/data/failures")
    has_exp  = api_get("/workflow/data/explanations")

    if not has_risk:
        st.info("💡 Run the QMIE engine to get full risk, plan, and AI predictions.")
        if st.button("▶ Run QMIE"): api_post("/workflow/step4/qmie"); st.rerun()
    else:
        qt1,qt2,qt3,qt4 = st.tabs(["🔴 Risk Scorer","📋 Migration Plan","🤖 AI Predictor","💡 Explainability"])

        with qt1:
            scores = has_risk.get("scores",[])
            cr,hi,md,lw = has_risk.get("critical",0),has_risk.get("high",0),has_risk.get("medium",0),0
            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#f87171;">{cr}</div><div class="metric-label">Critical NFs</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#fbbf24;">{hi}</div><div class="metric-label">High Risk</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#22d3ee;">{has_risk.get("avg_qmis",0):.1f}</div><div class="metric-label">Avg QMIS</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-card"><div class="metric-value">{len(scores)}</div><div class="metric-label">Total NFs</div></div>', unsafe_allow_html=True)
            
            if scores:
                df = pd.DataFrame(scores)
                fig = go.Figure(go.Bar(
                    x=df["node_id"][:15], y=df["qmis"][:15],
                    marker=dict(color=df["qmis"][:15], colorscale=[[0,"rgba(52,211,153,0.7)"],[0.5,"rgba(251,191,36,0.8)"],[1,"rgba(248,113,113,0.9)"]]),
                ))
                fig.update_layout(title="QMIS Risk Scores per NF", **_plot_layout())
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df[["node_id","nf_type","qmis","risk_tier","crypto_risk","centrality_impact","hndl_risk"]], use_container_width=True, hide_index=True)

        with qt2:
            if has_plan:
                steps = has_plan.get("steps",[])
                c1,c2 = st.columns(2)
                c1.markdown(f'<div class="metric-card"><div class="metric-value">{has_plan.get("total_nfs",0)}</div><div class="metric-label">NFs to Migrate</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><div class="metric-value">{has_plan.get("total_downtime_min",0):.0f} min</div><div class="metric-label">Est. Downtime</div></div>', unsafe_allow_html=True)
                if steps:
                    df = pd.DataFrame(steps)
                    st.dataframe(df[["step_number","node_id","migration_strategy","target_algo","estimated_downtime_min","maintenance_window"]], use_container_width=True, hide_index=True)

        with qt3:
            if has_fail:
                preds = has_fail.get("predictions",[])
                c1,c2,c3 = st.columns(3)
                c1.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#f87171;">🔴 {has_fail.get("red",0)}</div><div class="metric-label">High Risk</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#fbbf24;">🟡 {has_fail.get("yellow",0)}</div><div class="metric-label">Medium Risk</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#34d399;">🟢 {has_fail.get("green",0)}</div><div class="metric-label">Low Risk</div></div>', unsafe_allow_html=True)
                if preds:
                    df = pd.DataFrame(preds)
                    st.dataframe(df[["node_id","risk_flag","registration_success_pct","rollback_probability","recommended_action"]], use_container_width=True, hide_index=True)

        with qt4:
            if has_exp:
                items = has_exp.get("items",[])
                for e in items[:4]:
                    with st.expander(f"🔍 {e['node_id']} · {e['nf_type']}", expanded=False):
                        st.markdown(f'<div class="alert-ok"><b>Plain English:</b> {e["plain_english_summary"]}</div>', unsafe_allow_html=True)
                        st.write("**Why this order?**", e["why_this_order"])
                        st.write("**What if delayed?**", e["what_if_delayed"])
                        st.write("**What if vendor upgraded?**", e["what_if_vendor_upgraded"])


# ── Tab 5: Digital Twin ───────────────────────────────────────────────────────
with tabs[4]:
    data = api_get("/workflow/data/twin")
    if not data:
        st.info("💡 Run the Digital Twin to simulate post-migration behavior.")
        if st.button("▶ Run Twin"): api_post("/workflow/step5/twin"); st.rerun()
    else:
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#34d399;">{data.get("passed",0)}</div><div class="metric-label">NFs Passed</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#f87171;">{data.get("failed",0)}</div><div class="metric-label">NFs Failed</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("confidence",0):.1f}%</div><div class="metric-label">Twin Confidence</div></div>', unsafe_allow_html=True)

        for r in data.get("reports",[])[:5]:
            icon = "✅" if r["overall_passed"] else "❌"
            with st.expander(f"{icon} {r['nf_id']} — Pass Rate {r['pass_rate_pct']}%"):
                st.write("**Recommendation:**", r["recommendation"])
                df_kpi = pd.DataFrame(r.get("kpi_deltas",[]))
                if not df_kpi.empty:
                    st.dataframe(df_kpi[["metric_name","before","after","delta_pct","within_sla"]], use_container_width=True, hide_index=True)


# ── Tab 6: PQC ───────────────────────────────────────────────────────────────
with tabs[5]:
    data = api_get("/workflow/data/pqc")
    if not data:
        st.info("💡 Validate the Hybrid PQC handshake (ML-KEM-768 + ML-DSA-65).")
        if st.button("▶ Run PQC Demo"): api_post("/workflow/step6/pqc"); st.rerun()
    else:
        if data.get("is_real_pqc"):
            st.markdown('<div class="alert-ok">✅ <b>liboqs present</b> — Running REAL NIST PQC (ML-KEM-768 + ML-DSA-65)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-high">⚠️ <b>liboqs not installed</b> — Simulated PQC fallback active</div>', unsafe_allow_html=True)
        
        c1,c2,c3,c4 = st.columns(4)
        for col, val, label, color in [
            (c1, f"{data.get('keygen_ms',0):.2f} ms", "KEM Keygen",   None),
            (c2, f"{data.get('encap_ms',0):.2f} ms",  "Encapsulate",  None),
            (c3, f"{data.get('decap_ms',0):.2f} ms",  "Decapsulate",  None),
            (c4, "✅ VALID" if data.get("kem_match") else "❌ FAIL", "KEM Match", "#34d399" if data.get("kem_match") else "#f87171"),
        ]:
            style = f'style="-webkit-text-fill-color:{color};"' if color else ""
            col.markdown(f'<div class="metric-card"><div class="metric-value" {style}>{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">QKD Live Status</div>', unsafe_allow_html=True)
        st.write(f"**Mode:** `{data.get('qkd_mode','N/A')}`  |  **Key Buffer:** `{data.get('key_buffer_bytes',0)} bytes`")


# ── Tab 7: Sentinel ───────────────────────────────────────────────────────────
with tabs[6]:
    data = api_get("/workflow/data/sentinel")
    if not data:
        st.info("💡 Start Edge Crypto Sentinel to monitor live TLS posture.")
        if st.button("▶ Run Sentinel"): api_get("/workflow/step7/sentinel"); st.rerun()
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("avg_posture_score",0):.0f}</div><div class="metric-label">Avg Posture</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#f87171;">{data.get("critical_alerts",0)}</div><div class="metric-label">Critical Alerts</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#fbbf24;">{data.get("warning_alerts",0)}</div><div class="metric-label">Warnings</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#22d3ee;">{data.get("pqc_cipher_count",0)}</div><div class="metric-label">PQC Connections</div></div>', unsafe_allow_html=True)

        # TLS Version pie chart
        tls_inv = data.get("tls_version_inventory",{})
        if tls_inv:
            fig = go.Figure(go.Pie(
                labels=list(tls_inv.keys()), values=list(tls_inv.values()), hole=0.5,
                marker=dict(colors=["#34d399","#fbbf24","#f87171","#a78bfa"]),
            ))
            fig.update_layout(title="TLS Version Distribution", **_plot_layout())
            fig.update_layout(legend=dict(font=dict(color="rgba(255,255,255,0.7)")))
            st.plotly_chart(fig, use_container_width=True)

        alerts = data.get("alerts",[])
        if alerts:
            st.markdown('<div class="section-header">Live Alerts</div>', unsafe_allow_html=True)
            df = pd.DataFrame(alerts)
            st.dataframe(df[["nf_id","alert_type","severity","message"]], use_container_width=True, hide_index=True)


# ── Tab 8: Policy ─────────────────────────────────────────────────────────────
with tabs[7]:
    data = api_get("/workflow/data/policy")
    if not data:
        st.info("💡 Run the Adaptive Policy Engine to evaluate compliance.")
        if st.button("▶ Run Policy Engine"): api_get("/workflow/step8/policy"); st.rerun()
    else:
        c1,c2,c3,c4 = st.columns(4)
        comp = data.get("compliance_pct",0)
        comp_col = "#34d399" if comp > 80 else "#fbbf24" if comp > 60 else "#f87171"
        c1.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:{comp_col};">{comp:.0f}%</div><div class="metric-label">Compliance</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">{data.get("total_violations",0)}</div><div class="metric-label">Total Violations</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#f87171;">{data.get("critical_violations",0)}</div><div class="metric-label">Critical</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:#34d399;">{data.get("auto_remediated",0)}</div><div class="metric-label">Auto-Remediated</div></div>', unsafe_allow_html=True)

        for s in data.get("statuses",[])[:5]:
            icon = "✅" if s["overall_compliant"] else "❌"
            with st.expander(f"{icon} {s['nf_id']} · Score: {s['compliance_score']}/100 · {s['risk_tier']}"):
                viols = s.get("violations",[])
                if viols:
                    df_v = pd.DataFrame(viols)
                    st.dataframe(df_v[["policy_rule","severity","description","auto_remediation"]], use_container_width=True, hide_index=True)
                acts = s.get("actions",[])
                if acts:
                    df_a = pd.DataFrame(acts)
                    st.dataframe(df_a[["action_type","description","status"]], use_container_width=True, hide_index=True)


# ── Tab 9: Executive Report ───────────────────────────────────────────────────
with tabs[8]:
    data = api_get("/workflow/data/report")
    if not data:
        st.info("💡 Complete the full workflow to generate the Executive Report.")
    else:
        st.markdown(f"### 📄 Executive Summary Report")
        st.caption(f"Generated at: `{data.get('generated_at')}` · Classification: **TOP SECRET // NCIIPC**")
        st.markdown("---")

        pipe = data.get("pipeline_summary", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{pipe.get("steps_completed",0)}/9</div><div class="metric-label">Steps Completed</div></div>', unsafe_allow_html=True)
        qmis = pipe.get("risk",{}).get("avg_qmis",0) if pipe.get("risk") else 0
        qcol = "#f87171" if qmis>70 else "#fbbf24" if qmis>40 else "#34d399"
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="-webkit-text-fill-color:{qcol};">{qmis:.1f}</div><div class="metric-label">Avg QMIS Risk</div></div>', unsafe_allow_html=True)
        comp = pipe.get("policy",{}).get("compliance_pct",0) if pipe.get("policy") else 0
        c3.markdown(f'<div class="metric-card"><div class="metric-value">{comp:.0f}%</div><div class="metric-label">Policy Compliance</div></div>', unsafe_allow_html=True)
        tw = pipe.get("twin",{}).get("confidence",0) if pipe.get("twin") else 0
        c4.markdown(f'<div class="metric-card"><div class="metric-value">{tw:.1f}%</div><div class="metric-label">Twin Confidence</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top:32px;">TAMPER-EVIDENT EVIDENCE LEDGER</div>', unsafe_allow_html=True)
        ledger = data.get("ledger", {})
        is_valid = ledger.get("chain_valid", False)

        lc1, lc2 = st.columns([1, 3])
        with lc1:
            badge_html = (
                '<div style="padding:24px;border-radius:20px;background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.4);text-align:center;backdrop-filter:blur(20px);">'
                '<div style="font-size:2.5rem;">🛡️</div>'
                '<div style="font-size:1.1rem;font-weight:800;color:#34d399;margin-top:8px;">CHAIN VALID</div>'
                '<div style="font-size:0.7rem;color:rgba(52,211,153,0.6);margin-top:4px;">Cryptographic Integrity Confirmed</div>'
                '</div>'
            ) if is_valid else (
                '<div style="padding:24px;border-radius:20px;background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.4);text-align:center;backdrop-filter:blur(20px);">'
                '<div style="font-size:2.5rem;">⚠️</div>'
                '<div style="font-size:1.1rem;font-weight:800;color:#f87171;margin-top:8px;">CHAIN BROKEN</div>'
                '<div style="font-size:0.7rem;color:rgba(248,113,113,0.6);margin-top:4px;">Tampering Detected</div>'
                '</div>'
            )
            st.markdown(badge_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.write(f"**Events:** {ledger.get('total_entries',0)}")
            st.markdown("<p style='font-size:0.7rem;color:rgba(255,255,255,0.35);margin-bottom:4px;'>ROOT HASH</p>", unsafe_allow_html=True)
            st.code(ledger.get("ledger_root_hash","N/A"), language="text")
        with lc2:
            st.write("### 📜 Immutable Event Log")
            entries = ledger.get("entries",[])
            if entries:
                df_l = pd.DataFrame(entries)
                df_l["timestamp"] = pd.to_datetime(df_l["timestamp"]).dt.strftime("%H:%M:%S.%f")
                st.dataframe(df_l[["sequence","timestamp","event_type","entry_id","previous_hash"]], use_container_width=True, hide_index=True)
                with st.expander("🔍 Raw Cryptographic Ledger JSON (Auditor View)"):
                    st.json(ledger)
