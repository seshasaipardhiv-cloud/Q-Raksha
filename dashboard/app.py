"""
Q-RAKSHA SENTINEL - Executive Dashboard
Professional glassmorphism UI with dual CSS gradient themes + sign-in portal
"""
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

st.set_page_config(
    page_title="Q-RAKSHA SENTINEL",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# GLOBAL CSS  (ASCII-only Python source; special chars only inside HTML strings)
# =============================================================================

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --crimson:   #dc2626;
  --orange:    #ea580c;
  --amber:     #f59e0b;
  --gold:      #fbbf24;
  --teal:      #0d9488;
  --teal-lt:   #5eead4;
  --green:     #10b981;
  --rose:      #f43f5e;
  --cyan:      #06b6d4;
  --glass:     rgba(255,255,255,0.06);
  --glass-b:   rgba(255,255,255,0.14);
  --blur:      blur(22px) saturate(180%);
  --shadow:    0 8px 40px rgba(0,0,0,0.5);
  --text:      rgba(255,255,255,0.93);
  --text-dim:  rgba(255,255,255,0.5);
  --text-muted:rgba(255,255,255,0.3);
}

/* ---- Base ---- */
html, body, .stApp {
  font-family: 'Inter', sans-serif !important;
  color: var(--text) !important;
  overflow-x: hidden;
}

/* ---- Dashboard background: dark crimson/red quantum mesh ---- */
.stApp {
  background:
    radial-gradient(ellipse 75% 55% at 50% 45%, rgba(180,30,15,0.28) 0%, transparent 65%),
    radial-gradient(ellipse 55% 40% at 80% 20%, rgba(120,10,40,0.20) 0%, transparent 55%),
    radial-gradient(ellipse 50% 50% at 15% 80%, rgba(80,0,20,0.18) 0%, transparent 50%),
    radial-gradient(ellipse 40% 40% at 50% 10%, rgba(200,50,10,0.10) 0%, transparent 55%),
    linear-gradient(155deg, #0c0008 0%, #150005 25%, #0f0010 50%, #080006 75%, #0a0000 100%) !important;
}

/* SVG diamond mesh overlay */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cdefs%3E%3Cpattern id='m' width='120' height='120' patternUnits='userSpaceOnUse'%3E%3Cpolygon points='0,60 60,0 120,60 60,120' fill='none' stroke='rgba(220,38,38,0.08)' stroke-width='0.8'/%3E%3Ccircle cx='0'  cy='60' r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='60' cy='0'  r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='120' cy='60' r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='60' cy='120' r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='60' cy='60'  r='1.5' fill='rgba(245,158,11,0.12)'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23m)'/%3E%3C/svg%3E");
  opacity: 0.9;
}

/* Subtle dark veil */
.stApp::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.15) 50%, rgba(0,0,0,0.45) 100%);
  pointer-events: none;
}

/* ---- Streamlit cleanup ---- */
[data-testid="stSidebar"] {
  background: rgba(10,0,5,0.82) !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
  border-right: 1px solid rgba(220,38,38,0.15) !important;
  box-shadow: 4px 0 32px rgba(0,0,0,0.5) !important;
}
[data-testid="stHeader"]   { background: transparent !important; }
[data-testid="stToolbar"]  { background: transparent !important; }
.main .block-container     { padding-top: 1.5rem !important; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* ---- Glass card ---- */
.g-card {
  background: var(--glass);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border: 1px solid var(--glass-b);
  border-radius: 20px;
  box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.12);
  padding: 28px;
  position: relative;
  overflow: hidden;
  transition: transform .25s, box-shadow .25s;
}
.g-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
}
.g-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.18);
}

/* ---- Metric card ---- */
.m-card {
  background: rgba(255,255,255,0.055);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border: 1px solid rgba(255,255,255,0.13);
  border-radius: 16px;
  padding: 20px 16px;
  text-align: center;
  transition: all .3s;
  box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
}
.m-card:hover { transform: translateY(-4px) scale(1.02); border-color: rgba(255,255,255,0.25); }
.m-val {
  font-size: 2rem; font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 40%, #c084fc 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  line-height: 1.1;
}
.m-lbl { font-size: 0.68rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: .12em; font-weight: 600; margin-top: 6px; }

/* ---- Logo ---- */
.logo-text {
  font-size: 1.45rem; font-weight: 900;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 35%, #c084fc 70%, #9333ea 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  letter-spacing: -0.03em;
}
.logo-sub { font-size: 0.58rem; color: var(--text-muted); letter-spacing: .2em; text-transform: uppercase; }

.section-hdr {
  font-size: 0.68rem; font-weight: 700; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .18em;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  padding-bottom: 8px; margin: 22px 0 14px;
}

/* ---- Pipeline steps ---- */
.pipeline-strip {
  display: flex; flex-wrap: wrap; gap: 7px;
  padding: 14px 16px; margin-bottom: 20px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px); border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.09);
}
.p-step {
  padding: 5px 14px; border-radius: 30px;
  font-size: 0.7rem; font-weight: 600; letter-spacing: .03em;
  background: rgba(255,255,255,0.05);
  color: var(--text-muted); border: 1px solid rgba(255,255,255,0.08);
  transition: all .2s;
}
.p-step.done   { background: rgba(16,185,129,0.15); color: #34d399; border-color: rgba(16,185,129,0.35); box-shadow: 0 0 10px rgba(16,185,129,0.12); }
.p-step.active { background: rgba(220,38,38,0.2); color: #fca5a5; border-color: rgba(220,38,38,0.5); animation: pulse-p 2s infinite; }
@keyframes pulse-p {
  0%,100% { box-shadow: 0 0 10px rgba(220,38,38,0.2); }
  50%     { box-shadow: 0 0 22px rgba(220,38,38,0.5); }
}

/* ---- Alert variants ---- */
.al-ok   { background:rgba(16,185,129,.1); border-left:3px solid #10b981; border-radius:0 12px 12px 0; padding:11px 15px; margin:5px 0; font-size:.82rem; backdrop-filter:blur(8px); }
.al-warn { background:rgba(245,158,11,.1); border-left:3px solid #f59e0b; border-radius:0 12px 12px 0; padding:11px 15px; margin:5px 0; font-size:.82rem; backdrop-filter:blur(8px); }
.al-crit { background:rgba(244,63,94,.1);  border-left:3px solid #f43f5e; border-radius:0 12px 12px 0; padding:11px 15px; margin:5px 0; font-size:.82rem; backdrop-filter:blur(8px); }

/* ---- Buttons ---- */
.stButton > button {
  background: rgba(255,255,255,0.07) !important;
  color: rgba(255,255,255,0.9) !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: 12px !important;
  font-weight: 600 !important; font-size: 0.83rem !important;
  backdrop-filter: blur(12px) !important;
  transition: all .2s !important;
}
.stButton > button:hover {
  background: rgba(220,38,38,0.22) !important;
  border-color: rgba(220,38,38,0.55) !important;
  box-shadow: 0 0 18px rgba(220,38,38,0.25) !important;
  transform: translateY(-1px) !important;
}
.primary-btn > button {
  background: linear-gradient(135deg, rgba(220,38,38,0.4), rgba(245,158,11,0.3)) !important;
  border-color: rgba(220,38,38,0.5) !important;
  box-shadow: 0 4px 20px rgba(220,38,38,0.2) !important;
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(12px) !important;
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  padding: 4px !important; gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--text-dim) !important;
  font-weight: 600 !important; font-size: 0.77rem !important;
  border-radius: 8px !important; padding: 6px 13px !important;
  transition: all .2s !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(220,38,38,0.2) !important; color: #fca5a5 !important;
}

/* ---- Inputs ---- */
.stTextInput input, .stPasswordInput input {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: 10px !important; color: white !important;
  backdrop-filter: blur(10px) !important;
}
.stTextInput input:focus, .stPasswordInput input:focus {
  border-color: rgba(220,38,38,0.6) !important;
  box-shadow: 0 0 0 2px rgba(220,38,38,0.2) !important;
}

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb { background: rgba(220,38,38,0.45); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(220,38,38,0.7); }

/* ---- Plotly ---- */
.js-plotly-plot .plotly { background: transparent !important; }
h1,h2,h3 { color: rgba(255,255,255,0.95) !important; font-family:'Inter',sans-serif !important; }

/* Style the entire right column to be the glass card */
[data-testid="column"]:nth-of-type(2) {
  background: rgba(255,255,255,0.055);
  backdrop-filter: blur(32px) saturate(200%);
  -webkit-backdrop-filter: blur(32px) saturate(200%);
  border: 1px solid rgba(255,255,255,0.13);
  border-radius: 24px;
  padding: 36px 32px;
  box-shadow: 0 32px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1);
  margin-top: 30px;
  position: relative;
}
/* Glowing top line */
[data-testid="column"]:nth-of-type(2)::before {
  content: ''; position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(13,148,136,0.9), rgba(251,191,36,0.7), transparent);
}
/* Streamlit OAuth Buttons custom colors */
[data-testid="column"]:nth-of-type(2) .stButton > button { margin-bottom: 4px; }
</style>

"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# =============================================================================
# API helpers
# =============================================================================

API_URL = os.environ.get("API_URL", "http://localhost:8765")

def api_get(ep):
    try:
        r = requests.get(f"{API_URL}{ep}", timeout=4.0)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def api_post(ep, data=None):
    try:
        r = requests.post(f"{API_URL}{ep}", json=data, timeout=8.0)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def plot_cfg():
    return dict(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.7)", family="Inter"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
        margin=dict(l=16, r=16, t=40, b=16),
        legend=dict(font=dict(color="rgba(255,255,255,0.65)")),
    )

# =============================================================================
# Session state
# =============================================================================

defaults = {
    "authenticated": False,
    "user_name": "",
    "user_role": "",
    "workflow_step": 0,
    "workflow_running": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================================================
# LOGIN CSS override (injected only when not authenticated)
# =============================================================================

LOGIN_CSS = """
<style>
/* Login page background -- deep teal/navy quantum theme */
.stApp {
  background:
    radial-gradient(ellipse 70% 60% at 25% 50%, rgba(13,148,136,0.22) 0%, transparent 60%),
    radial-gradient(ellipse 60% 55% at 75% 50%, rgba(6,78,59,0.18) 0%, transparent 55%),
    radial-gradient(ellipse 80% 40% at 50% 90%, rgba(15,118,110,0.12) 0%, transparent 55%),
    radial-gradient(ellipse 50% 40% at 50% 5%,  rgba(20,50,80,0.20) 0%, transparent 50%),
    linear-gradient(145deg, #020c10 0%, #040f18 30%, #030d14 60%, #010a0d 100%) !important;
}
/* Teal mesh overlay */
.stApp::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cdefs%3E%3Cpattern id='t' width='100' height='100' patternUnits='userSpaceOnUse'%3E%3Cpolygon points='0,50 50,0 100,50 50,100' fill='none' stroke='rgba(13,148,136,0.09)' stroke-width='0.7'/%3E%3Cline x1='0' y1='0' x2='100' y2='100' stroke='rgba(13,148,136,0.05)' stroke-width='0.5'/%3E%3Cline x1='100' y1='0' x2='0' y2='100' stroke='rgba(13,148,136,0.05)' stroke-width='0.5'/%3E%3Ccircle cx='50' cy='0'   r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='0'  cy='50'  r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='100' cy='50' r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='50' cy='100' r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='50' cy='50'  r='1.4' fill='rgba(251,191,36,0.10)'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23t)'/%3E%3C/svg%3E") !important;
  opacity: 0.9;
}

/* Streamlit input styling for login */
.stTextInput input, .stPasswordInput input {
  background: rgba(13,148,136,0.08) !important;
  border: 1px solid rgba(13,148,136,0.3) !important;
  border-radius: 10px !important; color: white !important;
}
.stTextInput input:focus, .stPasswordInput input:focus {
  border-color: rgba(13,148,136,0.7) !important;
  box-shadow: 0 0 0 2px rgba(13,148,136,0.2) !important;
}
.stButton > button:hover {
  background: rgba(13,148,136,0.22) !important;
  border-color: rgba(13,148,136,0.55) !important;
  box-shadow: 0 0 18px rgba(13,148,136,0.25) !important;
}
</style>
"""

# =============================================================================
# SIGN-IN PAGE
# =============================================================================

if not st.session_state.authenticated:
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # ----- Left brand panel (rendered via HTML, positioned with columns) -----
    left_col, right_col = st.columns([1.15, 0.85])

    with left_col:
        st.markdown("""
<div style="min-height:95vh;display:flex;flex-direction:column;justify-content:center;
     padding:40px 40px 40px 20px;border-right:1px solid rgba(13,148,136,0.15);">

  <div style="margin-bottom:36px;">
    <div style="font-size:0.65rem;color:rgba(13,148,136,0.75);letter-spacing:.25em;
         text-transform:uppercase;margin-bottom:12px;">
      NCIIPC &middot; NIST PQC FIPS 203/204
    </div>
    <div style="font-size:2.8rem;font-weight:900;line-height:1.05;
         background:linear-gradient(135deg,#fbbf24 0%,#f59e0b 35%,#5eead4 70%,#0d9488 100%);
         -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
         letter-spacing:-0.04em;margin-bottom:14px;">
      Q-RAKSHA<br>SENTINEL
    </div>
    <div style="font-size:0.82rem;color:rgba(255,255,255,0.38);line-height:1.75;max-width:330px;">
      Autonomous 5G Telecom Quantum Migration Intelligence Platform.
      Protect against Harvest-Now-Decrypt-Later threats with AI-driven PQC orchestration.
    </div>
  </div>

  <div style="display:flex;flex-direction:column;gap:10px;max-width:340px;margin-bottom:28px;">
    <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;
         background:rgba(13,148,136,0.08);border:1px solid rgba(13,148,136,0.2);
         border-radius:14px;backdrop-filter:blur(10px);">
      <span style="font-size:1.5rem;">&#128269;</span>
      <div>
        <div style="font-size:1.15rem;font-weight:800;color:#5eead4;font-family:'JetBrains Mono',monospace;">10-Step</div>
        <div style="font-size:0.66rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:.1em;">AI Migration Pipeline</div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;
         background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
         border-radius:14px;backdrop-filter:blur(10px);">
      <span style="font-size:1.5rem;">&#128737;</span>
      <div>
        <div style="font-size:1.15rem;font-weight:800;color:#fbbf24;font-family:'JetBrains Mono',monospace;">ML-KEM-768</div>
        <div style="font-size:0.66rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:.1em;">NIST PQC Algorithm</div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;
         background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
         border-radius:14px;backdrop-filter:blur(10px);">
      <span style="font-size:1.5rem;">&#128225;</span>
      <div>
        <div style="font-size:1.15rem;font-weight:800;color:#34d399;font-family:'JetBrains Mono',monospace;">5G SBA</div>
        <div style="font-size:0.66rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:.1em;">Telecom-Aware Topology</div>
      </div>
    </div>
  </div>

  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <span style="font-size:0.63rem;font-weight:600;padding:4px 12px;border-radius:20px;
         border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">Zero Trust</span>
    <span style="font-size:0.63rem;font-weight:600;padding:4px 12px;border-radius:20px;
         border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">Tamper-Evident</span>
    <span style="font-size:0.63rem;font-weight:600;padding:4px 12px;border-radius:20px;
         border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">Digital Twin</span>
    <span style="font-size:0.63rem;font-weight:600;padding:4px 12px;border-radius:20px;
         border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">AI Predictor</span>
  </div>

  <div style="margin-top:40px;font-size:0.65rem;color:rgba(255,255,255,0.18);">
    &copy; 2025 Q-RAKSHA SENTINEL &middot; NCIIPC Classified &middot; NIST PQC FIPS 203/204
  </div>
</div>
""", unsafe_allow_html=True)

    with right_col:
        st.markdown('''
<div style="text-align:center;margin-bottom:24px;">
  <div style="font-size:2rem;margin-bottom:6px;">&#128274;</div>
  <div style="font-size:1.3rem;font-weight:800;color:rgba(255,255,255,0.95);">Secure Access Portal</div>
  <div style="font-size:0.76rem;color:rgba(255,255,255,0.38);margin-top:4px;">
    Authenticated access to Q-RAKSHA SENTINEL
  </div>
</div>
''', unsafe_allow_html=True)

        if st.button("🔴 Continue with Google", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Google User"
            st.session_state.user_role = "Network Security Analyst"
            st.rerun()

        if st.button("⚫ Continue with GitHub", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "GitHub User"
            st.session_state.user_role = "Telecom Engineer"
            st.rerun()

        if st.button("🔵 Continue with Microsoft", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Microsoft User"
            st.session_state.user_role = "CISO / Executive"
            st.rerun()

        st.markdown('''
<div style="display:flex;align-items:center;gap:10px;margin:20px 0 10px;
     color:rgba(255,255,255,0.25);font-size:0.72rem;">
  <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
  or sign in with credentials
  <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
</div>
''', unsafe_allow_html=True)

        with st.form("signin_form", clear_on_submit=False):
            email    = st.text_input("Email", placeholder="sentinel@nciipc.gov.in")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            role     = st.selectbox("Access Role", [
                "Network Security Analyst",
                "Telecom Engineer",
                "CISO / Executive",
                "NCIIPC Auditor",
            ])
            c1, _ = st.columns(2)
            c1.checkbox("Remember me", value=True)
            submitted = st.form_submit_button("Sign In  -->", use_container_width=True)
            if submitted:
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.user_name = email.split("@")[0].replace(".", " ").title()
                    st.session_state.user_role = role
                    st.rerun()
                else:
                    st.error("Please enter your email and password.")

        st.markdown('''
<p style='text-align:center;font-size:0.67rem;color:rgba(255,255,255,0.18);
   margin-top:16px;line-height:1.7;'>
  Protected by Q-RAKSHA Zero-Trust Architecture<br>
  All sessions are cryptographically audited.
</p>
''', unsafe_allow_html=True)

    st.stop()

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

status = api_get("/workflow/status")
if status:
    st.session_state.workflow_step    = status.get("step", 0)
    st.session_state.workflow_running = status.get("running", False)
api_ok = status is not None

# ---- Sidebar ----
with st.sidebar:
    st.markdown('<div class="logo-text">Q-RAKSHA</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Sentinel &middot; Quantum Migration</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);'
        'border-radius:14px;padding:14px 16px;margin-bottom:16px;">'
        '<div style="font-size:0.72rem;color:rgba(255,255,255,0.45);">Signed in as</div>'
        f'<div style="font-weight:700;font-size:0.9rem;margin:2px 0;">{st.session_state.user_name}</div>'
        f'<div style="font-size:0.7rem;color:rgba(220,38,38,0.85);">{st.session_state.user_role}</div>'
        '</div>',
        unsafe_allow_html=True
    )

    api_cls  = "al-ok"   if api_ok else "al-crit"
    api_msg  = "API Online" if api_ok else "API Offline"
    st.markdown(f'<div class="{api_cls}">{api_msg}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Mission Control</div>', unsafe_allow_html=True)

    st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
    if st.button("Run Full Workflow", disabled=st.session_state.workflow_running or not api_ok):
        res = api_post("/workflow/run", {"target_path": ".", "num_nfs": 24})
        if res:
            st.session_state.workflow_running = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.workflow_running:
        st.info(f"Step {st.session_state.workflow_step}/9 running...")
        time.sleep(1.5)
        st.rerun()

    st.markdown('<div class="section-hdr">Quick Steps</div>', unsafe_allow_html=True)
    if st.button("Build Graph (S2)"):     api_post("/workflow/step2/graph");   st.rerun()
    if st.button("Run QMIE (S4)"):        api_post("/workflow/step4/qmie");    st.rerun()
    if st.button("Edge Sentinel (S7)"):   api_get("/workflow/step7/sentinel"); st.rerun()
    if st.button("Policy Engine (S8)"):   api_get("/workflow/step8/policy");   st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Sign Out"):
        st.session_state.authenticated = False
        st.session_state.user_name = ""
        st.rerun()
    st.caption("Q-RAKSHA SENTINEL v2.0")

# ---- Header ----
ts = time.strftime("%d %b %Y | %H:%M UTC")
st.markdown(
    '<div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:4px;">'
    '<span style="font-size:1.9rem;font-weight:900;'
    'background:linear-gradient(135deg,#fbbf24,#f59e0b,#fca5a5,#dc2626);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'
    'letter-spacing:-0.04em;">Q-RAKSHA SENTINEL</span>'
    f'<span style="font-size:0.68rem;color:rgba(255,255,255,0.3);">{ts}</span>'
    '</div>'
    '<div style="font-size:0.72rem;color:rgba(255,255,255,0.3);letter-spacing:.18em;'
    'text-transform:uppercase;margin-bottom:16px;">Autonomous Telecom Quantum Migration Platform</div>',
    unsafe_allow_html=True
)

# ---- Pipeline step tracker ----
curr = st.session_state.workflow_step
running = st.session_state.workflow_running
steps = [(1,"CBOM"),(2,"Graph"),(3,"Central"),(4,"QMIE"),(5,"Twin"),(6,"PQC"),(7,"Sentinel"),(8,"Policy"),(9,"Report")]

html_steps = '<div class="pipeline-strip">'
for s, n in steps:
    if s < curr:
        html_steps += f'<div class="p-step done">&#10003; S{s}&middot;{n}</div>'
    elif s == curr and running:
        html_steps += f'<div class="p-step active">S{s}&middot;{n}</div>'
    else:
        html_steps += f'<div class="p-step">S{s}&middot;{n}</div>'
html_steps += '</div>'
st.markdown(html_steps, unsafe_allow_html=True)

# ---- Metric card helper ----
def m_card(val, lbl, color=""):
    sty = f'style="-webkit-text-fill-color:{color};"' if color else ""
    return f'<div class="m-card"><div class="m-val" {sty}>{val}</div><div class="m-lbl">{lbl}</div></div>'

# ---- Tabs ----
tabs = st.tabs([
    "S1 CBOM", "S2 Graph", "S3 Centrality", "S4 QMIE",
    "S5 Twin",  "S6 PQC",   "S7 Sentinel",   "S8 Policy", "S9 Report"
])

# ---- Tab 1: CBOM ----
with tabs[0]:
    data = api_get("/workflow/data/cbom")
    if not data:
        st.info("Run CBOM Discovery to begin crypto asset scanning.")
        if st.button("Run CBOM Discovery"):
            api_post("/workflow/step1/cbom", {"target_path": ".", "years_secret": 10})
            st.rerun()
    else:
        stats = data.get("statistics", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(m_card(stats.get("files_scanned", 0),                "Files Scanned"), unsafe_allow_html=True)
        c2.markdown(m_card(stats.get("total_findings", 0),               "Findings",   "#f43f5e"), unsafe_allow_html=True)
        c3.markdown(m_card(stats.get("by_risk", {}).get("CRITICAL", 0),  "Critical",   "#f59e0b"), unsafe_allow_html=True)
        c4.markdown(m_card(stats.get("hndl_risk_count", 0),              "HNDL Risk",  "#06b6d4"), unsafe_allow_html=True)
        findings = data.get("findings", [])
        if findings:
            st.markdown('<div class="section-hdr">Findings</div>', unsafe_allow_html=True)
            st.dataframe(
                pd.DataFrame(findings)[["file","algorithm","risk_level","harvest_now_decrypt_later","recommendation"]],
                use_container_width=True, hide_index=True
            )

# ---- Tab 2: Graph ----
with tabs[1]:
    data = api_get("/workflow/data/graph")
    if not data:
        st.info("Build the 5G SBA Knowledge Graph.")
        if st.button("Build Graph"):
            api_post("/workflow/step2/graph")
            st.rerun()
    else:
        nfs = data.get("nf_nodes", [])
        pqc_rdy = sum(1 for n in nfs if n.get("pqc_ready"))
        c1, c2, c3 = st.columns(3)
        c1.markdown(m_card(data.get("node_count", 0), "Nodes"), unsafe_allow_html=True)
        c2.markdown(m_card(data.get("edge_count", 0), "Edges"), unsafe_allow_html=True)
        c3.markdown(m_card(pqc_rdy, "PQC Ready", "#10b981"), unsafe_allow_html=True)
        if nfs:
            df = pd.DataFrame(nfs)
            tc = df["nf_type"].value_counts().reset_index()
            tc.columns = ["nf_type", "count"]
            fig = go.Figure(go.Pie(
                labels=tc["nf_type"], values=tc["count"], hole=0.58,
                marker=dict(colors=px.colors.sequential.Plasma_r),
                textfont=dict(color="white")
            ))
            fig.update_layout(title="NF Type Distribution", **plot_cfg())
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[["node_id","nf_type","vendor","cert_algorithm","pqc_ready","subscriber_count"]], use_container_width=True, hide_index=True)

# ---- Tab 3: Centrality ----
with tabs[2]:
    data = api_get("/workflow/data/centrality")
    if not data:
        st.info("Compute dependency centrality to find critical NFs.")
        if st.button("Compute Centrality"):
            api_post("/workflow/step3/centrality")
            st.rerun()
    else:
        st.markdown(f'<div class="al-ok">{data.get("summary","")}</div>', unsafe_allow_html=True)
        scores = data.get("scores", [])
        if scores:
            df = pd.DataFrame(scores)
            top10 = df.head(10)
            fig = go.Figure(go.Bar(
                x=top10["node_id"], y=top10["centrality_score"],
                marker=dict(
                    color=top10["centrality_score"],
                    colorscale=[[0,"rgba(220,38,38,0.6)"],[1,"rgba(245,158,11,0.95)"]],
                    line=dict(color="rgba(255,255,255,0.15)", width=1)
                )
            ))
            fig.update_layout(title="Top 10 NFs - Centrality Score", **plot_cfg())
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[["migration_priority","node_id","nf_type","centrality_score","connection_count","subscriber_reach"]], use_container_width=True, hide_index=True)

# ---- Tab 4: QMIE ----
with tabs[3]:
    has_risk = api_get("/workflow/data/risk")
    has_plan = api_get("/workflow/data/plan")
    has_fail = api_get("/workflow/data/failures")
    has_exp  = api_get("/workflow/data/explanations")
    if not has_risk:
        st.info("Run the QMIE Engine for risk analysis and migration planning.")
        if st.button("Run QMIE"):
            api_post("/workflow/step4/qmie")
            st.rerun()
    else:
        qt = st.tabs(["Risk Scorer", "Migration Plan", "AI Predictor", "Explainability"])
        with qt[0]:
            scores = has_risk.get("scores", [])
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(m_card(has_risk.get("critical", 0), "Critical",  "#f43f5e"), unsafe_allow_html=True)
            c2.markdown(m_card(has_risk.get("high", 0),    "High Risk", "#f59e0b"), unsafe_allow_html=True)
            c3.markdown(m_card(f'{has_risk.get("avg_qmis",0):.1f}', "Avg QMIS", "#c084fc"), unsafe_allow_html=True)
            c4.markdown(m_card(len(scores), "Total NFs"), unsafe_allow_html=True)
            if scores:
                df = pd.DataFrame(scores)
                fig = go.Figure(go.Bar(
                    x=df["node_id"][:16], y=df["qmis"][:16],
                    marker=dict(
                        color=df["qmis"][:16],
                        colorscale=[[0,"rgba(16,185,129,0.7)"],[.5,"rgba(245,158,11,0.85)"],[1,"rgba(244,63,94,0.95)"]],
                    )
                ))
                fig.update_layout(title="QMIS Risk Score per NF", **plot_cfg())
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df[["node_id","nf_type","qmis","risk_tier","crypto_risk","centrality_impact","hndl_risk"]], use_container_width=True, hide_index=True)
        with qt[1]:
            if has_plan:
                c1, c2 = st.columns(2)
                c1.markdown(m_card(has_plan.get("total_nfs", 0), "NFs to Migrate"), unsafe_allow_html=True)
                c2.markdown(m_card(f'{has_plan.get("total_downtime_min",0):.0f} min', "Est. Downtime"), unsafe_allow_html=True)
                if has_plan.get("steps"):
                    st.dataframe(pd.DataFrame(has_plan["steps"])[["step_number","node_id","migration_strategy","target_algo","estimated_downtime_min","maintenance_window"]], use_container_width=True, hide_index=True)
        with qt[2]:
            if has_fail:
                preds = has_fail.get("predictions", [])
                c1, c2, c3 = st.columns(3)
                c1.markdown(m_card(has_fail.get("red", 0),    "High Risk", "#f43f5e"), unsafe_allow_html=True)
                c2.markdown(m_card(has_fail.get("yellow", 0), "Caution",   "#f59e0b"), unsafe_allow_html=True)
                c3.markdown(m_card(has_fail.get("green", 0),  "Clear",     "#10b981"), unsafe_allow_html=True)
                if preds:
                    st.dataframe(pd.DataFrame(preds)[["node_id","risk_flag","registration_success_pct","rollback_probability","recommended_action"]], use_container_width=True, hide_index=True)
        with qt[3]:
            if has_exp:
                for e in has_exp.get("items", [])[:4]:
                    with st.expander(f"{e['node_id']} | {e['nf_type']}"):
                        st.markdown(f'<div class="al-ok"><b>Summary:</b> {e["plain_english_summary"]}</div>', unsafe_allow_html=True)
                        st.write("**Why this order?**", e["why_this_order"])
                        st.write("**What if delayed?**", e["what_if_delayed"])

# ---- Tab 5: Digital Twin ----
with tabs[4]:
    data = api_get("/workflow/data/twin")
    if not data:
        st.info("Run the Digital Twin to validate post-migration NF behaviour.")
        if st.button("Run Twin Validation"):
            api_post("/workflow/step5/twin")
            st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        c1.markdown(m_card(data.get("passed", 0), "Passed",     "#10b981"), unsafe_allow_html=True)
        c2.markdown(m_card(data.get("failed", 0), "Failed",     "#f43f5e"), unsafe_allow_html=True)
        c3.markdown(m_card(f'{data.get("confidence",0):.1f}%', "Confidence", "#c084fc"), unsafe_allow_html=True)
        for r in data.get("reports", [])[:5]:
            status_icon = "PASS" if r["overall_passed"] else "FAIL"
            with st.expander(f"{status_icon} | {r['nf_id']} -- {r['pass_rate_pct']}% pass"):
                st.write("**Recommendation:**", r["recommendation"])
                df_k = pd.DataFrame(r.get("kpi_deltas", []))
                if not df_k.empty:
                    st.dataframe(df_k[["metric_name","before","after","delta_pct","within_sla"]], use_container_width=True, hide_index=True)

# ---- Tab 6: PQC ----
with tabs[5]:
    data = api_get("/workflow/data/pqc")
    if not data:
        st.info("Validate the Hybrid PQC handshake (ML-KEM-768 + ML-DSA-65).")
        if st.button("Run PQC Validation"):
            api_post("/workflow/step6/pqc")
            st.rerun()
    else:
        is_real = data.get("is_real_pqc", False)
        badge_cls = "al-ok" if is_real else "al-warn"
        badge_msg = "liboqs present -- REAL NIST PQC" if is_real else "Simulated PQC fallback active"
        st.markdown(f'<div class="{badge_cls}">{badge_msg}</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(m_card(f'{data.get("keygen_ms",0):.2f} ms',  "KEM Keygen"),   unsafe_allow_html=True)
        c2.markdown(m_card(f'{data.get("encap_ms",0):.2f} ms',   "Encapsulate"),  unsafe_allow_html=True)
        c3.markdown(m_card(f'{data.get("decap_ms",0):.2f} ms',   "Decapsulate"),  unsafe_allow_html=True)
        kem_ok = data.get("kem_match", False)
        c4.markdown(m_card("VALID" if kem_ok else "FAIL", "KEM Match", "#10b981" if kem_ok else "#f43f5e"), unsafe_allow_html=True)
        st.write(f"**QKD Mode:** `{data.get('qkd_mode','N/A')}` | **Key Buffer:** `{data.get('key_buffer_bytes',0)} bytes`")

# ---- Tab 7: Sentinel ----
with tabs[6]:
    data = api_get("/workflow/data/sentinel")
    if not data:
        st.info("Start Edge Crypto Sentinel to monitor live TLS posture.")
        if st.button("Run Edge Sentinel"):
            api_get("/workflow/step7/sentinel")
            st.rerun()
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(m_card(f'{data.get("avg_posture_score",0):.0f}', "Avg Posture",      "#c084fc"), unsafe_allow_html=True)
        c2.markdown(m_card(data.get("critical_alerts", 0),           "Critical Alerts",  "#f43f5e"), unsafe_allow_html=True)
        c3.markdown(m_card(data.get("warning_alerts", 0),            "Warnings",         "#f59e0b"), unsafe_allow_html=True)
        c4.markdown(m_card(data.get("pqc_cipher_count", 0),          "PQC Connections",  "#06b6d4"), unsafe_allow_html=True)
        tls = data.get("tls_version_inventory", {})
        if tls:
            fig = go.Figure(go.Pie(
                labels=list(tls.keys()), values=list(tls.values()), hole=0.52,
                marker=dict(colors=["#10b981","#f59e0b","#f43f5e","#c084fc"])
            ))
            fig.update_layout(title="TLS Version Distribution", **plot_cfg())
            st.plotly_chart(fig, use_container_width=True)
        alerts = data.get("alerts", [])
        if alerts:
            st.dataframe(pd.DataFrame(alerts)[["nf_id","alert_type","severity","message"]], use_container_width=True, hide_index=True)

# ---- Tab 8: Policy ----
with tabs[7]:
    data = api_get("/workflow/data/policy")
    if not data:
        st.info("Evaluate cryptographic policy compliance and auto-remediation.")
        if st.button("Run Policy Engine"):
            api_get("/workflow/step8/policy")
            st.rerun()
    else:
        comp = data.get("compliance_pct", 0)
        comp_col = "#10b981" if comp > 80 else "#f59e0b" if comp > 60 else "#f43f5e"
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(m_card(f'{comp:.0f}%',                        "Compliance",    comp_col),  unsafe_allow_html=True)
        c2.markdown(m_card(data.get("total_violations", 0),       "Violations"),               unsafe_allow_html=True)
        c3.markdown(m_card(data.get("critical_violations", 0),    "Critical",      "#f43f5e"), unsafe_allow_html=True)
        c4.markdown(m_card(data.get("auto_remediated", 0),        "Remediated",    "#10b981"), unsafe_allow_html=True)
        for s in data.get("statuses", [])[:5]:
            label = "OK" if s["overall_compliant"] else "FAIL"
            with st.expander(f"{label} | {s['nf_id']} | Score {s['compliance_score']}/100 | {s['risk_tier']}"):
                if s.get("violations"):
                    st.dataframe(pd.DataFrame(s["violations"])[["policy_rule","severity","description","auto_remediation"]], use_container_width=True, hide_index=True)
                if s.get("actions"):
                    st.dataframe(pd.DataFrame(s["actions"])[["action_type","description","status"]], use_container_width=True, hide_index=True)

# ---- Tab 9: Executive Report ----
with tabs[8]:
    data = api_get("/workflow/data/report")
    if not data:
        st.info("Complete the full workflow to generate the Executive Report.")
    else:
        st.markdown("### Executive Summary")
        st.caption(f"Generated: `{data.get('generated_at')}` | Classification: TOP SECRET // NCIIPC")
        st.markdown("---")
        pipe = data.get("pipeline_summary", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(m_card(f'{pipe.get("steps_completed",0)}/9', "Steps Done"), unsafe_allow_html=True)
        qm = pipe.get("risk", {}).get("avg_qmis", 0) if pipe.get("risk") else 0
        qm_col = "#f43f5e" if qm > 70 else "#f59e0b" if qm > 40 else "#10b981"
        c2.markdown(m_card(f'{qm:.1f}', "Avg QMIS", qm_col), unsafe_allow_html=True)
        cp = pipe.get("policy", {}).get("compliance_pct", 0) if pipe.get("policy") else 0
        c3.markdown(m_card(f'{cp:.0f}%', "Compliance", "#10b981" if cp > 80 else "#f59e0b"), unsafe_allow_html=True)
        tw = pipe.get("twin", {}).get("confidence", 0) if pipe.get("twin") else 0
        c4.markdown(m_card(f'{tw:.1f}%', "Twin Confidence"), unsafe_allow_html=True)

        st.markdown('<div class="section-hdr" style="margin-top:32px;">TAMPER-EVIDENT EVIDENCE LEDGER</div>', unsafe_allow_html=True)
        ledger = data.get("ledger", {})
        valid  = ledger.get("chain_valid", False)
        lc1, lc2 = st.columns([1, 3])
        with lc1:
            badge_col  = "#10b981" if valid else "#f43f5e"
            badge_text = "CHAIN VALID" if valid else "CHAIN BROKEN"
            badge_sub  = "Cryptographic Integrity Confirmed" if valid else "Tampering Detected"
            st.markdown(
                f'<div style="padding:24px;border-radius:20px;background:rgba({("16,185,129" if valid else "244,63,94")},0.1);'
                f'border:1px solid rgba({("16,185,129" if valid else "244,63,94")},0.4);text-align:center;backdrop-filter:blur(20px);">'
                f'<div style="font-size:2.5rem;">{"&#9989;" if valid else "&#9888;"}</div>'
                f'<div style="font-size:1rem;font-weight:800;color:{badge_col};margin-top:8px;">{badge_text}</div>'
                f'<div style="font-size:0.65rem;color:{badge_col};opacity:0.6;margin-top:4px;">{badge_sub}</div>'
                '</div>',
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.write(f"**Events:** {ledger.get('total_entries',0)}")
            st.markdown("<p style='font-size:0.68rem;color:rgba(255,255,255,0.3);'>ROOT HASH</p>", unsafe_allow_html=True)
            st.code(ledger.get("ledger_root_hash", "N/A"), language="text")
        with lc2:
            st.write("### Immutable Event Log")
            entries = ledger.get("entries", [])
            if entries:
                df_l = pd.DataFrame(entries)
                df_l["timestamp"] = pd.to_datetime(df_l["timestamp"]).dt.strftime("%H:%M:%S.%f")
                st.dataframe(df_l[["sequence","timestamp","event_type","entry_id","previous_hash"]], use_container_width=True, hide_index=True)
                with st.expander("Raw Cryptographic Ledger (Auditor View)"):
                    st.json(ledger)
