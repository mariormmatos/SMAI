from __future__ import annotations

import streamlit as st


THEME_CSS = """
<style>
  :root{
    --bg0:#0b0f14; --bg1:#0f1620; --card:#111a24; --text:#e9eef6; --muted:#9fb0c3;
    --accent:#4ea1ff; --good:#2ecc71; --bad:#ff5c5c;
    --stroke: rgba(255,255,255,0.08);
  }
  .stApp { background: radial-gradient(1200px 700px at 30% 0%, #182235 0%, var(--bg0) 55%, #070a0e 100%); color: var(--text); }
  section[data-testid="stSidebar"]{ background: linear-gradient(180deg, #0f141b 0%, #0b0f14 100%); border-right: 1px solid rgba(255,255,255,0.06); }
  section[data-testid="stSidebar"] * { color: var(--text) !important; }
  .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
    background: rgba(17,26,36,0.85) !important; border: 1px solid rgba(255,255,255,0.10) !important;
    color: var(--text) !important; border-radius: 12px !important;
  }
  button[role="tab"]{ background: rgba(255,255,255,0.08) !important; border: 1px solid rgba(255,255,255,0.10) !important; color: var(--text) !important; border-radius: 999px !important; padding: 8px 14px !important; margin-right: 8px !important; }
  button[role="tab"][aria-selected="true"]{ background: rgba(78,161,255,0.18) !important; border: 1px solid rgba(78,161,255,0.35) !important; box-shadow: 0 0 0 1px rgba(78,161,255,0.20) inset; }
  h1,h2,h3 { color: var(--text) !important; }
  small, .stCaption, .stMarkdown p { color: var(--muted); }
  hr { border-color: rgba(255,255,255,0.08) !important; }

  .smai-hero{
    background: rgba(17,26,36,0.45);
    border: 1px solid var(--stroke);
    border-radius: 18px;
    padding: 14px 16px;
    box-shadow: 0 10px 26px rgba(0,0,0,0.25);
  }
  .smai-card{
    background: rgba(17,26,36,0.70);
    border: 1px solid var(--stroke);
    border-radius: 18px;
    padding: 14px 16px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.25);
  }
  .smai-subtle{ color: var(--muted); font-size: 0.92rem; }
  .smai-pill{
    display:inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid var(--stroke);
    background: rgba(17,26,36,0.9);
    font-size: 0.85rem;
    color: #d6deea;
  }
  .smai-kbd{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace;
    font-size: 0.82rem;
    padding: 2px 7px;
    border-radius: 8px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.06);
  }

  div[data-testid="stMetric"]{
    background: rgba(17,26,36,0.85);
    border: 1px solid var(--stroke);
    border-radius: 16px;
    padding: 12px 12px;
  }

  .stDataFrame, .stTable { color: var(--text) !important; }
</style>
"""


def apply_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
