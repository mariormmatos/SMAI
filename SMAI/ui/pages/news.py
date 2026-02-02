from __future__ import annotations

import datetime as dt

import streamlit as st

from SMAI.core.data_yf import fetch_yahoo_markets_rss, yf_news
from SMAI.ui.components import render_news_bullets


def render_news(ticker: str) -> None:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Stock News & Summaries")

    n1, n2 = st.tabs(["📢 Market news (US/EU)", f"📌 {ticker} news"])

    with n1:
        st.markdown("### Latest market headlines (Yahoo Finance RSS)")
        st.caption("Bullets com link. Se falhar, é normalmente rate-limit ou bloqueio temporário.")
        items = fetch_yahoo_markets_rss(limit=18)
        render_news_bullets(items)

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
        render_news_bullets(items)

    st.markdown("</div>", unsafe_allow_html=True)
