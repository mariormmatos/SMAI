# SMAI.py
# Stock Market Analysis & Insights (SMAI)
# Streamlit app inspired by forecast.biz look & feel
#
# Data sources:
# - Prices, company info, financial statements, basic news: Yahoo Finance via yfinance
# - Sentiment: Stocktwits + Reddit (public JSON)
# - Buffett module: Discounted Cash Flow (DCF)
#
# Notes:
# - Yahoo Finance data coverage varies by ticker/region.
# - This app is for research/education, not investment advice.

from __future__ import annotations

import math
import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# ============================================================
# APP CONFIG + THEME (forecast.biz-inspired)
# ============================================================

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
  --shadow: 0 10px 26px rgba(10,20,35,0.07);
  --shadow2: 0 6px 18px rgba(10,20,35,0.06);
  --radius: 16px;
  --radius2: 20px;
}

html, body, [class*="css"]{
  color: var(--text);
  background: var(--bg);
}

.block-container { padding-top: 1.1rem; padding-bottom: 2rem; }

.smai-hero{
  background: linear-gradient(135deg, rgba(10,20,35,0.06), rgba(10,20,35,0.015));
  border: 1px solid var(--stroke);
  border-radius: var(--radius2);
  padding: 14px 16px;
  box-shadow: var(--shadow);
}

.smai-card{
  background: var(--card);
  border: 1px solid var(--stroke);
  border-radius: var(--radius2);
  padding: 14px 14px;
  box-shadow: var(--shadow2);
}

.smai-subtle{ color: var(--muted); font-size: 0.92rem; }

.smai-pill{
  display:inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.75);
  font-size: 0.85rem;
  color: rgba(10,20,35,0.78);
}

.smai-kbd{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.82rem;
  padding: 2px 7px;
  border-radius: 8px;
  border: 1px solid var(--stroke);
  background: rgba(10,20,35,0.03);
}

div[data-testid="stMetric"]{
  background: var(--card);
  border: 1px solid var(--stroke);
  border-radius: 16px;
  padding: 12px 12px;
  box-shadow: var(--shadow2);
}

section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.93));
  border-right: 1px solid var(--stroke);
}

.stTabs [data-baseweb="tab-list"]{ gap: 8px; }
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

# ============================================================
# CONSTANTS
# ============================================================

# Timeframes for *price/technicals/sentiment* (intraday where useful)
PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "10Y": ("10y", "1mo"),
}

# Financial statements are not "1D/1M". We'll "slice last N points" for display.
STAT_POINTS_MAP = {"1Y": 4, "5Y": 5, "10Y": 10}

# Common statement row labels used by yfinance (may vary by ticker)
INCOME_ROWS = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Diluted EPS"]
CASHFLOW_ROWS = ["Total Cash From Operating Activities", "Capital Expenditures", "Free Cash Flow"]
BALANCE_ROWS = ["Total Assets", "Total Liab", "Total Stockholder Equity", "Cash", "Long Term Debt"]

# ============================================================
# UTILS
# ============================================================

@dataclass
class DcfInputs:
    years: int
    fcf_growth: float
    discount_rate: float
    terminal_growth: float
    net_debt: float               # debt - cash
    shares_outstanding: float
    starting_fcf: float

def _safe_float(x, default=np.nan) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def _is_bad(x: float) -> bool:
    return x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))

def _fmt_num(x: float) -> str:
    if _is_bad(x):
        return "N/A"
    ax = abs(float(x))
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
    if _is_bad(x):
        return "N/A"
    return f"{x*100:.{digits}f}%"

def _coerce_dt_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=False)

def _ensure_date_col(df: pd.DataFrame, idx_name: str = "Date") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if idx_name not in out.columns:
        if isinstance(out.index, pd.DatetimeIndex):
            out.insert(0, idx_name, out.index)
        else:
            out = out.reset_index()
            if "index" in out.columns:
                out.rename(columns={"index": idx_name}, inplace=True)
    out[idx_name] = pd.to_datetime(out[idx_name], errors="coerce")
    out = out.dropna(subset=[idx_name])
    return out

# ============================================================
# CHARTS (forecast.biz-like filled areas)
# ============================================================

def _plot_area(
    df: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    title: str,
    yaxis_title: str = "",
    percent: bool = False,
):
    df = df.copy()
    if df is None or df.empty:
        st.info("Sem dados para gráfico.")
        return

    # For percent charts, keep as is; caller pre-converts.
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
        yaxis=dict(
            title=yaxis_title,
            showgrid=True,
            gridcolor="rgba(10,20,35,0.08)",
            tickformat=".0f" if not percent else ".1f",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

def _plot_candles(df: pd.DataFrame, title: str, currency: str):
    if df is None or df.empty:
        st.info("Sem dados para gráfico.")
        return
    fig = go.Figure(
        data=[go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        )]
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=48, b=10),
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(title=f"Price ({currency})", showgrid=True, gridcolor="rgba(10,20,35,0.08)"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# DATA ACCESS (Yahoo Finance)
# ============================================================

@st.cache_data(ttl=60 * 20, show_spinner=False)
def yf_price_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    return df

@st.cache_data(ttl=60 * 60, show_spinner=False)
def yf_info(ticker: str) -> Dict:
    t = yf.Ticker(ticker)
    try:
        return t.info or {}
    except Exception:
        return {}

@st.cache_data(ttl=60 * 60, show_spinner=False)
def yf_statements(ticker: str) -> Dict[str, pd.DataFrame]:
    t = yf.Ticker(ticker)
    out: Dict[str, pd.DataFrame] = {}
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

@st.cache_data(ttl=60 * 30, show_spinner=False)
def yf_news(ticker: str) -> List[Dict]:
    """
    yfinance returns a list with keys like: title, publisher, link, providerPublishTime, type
    """
    t = yf.Ticker(ticker)
    try:
        news = t.news or []
        if not isinstance(news, list):
            return []
        return news[:30]
    except Exception:
        return []

def _statement_to_timeseries(stmt: pd.DataFrame, rows: List[str]) -> pd.DataFrame:
    """
    yfinance statements: index = line items, columns = dates
    Transpose -> Date + selected rows as columns.
    """
    if stmt is None or stmt.empty:
        return pd.DataFrame()
    s = stmt.copy()
    try:
        s.columns = pd.to_datetime(s.columns)
    except Exception:
        pass
    s = s.T.sort_index()
    keep = [r for r in rows if r in s.columns]
    if not keep:
        return pd.DataFrame()
    df = s[keep].copy()
    df.insert(0, "Date", df.index)
    df.reset_index(drop=True, inplace=True)
    return df

# ============================================================
# FUNDAMENTAL METRICS / SCORECARD
# ============================================================

def _compute_snapshot_ratios(info: Dict) -> Dict[str, float]:
    return {
        "Trailing P/E": _safe_float(info.get("trailingPE")),
        "Forward P/E": _safe_float(info.get("forwardPE")),
        "P/B": _safe_float(info.get("priceToBook")),
        "P/S (TTM)": _safe_float(info.get("priceToSalesTrailing12Months")),
        "EV/EBITDA": _safe_float(info.get("enterpriseToEbitda")),
        "ROE": _safe_float(info.get("returnOnEquity")),
        "ROA": _safe_float(info.get("returnOnAssets")),
        "Profit Margin": _safe_float(info.get("profitMargins")),
        "Operating Margin": _safe_float(info.get("operatingMargins")),
        "Dividend Yield": _safe_float(info.get("dividendYield")),
        "Payout Ratio": _safe_float(info.get("payoutRatio")),
        "Beta": _safe_float(info.get("beta")),
        "Debt/Equity": _safe_float(info.get("debtToEquity")),
    }

def _scorecard(r: Dict[str, float]) -> Tuple[int, List[str]]:
    """
    Deterministic rubric (0-100). Not a recommendation—just a consistent diagnostic.
    """
    score = 0
    notes: List[str] = []

    pe = r.get("Trailing P/E", np.nan)
    ps = r.get("P/S (TTM)", np.nan)
    pb = r.get("P/B", np.nan)

    if not _is_bad(pe):
        if pe <= 15:
            score += 18; notes.append("Valuation: P/E <= 15 (+18)")
        elif pe <= 25:
            score += 10; notes.append("Valuation: 15 < P/E <= 25 (+10)")
        else:
            score += 3; notes.append("Valuation: P/E > 25 (+3)")
    else:
        notes.append("Valuation: P/E N/A (+0)")

    if not _is_bad(ps):
        if ps <= 3:
            score += 10; notes.append("Valuation: P/S <= 3 (+10)")
        elif ps <= 7:
            score += 6; notes.append("Valuation: 3 < P/S <= 7 (+6)")
        else:
            score += 2; notes.append("Valuation: P/S > 7 (+2)")
    else:
        notes.append("Valuation: P/S N/A (+0)")

    if not _is_bad(pb):
        if pb <= 2:
            score += 6; notes.append("Balance/Valuation: P/B <= 2 (+6)")
        elif pb <= 5:
            score += 4; notes.append("Balance/Valuation: 2 < P/B <= 5 (+4)")
        else:
            score += 1; notes.append("Balance/Valuation: P/B > 5 (+1)")
    else:
        notes.append("Balance/Valuation: P/B N/A (+0)")

    roe = r.get("ROE", np.nan)
    opm = r.get("Operating Margin", np.nan)

    if not _is_bad(roe):
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

    if not _is_bad(opm):
        if opm >= 0.25:
            score += 14; notes.append("Quality: Operating margin >= 25% (+14)")
        elif opm >= 0.12:
            score += 9; notes.append("Quality: 12% <= operating margin < 25% (+9)")
        elif opm >= 0.05:
            score += 5; notes.append("Quality: 5% <= operating margin < 12% (+5)")
        else:
            score += 1; notes.append("Quality: operating margin < 5% (+1)")
    else:
        notes.append("Quality: operating margin N/A (+0)")

    beta = r.get("Beta", np.nan)
    if not _is_bad(beta):
        if beta <= 1.0:
            score += 10; notes.append("Risk: beta <= 1.0 (+10)")
        elif beta <= 1.5:
            score += 6; notes.append("Risk: 1.0 < beta <= 1.5 (+6)")
        else:
            score += 2; notes.append("Risk: beta > 1.5 (+2)")
    else:
        notes.append("Risk: beta N/A (+0)")

    dy = r.get("Dividend Yield", np.nan)
    if not _is_bad(dy):
        if dy >= 0.03:
            score += 8; notes.append("Shareholder return: dividend yield >= 3% (+8)")
        elif dy >= 0.015:
            score += 5; notes.append("Shareholder return: 1.5%–3% (+5)")
        elif dy > 0:
            score += 2; notes.append("Shareholder return: < 1.5% (+2)")
        else:
            score += 0; notes.append("Shareholder return: no dividend (+0)")
    else:
        notes.append("Shareholder return: dividend yield N/A (+0)")

    score = max(0, min(100, score))
    return score, notes

# ============================================================
# SENTIMENT (Stocktwits + Reddit public JSON)
# ============================================================

POS_WORDS = {
    "beat", "beats", "strong", "upside", "bull", "bullish", "growth", "buy", "accumulate",
    "undervalued", "record", "profit", "surge", "upgrade", "outperform"
}
NEG_WORDS = {
    "miss", "missed", "weak", "downside", "bear", "bearish", "sell", "overvalued", "fraud",
    "drop", "plunge", "lawsuit", "warning", "downgrade", "underperform"
}

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
def fetch_stocktwits(ticker: str, limit: int = 40) -> pd.DataFrame:
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()
        j = r.json()
        msgs = (j.get("messages") or [])[:limit]
        rows = []
        for m in msgs:
            body = m.get("body", "")
            created = m.get("created_at", "")
            user = (m.get("user") or {}).get("username", "")
            rows.append({
                "source": "stocktwits",
                "created_at": created,
                "user": user,
                "text": body,
                "sentiment": _lex_sentiment(body),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60 * 20, show_spinner=False)
def fetch_reddit_search(query: str, limit: int = 40) -> pd.DataFrame:
    """
    Public Reddit search endpoint (no auth). Rate-limits can happen; keep small & cached.
    """
    url = "https://www.reddit.com/search.json"
    headers = {"User-Agent": "SMAI/1.0 (Streamlit; personal analysis app)"}
    params = {"q": query, "sort": "new", "limit": min(limit, 50), "t": "week"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        if r.status_code != 200:
            return pd.DataFrame()
        j = r.json()
        children = (((j.get("data") or {}).get("children")) or [])[:limit]
        rows = []
        for c in children:
            d = c.get("data") or {}
            title = d.get("title", "")
            created_utc = d.get("created_utc")
            created_at = dt.datetime.utcfromtimestamp(created_utc).isoformat() if created_utc else ""
            rows.append({
                "source": "reddit",
                "created_at": created_at,
                "user": d.get("author", ""),
                "subreddit": d.get("subreddit", ""),
                "text": title,
                "sentiment": _lex_sentiment(title + " " + (d.get("selftext") or "")),
                "permalink": "https://www.reddit.com" + (d.get("permalink") or ""),
            })
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

# ============================================================
# BUFFETT (DCF)
# ============================================================

def run_dcf(inp: DcfInputs) -> Dict[str, float]:
    """
    Single-stage FCF projection with terminal value (Gordon Growth).
    Returns enterprise value, equity value, intrinsic per share.
    """
    fcf0 = max(0.0, float(inp.starting_fcf))
    years = int(inp.years)

    fcfs = [fcf0 * ((1.0 + inp.fcf_growth) ** y) for y in range(1, years + 1)]
    dfs = [(1.0 / ((1.0 + inp.discount_rate) ** y)) for y in range(1, years + 1)]
    pv_fcfs = float(sum(f * d for f, d in zip(fcfs, dfs)))

    g = float(inp.terminal_growth)
    r = float(inp.discount_rate)
    fcf_n = fcfs[-1] if fcfs else fcf0
    terminal_value = 0.0 if r <= g else float((fcf_n * (1.0 + g)) / (r - g))
    pv_terminal = float(terminal_value * (dfs[-1] if dfs else 0.0))

    enterprise_value = pv_fcfs + pv_terminal
    equity_value = enterprise_value - float(inp.net_debt)
    intrinsic_per_share = (equity_value / float(inp.shares_outstanding)) if inp.shares_outstanding else np.nan

    return {
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_per_share": intrinsic_per_share,
        "pv_fcfs": pv_fcfs,
        "pv_terminal": pv_terminal,
    }

def dcf_sensitivity(base: DcfInputs, discount_rates: List[float], terminal_growths: List[float]) -> pd.DataFrame:
    rows = []
    for r in discount_rates:
        row = {"Discount Rate": r}
        for g in terminal_growths:
            out = run_dcf(DcfInputs(**{**base.__dict__, "discount_rate": float(r), "terminal_growth": float(g)}))
            row[f"g={g:.1%}"] = out["intrinsic_per_share"]
        rows.append(row)
    return pd.DataFrame(rows)

# ============================================================
# MODULE 2: NEWS (Yahoo Finance + RSS fallback)
# ============================================================

@st.cache_data(ttl=60 * 15, show_spinner=False)
def fetch_yahoo_markets_rss(limit: int = 20) -> List[Dict]:
    """
    Lightweight market headlines (no key). Yahoo Finance RSS.
    """
    rss_url = "https://finance.yahoo.com/news/rssindex"
    try:
        r = requests.get(rss_url, timeout=10)
        if r.status_code != 200:
            return []
        text = r.text
        # tiny XML parse (no extra deps): naive but effective for RSS
        items = text.split("<item>")[1:]
        out = []
        for it in items[:limit]:
            title = _between(it, "<title>", "</title>")
            link = _between(it, "<link>", "</link>")
            pub = _between(it, "<pubDate>", "</pubDate>")
            out.append({"title": _clean_xml(title), "link": _clean_xml(link), "published": _clean_xml(pub)})
        return out
    except Exception:
        return []

def _between(s: str, a: str, b: str) -> str:
    try:
        i = s.index(a) + len(a)
        j = s.index(b, i)
        return s[i:j]
    except Exception:
        return ""

def _clean_xml(s: str) -> str:
    return (s or "").replace("&amp;", "&").replace("&quot;", '"').replace("&apos;", "'").replace("&lt;", "<").replace("&gt;", ">").strip()

def _render_news_bullets(items: List[Dict], title_key: str = "title", link_key: str = "link"):
    if not items:
        st.info("Sem headlines disponíveis (ou rate-limit).")
        return
    for it in items:
        title = it.get(title_key) or ""
        link = it.get(link_key) or ""
        meta = it.get("publisher") or it.get("published") or ""
        if link:
            st.markdown(f"- [{title}]({link})  \n  <span class='smai-subtle'>{meta}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"- {title}  \n  <span class='smai-subtle'>{meta}</span>", unsafe_allow_html=True)

# ============================================================
# SIDEBAR (Global controls)
# ============================================================

st.markdown(
    """
<div class="smai-hero">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <div>
      <div style="font-size:1.2rem; font-weight:800;">SMAI — Stock Market Analysis & Insights</div>
      <div class="smai-subtle">Fundamentals • News • Screener • Technicals • Sentiment • Buffett (DCF)</div>
    </div>
    <div class="smai-pill">Streamlit • Yahoo Finance • v1</div>
  </div>
  <div class="smai-subtle" style="margin-top:8px;">
    Dica: escreve um ticker e usa <span class="smai-kbd">Enter</span>. Para Europa usa sufixos: <span class="smai-kbd">EOAN.DE</span>, <span class="smai-kbd">MC.PA</span>.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Inputs")

    ticker = st.text_input("Ticker", value="MSFT").strip().upper()
    timeframe = st.selectbox("Timeframe (charts)", list(PERIOD_MAP.keys()), index=5)
    period, interval = PERIOD_MAP[timeframe]

    st.divider()
    st.subheader("Fundamentals view")
    stmt_mode = st.radio("Statements frequency", ["Annual", "Quarterly"], horizontal=True)
    stmt_span = st.selectbox("Statements span (display)", ["10Y", "5Y", "1Y"], index=0)

    st.divider()
    st.subheader("Screener")
    st.caption("Por defeito usa um universo configurável. Para índices completos, carrega CSV com uma coluna Ticker.")
    screener_universe_choice = st.selectbox("Universe preset", ["Custom", "S&P500 (mini)", "Nasdaq-100 (mini)", "CAC40 (mini)", "Xetra DAX (mini)", "NSE NIFTY50 (mini)"], index=0)
    min_div = st.slider("Min Dividend Yield (%)", 0.0, 10.0, 2.0, 0.1)
    max_pe = st.slider("Max Trailing P/E", 5, 120, 25, 1)
    min_mcap_b = st.slider("Min Market Cap ($B)", 0, 2000, 10, 1)

    st.divider()
    st.subheader("Watchlist & alerts")
    watchlist_str = st.text_input("Watchlist tickers", value="NVO, PFE, NEE, EOAN.DE, ASML, NVDA, MSFT")
    drop_threshold = st.slider("Alert if drawdown from 52W High >=", 5, 60, 20, 1)

# ============================================================
# LOAD CORE DATA
# ============================================================

if not ticker:
    st.stop()

with st.spinner("Loading market data (Yahoo Finance)…"):
    info = yf_info(ticker)
    px = yf_price_history(ticker, period=period, interval=interval)
    stmts = yf_statements(ticker)

if px.empty:
    st.error("Sem dados de preço para este ticker (ou limite do Yahoo Finance). Confirma o ticker e tenta outro timeframe.")
    st.stop()

currency = info.get("currency", "")
last_close = float(px["Close"].iloc[-1])
prev_close = float(px["Close"].iloc[-2]) if len(px) > 1 else last_close
chg = (last_close / prev_close - 1.0) if prev_close else 0.0

mcap = _safe_float(info.get("marketCap"))
name = info.get("longName") or info.get("shortName") or ticker

ratios = _compute_snapshot_ratios(info)
score, score_notes = _scorecard(ratios)

# Top summary row
c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1, 1.2])
c1.metric("Last", f"{last_close:.2f} {currency}", _fmt_pct(chg))
c2.metric("Market Cap", _fmt_num(mcap))
c3.metric("Trailing P/E", "N/A" if _is_bad(ratios["Trailing P/E"]) else f"{ratios['Trailing P/E']:.2f}")
c4.metric("ROE", "N/A" if _is_bad(ratios["ROE"]) else _fmt_pct(ratios["ROE"]))
c5.metric("Scorecard", f"{score}/100")
st.write("")

# ============================================================
# MAIN MODULE TABS (each module = its own screen/tab)
# Module 1: Fundamental Analysis
# Module 2: Stock News & Summaries
# Module 3: Stock Screener
# (Extra tabs: Technical, Sentiment, Buffett, Watchlist, Report)
# ============================================================

tab_fund, tab_news, tab_screen, tab_tech, tab_sent, tab_buff, tab_watch, tab_report = st.tabs(
    [
        "1) Fundamental Analysis",
        "2) Stock News & Summaries",
        "3) Stock Screener",
        "4) Technical Analysis",
        "5) Sentiment",
        "6) Buffett (DCF)",
        "7) Watchlist & Alerts",
        "8) Report",
    ]
)

# ============================================================
# MODULE 1 — FUNDAMENTAL ANALYSIS
# ============================================================

with tab_fund:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader(f"Fundamental Analysis — {name} ({ticker})")
    st.caption("Fonte: Yahoo Finance (yfinance). A disponibilidade/labels podem variar por ticker.")

    # 5 areas as requested (first 2: charts, last 3: text)
    areas = st.tabs(
        [
            "1️⃣ Financial Statements Analysis",
            "2️⃣ Valuation Metrics",
            "3️⃣ Growth Potential & Competitive Positioning",
            "4️⃣ Risk Analysis",
            "5️⃣ Recent News & Catalysts",
        ]
    )

    # ---- Area 1: Financial Statements Analysis (charts, selectable span)
    with areas[0]:
        st.markdown("### Financial Statements Analysis (charts)")
        st.caption("Inclui: Revenue, profitability, EPS, debt levels (proxy), cash flow. Display por 'span' (10Y/5Y/1Y) e frequência (annual/quarterly).")

        if stmt_mode == "Annual":
            inc = stmts.get("financials", pd.DataFrame())
            cf = stmts.get("cashflow", pd.DataFrame())
            bs = stmts.get("balance_sheet", pd.DataFrame())
        else:
            inc = stmts.get("quarterly_financials", pd.DataFrame())
            cf = stmts.get("quarterly_cashflow", pd.DataFrame())
            bs = stmts.get("quarterly_balance_sheet", pd.DataFrame())

        n_points = STAT_POINTS_MAP.get(stmt_span, 10)

        # Income
        inc_ts = _statement_to_timeseries(inc, INCOME_ROWS)
        if inc_ts.empty:
            st.info("Sem Income Statement suficiente no Yahoo Finance para este ticker.")
        else:
            inc_ts = inc_ts.sort_values("Date").tail(n_points)
            _plot_area(
                inc_ts,
                "Date",
                [c for c in INCOME_ROWS if c in inc_ts.columns],
                title=f"Income Statement ({stmt_mode}, last {stmt_span})",
                yaxis_title=f"Amount ({currency})",
            )

        # Cash flow + Free Cash Flow (approx if needed)
        cf_ts = _statement_to_timeseries(cf, CASHFLOW_ROWS)
        if not cf_ts.empty and "Free Cash Flow" not in cf_ts.columns:
            if "Total Cash From Operating Activities" in cf_ts.columns and "Capital Expenditures" in cf_ts.columns:
                cf_ts["Free Cash Flow"] = cf_ts["Total Cash From Operating Activities"] + cf_ts["Capital Expenditures"]
        if cf_ts.empty:
            st.info("Sem Cash Flow suficiente no Yahoo Finance para este ticker.")
        else:
            cf_ts = cf_ts.sort_values("Date").tail(n_points)
            _plot_area(
                cf_ts,
                "Date",
                [c for c in ["Total Cash From Operating Activities", "Capital Expenditures", "Free Cash Flow"] if c in cf_ts.columns],
                title=f"Cash Flow ({stmt_mode}, last {stmt_span})",
                yaxis_title=f"Amount ({currency})",
            )

        # Balance sheet
        bs_ts = _statement_to_timeseries(bs, BALANCE_ROWS)
        if bs_ts.empty:
            st.info("Sem Balance Sheet suficiente no Yahoo Finance para este ticker.")
        else:
            bs_ts = bs_ts.sort_values("Date").tail(n_points)
            _plot_area(
                bs_ts,
                "Date",
                [c for c in BALANCE_ROWS if c in bs_ts.columns],
                title=f"Balance Sheet ({stmt_mode}, last {stmt_span})",
                yaxis_title=f"Amount ({currency})",
            )

        # Derived "Debt levels" proxy (Debt/Equity) from snapshot (not historical)
        st.markdown("### Debt & Liquidity (snapshot)")
        cA, cB, cC, cD = st.columns(4)
        cA.metric("Debt/Equity", "N/A" if _is_bad(ratios.get("Debt/Equity")) else f"{ratios['Debt/Equity']:.2f}")
        cB.metric("Total Debt", _fmt_num(_safe_float(info.get("totalDebt"))))
        cC.metric("Total Cash", _fmt_num(_safe_float(info.get("totalCash"))))
        nd = _safe_float(info.get("totalDebt")) - _safe_float(info.get("totalCash"))
        cD.metric("Net Debt", _fmt_num(nd))

    # ---- Area 2: Valuation Metrics (charts)
    with areas[1]:
        st.markdown("### Valuation Metrics (charts)")
        st.caption("Como o Yahoo não fornece séries históricas completas de múltiplos, aqui combinamos: preço (série) + snapshot de múltiplos e alguns proxies com base em statements anuais.")

        # Price (filled area) per selected timeframe (1D..10Y)
        px2 = _ensure_date_col(px.reset_index().rename(columns={"index": "Date"}), "Date")
        px2 = px2[["Date", "Close"]].dropna()
        _plot_area(px2, "Date", ["Close"], title=f"{ticker} price ({timeframe})", yaxis_title=f"Price ({currency})")

        # Build profitability margins series from annual income statement
        income_annual = stmts.get("financials", pd.DataFrame())
        inc_ts = _statement_to_timeseries(income_annual, ["Total Revenue", "Net Income", "Operating Income", "Diluted EPS"])
        if inc_ts.empty:
            st.info("Sem dados anuais suficientes para séries de margens/EPS.")
        else:
            inc_ts = inc_ts.sort_values("Date").tail(STAT_POINTS_MAP.get(stmt_span, 10))
            vdf = inc_ts[["Date"]].copy()
            if "Operating Income" in inc_ts.columns and "Total Revenue" in inc_ts.columns:
                vdf["Operating Margin %"] = (inc_ts["Operating Income"] / inc_ts["Total Revenue"]) * 100.0
            if "Net Income" in inc_ts.columns and "Total Revenue" in inc_ts.columns:
                vdf["Net Margin %"] = (inc_ts["Net Income"] / inc_ts["Total Revenue"]) * 100.0
            if "Diluted EPS" in inc_ts.columns:
                vdf["EPS"] = inc_ts["Diluted EPS"]

            cols = [c for c in ["Operating Margin %", "Net Margin %"] if c in vdf.columns]
            if cols:
                _plot_area(vdf, "Date", cols, title="Profitability margins (annual)", yaxis_title="%", percent=True)

            if "EPS" in vdf.columns:
                _plot_area(vdf, "Date", ["EPS"], title="Diluted EPS (annual)", yaxis_title=f"EPS ({currency})")

        # Snapshot multiples
        st.markdown("### Valuation Snapshot (Yahoo info)")
        snap = [
            ("Trailing P/E", "N/A" if _is_bad(ratios["Trailing P/E"]) else f"{ratios['Trailing P/E']:.2f}"),
            ("Forward P/E", "N/A" if _is_bad(ratios["Forward P/E"]) else f"{ratios['Forward P/E']:.2f}"),
            ("P/B", "N/A" if _is_bad(ratios["P/B"]) else f"{ratios['P/B']:.2f}"),
            ("P/S (TTM)", "N/A" if _is_bad(ratios["P/S (TTM)"]) else f"{ratios['P/S (TTM)']:.2f}"),
            ("EV/EBITDA", "N/A" if _is_bad(ratios["EV/EBITDA"]) else f"{ratios['EV/EBITDA']:.2f}"),
            ("Dividend Yield", _fmt_pct(ratios.get("Dividend Yield", np.nan))),
        ]
        st.dataframe(pd.DataFrame(snap, columns=["Metric", "Value"]), use_container_width=True, hide_index=True)

    # ---- Area 3: Growth Potential & Competitive Positioning (text)
    with areas[2]:
        st.markdown("### Growth Potential & Competitive Positioning")
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        summary = (info.get("longBusinessSummary") or "").strip()

        st.markdown("**Sector / Industry**")
        st.write(f"{sector} / {industry}")

        if summary:
            st.markdown("**Business summary (Yahoo)**")
            st.write(summary)
        else:
            st.info("Sem descrição disponível no Yahoo para este ticker.")

        st.markdown("**Framework (preenche com a tua análise)**")
        st.write(
            """
- **Industry trends**: drivers estruturais, ciclo, regulação, TAM.
- **Competitive advantage**: custo, marca, switching costs, network effects, eficiência de escala.
- **Innovation & R&D**: ritmo de lançamento, intensidade de capex/R&D, patentes, moat tecnológico.
- **Management & leadership**: track record, capital allocation, incentivos, consistência de guidance.
"""
        )

        st.markdown("**Quick numeric hints**")
        st.write(f"- **Revenue (TTM, proxy)**: {_fmt_num(_safe_float(info.get('totalRevenue')))}")
        st.write(f"- **Operating margin (snapshot)**: {_fmt_pct(ratios.get('Operating Margin', np.nan))}")
        st.write(f"- **ROE (snapshot)**: {_fmt_pct(ratios.get('ROE', np.nan))}")

        st.markdown("**Your notes (session)**")
        st.text_area("Pontos sobre crescimento/competição", height=160)

    # ---- Area 4: Risk Analysis (text)
    with areas[3]:
        st.markdown("### Risk Analysis")
        st.write(
            """
**Checklist** (exemplos):
- **Market risks**: taxa de juro, inflação, recessão, FX, commodity exposure, geopolítica.
- **Operational risks**: supply chain, litigância, regulação setorial, dependência de fornecedores.
- **Debt & liquidity**: maturidades, covenants, refinanciamento, custo médio da dívida.
- **Valuation risk**: múltiplos exigentes + compressão se o crescimento desacelerar.
"""
        )

        # Snapshot risk signals
        st.markdown("**Snapshot signals (Yahoo info)**")
        st.write(f"- **Beta**: {'N/A' if _is_bad(ratios.get('Beta')) else f'{ratios['Beta']:.2f}'}")
        st.write(f"- **Debt/Equity**: {'N/A' if _is_bad(ratios.get('Debt/Equity')) else f'{ratios['Debt/Equity']:.2f}'}")
        st.write(f"- **52W range**: {info.get('fiftyTwoWeekLow','N/A')} → {info.get('fiftyTwoWeekHigh','N/A')} {currency}")
        st.write(f"- **Recommendation mean (Yahoo)**: {info.get('recommendationMean','N/A')} (quanto menor, mais bullish)")

        st.markdown("**Your risk notes (session)**")
        st.text_area("Riscos específicos (tese bearish)", height=170)

    # ---- Area 5: Recent News & Catalysts (text)
    with areas[4]:
        st.markdown("### Recent News & Catalysts")
        st.caption("Este bloco puxa notícias via yfinance (quando disponível). Para contexto global do mercado, usa o módulo 2.")

        news = yf_news(ticker)
        if not news:
            st.info("Sem notícias via Yahoo Finance para este ticker (pode acontecer em alguns tickers).")
        else:
            items = []
            for n in news[:12]:
                ts = n.get("providerPublishTime")
                published = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC") if ts else ""
                items.append({
                    "title": n.get("title", ""),
                    "publisher": n.get("publisher", ""),
                    "link": n.get("link", ""),
                    "published": published,
                    "type": n.get("type", ""),
                })
            _render_news_bullets(items, title_key="title", link_key="link")

        st.markdown("**Catalysts (framework)**")
        st.write(
            """
- Earnings beat/miss e guidance
- M&A / parcerias
- Novos produtos/lançamentos
- Mudanças regulatórias
- Re-rating de múltiplos (juros a cair/subir, risk-on/off)
"""
        )
        st.text_area("Catalysts que estás a monitorizar", height=140)

    # Buffett conclusion inside module 1 (as requested)
    st.divider()
    st.markdown("## 🔍 If you were Warren Buffett, would you invest in this stock?")
    st.caption("Este é um framework + alguns sinais automáticos. A decisão final é tua.")

    buff_cols = st.columns([1, 1, 1, 1])
    buff_cols[0].metric("Quality (ROE)", _fmt_pct(ratios.get("ROE", np.nan)))
    buff_cols[1].metric("Operating Margin", _fmt_pct(ratios.get("Operating Margin", np.nan)))
    buff_cols[2].metric("Valuation (P/E)", "N/A" if _is_bad(ratios.get("Trailing P/E")) else f"{ratios['Trailing P/E']:.2f}")
    buff_cols[3].metric("Scorecard", f"{score}/100")

    with st.expander("Rubric details (how scorecard was computed)"):
        st.write("\n".join([f"- {n}" for n in score_notes]))

    st.text_area("A tua conclusão (estilo Buffett): moat, previsibilidade, gestão, preço e margem de segurança.", height=160)

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# MODULE 2 — STOCK NEWS & SUMMARIES
# ============================================================

with tab_news:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Stock News & Summaries")

    n1, n2 = st.tabs(["📢 Market news (US/EU)", f"📌 {ticker} news"])

    with n1:
        st.markdown("### Latest market headlines (Yahoo Finance RSS)")
        st.caption("Bullets com link. Se falhar, é normalmente rate-limit ou bloqueio temporário.")
        items = fetch_yahoo_markets_rss(limit=18)
        _render_news_bullets(items)

    with n2:
        st.markdown(f"### Latest news for {ticker} (Yahoo Finance via yfinance)")
        items = []
        for n in yf_news(ticker)[:18]:
            ts = n.get("providerPublishTime")
            published = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC") if ts else ""
            items.append({
                "title": n.get("title", ""),
                "publisher": n.get("publisher", ""),
                "link": n.get("link", ""),
                "published": published,
            })
        _render_news_bullets(items)

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# MODULE 3 — STOCK SCREENER
# ============================================================

def _preset_universe(choice: str) -> List[str]:
    presets = {
        "S&P500 (mini)": ["MSFT","AAPL","NVDA","AMZN","GOOGL","META","BRK-B","JPM","UNH","XOM","LLY","AVGO","TSLA","V","MA","PG","COST","HD","KO","PEP"],
        "Nasdaq-100 (mini)": ["MSFT","AAPL","NVDA","AMZN","GOOGL","META","AVGO","AMD","ADBE","CSCO","NFLX","INTC","QCOM","TXN","AMAT","BKNG","PYPL","PEP","COST","INTU"],
        "CAC40 (mini)": ["MC.PA","OR.PA","TTE.PA","AI.PA","SAN.PA","BNP.PA","DG.PA","KER.PA","CAP.PA","SU.PA","RI.PA","ACA.PA"],
        "Xetra DAX (mini)": ["SAP.DE","SIE.DE","AIR.DE","ALV.DE","BAS.DE","BAYN.DE","BMW.DE","DBK.DE","ADS.DE","VOW3.DE","DTE.DE","MUV2.DE"],
        "NSE NIFTY50 (mini)": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","HINDUNILVR.NS","ITC.NS","LT.NS","SBIN.NS","BHARTIARTL.NS"],
    }
    return presets.get(choice, [])

def _load_universe_from_upload(uploaded) -> List[str]:
    if uploaded is None:
        return []
    try:
        dfu = pd.read_csv(uploaded)
        cols = [c for c in dfu.columns if c.lower() in {"ticker","symbol"}]
        if not cols:
            return []
        return [str(x).strip().upper() for x in dfu[cols[0]].dropna().tolist()]
    except Exception:
        return []

def _valuation_screen_row(tk: str) -> Dict:
    inf = yf_info(tk)
    r = _compute_snapshot_ratios(inf)
    mcap_i = _safe_float(inf.get("marketCap"))
    score_i, _ = _scorecard(r)
    return {
        "Ticker": tk,
        "Name": inf.get("shortName", ""),
        "MarketCap($B)": (mcap_i / 1e9) if not _is_bad(mcap_i) else np.nan,
        "P/E": r.get("Trailing P/E", np.nan),
        "P/B": r.get("P/B", np.nan),
        "EV/EBITDA": r.get("EV/EBITDA", np.nan),
        "DivYield%": (r.get("Dividend Yield", np.nan) * 100.0) if not _is_bad(r.get("Dividend Yield", np.nan)) else np.nan,
        "ROE%": (r.get("ROE", np.nan) * 100.0) if not _is_bad(r.get("ROE", np.nan)) else np.nan,
        "Debt/Equity": r.get("Debt/Equity", np.nan),
        "Scorecard": score_i,
    }

def _passes_filters(row: Dict, min_div_y: float, max_pe_v: float, min_mcap: float) -> bool:
    # Dividend yield
    dy = row.get("DivYield%")
    pe = row.get("P/E")
    mcapb = row.get("MarketCap($B)")
    ok = True
    if dy is not None and not _is_bad(float(dy)):
        ok &= float(dy) >= float(min_div_y)
    else:
        ok &= (float(min_div_y) <= 0.0)
    if pe is not None and not _is_bad(float(pe)):
        ok &= float(pe) <= float(max_pe_v)
    else:
        ok &= False
    if mcapb is not None and not _is_bad(float(mcapb)):
        ok &= float(mcapb) >= float(min_mcap)
    else:
        ok &= False
    return bool(ok)

with tab_screen:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Stock Screener — Undervalued candidates (fundamental filters)")

    colU, colV = st.columns([1.2, 1])
    with colU:
        uploaded = st.file_uploader("Upload universe CSV (col: Ticker or Symbol)", type=["csv"])
        custom_universe = st.text_area(
            "Universe tickers (comma-separated) — used when preset=Custom and no CSV",
            value="MSFT, NVDA, AAPL, GOOGL, AMZN, META, TSLA, NVO, PFE, NEE, EOAN.DE, ASML, AVGO, AMD, JPM, XOM, MC.PA, OR.PA, SAP.DE, SIE.DE",
            height=90,
        )
    with colV:
        st.markdown("### Discussion links (retail investors)")
        st.caption("Links rápidos para contexto (não são dados 'limpos').")
        st.markdown(f"- Reddit search: https://www.reddit.com/search/?q={ticker}")
        st.markdown(f"- Stocktwits: https://stocktwits.com/symbol/{ticker}")
        st.markdown(f"- ValuePickr: https://forum.valuepickr.com/search?q={ticker}")

    if uploaded is not None:
        universe = _load_universe_from_upload(uploaded)
        source_lbl = "CSV"
    else:
        if screener_universe_choice != "Custom":
            universe = _preset_universe(screener_universe_choice)
            source_lbl = screener_universe_choice
        else:
            universe = [t.strip().upper() for t in custom_universe.split(",") if t.strip()]
            source_lbl = "Custom"

    if not universe:
        st.info("Define um universo (preset, CSV ou custom tickers).")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    st.caption(f"Universe source: **{source_lbl}** • Tickers: {len(universe)}")

    rows = []
    progress = st.progress(0)
    for i, tk in enumerate(universe):
        progress.progress(int((i + 1) / len(universe) * 100))
        try:
            row = _valuation_screen_row(tk)
            row["Passes"] = _passes_filters(row, min_div, max_pe, min_mcap_b)
            rows.append(row)
        except Exception:
            rows.append({"Ticker": tk, "Passes": False})

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Sem resultados.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # Rank: passes first, then higher scorecard, then larger market cap
    df_sorted = df.sort_values(["Passes", "Scorecard", "MarketCap($B)"], ascending=[False, False, False])

    st.markdown("### Results")
    st.dataframe(df_sorted, use_container_width=True, hide_index=True)

    st.markdown("### Top picks — with sentiment quick check")
    top = df_sorted[df_sorted["Passes"] == True].head(8)
    if top.empty:
        st.info("Nenhum ticker passou os filtros atuais.")
    else:
        pick = st.selectbox("Select a candidate", top["Ticker"].tolist(), index=0)
        st.write("**Recent retail sentiment (quick heuristic)**")
        stt = fetch_stocktwits(pick, limit=30)
        rdd = fetch_reddit_search(pick, limit=30)
        all_s = pd.concat([stt, rdd], ignore_index=True)
        ssum = sentiment_summary(all_s) if not all_s.empty else {"count": 0, "avg": 0.0, "pos_share": 0.0, "neg_share": 0.0}
        a, b, c = st.columns(3)
        a.metric("Posts/messages", int(ssum["count"]))
        b.metric("Avg sentiment", f"{ssum['avg']:+.3f}")
        c.metric("Neg share", f"{ssum['neg_share']*100:.1f}%")

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# EXTRA TAB — TECHNICAL ANALYSIS
# ============================================================

with tab_tech:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Technical Analysis")
    t_tabs = st.tabs(["Price (candles)", "Indicators", "Levels & Volatility"])

    with t_tabs[0]:
        _plot_candles(px, f"{ticker} candlestick ({timeframe})", currency)

    with t_tabs[1]:
        df = px.copy()
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()

        # RSI 14
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
        rsi_df = _ensure_date_col(rsi_df, "Date")
        _plot_area(rsi_df, "Date", ["RSI14"], title="RSI(14)", yaxis_title="RSI")

    with t_tabs[2]:
        df = px.copy()
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

        win = st.slider("Level window (days)", 20, 260, 60, 10)
        df2 = df.copy()
        df2["Rolling Low"] = df2["Low"].rolling(win).min()
        df2["Rolling High"] = df2["High"].rolling(win).max()
        lvl_df = _ensure_date_col(df2.reset_index().rename(columns={"index": "Date"}), "Date")
        _plot_area(lvl_df, "Date", ["Rolling Low", "Rolling High"], title=f"Rolling support/resistance proxy ({win}d)", yaxis_title=f"Price ({currency})")

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# EXTRA TAB — SENTIMENT
# ============================================================

with tab_sent:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Sentiment — Reddit & Stocktwits")
    st.caption("Heurística simples (lexicon). Para produção, troca por VADER/FinBERT.")

    colA, colB = st.columns([1, 1])
    with colA:
        st.markdown("**Stocktwits**")
        st_df = fetch_stocktwits(ticker, limit=50)
        st_sum = sentiment_summary(st_df)
        st.metric("Messages", int(st_sum["count"]))
        st.metric("Avg sentiment", f"{st_sum['avg']:+.3f}")
        st.metric("Positive share", f"{st_sum['pos_share']*100:.1f}%")
        st.metric("Negative share", f"{st_sum['neg_share']*100:.1f}%")

    with colB:
        st.markdown("**Reddit**")
        rd_df = fetch_reddit_search(ticker, limit=50)
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
        tmp = all_sent.copy()
        tmp["dt"] = pd.to_datetime(tmp["created_at"], errors="coerce", utc=True)
        tmp = tmp.dropna(subset=["dt"]).sort_values("dt")
        if not tmp.empty:
            daily = tmp.set_index("dt").resample("1D")["sentiment"].mean().reset_index()
            daily.rename(columns={"dt": "Date", "sentiment": "Avg Sentiment"}, inplace=True)
            daily["Date"] = pd.to_datetime(daily["Date"]).dt.tz_convert(None)
            _plot_area(daily, "Date", ["Avg Sentiment"], title="Daily average sentiment (Reddit + Stocktwits)", yaxis_title="Score")

        st.markdown("**Latest posts/messages**")
        show_cols = [c for c in ["source", "created_at", "user", "subreddit", "sentiment", "text", "permalink"] if c in all_sent.columns]
        st.dataframe(all_sent[show_cols].head(60), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# EXTRA TAB — BUFFETT (DCF)
# ============================================================

with tab_buff:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Warren Buffett Module — DCF Intrinsic Value")

    fcf = _safe_float(info.get("freeCashflow"))
    if _is_bad(fcf):
        # approximate from annual cashflow if possible
        cf_a = stmts.get("cashflow", pd.DataFrame())
        cf_ts = _statement_to_timeseries(cf_a, ["Total Cash From Operating Activities", "Capital Expenditures"])
        if not cf_ts.empty and "Total Cash From Operating Activities" in cf_ts.columns and "Capital Expenditures" in cf_ts.columns:
            fcf = float((cf_ts["Total Cash From Operating Activities"] + cf_ts["Capital Expenditures"]).dropna().tail(1).iloc[0])

    cash = _safe_float(info.get("totalCash"))
    debt = _safe_float(info.get("totalDebt"))
    shares = _safe_float(info.get("sharesOutstanding"))
    net_debt = (debt - cash) if (not _is_bad(debt) and not _is_bad(cash)) else 0.0

    st.caption("O DCF é sensível a crescimento, desconto e crescimento terminal. Mantém conservador.")
    cL, cM, cR = st.columns([1, 1, 1])
    with cL:
        years = st.slider("Projection years", 5, 15, 10, 1)
        fcf_growth = st.slider("FCF growth (annual)", 0.00, 0.30, 0.08, 0.01)
        terminal_growth = st.slider("Terminal growth", 0.00, 0.06, 0.025, 0.005)
    with cM:
        discount_rate = st.slider("Discount rate (required return)", 0.05, 0.18, 0.10, 0.005)
        st.write("")
    with cR:
        starting_fcf = st.number_input("Starting FCF (base year)", value=float(0.0 if _is_bad(fcf) else fcf), step=1e8, format="%.2f")
        shares_out = st.number_input("Shares outstanding", value=float(0.0 if _is_bad(shares) else shares), step=1e7, format="%.0f")
        net_debt_in = st.number_input("Net debt (Debt - Cash)", value=float(net_debt), step=1e8, format="%.2f")

    base = DcfInputs(
        years=int(years),
        fcf_growth=float(fcf_growth),
        discount_rate=float(discount_rate),
        terminal_growth=float(terminal_growth),
        net_debt=float(net_debt_in),
        shares_outstanding=float(shares_out),
        starting_fcf=float(starting_fcf),
    )

    out = run_dcf(base)
    intrinsic = out["intrinsic_per_share"]
    mos = (intrinsic / last_close - 1.0) if (last_close and not _is_bad(intrinsic)) else np.nan

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("PV projected FCF", _fmt_num(out["pv_fcfs"]))
    k2.metric("PV terminal value", _fmt_num(out["pv_terminal"]))
    k3.metric("Equity value (DCF)", _fmt_num(out["equity_value"]))
    k4.metric("Intrinsic / share", "N/A" if _is_bad(intrinsic) else f"{intrinsic:.2f} {currency}")

    st.write("")
    if not _is_bad(mos):
        if mos >= 0.25:
            st.success(f"Margin of safety: {_fmt_pct(mos)}")
        elif mos >= 0.05:
            st.warning(f"Margin of safety: {_fmt_pct(mos)} (sensível aos inputs)")
        else:
            st.error(f"Margin of safety: {_fmt_pct(mos)} (pouca folga)")

    st.markdown("### Sensitivity (intrinsic / share)")
    dr_grid = [max(0.03, discount_rate - 0.02), max(0.03, discount_rate - 0.01), discount_rate, discount_rate + 0.01, discount_rate + 0.02]
    tg_grid = [max(0.0, terminal_growth - 0.01), terminal_growth, terminal_growth + 0.01]
    sens = dcf_sensitivity(base, dr_grid, tg_grid)

    disp = sens.copy()
    for c in disp.columns:
        if c.startswith("g="):
            disp[c] = disp[c].apply(lambda v: "N/A" if _is_bad(v) else f"{float(v):.2f}")
    disp["Discount Rate"] = disp["Discount Rate"].apply(lambda x: f"{float(x)*100:.1f}%")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# EXTRA TAB — WATCHLIST & ALERTS
# ============================================================

with tab_watch:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Watchlist & Alerts")

    watch = [t.strip().upper() for t in watchlist_str.split(",") if t.strip()]
    if not watch:
        st.info("Define uma watchlist na sidebar.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    rows = []
    for tk in watch:
        p = yf_price_history(tk, period="1y", interval="1d")
        if p.empty:
            rows.append({"Ticker": tk, "Status": "No data"})
            continue
        last = float(p["Close"].iloc[-1])
        high_52w = float(p["High"].max())
        dd = (last / high_52w - 1.0) if high_52w else np.nan
        alert = (dd <= -(drop_threshold / 100.0)) if not _is_bad(dd) else False
        rows.append({
            "Ticker": tk,
            "Last": last,
            "52W High": high_52w,
            "Drawdown%": dd * 100.0 if not _is_bad(dd) else np.nan,
            "Alert": bool(alert),
        })

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

# ============================================================
# EXTRA TAB — REPORT (Markdown export)
# ============================================================

with tab_report:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("One-page Report (Markdown export)")

    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")

    report_md = f"""# SMAI Report — {ticker}

**Company:** {name}  
**Sector/Industry:** {sector} / {industry}  
**Last:** {last_close:.2f} {currency}  ({_fmt_pct(chg)})

## Snapshot (Yahoo)
- Market cap: {_fmt_num(mcap)}
- Trailing P/E: {"N/A" if _is_bad(ratios["Trailing P/E"]) else f"{ratios['Trailing P/E']:.2f}"}
- Forward P/E: {"N/A" if _is_bad(ratios["Forward P/E"]) else f"{ratios['Forward P/E']:.2f}"}
- EV/EBITDA: {"N/A" if _is_bad(ratios["EV/EBITDA"]) else f"{ratios['EV/EBITDA']:.2f}"}
- ROE: {_fmt_pct(ratios.get("ROE", np.nan))}
- Operating margin: {_fmt_pct(ratios.get("Operating Margin", np.nan))}
- Dividend yield: {_fmt_pct(ratios.get("Dividend Yield", np.nan))}
- Scorecard: {score}/100

## Fundamental thesis (fill)
- Bull case:
- Bear case:
- Key risks:
- Catalysts:

## Buffett (DCF) — current assumptions
- Projection years: {int(10)}
- Intrinsic / share: (run in tab 6)

## Notes
- This report is generated from Yahoo Finance data via yfinance. Coverage can vary by ticker/region.
"""
    st.text_area("Report (Markdown)", value=report_md, height=360)
    st.download_button("Download report.md", data=report_md.encode("utf-8"), file_name=f"SMAI_{ticker}_report.md", mime="text/markdown")

    st.markdown("</div>", unsafe_allow_html=True)
