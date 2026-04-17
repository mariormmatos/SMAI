from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import streamlit as st

from SMAI.core.data_yf import yf_info, yf_price_history, yf_statements
from SMAI.core.formatting import fmt_compact, safe_float
from SMAI.core.scoring import compute_snapshot_ratios, scorecard
from SMAI.ui.components import kpi_card
from SMAI.ui.theme import apply_theme
from SMAI.ui.pages.fundamentals import render_fundamentals
from SMAI.ui.pages.news import render_news
from SMAI.ui.pages.screener import render_screener
from SMAI.ui.pages.technical import render_technical
from SMAI.ui.pages.sentiment import render_sentiment
from SMAI.ui.pages.buffett import render_buffett
from SMAI.ui.pages.watchlist import render_watchlist
from SMAI.ui.pages.report import render_report


PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "10Y": ("10y", "1mo"),
}


def main() -> None:
    st.set_page_config(
        page_title="SMAI | Stock Market Analysis & Insights",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    st.markdown(
        """
<div class="smai-hero">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
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
        screener_universe_choice = st.selectbox(
            "Universe preset",
            ["Custom", "S&P500 (mini)", "Nasdaq-100 (mini)", "CAC40 (mini)", "Xetra DAX (mini)", "NSE NIFTY50 (mini)"],
            index=0,
        )
        min_div = st.slider("Min Dividend Yield (%)", 0.0, 10.0, 2.0, 0.1)
        max_pe = st.slider("Max Trailing P/E", 5, 120, 25, 1)
        min_mcap_b = st.slider("Min Market Cap ($B)", 0, 2000, 10, 1)

        st.divider()
        st.subheader("Watchlist & alerts")
        watchlist_str = st.text_input("Watchlist tickers", value="NVO, PFE, NEE, EOAN.DE, ASML, NVDA, MSFT")
        drop_threshold = st.slider("Alert if drawdown from 52W High >=", 5, 60, 20, 1)

    if not ticker:
        st.stop()

    with st.spinner("Loading market data (Yahoo Finance)…"):
        info = yf_info(ticker)
        px = yf_price_history(ticker, period=period, interval=interval)
        stmts = yf_statements(ticker)

    # --- debug panel (temporary) ---
    with st.expander("🔍 Debug info (temporário)", expanded=False):
        import sys
        st.write(f"Python: {sys.version}")
        try:
            import yfinance as _yf
            st.write(f"yfinance: {_yf.__version__}")
        except Exception as e:
            st.write(f"yfinance import error: {e}")
        try:
            import curl_cffi
            st.write(f"curl_cffi: {curl_cffi.__version__}")
        except Exception as e:
            st.write(f"curl_cffi: NOT AVAILABLE — {e}")
        st.write(f"px.empty: {px.empty}, px.shape: {px.shape if not px.empty else 'n/a'}")
        if not px.empty:
            st.write(f"px columns: {list(px.columns)}")
            st.write(f"px Close last: {px['Close'].iloc[-1] if 'Close' in px.columns else 'NO CLOSE COL'}")
        st.write(f"info keys: {len(info)}")
        if "_dbg_px_err" in st.session_state:
            st.error(f"px error: {st.session_state['_dbg_px_err']}")
        if "_dbg_info_err" in st.session_state:
            st.error(f"info error: {st.session_state['_dbg_info_err']}")
    # --- end debug ---

    if px.empty:
        st.error("Sem dados de preço para este ticker (ou limite do Yahoo Finance). Confirma o ticker e tenta outro timeframe.")
        st.stop()

    currency = info.get("currency", "")
    last_close = float(px["Close"].iloc[-1])
    prev_close = float(px["Close"].iloc[-2]) if len(px) > 1 else last_close
    chg = (last_close / prev_close - 1.0) if prev_close else 0.0

    ratios = compute_snapshot_ratios(info)
    score, score_notes = scorecard(ratios)

    last_price = (
        safe_float(info.get("currentPrice"), default=None)
        or safe_float(info.get("regularMarketPrice"), default=None)
        or last_close
    )
    prev_close = safe_float(info.get("previousClose"), default=None) or safe_float(info.get("regularMarketPreviousClose"), default=None)
    day_change = None
    if last_price is not None and prev_close not in (None, 0):
        day_change = (last_price / prev_close - 1.0) * 100.0

    mcap = safe_float(info.get("marketCap"), default=None)
    pe = safe_float(info.get("trailingPE"), default=None)
    roe = safe_float(info.get("returnOnEquity"), default=None)

    c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1, 1.2])
    with c1:
        kpi_card(
            "Last",
            f"{last_price:.2f} {currency}" if last_price is not None else "-",
            delta=(f"{day_change:+.2f}%" if day_change is not None else None),
            delta_color=("good" if (day_change or 0) > 0 else "bad") if day_change is not None else "neutral",
        )
    with c2:
        kpi_card("Market Cap", fmt_compact(mcap) if mcap is not None else "-")
    with c3:
        kpi_card("Trailing P/E", f"{pe:.2f}" if pe is not None else "N/A")
    with c4:
        kpi_card("ROE", f"{roe*100:.2f}%" if roe is not None else "N/A")
    with c5:
        kpi_card("Scorecard", f"{score}/100")

    st.write("")

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

    name = info.get("longName") or info.get("shortName") or ticker

    with tab_fund:
        render_fundamentals(
            ticker=ticker,
            name=name,
            currency=currency,
            px=px,
            stmts=stmts,
            info=info,
            ratios=ratios,
            score=score,
            score_notes=score_notes,
            stmt_mode=stmt_mode,
            stmt_span=stmt_span,
            timeframe=timeframe,
        )

    with tab_news:
        render_news(ticker)

    with tab_screen:
        render_screener(ticker, screener_universe_choice, min_div, max_pe, min_mcap_b)

    with tab_tech:
        render_technical(px, ticker, timeframe, currency)

    with tab_sent:
        render_sentiment(ticker)

    with tab_buff:
        render_buffett(info, stmts, last_close, currency)

    with tab_watch:
        render_watchlist(watchlist_str, drop_threshold)

    with tab_report:
        render_report(ticker, name, currency, last_close, chg, info, ratios, score)


if __name__ == "__main__":
    main()
