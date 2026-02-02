from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from SMAI.core.data_yf import yf_price_history
from SMAI.core.formatting import is_bad


def render_watchlist(watchlist_str: str, drop_threshold: int) -> None:
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
        alert = (dd <= -(drop_threshold / 100.0)) if not is_bad(dd) else False
        rows.append({
            "Ticker": tk,
            "Last": last,
            "52W High": high_52w,
            "Drawdown%": dd * 100.0 if not is_bad(dd) else np.nan,
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
