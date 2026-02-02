from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
import streamlit as st

from SMAI.core.data_yf import yf_info
from SMAI.core.formatting import is_bad, safe_float
from SMAI.core.scoring import compute_snapshot_ratios, scorecard
from SMAI.core.sentiment import fetch_reddit_search, fetch_stocktwits, sentiment_summary


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
        cols = [c for c in dfu.columns if c.lower() in {"ticker", "symbol"}]
        if not cols:
            return []
        return [str(x).strip().upper() for x in dfu[cols[0]].dropna().tolist()]
    except Exception:
        return []


def _valuation_screen_row(ticker: str) -> Dict:
    info = yf_info(ticker)
    ratios = compute_snapshot_ratios(info)
    mcap_i = safe_float(info.get("marketCap"))
    score_i, _ = scorecard(ratios)
    return {
        "Ticker": ticker,
        "Name": info.get("shortName", ""),
        "MarketCap($B)": (mcap_i / 1e9) if not is_bad(mcap_i) else np.nan,
        "P/E": ratios.get("Trailing P/E", np.nan),
        "P/B": ratios.get("P/B", np.nan),
        "EV/EBITDA": ratios.get("EV/EBITDA", np.nan),
        "DivYield%": (ratios.get("Dividend Yield", np.nan) * 100.0) if not is_bad(ratios.get("Dividend Yield", np.nan)) else np.nan,
        "ROE%": (ratios.get("ROE", np.nan) * 100.0) if not is_bad(ratios.get("ROE", np.nan)) else np.nan,
        "Debt/Equity": ratios.get("Debt/Equity", np.nan),
        "Scorecard": score_i,
    }


def _passes_filters(row: Dict, min_div_y: float, max_pe_v: float, min_mcap: float) -> bool:
    dy = row.get("DivYield%")
    pe = row.get("P/E")
    mcapb = row.get("MarketCap($B)")
    ok = True
    if dy is not None and not is_bad(float(dy)):
        ok &= float(dy) >= float(min_div_y)
    else:
        ok &= float(min_div_y) <= 0.0
    if pe is not None and not is_bad(float(pe)):
        ok &= float(pe) <= float(max_pe_v)
    else:
        ok &= False
    if mcapb is not None and not is_bad(float(mcapb)):
        ok &= float(mcapb) >= float(min_mcap)
    else:
        ok &= False
    return bool(ok)


def render_screener(
    ticker: str,
    screener_universe_choice: str,
    min_div: float,
    max_pe: float,
    min_mcap_b: float,
) -> None:
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
