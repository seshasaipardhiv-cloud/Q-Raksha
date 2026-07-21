"""
Q-RAKSHA SENTINEL — Executive Dashboard (Professional Glass Edition)
Full sign-in flow + dual-theme gradient backgrounds + glassmorphism UI
"""
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

st.set_page_config(
    page_title="Q-RAKSHA SENTINEL",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Two themed CSS gradient backgrounds
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ─── Root Variables ──────────────────────────────────────── */
:root {
  --crimson:  #dc2626;
  --orange:   #ea580c;
  --amber:    #f59e0b;
  --gold:     #fbbf24;
  --rose:     #f43f5e;
  --cyan:     #06b6d4;
  --teal:     #0d9488;
  --green:    #10b981;
  --glass:    rgba(255,255,255,0.06);
  --glass-b:  rgba(255,255,255,0.14);
  --blur:     blur(22px) saturate(180%);
  --shadow:   0 8px 40px rgba(0,0,0,0.5);
  --text:     rgba(255,255,255,0.93);
  --text-dim: rgba(255,255,255,0.5);
  --text-muted: rgba(255,255,255,0.3);
}

/* ─── Base ────────────────────────────────────────────────── */
html, body, .stApp {
  font-family: 'Inter', sans-serif !important;
  color: var(--text) !important;
  overflow-x: hidden;
}

/* ─── Dashboard background: Dark Red/Crimson Quantum Mesh ─── */
.stApp {
  background:
    radial-gradient(ellipse 75% 55% at 50% 45%, rgba(180,30,15,0.28) 0%, transparent 65%),
    radial-gradient(ellipse 55% 40% at 80% 20%, rgba(120,10,40,0.20) 0%, transparent 55%),
    radial-gradient(ellipse 50% 50% at 15% 80%, rgba(80,0,20,0.18) 0%, transparent 50%),
    radial-gradient(ellipse 40% 40% at 50% 10%, rgba(200,50,10,0.10) 0%, transparent 55%),
    linear-gradient(155deg, #0c0008 0%, #150005 25%, #0f0010 50%, #080006 75%, #0a0000 100%) !important;
}

/* Geometric mesh overlay */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cdefs%3E%3Cpattern id='m' width='120' height='120' patternUnits='userSpaceOnUse'%3E%3Cpolygon points='0,60 60,0 120,60 60,120' fill='none' stroke='rgba(220,38,38,0.08)' stroke-width='0.8'/%3E%3Ccircle cx='0' cy='60' r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='60' cy='0' r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='120' cy='60' r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='60' cy='120' r='2' fill='rgba(220,38,38,0.14)'/%3E%3Ccircle cx='60' cy='60' r='1.5' fill='rgba(245,158,11,0.12)'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23m)'/%3E%3C/svg%3E");
  opacity: 0.9;
}

/* Dark veil */
.stApp::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.15) 50%, rgba(0,0,0,0.45) 100%);
  pointer-events: none;
}

/* ─── Streamlit layout cleanup ─────────────────────────────── */
[data-testid="stSidebar"] {{
  background: rgba(10,5,30,0.75) !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
  border-right: 1px solid rgba(255,255,255,0.1) !important;
  box-shadow: 4px 0 32px rgba(0,0,0,0.5) !important;
}}
[data-testid="stHeader"]   {{ background: transparent !important; }}
[data-testid="stToolbar"]  {{ background: transparent !important; }}
.main .block-container     {{ padding-top: 1.5rem !important; }}
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}

/* ─── Glass card ───────────────────────────────────────────── */
.g-card {{
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
}}
.g-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
}}
.g-card:hover {{
  transform: translateY(-3px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.18);
}}

/* ─── Metric cards ─────────────────────────────────────────── */
.m-card {{
  background: rgba(255,255,255,0.055);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border: 1px solid rgba(255,255,255,0.13);
  border-radius: 16px;
  padding: 20px 16px;
  text-align: center;
  transition: all .3s;
  box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
}}
.m-card:hover {{ transform: translateY(-4px) scale(1.02); border-color: rgba(255,255,255,0.25); }}
.m-val {{
  font-size: 2rem; font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 40%, #c084fc 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  line-height: 1.1;
}}
.m-lbl {{ font-size: 0.68rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: .12em; font-weight: 600; margin-top: 6px; }}

/* ─── Sign-in page ─────────────────────────────────────────── */
.signin-wrap {{
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
}}
.signin-box {{
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(32px) saturate(200%);
  -webkit-backdrop-filter: blur(32px) saturate(200%);
  border: 1px solid rgba(255,255,255,0.16);
  border-radius: 28px;
  padding: 48px 40px;
  max-width: 440px;
  width: 100%;
  box-shadow: 0 24px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.15);
  position: relative;
  overflow: hidden;
}}
.signin-box::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(147,51,234,0.8) 40%, rgba(245,158,11,0.8) 60%, transparent 100%);
}}
.signin-logo {{
  text-align: center;
  margin-bottom: 32px;
}}
.signin-logo .brand {{
  font-size: 1.8rem; font-weight: 900;
  background: linear-gradient(135deg, #fbbf24, #f59e0b, #c084fc, #9333ea);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  letter-spacing: -0.03em;
}}
.signin-logo .sub {{
  font-size: 0.65rem; color: var(--text-muted);
  letter-spacing: .2em; text-transform: uppercase; margin-top: 4px;
}}
.divider {{
  display: flex; align-items: center; gap: 12px;
  margin: 20px 0; color: var(--text-muted); font-size: 0.75rem;
}}
.divider::before, .divider::after {{
  content: ''; flex: 1; height: 1px;
  background: rgba(255,255,255,0.1);
}}
.oauth-btn {{
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 12px 20px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 12px; cursor: pointer;
  color: var(--text); font-size: 0.88rem; font-weight: 600;
  transition: all .2s; margin-bottom: 10px;
  backdrop-filter: blur(12px);
  font-family: 'Inter', sans-serif;
}}
.oauth-btn:hover {{
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.28);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}}
.oauth-btn.google {{ border-color: rgba(234,67,53,0.4); }}
.oauth-btn.github {{ border-color: rgba(255,255,255,0.2); }}
.oauth-btn.msft   {{ border-color: rgba(0,120,212,0.4); }}

/* ─── Logo, headers ────────────────────────────────────────── */
.logo-text {{
  font-size: 1.45rem; font-weight: 900;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 35%, #c084fc 70%, #9333ea 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  letter-spacing: -0.03em;
}}
.logo-sub {{ font-size: 0.58rem; color: var(--text-muted); letter-spacing: .2em; text-transform: uppercase; }}

.section-hdr {{
  font-size: 0.68rem; font-weight: 700; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .18em;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  padding-bottom: 8px; margin: 22px 0 14px;
}}

/* ─── Pipeline steps ───────────────────────────────────────── */
.pipeline-strip {{
  display: flex; flex-wrap: wrap; gap: 7px;
  padding: 14px 16px; margin-bottom: 20px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px); border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.09);
}}
.p-step {{
  padding: 5px 14px; border-radius: 30px;
  font-size: 0.7rem; font-weight: 600; letter-spacing: .03em;
  background: rgba(255,255,255,0.05);
  color: var(--text-muted); border: 1px solid rgba(255,255,255,0.08);
  transition: all .2s;
}}
.p-step.done   {{ background: rgba(16,185,129,0.15); color: #34d399; border-color: rgba(16,185,129,0.35); box-shadow: 0 0 10px rgba(16,185,129,0.12); }}
.p-step.active {{ background: rgba(147,51,234,0.2); color: #c084fc; border-color: rgba(147,51,234,0.5); animation: pulse-p 2s infinite; }}
@keyframes pulse-p {{
  0%,100% {{ box-shadow: 0 0 10px rgba(147,51,234,0.2); }}
  50%     {{ box-shadow: 0 0 22px rgba(147,51,234,0.5); }}
}}

/* ─── Alert variants ───────────────────────────────────────── */
.al-ok   {{ background:rgba(16,185,129,.1); border-left:3px solid #10b981; border-radius:0 12px 12px 0; padding:11px 15px; margin:5px 0; font-size:.82rem; backdrop-filter:blur(8px); }}
.al-warn {{ background:rgba(245,158,11,.1); border-left:3px solid #f59e0b; border-radius:0 12px 12px 0; padding:11px 15px; margin:5px 0; font-size:.82rem; backdrop-filter:blur(8px); }}
.al-crit {{ background:rgba(244,63,94,.1);  border-left:3px solid #f43f5e; border-radius:0 12px 12px 0; padding:11px 15px; margin:5px 0; font-size:.82rem; backdrop-filter:blur(8px); }}

/* ─── Buttons ──────────────────────────────────────────────── */
.stButton > button {{
  background: rgba(255,255,255,0.07) !important;
  color: rgba(255,255,255,0.9) !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: 12px !important;
  font-weight: 600 !important; font-size: 0.83rem !important;
  backdrop-filter: blur(12px) !important;
  transition: all .2s !important;
}}
.stButton > button:hover {{
  background: rgba(147,51,234,0.25) !important;
  border-color: rgba(147,51,234,0.6) !important;
  box-shadow: 0 0 18px rgba(147,51,234,0.3) !important;
  transform: translateY(-1px) !important;
}}
.primary-btn > button {{
  background: linear-gradient(135deg, rgba(147,51,234,0.45), rgba(245,158,11,0.3)) !important;
  border-color: rgba(147,51,234,0.55) !important;
  box-shadow: 0 4px 20px rgba(147,51,234,0.25) !important;
}}

/* ─── Tabs ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(12px) !important;
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  padding: 4px !important; gap: 2px !important;
}}
.stTabs [data-baseweb="tab"] {{
  color: var(--text-dim) !important;
  font-weight: 600 !important; font-size: 0.77rem !important;
  border-radius: 8px !important; padding: 6px 13px !important;
  transition: all .2s !important;
}}
.stTabs [aria-selected="true"] {{
  background: rgba(147,51,234,0.22) !important; color: #c084fc !important;
}}

/* ─── Inputs ───────────────────────────────────────────────── */
.stTextInput input, .stSelectbox, .stPasswordInput input {{
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: 10px !important; color: white !important;
  backdrop-filter: blur(10px) !important;
}}
.stTextInput input:focus, .stPasswordInput input:focus {{
  border-color: rgba(147,51,234,0.6) !important;
  box-shadow: 0 0 0 2px rgba(147,51,234,0.2) !important;
}}

/* ─── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.02); }}
::-webkit-scrollbar-thumb {{ background: rgba(147,51,234,0.45); border-radius:3px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(147,51,234,0.7); }}

/* ─── Plotly ───────────────────────────────────────────────── */
.js-plotly-plot .plotly {{ background: transparent !important; }}
h1,h2,h3 {{ color: rgba(255,255,255,0.95) !important; font-family:'Inter',sans-serif !important; }}
</style>

<!-- Floating background orbs -->
<div class="particle-orb orb1"></div>
<div class="particle-orb orb2"></div>
<div class="particle-orb orb3"></div>
""", unsafe_allow_html=True)


# ─── Config ──────────────────────────────────────────────────────────────────

API_URL = os.environ.get("API_URL", "http://localhost:8765")

def api_get(ep):
    try:
        r = requests.get(f"{API_URL}{ep}", timeout=4.0)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def api_post(ep, data=None):
    try:
        r = requests.post(f"{API_URL}{ep}", json=data, timeout=8.0)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def _plot_cfg():
    return dict(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.7)", family="Inter"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
        margin=dict(l=16, r=16, t=40, b=16),
        legend=dict(font=dict(color="rgba(255,255,255,0.65)")),
    )


# ─── Session State ────────────────────────────────────────────────────────────

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name"     not in st.session_state:
    st.session_state.user_name = ""
if "user_role"     not in st.session_state:
    st.session_state.user_role = ""
if "workflow_step" not in st.session_state:
    st.session_state.workflow_step = 0
if "workflow_running" not in st.session_state:
    st.session_state.workflow_running = False
if "signin_tab"    not in st.session_state:
    st.session_state.signin_tab = "signin"


# ─────────────────────────────────────────────────────────────────────────────
# SIGN-IN PAGE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:

    # Override the app background specifically for the login page
    st.markdown("""
    <style>
    /* Login page — deep navy/teal quantum background */
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
      background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cdefs%3E%3Cpattern id='t' width='100' height='100' patternUnits='userSpaceOnUse'%3E%3Cpolygon points='0,50 50,0 100,50 50,100' fill='none' stroke='rgba(13,148,136,0.09)' stroke-width='0.7'/%3E%3Cline x1='0' y1='0' x2='100' y2='100' stroke='rgba(13,148,136,0.05)' stroke-width='0.5'/%3E%3Cline x1='100' y1='0' x2='0' y2='100' stroke='rgba(13,148,136,0.05)' stroke-width='0.5'/%3E%3Ccircle cx='50' cy='0' r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='0' cy='50' r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='100' cy='50' r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='50' cy='100' r='1.8' fill='rgba(13,148,136,0.18)'/%3E%3Ccircle cx='50' cy='50' r='1.4' fill='rgba(251,191,36,0.1)'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23t)'/%3E%3C/svg%3E") !important;
    }
    /* Login layout */
    .login-wrap { min-height: 100vh; display: flex; }
    .login-left {
      flex: 1.1;
      background:
        radial-gradient(ellipse 90% 70% at 40% 50%, rgba(13,148,136,0.18) 0%, transparent 70%),
        rgba(2,12,18,0.0);
      display: flex; flex-direction: column;
      justify-content: center; padding: 60px 56px;
      border-right: 1px solid rgba(13,148,136,0.15);
      backdrop-filter: blur(4px);
    }
    .login-right {
      flex: 0.9;
      display: flex; align-items: center; justify-content: center;
      padding: 40px 48px;
      background: rgba(0,0,0,0.15);
      backdrop-filter: blur(8px);
    }
    .login-card {
      width: 100%; max-width: 400px;
      background: rgba(255,255,255,0.055);
      backdrop-filter: blur(32px) saturate(200%);
      -webkit-backdrop-filter: blur(32px) saturate(200%);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 24px;
      padding: 40px 36px;
      box-shadow: 0 32px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1);
      position: relative; overflow: hidden;
    }
    .login-card::before {
      content: '';
      position: absolute; top: 0; left: 0; right: 0; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(13,148,136,0.9), rgba(251,191,36,0.7), transparent);
    }
    .stat-box {
      display: flex; align-items: center; gap: 14px;
      padding: 14px 18px; margin-bottom: 12px;
      background: rgba(13,148,136,0.08);
      border: 1px solid rgba(13,148,136,0.18);
      border-radius: 14px;
      backdrop-filter: blur(8px);
    }
    .stat-icon { font-size: 1.5rem; }
    .stat-val { font-size: 1.3rem; font-weight: 800; color: #5eead4; font-family: 'JetBrains Mono', monospace; }
    .stat-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: .1em; }
    .badge-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 28px; }
    .badge {
      font-size: 0.65rem; font-weight: 600; padding: 4px 12px;
      border-radius: 20px; border: 1px solid rgba(13,148,136,0.3);
      color: rgba(94,234,212,0.75); letter-spacing: .08em; text-transform: uppercase;
    }
    .oauth-row { display: flex; flex-direction: column; gap: 8px; margin: 16px 0; }
    .o-btn {
      display: flex; align-items: center; justify-content: center; gap: 10px;
      padding: 11px 18px; border-radius: 12px; width: 100%;
      font-size: 0.84rem; font-weight: 600; cursor: pointer; border: 1px solid;
      color: rgba(255,255,255,0.88); font-family: 'Inter', sans-serif;
      transition: all .2s; backdrop-filter: blur(10px);
    }
    .o-btn-g { background: rgba(234,67,53,0.1);  border-color: rgba(234,67,53,0.35); }
    .o-btn-h { background: rgba(36,41,46,0.5);   border-color: rgba(255,255,255,0.18); }
    .o-btn-m { background: rgba(0,120,212,0.12); border-color: rgba(0,120,212,0.38); }
    .o-btn:hover { filter: brightness(1.2); transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }
    .sep { display: flex; align-items: center; gap: 10px; margin: 14px 0; color: rgba(255,255,255,0.25); font-size: 0.72rem; }
    .sep::before,.sep::after { content:''; flex:1; height:1px; background: rgba(255,255,255,0.08); }
    </style>
    """, unsafe_allow_html=True)

    # Two-column login layout using HTML
    st.markdown("""
    <div style="display:grid;grid-template-columns:1.1fr 0.9fr;min-height:100vh;">

      <!-- LEFT: Brand panel -->
      <div style="display:flex;flex-direction:column;justify-content:center;padding:60px 56px;
           border-right:1px solid rgba(13,148,136,0.15);background:rgba(13,148,136,0.02);">

        <div style="margin-bottom:40px;">
          <div style="font-size:0.65rem;color:rgba(13,148,136,0.7);letter-spacing:.25em;text-transform:uppercase;margin-bottom:10px;">
            NCIIPC · NIST PQC FIPS 203/204
          </div>
          <div style="font-size:2.6rem;font-weight:900;line-height:1;
               background:linear-gradient(135deg,#fbbf24 0%,#f59e0b 35%,#5eead4 70%,#0d9488 100%);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
               letter-spacing:-0.04em;margin-bottom:12px;">
            Q-RAKSHA<br>SENTINEL
          </div>
          <div style="font-size:0.8rem;color:rgba(255,255,255,0.4);letter-spacing:.08em;max-width:320px;line-height:1.7;">
            Autonomous 5G Telecom Quantum Migration Intelligence Platform. Protect against Harvest-Now-Decrypt-Later threats with AI-driven PQC orchestration.
          </div>
        </div>

        <!-- Stats -->
        <div style="display:flex;flex-direction:column;gap:10px;max-width:340px;">
          <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;
               background:rgba(13,148,136,0.08);border:1px solid rgba(13,148,136,0.18);
               border-radius:14px;backdrop-filter:blur(8px);">
            <div style="font-size:1.4rem;">🔍</div>
            <div>
              <div style="font-size:1.2rem;font-weight:800;color:#5eead4;font-family:'JetBrains Mono',monospace;">10-Step</div>
              <div style="font-size:0.66rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:.1em;">AI Migration Pipeline</div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;
               background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.18);
               border-radius:14px;backdrop-filter:blur(8px);">
            <div style="font-size:1.4rem;">🛡️</div>
            <div>
              <div style="font-size:1.2rem;font-weight:800;color:#fbbf24;font-family:'JetBrains Mono',monospace;">ML-KEM-768</div>
              <div style="font-size:0.66rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:.1em;">NIST PQC Algorithm</div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;
               background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.18);
               border-radius:14px;backdrop-filter:blur(8px);">
            <div style="font-size:1.4rem;">📡</div>
            <div>
              <div style="font-size:1.2rem;font-weight:800;color:#34d399;font-family:'JetBrains Mono',monospace;">5G SBA</div>
              <div style="font-size:0.66rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:.1em;">Telecom-Aware Topology</div>
            </div>
          </div>
        </div>

        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:28px;">
          <span style="font-size:0.63rem;font-weight:600;padding:4px 11px;border-radius:20px;border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">Zero Trust</span>
          <span style="font-size:0.63rem;font-weight:600;padding:4px 11px;border-radius:20px;border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">Tamper-Evident</span>
          <span style="font-size:0.63rem;font-weight:600;padding:4px 11px;border-radius:20px;border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">Digital Twin</span>
          <span style="font-size:0.63rem;font-weight:600;padding:4px 11px;border-radius:20px;border:1px solid rgba(13,148,136,0.3);color:rgba(94,234,212,0.7);letter-spacing:.08em;text-transform:uppercase;">AI Predictor</span>
        </div>
      </div>

      <!-- RIGHT: spacer (actual form rendered via Streamlit below) -->
      <div></div>
    </div>
    """, unsafe_allow_html=True)

    # Use Streamlit columns to overlay the login card on the right
    _, right_col = st.columns([1.1, 0.9])
    with right_col:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.055);backdrop-filter:blur(32px) saturate(200%);
             -webkit-backdrop-filter:blur(32px) saturate(200%);
             border:1px solid rgba(255,255,255,0.12);border-radius:24px;
             padding:36px 32px;
             box-shadow:0 32px 80px rgba(0,0,0,0.6),inset 0 1px 0 rgba(255,255,255,0.1);
             position:relative;overflow:hidden;margin-top:-85vh;">
          <div style="position:absolute;top:0;left:0;right:0;height:1px;
               background:linear-gradient(90deg,transparent,rgba(13,148,136,0.9),rgba(251,191,36,0.7),transparent);">
          </div>
          <div style="text-align:center;margin-bottom:26px;">
            <div style="font-size:1.8rem;margin-bottom:4px;">🔐</div>
            <div style="font-size:1.3rem;font-weight:800;color:rgba(255,255,255,0.95);">Secure Access Portal</div>
            <div style="font-size:0.76rem;color:rgba(255,255,255,0.38);margin-top:4px;">Authenticated access to Q-RAKSHA SENTINEL</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # OAuth Buttons
        st.markdown("""
        <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:4px;">
          <button style="display:flex;align-items:center;justify-content:center;gap:10px;padding:12px;border-radius:12px;width:100%;font-size:0.84rem;font-weight:600;cursor:pointer;border:1px solid rgba(234,67,53,0.38);color:rgba(255,255,255,0.88);font-family:Inter,sans-serif;background:rgba(234,67,53,0.1);backdrop-filter:blur(10px);">
            <svg width="17" height="17" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 7.9 2.9l5.7-5.7C34.5 6.5 29.6 4 24 4 12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20c0-1.3-.1-2.7-.4-3.9z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.1 7.9 2.9l5.7-5.7C34.5 6.5 29.6 4 24 4 16.3 4 9.7 8.4 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.1l-6.2-5.2C29.3 35.3 26.8 36 24 36c-5.3 0-9.7-3.3-11.3-8H6.2C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.3 5.7l6.2 5.2C36.9 39.8 44 34.1 44 24c0-1.3-.1-2.7-.4-3.9z"/></svg>
            Continue with Google
          </button>
          <button style="display:flex;align-items:center;justify-content:center;gap:10px;padding:12px;border-radius:12px;width:100%;font-size:0.84rem;font-weight:600;cursor:pointer;border:1px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.88);font-family:Inter,sans-serif;background:rgba(36,41,46,0.5);backdrop-filter:blur(10px);">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="white"><path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/></svg>
            Continue with GitHub
          </button>
          <button style="display:flex;align-items:center;justify-content:center;gap:10px;padding:12px;border-radius:12px;width:100%;font-size:0.84rem;font-weight:600;cursor:pointer;border:1px solid rgba(0,120,212,0.38);color:rgba(255,255,255,0.88);font-family:Inter,sans-serif;background:rgba(0,120,212,0.12);backdrop-filter:blur(10px);">
            <svg width="17" height="17" viewBox="0 0 21 21"><rect x="1" y="1" width="9" height="9" fill="#f25022"/><rect x="11" y="1" width="9" height="9" fill="#7fba00"/><rect x="1" y="11" width="9" height="9" fill="#00a4ef"/><rect x="11" y="11" width="9" height="9" fill="#ffb900"/></svg>
            Continue with Microsoft
          </button>

        st.markdown('<div class="divider">or sign in with credentials</div>', unsafe_allow_html=True)

        # ── Credential form ──
        with st.form("signin_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="sentinel@nciipc.gov.in")
            password = st.text_input("Password", type="password", placeholder="••••••••••")
            role = st.selectbox("Access Role", ["Network Security Analyst", "Telecom Engineer", "CISO / Executive", "NCIIPC Auditor"])

            c1, c2 = st.columns(2)
            remember = c1.checkbox("Remember me", value=True)
            
            submitted = st.form_submit_button("🔐 Sign In", use_container_width=True)
            if submitted:
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.user_name = email.split("@")[0].replace(".", " ").title()
                    st.session_state.user_role = role
                    st.rerun()
                else:
                    st.error("Please enter your email and password.")

        # OAuth quick demo sign in
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Quick Demo Access (No Auth)", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Demo Analyst"
            st.session_state.user_role = "Network Security Analyst"
            st.rerun()

        st.markdown("""
        <p style='text-align:center;font-size:0.7rem;color:rgba(255,255,255,0.2);margin-top:20px;'>
          Protected by Q-RAKSHA SENTINEL Zero-Trust Architecture<br>
          All access is logged and cryptographically audited.
        </p>
        """, unsafe_allow_html=True)

    # Footer on sign-in page
    st.markdown("""
    <div style='text-align:center; margin-top:40px; padding: 20px;'>
      <div style='font-size:0.7rem; color:rgba(255,255,255,0.2);'>
        © 2025 Q-RAKSHA SENTINEL · NCIIPC Classified · NIST PQC FIPS 203/204 Compliant
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD (after auth)
# ─────────────────────────────────────────────────────────────────────────────

# Sync pipeline status
status = api_get("/workflow/status")
if status:
    st.session_state.workflow_step = status.get("step", 0)
    st.session_state.workflow_running = status.get("running", False)
api_ok = status is not None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="logo-text">🛡️ Q-RAKSHA</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Sentinel · Quantum Migration</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # User badge
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);
         border-radius:14px;padding:14px 16px;margin-bottom:16px;">
      <div style="font-size:0.72rem;color:rgba(255,255,255,0.45);">Signed in as</div>
      <div style="font-weight:700;font-size:0.9rem;margin:2px 0;">👤 {st.session_state.user_name}</div>
      <div style="font-size:0.7rem;color:rgba(147,51,234,0.85);">{st.session_state.user_role}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div class="{"al-ok" if api_ok else "al-crit"}">{"⚡ API Online" if api_ok else "🔴 API Offline"}</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-hdr">Mission Control</div>', unsafe_allow_html=True)

    st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
    if st.button("▶️ Run Full Workflow", disabled=st.session_state.workflow_running or not api_ok):
        res = api_post("/workflow/run", {"target_path": ".", "num_nfs": 24})
        if res:
            st.session_state.workflow_running = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.workflow_running:
        st.info(f"⏳ Step {st.session_state.workflow_step}/9 in progress...")
        time.sleep(1.5); st.rerun()

    st.markdown('<div class="section-hdr">Quick Actions</div>', unsafe_allow_html=True)
    if st.button("🔍 Step 2: Build Graph"):      api_post("/workflow/step2/graph"); st.rerun()
    if st.button("⚡ Step 4: Run QMIE"):         api_post("/workflow/step4/qmie"); st.rerun()
    if st.button("👁 Step 7: Edge Sentinel"):    api_get("/workflow/step7/sentinel"); st.rerun()
    if st.button("📋 Step 8: Policy Engine"):    api_get("/workflow/step8/policy"); st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out"):
        st.session_state.authenticated = False
        st.session_state.user_name = ""
        st.rerun()
    st.caption("Q-RAKSHA SENTINEL v2.0 · NCIIPC")

# ── Top Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
  <div>
    <span style="font-size:1.9rem;font-weight:900;
      background:linear-gradient(135deg,#fbbf24,#f59e0b,#c084fc,#9333ea);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
      letter-spacing:-0.04em;">Q-RAKSHA SENTINEL</span>
  </div>
  <div style="text-align:right;">
    <div style="font-size:0.68rem;color:rgba(255,255,255,0.3);text-transform:uppercase;letter-spacing:.1em;">
      {time.strftime("%d %b %Y · %H:%M UTC")}
    </div>
    <div style="font-size:0.72rem;color:rgba(147,51,234,0.7);font-weight:600;">
      {st.session_state.user_role}
    </div>
  </div>
</div>
<div style="font-size:0.72rem;color:rgba(255,255,255,0.3);letter-spacing:.18em;text-transform:uppercase;margin-bottom:16px;">
  Autonomous Telecom Quantum Migration Platform
</div>
""", unsafe_allow_html=True)

# ── Pipeline Step Tracker ─────────────────────────────────────────────────────
curr_step = st.session_state.workflow_step
steps_def = [(1,"CBOM"),(2,"Graph"),(3,"Centrality"),(4,"QMIE"),(5,"Twin"),(6,"PQC"),(7,"Sentinel"),(8,"Policy"),(9,"Report")]
html = '<div class="pipeline-strip">'
for s, n in steps_def:
    cls = "p-step"
    if s < curr_step: cls += " done"
    elif s == curr_step and st.session_state.workflow_running: cls += " active"
    icon = "✓ " if s < curr_step else ""
    html += f'<div class="{cls}">{icon}S{s}·{n}</div>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tabs = st.tabs(["1️⃣ CBOM","2️⃣ Graph","3️⃣ Centrality","4️⃣ QMIE","5️⃣ Twin","6️⃣ PQC","7️⃣ Sentinel","8️⃣ Policy","9️⃣ Report"])

def m_card(val, lbl, color=None):
    sty = f'style="-webkit-text-fill-color:{color};"' if color else ""
    return f'<div class="m-card"><div class="m-val" {sty}>{val}</div><div class="m-lbl">{lbl}</div></div>'

# ── Tab 1: CBOM ───────────────────────────────────────────────────────────────
with tabs[0]:
    data = api_get("/workflow/data/cbom")
    if not data:
        st.info("💡 Run the workflow or click **Step 1** to begin crypto discovery.")
        if st.button("▶ Run CBOM Discovery"): api_post("/workflow/step1/cbom",{"target_path":".","years_secret":10}); st.rerun()
    else:
        stats = data.get("statistics", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(m_card(stats.get("files_scanned",0),      "Files Scanned"), unsafe_allow_html=True)
        c2.markdown(m_card(stats.get("total_findings",0),     "Findings",   "#f43f5e"), unsafe_allow_html=True)
        c3.markdown(m_card(stats.get("by_risk",{}).get("CRITICAL",0),"Critical","#f59e0b"), unsafe_allow_html=True)
        c4.markdown(m_card(stats.get("hndl_risk_count",0),    "HNDL Exposed","#06b6d4"), unsafe_allow_html=True)
        st.markdown('<div class="section-hdr">Telecom CBOM Findings</div>', unsafe_allow_html=True)
        findings = data.get("findings", [])
        if findings:
            st.dataframe(pd.DataFrame(findings)[["file","algorithm","risk_level","harvest_now_decrypt_later","recommendation"]], use_container_width=True, hide_index=True)

# ── Tab 2: Graph ──────────────────────────────────────────────────────────────
with tabs[1]:
    data = api_get("/workflow/data/graph")
    if not data:
        st.info("💡 Build the 5G SBA Knowledge Graph.")
        if st.button("▶ Build Graph"): api_post("/workflow/step2/graph"); st.rerun()
    else:
        nfs = data.get("nf_nodes", [])
        pqc_rdy = sum(1 for n in nfs if n.get("pqc_ready"))
        c1,c2,c3 = st.columns(3)
        c1.markdown(m_card(data.get("node_count",0), "Total Nodes"), unsafe_allow_html=True)
        c2.markdown(m_card(data.get("edge_count",0), "SBA Edges"), unsafe_allow_html=True)
        c3.markdown(m_card(pqc_rdy, "PQC Ready", "#10b981"), unsafe_allow_html=True)
        if nfs:
            df = pd.DataFrame(nfs)
            tc = df["nf_type"].value_counts().reset_index(); tc.columns=["nf_type","count"]
            fig = go.Figure(go.Pie(labels=tc["nf_type"],values=tc["count"],hole=0.58,
                marker=dict(colors=px.colors.sequential.Plasma_r), textfont=dict(color="white")))
            fig.update_layout(title="NF Type Distribution", **_plot_cfg())
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[["node_id","nf_type","vendor","cert_algorithm","pqc_ready","subscriber_count"]], use_container_width=True, hide_index=True)

# ── Tab 3: Centrality ─────────────────────────────────────────────────────────
with tabs[2]:
    data = api_get("/workflow/data/centrality")
    if not data:
        st.info("💡 Compute dependency centrality to find critical NFs.")
        if st.button("▶ Compute Centrality"): api_post("/workflow/step3/centrality"); st.rerun()
    else:
        st.markdown(f'<div class="al-ok">{data.get("summary","")}</div>', unsafe_allow_html=True)
        scores = data.get("scores", [])
        if scores:
            df = pd.DataFrame(scores); top10 = df.head(10)
            fig = go.Figure(go.Bar(x=top10["node_id"],y=top10["centrality_score"],
                marker=dict(color=top10["centrality_score"],colorscale=[[0,"rgba(124,58,237,0.7)"],[1,"rgba(245,158,11,0.95)"]],
                line=dict(color="rgba(255,255,255,0.15)",width=1))))
            fig.update_layout(title="Top 10 NFs — Centrality Score", **_plot_cfg())
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[["migration_priority","node_id","nf_type","centrality_score","connection_count","subscriber_reach"]], use_container_width=True, hide_index=True)

# ── Tab 4: QMIE ──────────────────────────────────────────────────────────────
with tabs[3]:
    has_risk = api_get("/workflow/data/risk")
    has_plan = api_get("/workflow/data/plan")
    has_fail = api_get("/workflow/data/failures")
    has_exp  = api_get("/workflow/data/explanations")
    if not has_risk:
        st.info("💡 Run the QMIE Engine for full risk analysis and migration planning.")
        if st.button("▶ Run QMIE"): api_post("/workflow/step4/qmie"); st.rerun()
    else:
        qt = st.tabs(["🔴 Risk Scorer","📋 Migration Plan","🤖 AI Predictor","💡 Explainability"])
        with qt[0]:
            scores = has_risk.get("scores",[])
            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(m_card(has_risk.get("critical",0), "Critical", "#f43f5e"), unsafe_allow_html=True)
            c2.markdown(m_card(has_risk.get("high",0),    "High Risk", "#f59e0b"), unsafe_allow_html=True)
            c3.markdown(m_card(f'{has_risk.get("avg_qmis",0):.1f}', "Avg QMIS", "#c084fc"), unsafe_allow_html=True)
            c4.markdown(m_card(len(scores), "Total NFs"), unsafe_allow_html=True)
            if scores:
                df = pd.DataFrame(scores)
                fig = go.Figure(go.Bar(x=df["node_id"][:16],y=df["qmis"][:16],
                    marker=dict(color=df["qmis"][:16],colorscale=[[0,"rgba(16,185,129,0.7)"],[.5,"rgba(245,158,11,0.85)"],[1,"rgba(244,63,94,0.95)"]]),))
                fig.update_layout(title="QMIS Risk Score per NF", **_plot_cfg())
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df[["node_id","nf_type","qmis","risk_tier","crypto_risk","centrality_impact","hndl_risk"]], use_container_width=True, hide_index=True)
        with qt[1]:
            if has_plan:
                c1,c2 = st.columns(2)
                c1.markdown(m_card(has_plan.get("total_nfs",0), "NFs to Migrate"), unsafe_allow_html=True)
                c2.markdown(m_card(f'{has_plan.get("total_downtime_min",0):.0f} min', "Est. Downtime"), unsafe_allow_html=True)
                if has_plan.get("steps"):
                    st.dataframe(pd.DataFrame(has_plan["steps"])[["step_number","node_id","migration_strategy","target_algo","estimated_downtime_min","maintenance_window"]], use_container_width=True, hide_index=True)
        with qt[2]:
            if has_fail:
                preds = has_fail.get("predictions",[])
                c1,c2,c3 = st.columns(3)
                c1.markdown(m_card(f'🔴 {has_fail.get("red",0)}',  "High Risk",  "#f43f5e"), unsafe_allow_html=True)
                c2.markdown(m_card(f'🟡 {has_fail.get("yellow",0)}',"Caution",    "#f59e0b"), unsafe_allow_html=True)
                c3.markdown(m_card(f'🟢 {has_fail.get("green",0)}', "Clear",      "#10b981"), unsafe_allow_html=True)
                if preds:
                    st.dataframe(pd.DataFrame(preds)[["node_id","risk_flag","registration_success_pct","rollback_probability","recommended_action"]], use_container_width=True, hide_index=True)
        with qt[3]:
            if has_exp:
                for e in has_exp.get("items",[])[:4]:
                    with st.expander(f"🔍 {e['node_id']} · {e['nf_type']}"):
                        st.markdown(f'<div class="al-ok"><b>📝 Plain English:</b> {e["plain_english_summary"]}</div>', unsafe_allow_html=True)
                        st.write("**Why this order?**", e["why_this_order"])
                        st.write("**What if delayed?**", e["what_if_delayed"])

# ── Tab 5: Twin ───────────────────────────────────────────────────────────────
with tabs[4]:
    data = api_get("/workflow/data/twin")
    if not data:
        st.info("💡 Run the Digital Twin to validate post-migration NF behaviour.")
        if st.button("▶ Run Twin Validation"): api_post("/workflow/step5/twin"); st.rerun()
    else:
        c1,c2,c3 = st.columns(3)
        c1.markdown(m_card(data.get("passed",0), "Passed", "#10b981"), unsafe_allow_html=True)
        c2.markdown(m_card(data.get("failed",0), "Failed", "#f43f5e"), unsafe_allow_html=True)
        c3.markdown(m_card(f'{data.get("confidence",0):.1f}%', "Confidence", "#c084fc"), unsafe_allow_html=True)
        for r in data.get("reports",[])[:5]:
            with st.expander(f"{'✅' if r['overall_passed'] else '❌'} {r['nf_id']} — {r['pass_rate_pct']}% pass"):
                st.write("**Recommendation:**", r["recommendation"])
                df_k = pd.DataFrame(r.get("kpi_deltas",[]))
                if not df_k.empty:
                    st.dataframe(df_k[["metric_name","before","after","delta_pct","within_sla"]], use_container_width=True, hide_index=True)

# ── Tab 6: PQC ────────────────────────────────────────────────────────────────
with tabs[5]:
    data = api_get("/workflow/data/pqc")
    if not data:
        st.info("💡 Validate the Hybrid PQC handshake (ML-KEM-768 + ML-DSA-65).")
        if st.button("▶ Run PQC Validation"): api_post("/workflow/step6/pqc"); st.rerun()
    else:
        st.markdown(f'<div class="{"al-ok" if data.get("is_real_pqc") else "al-warn"}">{"✅ liboqs present — REAL NIST PQC" if data.get("is_real_pqc") else "⚠️ Simulated PQC fallback"}</div>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(m_card(f'{data.get("keygen_ms",0):.2f} ms',"KEM Keygen"), unsafe_allow_html=True)
        c2.markdown(m_card(f'{data.get("encap_ms",0):.2f} ms', "Encapsulate"), unsafe_allow_html=True)
        c3.markdown(m_card(f'{data.get("decap_ms",0):.2f} ms', "Decapsulate"), unsafe_allow_html=True)
        c4.markdown(m_card("✅ VALID" if data.get("kem_match") else "❌ FAIL", "KEM Match", "#10b981" if data.get("kem_match") else "#f43f5e"), unsafe_allow_html=True)
        st.write(f"**QKD Mode:** `{data.get('qkd_mode','N/A')}` | **Key Buffer:** `{data.get('key_buffer_bytes',0)} bytes`")

# ── Tab 7: Sentinel ───────────────────────────────────────────────────────────
with tabs[6]:
    data = api_get("/workflow/data/sentinel")
    if not data:
        st.info("💡 Start Edge Crypto Sentinel to monitor live TLS posture.")
        if st.button("▶ Run Edge Sentinel"): api_get("/workflow/step7/sentinel"); st.rerun()
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(m_card(f'{data.get("avg_posture_score",0):.0f}', "Avg Posture", "#c084fc"), unsafe_allow_html=True)
        c2.markdown(m_card(data.get("critical_alerts",0), "Critical", "#f43f5e"), unsafe_allow_html=True)
        c3.markdown(m_card(data.get("warning_alerts",0), "Warnings", "#f59e0b"), unsafe_allow_html=True)
        c4.markdown(m_card(data.get("pqc_cipher_count",0), "PQC Connections", "#06b6d4"), unsafe_allow_html=True)
        tls = data.get("tls_version_inventory",{})
        if tls:
            fig = go.Figure(go.Pie(labels=list(tls.keys()),values=list(tls.values()),hole=0.52,
                marker=dict(colors=["#10b981","#f59e0b","#f43f5e","#c084fc"])))
            fig.update_layout(title="TLS Version Distribution", **_plot_cfg())
            st.plotly_chart(fig, use_container_width=True)
        alerts = data.get("alerts",[])
        if alerts:
            st.dataframe(pd.DataFrame(alerts)[["nf_id","alert_type","severity","message"]], use_container_width=True, hide_index=True)

# ── Tab 8: Policy ─────────────────────────────────────────────────────────────
with tabs[7]:
    data = api_get("/workflow/data/policy")
    if not data:
        st.info("💡 Evaluate cryptographic policy compliance and auto-remediation.")
        if st.button("▶ Run Policy Engine"): api_get("/workflow/step8/policy"); st.rerun()
    else:
        comp = data.get("compliance_pct",0)
        col = "#10b981" if comp>80 else "#f59e0b" if comp>60 else "#f43f5e"
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(m_card(f'{comp:.0f}%', "Compliance", col), unsafe_allow_html=True)
        c2.markdown(m_card(data.get("total_violations",0), "Violations"), unsafe_allow_html=True)
        c3.markdown(m_card(data.get("critical_violations",0), "Critical", "#f43f5e"), unsafe_allow_html=True)
        c4.markdown(m_card(data.get("auto_remediated",0), "Remediated", "#10b981"), unsafe_allow_html=True)
        for s in data.get("statuses",[])[:5]:
            with st.expander(f"{'✅' if s['overall_compliant'] else '❌'} {s['nf_id']} · Score {s['compliance_score']}/100 · {s['risk_tier']}"):
                if s.get("violations"):
                    st.dataframe(pd.DataFrame(s["violations"])[["policy_rule","severity","description","auto_remediation"]], use_container_width=True, hide_index=True)
                if s.get("actions"):
                    st.dataframe(pd.DataFrame(s["actions"])[["action_type","description","status"]], use_container_width=True, hide_index=True)

# ── Tab 9: Executive Report ───────────────────────────────────────────────────
with tabs[8]:
    data = api_get("/workflow/data/report")
    if not data:
        st.info("💡 Complete the full workflow to generate the Executive Report.")
    else:
        st.markdown(f"### 📄 Executive Summary")
        st.caption(f"Generated: `{data.get('generated_at')}` · Classification: **TOP SECRET // NCIIPC**")
        st.markdown("---")
        pipe = data.get("pipeline_summary",{})
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(m_card(f'{pipe.get("steps_completed",0)}/9',"Steps Done"), unsafe_allow_html=True)
        qm = pipe.get("risk",{}).get("avg_qmis",0) if pipe.get("risk") else 0
        c2.markdown(m_card(f'{qm:.1f}',"Avg QMIS","#f43f5e" if qm>70 else "#f59e0b" if qm>40 else "#10b981"), unsafe_allow_html=True)
        cp = pipe.get("policy",{}).get("compliance_pct",0) if pipe.get("policy") else 0
        c3.markdown(m_card(f'{cp:.0f}%',"Compliance","#10b981" if cp>80 else "#f59e0b"), unsafe_allow_html=True)
        tw = pipe.get("twin",{}).get("confidence",0) if pipe.get("twin") else 0
        c4.markdown(m_card(f'{tw:.1f}%',"Twin Confidence"), unsafe_allow_html=True)

        st.markdown('<div class="section-hdr" style="margin-top:32px;">TAMPER-EVIDENT EVIDENCE LEDGER</div>', unsafe_allow_html=True)
        ledger = data.get("ledger",{})
        valid = ledger.get("chain_valid",False)
        lc1,lc2 = st.columns([1,3])
        with lc1:
            badge = (
                '<div style="padding:24px;border-radius:20px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.4);text-align:center;backdrop-filter:blur(20px);">'
                '<div style="font-size:2.5rem;">🛡️</div><div style="font-size:1rem;font-weight:800;color:#10b981;margin-top:8px;">CHAIN VALID</div>'
                '<div style="font-size:0.65rem;color:rgba(16,185,129,0.6);margin-top:4px;">Cryptographic Integrity Confirmed</div></div>'
            ) if valid else (
                '<div style="padding:24px;border-radius:20px;background:rgba(244,63,94,0.1);border:1px solid rgba(244,63,94,0.4);text-align:center;backdrop-filter:blur(20px);">'
                '<div style="font-size:2.5rem;">⚠️</div><div style="font-size:1rem;font-weight:800;color:#f43f5e;margin-top:8px;">CHAIN BROKEN</div>'
                '<div style="font-size:0.65rem;color:rgba(244,63,94,0.6);margin-top:4px;">Tampering Detected</div></div>'
            )
            st.markdown(badge, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.write(f"**Events:** {ledger.get('total_entries',0)}")
            st.markdown("<p style='font-size:0.68rem;color:rgba(255,255,255,0.3);'>ROOT HASH</p>", unsafe_allow_html=True)
            st.code(ledger.get("ledger_root_hash","N/A"), language="text")
        with lc2:
            st.write("### 📜 Immutable Event Log")
            entries = ledger.get("entries",[])
            if entries:
                df_l = pd.DataFrame(entries)
                df_l["timestamp"] = pd.to_datetime(df_l["timestamp"]).dt.strftime("%H:%M:%S.%f")
                st.dataframe(df_l[["sequence","timestamp","event_type","entry_id","previous_hash"]], use_container_width=True, hide_index=True)
                with st.expander("🔍 Raw Cryptographic Ledger (Auditor View)"):
                    st.json(ledger)
