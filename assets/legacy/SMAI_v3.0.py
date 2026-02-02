import math
import time
import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# =========================
# UI / THEME (forecast.biz-inspired)
# =========================

st.set_page_config(
    page_title="SMAI | Stock Market Analysis & Insights",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_CSS = """
<style>
:root{
  --bg: #f6f7fb;
  --card: #ffffff;
  --muted: rgba(10,20,35,0.65);
  --text: #0a1423;
  --stroke: rgba(10,20,35,0.10);
  --shadow: 0 8px 24px rgba(10,20,35,0.06);
  --shadow2: 0 4px 12px rgba(10,20,35,0.06);
  --radius: 16px;
}

html, body, [class*="css"]{
  color: var(--text);
  background: var(--bg);
}

.block-container { padding-top: 1.1rem; padding-bottom: 2rem; }

.smai-hero{
  background: linear-gradient(135deg, rgba(10,20,35,0.06), rgba(10,20,35,0.02));
  border: 1px solid var(--stroke);
  border-radius: var(--radius);
  padding: 14px 16px;
  box-shadow: var(--shadow);
}

.smai-card{
  background: var(--card);
  border: 1px solid var(--stroke);
  border-radius: var(--radius);
  padding: 14px 14px;
  box-shadow: var(--shadow2);
}

.smai-subtle{
  color: var(--muted);
  font-size: 0.92rem;
}

.smai-pill{
  display:inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.7);
  font-size: 0.85rem;
  color: rgba(10,20,35,0.78);
}

div[data-testid="stMetric"]{
  background: var(--card);
  border: 1px solid var(--stroke);
  border-radius: 14px;
  padding: 12px 12px;
  box-shadow: var(--shadow2);
}

section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.92));
  border-right: 1px solid var(--stroke);
}

.stTabs [data-baseweb="tab-list"]{
  gap: 8px;
}

.stTabs [data-baseweb="tab"]{
  border: 1px solid var(--stroke);
  border-radius: 999px;
  padding: 6px 12px;
  background: rgba(255,255,255,0.75);
}

.stTabs [aria-selected="true"]{
  background: #ffffff !important;
  box-shadow: var(--shadow2);
}

a { text-decoration: none; }
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

# =========================
# CONFIG / HELPERS
# =========================

PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "10Y": ("10y", "1mo"),
}

@dataclass
class DcfInputs:
    years: int
    revenue_growth: float         # used as fallback proxy
    fcf_growth: float
    discount_rate: float
    terminal_growth: float
    tax_rate: float
    net_debt: float               # debt - cash
    shares_outstanding: float
    starting_fcf: float

def _safe_float(x, default=np.nan):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def _fmt_num(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "N/A"
    ax = abs(x)
    if ax >= 1e12:
        return f"{x/1e12:.2f}T"
    if ax >= 1e9:
        return f"{x/1e9:.2f}B"
    if ax >= 1e6:
        return f"{x/1e6:.2f}M"
    if ax >= 1e3:
        return f"{x/1e3:.2f}K"
    return f"{x:.2f}"

def _fmt_pct(x: float, digits=2) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "N/A"
    return f"{x*100:.{digits}f}%"

def _plot_area(
    df: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    title: str,
    yaxis_title: str = "",
    hover_suffix: str = "",
):
    fig = go.Figure()
    for i, col in enumerate(y_cols):
        if col not in df.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[col],
                mode="lines",
                name=col,
                fill="tozeroy" if i == 0 else None,
            )
        )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=360,
        margin=dict(l=10, r=10, t=48, b=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(title=yaxis_title, showgrid=True, gridcolor="rgba(10,20,35,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

def _plot_candles(df: pd.DataFrame, title: str):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price",
            )
        ]
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=48, b=10),
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(10,20,35,0.08)"),
    )
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl=60 * 30, show_spinner=False)
def get_price_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    return df

@st.cache_data(ttl=60 * 60, show_spinner=False)
def get_info(ticker: str) -> Dict:
    t = yf.Ticker(ticker)
    try:
        return t.info or {}
    except Exception:
        return {}

@st.cache_data(ttl=60 * 60, show_spinner=False)
def get_statements(ticker: str) -> Dict[str, pd.DataFrame]:
    t = yf.Ticker(ticker)
    out = {}
    # yfinance sometimes fails per attribute; keep resilient
    for k, attr in [
        ("financials", "financials"),                 # income statement (annual)
        ("quarterly_financials", "quarterly_financials"),
        ("balance_sheet", "balance_sheet"),
        ("quarterly_balance_sheet", "quarterly_balance_sheet"),
        ("cashflow", "cashflow"),
        ("quarterly_cashflow", "quarterly_cashflow"),
    ]:
        try:
            out[k] = getattr(t, attr)
        except Exception:
            out[k] = pd.DataFrame()
    return out

def _statement_to_timeseries(stmt: pd.DataFrame, rows: List[str]) -> pd.DataFrame:
    """
    yfinance statements: index = line items, columns = dates
    We transpose to: Date + requested rows as columns
    """
    if stmt is None or stmt.empty:
        return pd.DataFrame()
    s = stmt.copy()
    s.columns = pd.to_datetime(s.columns)
    s = s.T.sort_index()
    cols = []
    for r in rows:
        if r in s.columns:
            cols.append(r)
    if not cols:
        return pd.DataFrame()
    df = s[cols].copy()
    df.insert(0, "Date", df.index)
    df.reset_index(drop=True, inplace=True)
    return df

def _compute_ratios(info: Dict) -> Dict[str, float]:
    # direct fields are spot values; still useful for scorecard
    pe = _safe_float(info.get("trailingPE"))
    fpe = _safe_float(info.get("forwardPE"))
    pb = _safe_float(info.get("priceToBook"))
    ps = _safe_float(info.get("priceToSalesTrailing12Months"))
    roe = _safe_float(info.get("returnOnEquity"))
    roa = _safe_float(info.get("returnOnAssets"))
    margin = _safe_float(info.get("profitMargins"))
    op_margin = _safe_float(info.get("operatingMargins"))
    div_yield = _safe_float(info.get("dividendYield"))
    beta = _safe_float(info.get("beta"))
    payout = _safe_float(info.get("payoutRatio"))
    return {
        "Trailing P/E": pe,
        "Forward P/E": fpe,
        "P/B": pb,
        "P/S (TTM)": ps,
        "ROE": roe,
        "ROA": roa,
        "Profit Margin": margin,
        "Operating Margin": op_margin,
        "Dividend Yield": div_yield,
        "Payout Ratio": payout,
        "Beta": beta,
    }

def _scorecard(r: Dict[str, float]) -> Tuple[int, List[str]]:
    """
    Simple, deterministic scoring (0-100) with explicit heuristics.
    This is not a recommendation; it's a consistent rubric.
    """
    score = 0
    notes = []

    # Valuation
    pe = r.get("Trailing P/E", np.nan)
    ps = r.get("P/S (TTM)", np.nan)
    pb = r.get("P/B", np.nan)

    if not math.isnan(pe):
        if pe <= 15:
            score += 18; notes.append("Valuation: P/E <= 15 (+18)")
        elif pe <= 25:
            score += 10; notes.append("Valuation: 15 < P/E <= 25 (+10)")
        else:
            score += 3; notes.append("Valuation: P/E > 25 (+3)")
    else:
        notes.append("Valuation: P/E N/A (+0)")

    if not math.isnan(ps):
        if ps <= 3:
            score += 10; notes.append("Valuation: P/S <= 3 (+10)")
        elif ps <= 7:
            score += 6; notes.append("Valuation: 3 < P/S <= 7 (+6)")
        else:
            score += 2; notes.append("Valuation: P/S > 7 (+2)")
    else:
        notes.append("Valuation: P/S N/A (+0)")

    if not math.isnan(pb):
        if pb <= 2:
            score += 6; notes.append("Balance/Valuation: P/B <= 2 (+6)")
        elif pb <= 5:
            score += 4; notes.append("Balance/Valuation: 2 < P/B <= 5 (+4)")
        else:
            score += 1; notes.append("Balance/Valuation: P/B > 5 (+1)")
    else:
        notes.append("Balance/Valuation: P/B N/A (+0)")

    # Quality
    roe = r.get("ROE", np.nan)
    opm = r.get("Operating Margin", np.nan)

    if not math.isnan(roe):
        if roe >= 0.20:
            score += 18; notes.append("Quality: ROE >= 20% (+18)")
        elif roe >= 0.12:
            score += 12; notes.append("Quality: 12% <= ROE < 20% (+12)")
        elif roe >= 0.06:
            score += 6; notes.append("Quality: 6% <= ROE < 12% (+6)")
        else:
            score += 2; notes.append("Quality: ROE < 6% (+2)")
    else:
        notes.append("Quality: ROE N/A (+0)")

    if not math.isnan(opm):
        if opm >= 0.25:
            score += 14; notes.append("Quality: Op. margin >= 25% (+14)")
        elif opm >= 0.12:
            score += 9; notes.append("Quality: 12% <= Op. margin < 25% (+9)")
        elif opm >= 0.05:
            score += 5; notes.append("Quality: 5% <= Op. margin < 12% (+5)")
        else:
            score += 1; notes.append("Quality: Op. margin < 5% (+1)")
    else:
        notes.append("Quality: Operating margin N/A (+0)")

    # Risk
    beta = r.get("Beta", np.nan)
    if not math.isnan(beta):
        if beta <= 1.0:
            score += 10; notes.append("Risk: Beta <= 1.0 (+10)")
        elif beta <= 1.5:
            score += 6; notes.append("Risk: 1.0 < Beta <= 1.5 (+6)")
        else:
            score += 2; notes.append("Risk: Beta > 1.5 (+2)")
    else:
        notes.append("Risk: Beta N/A (+0)")

    # Shareholder return
    dy = r.get("Dividend Yield", np.nan)
    if not math.isnan(dy):
        if dy >= 0.03:
            score += 8; notes.append("Shareholder return: Div. yield >= 3% (+8)")
        elif dy >= 0.015:
            score += 5; notes.append("Shareholder return: 1.5%–3% (+5)")
        elif dy > 0:
            score += 2; notes.append("Shareholder return: < 1.5% (+2)")
        else:
            score += 0; notes.append("Shareholder return: no dividend (+0)")
    else:
        notes.append("Shareholder return: Dividend yield N/A (+0)")

    score = max(0, min(100, score))
    return score, notes

# =========================
# SENTIMENT (Stocktwits + Reddit public JSON)
# =========================

POS_WORDS = {"beat", "beats", "strong", "upside", "bull", "bullish", "growth", "buy", "accumulate", "undervalued", "record", "profit", "surge"}
NEG_WORDS = {"miss", "missed", "weak", "downside", "bear", "bearish", "sell", "overvalued", "fraud", "drop", "plunge", "lawsuit", "warning"}

def _lex_sentiment(text: str) -> float:
    if not text:
        return 0.0
    t = text.lower()
    pos = sum(w in t for w in POS_WORDS)
    neg = sum(w in t for w in NEG_WORDS)
    if pos == 0 and neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)

@st.cache_data(ttl=60 * 20, show_spinner=False)
def fetch_stocktwits(ticker: str, limit: int = 30) -> pd.DataFrame:
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return pd.DataFrame()
        j = r.json()
        msgs = j.get("messages", [])[:limit]
        rows = []
        for m in msgs:
            body = m.get("body", "")
            created = m.get("created_at", "")
            user = (m.get("user") or {}).get("username", "")
            sentiment = _lex_sentiment(body)
            rows.append({"source": "stocktwits", "created_at": created, "user": user, "text": body, "sentiment": sentiment})
        df = pd.DataFrame(rows)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60 * 20, show_spinner=False)
def fetch_reddit_search(ticker: str, limit: int = 30) -> pd.DataFrame:
    """
    Public Reddit search endpoint (no auth). Rate-limits can happen; keep small & cached.
    """
    url = "https://www.reddit.com/search.json"
    headers = {"User-Agent": "SMAI/1.0 (Streamlit; personal analysis app)"}
    params = {"q": ticker, "sort": "new", "limit": min(limit, 50)}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()
        j = r.json()
        children = (((j.get("data") or {}).get("children")) or [])[:limit]
        rows = []
        for c in children:
            d = c.get("data") or {}
            title = d.get("title", "")
            selftext = d.get("selftext", "")
            created_utc = d.get("created_utc", None)
            created_at = dt.datetime.utcfromtimestamp(created_utc).isoformat() if created_utc else ""
            author = d.get("author", "")
            subreddit = d.get("subreddit", "")
            text = (title + " " + selftext).strip()
            sentiment = _lex_sentiment(text)
            rows.append({"source": "reddit", "created_at": created_at, "user": author, "subreddit": subreddit, "text": title, "sentiment": sentiment})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def sentiment_summary(df: pd.DataFrame) -> Dict[str, float]:
    if df is None or df.empty:
        return {"count": 0, "avg": 0.0, "pos_share": 0.0, "neg_share": 0.0}
    s = df["sentiment"].fillna(0.0)
    return {
        "count": float(len(df)),
        "avg": float(s.mean()),
        "pos_share": float((s > 0.05).mean()),
        "neg_share": float((s < -0.05).mean()),
    }

# =========================
# DCF (Buffett module)
# =========================

def run_dcf(inp: DcfInputs) -> Dict[str, float]:
    """
    Single-stage FCF projection with terminal value (Gordon Growth).
    Returns enterprise value, equity value, intrinsic per share.
    """
    fcf0 = max(0.0, float(inp.starting_fcf))
    years = int(inp.years)

    # Project FCFs
    fcfs = []
    for y in range(1, years + 1):
        fcf_y = fcf0 * ((1.0 + inp.fcf_growth) ** y)
        fcfs.append(fcf_y)

    # Discount factors
    dfs = [(1.0 / ((1.0 + inp.discount_rate) ** y)) for y in range(1, years + 1)]
    pv_fcfs = sum(f * d for f, d in zip(fcfs, dfs))

    # Terminal value
    g = inp.terminal_growth
    r = inp.discount_rate
    fcf_n = fcfs[-1] if fcfs else fcf0
    if r <= g:
        # avoid nonsense
        terminal_value = 0.0
    else:
        terminal_value = (fcf_n * (1.0 + g)) / (r - g)
    pv_terminal = terminal_value * dfs[-1] if dfs else 0.0

    enterprise_value = pv_fcfs + pv_terminal
    equity_value = enterprise_value - float(inp.net_debt)
    intrinsic_per_share = equity_value / float(inp.shares_outstanding) if inp.shares_outstanding else np.nan

    return {
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_per_share": intrinsic_per_share,
        "pv_fcfs": pv_fcfs,
        "pv_terminal": pv_terminal,
    }

def dcf_sensitivity(
    base: DcfInputs,
    discount_rates: List[float],
    terminal_growths: List[float],
) -> pd.DataFrame:
    rows = []
    for r in discount_rates:
        row = {"Discount Rate": r}
        for g in terminal_growths:
            inp = DcfInputs(**{**base.__dict__, "discount_rate": r, "terminal_growth": g})
            out = run_dcf(inp)
            row[f"g={g:.1%}"] = out["intrinsic_per_share"]
        rows.append(row)
    return pd.DataFrame(rows)

# =========================
# SIDEBAR
# =========================

st.markdown(
    """
<div class="smai-hero">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <div>
      <div style="font-size:1.2rem; font-weight:700;">SMAI — Stock Market Analysis & Insights</div>
      <div class="smai-subtle">Fundamentals • Technicals • Sentiment • Buffett (DCF) • Screener • Watchlist</div>
    </div>
    <div class="smai-pill">Private • Streamlit Cloud Ready</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Inputs")

    ticker = st.text_input("Ticker", value="MSFT").strip().upper()
    timeframe = st.selectbox("Timeframe", list(PERIOD_MAP.keys()), index=5)  # default 10Y
    period, interval = PERIOD_MAP[timeframe]

    st.divider()
    st.subheader("Screener Filters (mini-universe)")
    min_div = st.slider("Min Dividend Yield (%)", 0.0, 10.0, 2.0, 0.1)
    max_pe = st.slider("Max Trailing P/E", 5, 120, 25, 1)
    min_mcap_b = st.slider("Min Market Cap ($B)", 0, 2000, 10, 1)
    tickers_universe = st.text_area(
        "Tickers universe (comma-separated)",
        value="MSFT, NVDA, AAPL, GOOGL, AMZN, META, TSLA, NVO, PFE, NEE, EOAN.DE, ASML, AVGO, AMD, JPM, XOM",
        height=90,
    )

    st.divider()
    st.subheader("Watchlist (alerts)")
    watchlist_default = "NVO, PFE, XIACF, NEE, EOAN.DE, UNH"
    watchlist_str = st.text_input("Watchlist tickers", value=watchlist_default)
    drop_threshold = st.slider("Alert if drawdown from 52W High >=", 5, 60, 20, 1)

    st.divider()
    st.caption("Tip: para tickers europeus usa sufixos (ex: EOAN.DE).")


# =========================
# LOAD DATA (robust)
# =========================

if not ticker:
    st.stop()

with st.spinner("Loading market data…"):
    info = get_info(ticker)
    px = get_price_history(ticker, period=period, interval=interval)
    stmts = get_statements(ticker)

if px.empty:
    st.error("Sem dados de preço para este ticker (ou limite do Yahoo Finance). Confirma o ticker e tenta outro timeframe.")
    st.stop()

# =========================
# TOP SUMMARY ROW
# =========================

last_close = float(px["Close"].iloc[-1])
prev_close = float(px["Close"].iloc[-2]) if len(px) > 1 else last_close
day_chg = (last_close / prev_close - 1.0) if prev_close else 0.0

mcap = _safe_float(info.get("marketCap"))
currency = info.get("currency", "")

ratios = _compute_ratios(info)
score, score_notes = _scorecard(ratios)

c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1, 1.2])
c1.metric("Last", f"{last_close:.2f} {currency}", _fmt_pct(day_chg))
c2.metric("Market Cap", _fmt_num(mcap))
c3.metric("Trailing P/E", "N/A" if math.isnan(ratios["Trailing P/E"]) else f"{ratios['Trailing P/E']:.2f}")
c4.metric("ROE", "N/A" if math.isnan(ratios["ROE"]) else _fmt_pct(ratios["ROE"]))
c5.metric("Scorecard", f"{score}/100")

st.write("")

# =========================
# MAIN MODULE TABS
# =========================

tab_fund, tab_tech, tab_sent, tab_buff, tab_screen, tab_watch, tab_report = st.tabs(
    [
        "1) Fundamental Analysis",
        "2) Technical Analysis",
        "3) Sentiment (Reddit/Stocktwits)",
        "4) Buffett (DCF)",
        "5) Screener",
        "6) Watchlist & Alerts",
        "7) Report",
    ]
)

# -------------------------
# 1) FUNDAMENTAL ANALYSIS
# -------------------------
with tab_fund:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Fundamental Analysis")

    areas = st.tabs(
        [
            "A) Financial Statements (charts)",
            "B) Ratios & KPIs (charts)",
            "C) Business Quality (text)",
            "D) Moat & Management (text)",
            "E) Risks & Catalysts (text)",
        ]
    )

    # A) Financial statements charts
    with areas[0]:
        st.caption("Fonte: Yahoo Finance (yfinance). As séries aqui são anuais e/ou trimestrais conforme disponibilidade.")

        income_annual = stmts.get("financials", pd.DataFrame())
        income_q = stmts.get("quarterly_financials", pd.DataFrame())
        cf_annual = stmts.get("cashflow", pd.DataFrame())
        cf_q = stmts.get("quarterly_cashflow", pd.DataFrame())
        bs_annual = stmts.get("balance_sheet", pd.DataFrame())
        bs_q = stmts.get("quarterly_balance_sheet", pd.DataFrame())

        colL, colR = st.columns([1, 1])
        with colL:
            mode = st.radio("Statements frequency", ["Annual", "Quarterly"], horizontal=True)
        with colR:
            st.write("")
            st.write("")

        if mode == "Annual":
            inc = income_annual
            cf = cf_annual
            bs = bs_annual
        else:
            inc = income_q
            cf = cf_q
            bs = bs_q

        # Income statement
        st.markdown("**Income Statement**")
        inc_rows = [
            "Total Revenue",
            "Gross Profit",
            "Operating Income",
            "Net Income",
            "Diluted EPS",
        ]
        inc_ts = _statement_to_timeseries(inc, inc_rows)
        if inc_ts.empty:
            st.info("Sem Income Statement suficiente no Yahoo Finance para este ticker.")
        else:
            _plot_area(
                inc_ts,
                "Date",
                [c for c in inc_rows if c in inc_ts.columns],
                title="Income Statement (over time)",
                yaxis_title=f"Amount ({currency})",
            )

        # Cash flow
        st.markdown("**Cash Flow**")
        cf_rows = [
            "Total Cash From Operating Activities",
            "Capital Expenditures",
            "Free Cash Flow",  # sometimes absent
        ]
        cf_ts = _statement_to_timeseries(cf, cf_rows)
        # If FCF missing, approximate CFO + CapEx (CapEx negative often)
        if not cf_ts.empty and "Free Cash Flow" not in cf_ts.columns:
            if "Total Cash From Operating Activities" in cf_ts.columns and "Capital Expenditures" in cf_ts.columns:
                cf_ts["Free Cash Flow"] = cf_ts["Total Cash From Operating Activities"] + cf_ts["Capital Expenditures"]

        if cf_ts.empty:
            st.info("Sem Cash Flow suficiente no Yahoo Finance para este ticker.")
        else:
            _plot_area(
                cf_ts,
                "Date",
                [c for c in ["Total Cash From Operating Activities", "Capital Expenditures", "Free Cash Flow"] if c in cf_ts.columns],
                title="Cash Flow (over time)",
                yaxis_title=f"Amount ({currency})",
            )

        # Balance sheet
        st.markdown("**Balance Sheet**")
        bs_rows = [
            "Total Assets",
            "Total Liab",
            "Total Stockholder Equity",
            "Cash",
            "Long Term Debt",
        ]
        bs_ts = _statement_to_timeseries(bs, bs_rows)
        if bs_ts.empty:
            st.info("Sem Balance Sheet suficiente no Yahoo Finance para este ticker.")
        else:
            _plot_area(
                bs_ts,
                "Date",
                [c for c in bs_rows if c in bs_ts.columns],
                title="Balance Sheet (over time)",
                yaxis_title=f"Amount ({currency})",
            )

    # B) Ratios & KPIs (charts)
    with areas[1]:
        st.caption("Alguns rácios são spot (info). Outros são estimados com base em statements disponíveis.")

        # Build a simple ratios time-series from annual statements if possible
        income_annual = stmts.get("financials", pd.DataFrame())
        bs_annual = stmts.get("balance_sheet", pd.DataFrame())

        inc_ts = _statement_to_timeseries(income_annual, ["Total Revenue", "Net Income", "Operating Income"])
        bs_ts = _statement_to_timeseries(bs_annual, ["Total Stockholder Equity", "Total Assets"])

        ratios_ts = pd.DataFrame()
        if not inc_ts.empty:
            ratios_ts = inc_ts[["Date"]].copy()
            if "Operating Income" in inc_ts.columns and "Total Revenue" in inc_ts.columns:
                ratios_ts["Operating Margin"] = inc_ts["Operating Income"] / inc_ts["Total Revenue"]
            if "Net Income" in inc_ts.columns and "Total Revenue" in inc_ts.columns:
                ratios_ts["Net Margin"] = inc_ts["Net Income"] / inc_ts["Total Revenue"]

        if not ratios_ts.empty and not bs_ts.empty:
            merged = pd.merge(ratios_ts, bs_ts, on="Date", how="left")
            if "Net Income" in inc_ts.columns and "Total Stockholder Equity" in merged.columns:
                merged["ROE (est.)"] = inc_ts["Net Income"].values[: len(merged)] / merged["Total Stockholder Equity"]
            if "Net Income" in inc_ts.columns and "Total Assets" in merged.columns:
                merged["ROA (est.)"] = inc_ts["Net Income"].values[: len(merged)] / merged["Total Assets"]
            ratios_ts = merged

        # Price-based “valuation ribbon” across selected timeframe (not a real historical P/E series)
        # We show price + (optionally) a constant trailing EPS proxy for quick visual context
        st.markdown("**Valuation context (price area chart)**")
        px2 = px.copy()
        px2 = px2.reset_index().rename(columns={"index": "Date"})
        if "Date" not in px2.columns:
            # yfinance may return DatetimeIndex
            px2["Date"] = px.index
        keep = ["Date", "Close"]
        px2 = px2[keep].dropna()

        _plot_area(px2, "Date", ["Close"], title=f"{ticker} price ({timeframe})", yaxis_title=f"Price ({currency})")

        st.markdown("**Profitability & Returns (estimated from annual statements)**")
        if ratios_ts is None or ratios_ts.empty:
            st.info("Sem dados anuais suficientes para construir séries de rácios (margens/ROE/ROA).")
        else:
            cols = [c for c in ["Operating Margin", "Net Margin", "ROE (est.)", "ROA (est.)"] if c in ratios_ts.columns]
            if cols:
                chart_df = ratios_ts[["Date"] + cols].copy()
                # Convert to percent for chart readability
                for c in cols:
                    chart_df[c] = chart_df[c] * 100.0
                _plot_area(chart_df, "Date", cols, title="Margins & Returns (annual)", yaxis_title="%")
            else:
                st.info("Rácios não calculáveis com o que o Yahoo devolveu para este ticker.")

        st.markdown("**Current snapshot (from info)**")
        snap = pd.DataFrame(
            [
                {"Metric": k, "Value": (f"{v:.2f}" if isinstance(v, float) and not math.isnan(v) else ("N/A" if (isinstance(v, float) and math.isnan(v)) else str(v)))}
                for k, v in ratios.items()
            ]
        )
        st.dataframe(snap, use_container_width=True, hide_index=True)

    # C) Business Quality (text)
    with areas[2]:
        st.markdown("#### Business Quality")
        long_name = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        summary = info.get("longBusinessSummary", "")

        st.markdown(f"**Company**: {long_name}")
        st.markdown(f"**Sector / Industry**: {sector} / {industry}")

        if summary:
            st.markdown("**Business summary (Yahoo)**")
            st.write(summary)
        else:
            st.info("Sem descrição disponível no Yahoo para este ticker.")

        st.markdown("**Quality checklist (preenchido com métricas disponíveis):**")
        q = []
        q.append(("ROE", _fmt_pct(ratios.get("ROE", np.nan)), "Proxy de eficiência do capital (atenção a buybacks/leverage)."))
        q.append(("Operating margin", _fmt_pct(ratios.get("Operating Margin", np.nan)), "Proxy de pricing power/eficiência operacional."))
        q.append(("Profit margin", _fmt_pct(ratios.get("Profit Margin", np.nan)), "Margem líquida (sensível a itens não recorrentes)."))
        q.append(("Beta", "N/A" if math.isnan(ratios.get("Beta", np.nan)) else f"{ratios.get('Beta'):.2f}", "Volatilidade vs mercado (proxy de risco)."))
        st.table(pd.DataFrame(q, columns=["Metric", "Value", "Interpretation hint"]))

    # D) Moat & Management (text)
    with areas[3]:
        st.markdown("#### Moat & Management (framework)")
        st.write(
            """
Usa isto como framework (texto) para preencheres com a tua análise:
- **Moat sources**: switching costs, network effects, cost advantage, intangible assets/brand, efficient scale.
- **Management**: capital allocation (buybacks/dividends/M&A), consistency, shareholder alignment, guidance credibility.
- **Unit economics**: ARPU/pricing power (se aplicável), churn, CAC/LTV (se aplicável).
- **Balance sheet discipline**: maturidades de dívida, liquidez, dependência de refinancing.
"""
        )

        st.markdown("**Hints automáticos (do Yahoo):**")
        st.write(f"- **Dividend yield**: {_fmt_pct(ratios.get('Dividend Yield', np.nan))}")
        st.write(f"- **Payout ratio**: {_fmt_pct(ratios.get('Payout Ratio', np.nan))}")
        st.write(f"- **Market cap**: {_fmt_num(mcap)}")
        st.write(f"- **52W range**: {info.get('fiftyTwoWeekLow','N/A')} → {info.get('fiftyTwoWeekHigh','N/A')}")

        st.markdown("**Notas do utilizador**")
        user_notes = st.text_area("Escreve aqui os teus pontos (fica só na sessão).", height=160)
        if user_notes.strip():
            st.success("Notas registadas na sessão (não persistente).")

    # E) Risks & Catalysts (text)
    with areas[4]:
        st.markdown("#### Risks & Catalysts")
        st.write(
            """
- **Risks** (exemplos): compressão de margens, disrupção tecnológica, regulação, concentração de clientes, FX, custo de capital, litigância.
- **Catalysts** (exemplos): earnings beats, novos produtos, re-rating de múltiplos, buybacks acelerados, cortes de custos, inflexão macro.
"""
        )

        st.markdown("**Quick signals (do Yahoo):**")
        st.write(f"- **Forward P/E**: {'N/A' if math.isnan(ratios.get('Forward P/E', np.nan)) else f'{ratios.get('Forward P/E'):.2f}'}")
        st.write(f"- **Analyst target mean**: {info.get('targetMeanPrice','N/A')} {currency}")
        st.write(f"- **Recommendation mean**: {info.get('recommendationMean','N/A')} (quanto menor, mais bullish no Yahoo)")

        st.markdown("**Your risk notes**")
        st.text_area("Lista riscos específicos (tese bearish).", height=120)
        st.markdown("**Your catalysts**")
        st.text_area("Lista catalisadores (tese bullish).", height=120)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 2) TECHNICAL ANALYSIS
# -------------------------
with tab_tech:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Technical Analysis")

    t_tabs = st.tabs(["Price (candles)", "Indicators", "Levels & Volatility"])

    with t_tabs[0]:
        _plot_candles(px, f"{ticker} candlestick ({timeframe})")

    with t_tabs[1]:
        df = px.copy()
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()

        # RSI
        delta = df["Close"].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        roll = 14
        rs = up.rolling(roll).mean() / (down.rolling(roll).mean() + 1e-9)
        df["RSI14"] = 100 - (100 / (1 + rs))

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", fill="tozeroy"))
        for ma in ["SMA20", "SMA50", "SMA200"]:
            fig.add_trace(go.Scatter(x=df.index, y=df[ma], mode="lines", name=ma))
        fig.update_layout(
            title=f"{ticker} price + moving averages",
            template="plotly_white",
            height=420,
            margin=dict(l=10, r=10, t=48, b=10),
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(10,20,35,0.08)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

        rsi_df = pd.DataFrame({"Date": df.index, "RSI14": df["RSI14"].values}).dropna()
        _plot_area(rsi_df, "Date", ["RSI14"], title="RSI(14)", yaxis_title="RSI")

    with t_tabs[2]:
        df = px.copy()
        # Bollinger (20,2)
        ma = df["Close"].rolling(20).mean()
        sd = df["Close"].rolling(20).std()
        df["BB_Mid"] = ma
        df["BB_Up"] = ma + 2 * sd
        df["BB_Low"] = ma - 2 * sd

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", fill="tozeroy"))
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Up"], mode="lines", name="BB Upper"))
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Mid"], mode="lines", name="BB Mid"))
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Low"], mode="lines", name="BB Lower"))
        fig.update_layout(
            title=f"{ticker} Bollinger Bands (20, 2σ)",
            template="plotly_white",
            height=420,
            margin=dict(l=10, r=10, t=48, b=10),
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(10,20,35,0.08)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Simple support/resistance from rolling min/max (quick heuristic)
        win = st.slider("Level window (days)", 20, 260, 60, 10)
        df2 = df.copy()
        df2["Rolling Low"] = df2["Low"].rolling(win).min()
        df2["Rolling High"] = df2["High"].rolling(win).max()
        lvl_df = df2.reset_index().rename(columns={"index": "Date"})
        _plot_area(lvl_df, "Date", ["Rolling Low", "Rolling High"], title=f"Rolling support/resistance proxy ({win}d)", yaxis_title=f"Price ({currency})")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 3) SENTIMENT
# -------------------------
with tab_sent:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Sentiment — Reddit & Stocktwits")

    st.caption("Heurística simples (lexicon). Em produção podes trocar por VADER/FinBERT (mais robusto), mas isto já dá sinal rápido.")

    colA, colB = st.columns([1, 1])
    with colA:
        st.markdown("**Stocktwits**")
        st_df = fetch_stocktwits(ticker, limit=40)
        st_sum = sentiment_summary(st_df)
        st.metric("Messages", int(st_sum["count"]))
        st.metric("Avg sentiment", f"{st_sum['avg']:+.3f}")
        st.metric("Positive share", f"{st_sum['pos_share']*100:.1f}%")
        st.metric("Negative share", f"{st_sum['neg_share']*100:.1f}%")

    with colB:
        st.markdown("**Reddit (public search)**")
        rd_df = fetch_reddit_search(ticker, limit=40)
        rd_sum = sentiment_summary(rd_df)
        st.metric("Posts", int(rd_sum["count"]))
        st.metric("Avg sentiment", f"{rd_sum['avg']:+.3f}")
        st.metric("Positive share", f"{rd_sum['pos_share']*100:.1f}%")
        st.metric("Negative share", f"{rd_sum['neg_share']*100:.1f}%")

    st.write("")
    all_sent = pd.concat([st_df, rd_df], ignore_index=True)
    if all_sent.empty:
        st.info("Sem dados de sentimento (pode ser rate-limit / ticker pouco falado).")
    else:
        # timeline chart
        tmp = all_sent.copy()
        # parse dates
        tmp["dt"] = pd.to_datetime(tmp["created_at"], errors="coerce", utc=True)
        tmp = tmp.dropna(subset=["dt"]).sort_values("dt")
        if not tmp.empty:
            daily = tmp.set_index("dt").resample("1D")["sentiment"].mean().reset_index()
            daily.rename(columns={"dt": "Date", "sentiment": "Avg Sentiment"}, inplace=True)
            _plot_area(daily, "Date", ["Avg Sentiment"], title="Daily average sentiment (Reddit + Stocktwits)", yaxis_title="Score")

        st.markdown("**Latest messages/posts**")
        show_cols = [c for c in ["source", "created_at", "user", "subreddit", "sentiment", "text"] if c in all_sent.columns]
        st.dataframe(all_sent[show_cols].head(40), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 4) BUFFETT (DCF)
# -------------------------
with tab_buff:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Warren Buffett Module — DCF Intrinsic Value")

    # Estimate starting FCF from Yahoo info or statements
    fcf_info = _safe_float(info.get("freeCashflow"))
    if math.isnan(fcf_info):
        cf_q = stmts.get("cashflow", pd.DataFrame())
        cf_ts = _statement_to_timeseries(cf_q, ["Total Cash From Operating Activities", "Capital Expenditures"])
        if not cf_ts.empty and "Total Cash From Operating Activities" in cf_ts.columns and "Capital Expenditures" in cf_ts.columns:
            fcf_info = float((cf_ts["Total Cash From Operating Activities"] + cf_ts["Capital Expenditures"]).dropna().iloc[0])

    cash = _safe_float(info.get("totalCash"))
    debt = _safe_float(info.get("totalDebt"))
    shares = _safe_float(info.get("sharesOutstanding"))
    net_debt = (debt - cash) if (not math.isnan(debt) and not math.isnan(cash)) else 0.0

    st.caption("O DCF é sensível a 3 inputs: crescimento, taxa de desconto (WACC/required return) e crescimento terminal. Mantém conservador.")

    cL, cM, cR = st.columns([1, 1, 1])
    with cL:
        years = st.slider("Projection years", 5, 15, 10, 1)
        fcf_growth = st.slider("FCF growth (annual)", 0.00, 0.30, 0.08, 0.01)
        terminal_growth = st.slider("Terminal growth", 0.00, 0.06, 0.025, 0.005)
    with cM:
        discount_rate = st.slider("Discount rate (required return)", 0.05, 0.18, 0.10, 0.005)
        tax_rate = st.slider("Tax rate (proxy)", 0.00, 0.35, 0.21, 0.01)
        st.write("")
    with cR:
        starting_fcf = st.number_input("Starting FCF (base year)", value=float(0.0 if math.isnan(fcf_info) else fcf_info), step=1e8, format="%.2f")
        shares_out = st.number_input("Shares outstanding", value=float(0.0 if math.isnan(shares) else shares), step=1e7, format="%.0f")
        net_debt_in = st.number_input("Net debt (Debt - Cash)", value=float(net_debt), step=1e8, format="%.2f")

    base = DcfInputs(
        years=int(years),
        revenue_growth=0.0,
        fcf_growth=float(fcf_growth),
        discount_rate=float(discount_rate),
        terminal_growth=float(terminal_growth),
        tax_rate=float(tax_rate),
        net_debt=float(net_debt_in),
        shares_outstanding=float(shares_out),
        starting_fcf=float(starting_fcf),
    )

    out = run_dcf(base)
    intrinsic = out["intrinsic_per_share"]
    mos = (intrinsic / last_close - 1.0) if (last_close and not math.isnan(intrinsic)) else np.nan

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("PV of projected FCF", _fmt_num(out["pv_fcfs"]))
    k2.metric("PV of terminal value", _fmt_num(out["pv_terminal"]))
    k3.metric("Equity value (DCF)", _fmt_num(out["equity_value"]))
    k4.metric("Intrinsic / share", "N/A" if math.isnan(intrinsic) else f"{intrinsic:.2f} {currency}")

    st.write("")
    if not math.isnan(mos):
        if mos >= 0.25:
            st.success(f"Margin of safety: {_fmt_pct(mos)} (price below intrinsic by a wide margin)")
        elif mos >= 0.05:
            st.warning(f"Margin of safety: {_fmt_pct(mos)} (some upside, still sensitive to assumptions)")
        else:
            st.error(f"Margin of safety: {_fmt_pct(mos)} (little/no upside under these assumptions)")

    st.markdown("**Sensitivity (intrinsic per share)**")
    dr_grid = [discount_rate - 0.02, discount_rate - 0.01, discount_rate, discount_rate + 0.01, discount_rate + 0.02]
    dr_grid = [max(0.03, float(x)) for x in dr_grid]
    tg_grid = [max(0.0, terminal_growth - 0.01), terminal_growth, terminal_growth + 0.01]

    sens = dcf_sensitivity(base, dr_grid, tg_grid)
    # format nicely
    disp = sens.copy()
    for c in disp.columns:
        if c.startswith("g="):
            disp[c] = disp[c].apply(lambda v: "N/A" if (v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))) else f"{v:.2f}")
    disp["Discount Rate"] = disp["Discount Rate"].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.markdown("**Buffett-style quick verdict (rubric)**")
    st.write("- Foco em qualidade (ROE, margens), previsibilidade, e preço com margem de segurança.")
    with st.expander("Scorecard details"):
        st.write("\n".join([f"- {n}" for n in score_notes]))

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 5) SCREENER (mini-universe)
# -------------------------
with tab_screen:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Screener (mini-universe via Yahoo)")

    universe = [t.strip().upper() for t in tickers_universe.split(",") if t.strip()]
    if not universe:
        st.info("Define um universo de tickers na sidebar.")
        st.stop()

    rows = []
    progress = st.progress(0)
    for i, tk in enumerate(universe):
        progress.progress(int((i + 1) / len(universe) * 100))
        inf = get_info(tk)
        r = _compute_ratios(inf)
        mcap_i = _safe_float(inf.get("marketCap"))
        dy = r.get("Dividend Yield", np.nan)
        pe = r.get("Trailing P/E", np.nan)

        passes = True
        if not math.isnan(dy):
            passes &= (dy * 100.0) >= float(min_div)
        else:
            passes &= (float(min_div) <= 0.0)  # if filter is 0, allow missing
        if not math.isnan(pe):
            passes &= pe <= float(max_pe)
        else:
            passes &= False  # require PE for PE filter
        if not math.isnan(mcap_i):
            passes &= (mcap_i / 1e9) >= float(min_mcap_b)
        else:
            passes &= False

        rows.append(
            {
                "Ticker": tk,
                "Name": inf.get("shortName", ""),
                "MarketCap($B)": (mcap_i / 1e9) if not math.isnan(mcap_i) else np.nan,
                "P/E": pe,
                "DivYield%": (dy * 100.0) if not math.isnan(dy) else np.nan,
                "ROE%": (r.get("ROE") * 100.0) if not math.isnan(r.get("ROE", np.nan)) else np.nan,
                "OpMargin%": (r.get("Operating Margin") * 100.0) if not math.isnan(r.get("Operating Margin", np.nan)) else np.nan,
                "Passes": passes,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Sem resultados.")
    else:
        df_sorted = df.sort_values(["Passes", "MarketCap($B)"], ascending=[False, False])
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 6) WATCHLIST & ALERTS
# -------------------------
with tab_watch:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Watchlist & Alerts")

    watch = [t.strip().upper() for t in watchlist_str.split(",") if t.strip()]
    if not watch:
        st.info("Define uma watchlist na sidebar.")
        st.stop()

    rows = []
    for tk in watch:
        p = get_price_history(tk, period="1y", interval="1d")
        if p.empty:
            rows.append({"Ticker": tk, "Status": "No data"})
            continue
        last = float(p["Close"].iloc[-1])
        high_52w = float(p["High"].max())
        dd = (last / high_52w - 1.0) if high_52w else np.nan
        alert = (dd <= -(drop_threshold / 100.0)) if not math.isnan(dd) else False
        rows.append(
            {
                "Ticker": tk,
                "Last": last,
                "52W High": high_52w,
                "Drawdown%": dd * 100.0 if not math.isnan(dd) else np.nan,
                "Alert": alert,
            }
        )

    wdf = pd.DataFrame(rows)
    if not wdf.empty and "Alert" in wdf.columns:
        alerts = wdf[wdf["Alert"] == True].copy()
        if not alerts.empty:
            st.error(f"Alerts: {len(alerts)} tickers abaixo de {drop_threshold}% do máximo 52W")
            st.dataframe(alerts.sort_values("Drawdown%"), use_container_width=True, hide_index=True)
        else:
            st.success("Sem alerts na watchlist (com o threshold atual).")

    st.markdown("**Watchlist table**")
    st.dataframe(wdf, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 7) REPORT
# -------------------------
with tab_report:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("One-page Report (export)")

    long_name = info.get("longName") or info.get("shortName") or ticker
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")

    report_md = f"""# SMAI Report — {ticker}

**Company:** {long_name}  
**Sector/Industry:** {sector} / {industry}  
**Last:** {last_close:.2f} {currency}  ({_fmt_pct(day_chg)})

## Snapshot
- Market cap: {_fmt_num(mcap)}
- Trailing P/E: {"N/A" if math.isnan(ratios["Trailing P/E"]) else f"{ratios['Trailing P/E']:.2f}"}
- ROE: {_fmt_pct(ratios.get("ROE", np.nan))}
- Operating margin: {_fmt_pct(ratios.get("Operating Margin", np.nan))}
- Dividend yield: {_fmt_pct(ratios.get("Dividend Yield", np.nan))}
- Scorecard: {score}/100

## Quick thesis (fill)
- Bull case:
- Bear case:
- Key risks:
- Catalysts:

## Buffett (DCF) — current assumptions
- Projection years: {years}
- FCF growth: {fcf_growth:.2%}
- Discount rate: {discount_rate:.2%}
- Terminal growth: {terminal_growth:.2%}
- Intrinsic / share: {"N/A" if math.isnan(intrinsic) else f"{intrinsic:.2f} {currency}"}
- Margin of safety vs price: {"N/A" if math.isnan(mos) else _fmt_pct(mos)}
"""

    st.text_area("Report (Markdown)", value=report_md, height=360)
    st.download_button("Download report.md", data=report_md.encode("utf-8"), file_name=f"SMAI_{ticker}_report.md", mime="text/markdown")

    st.markdown("</div>", unsafe_allow_html=True)
