from __future__ import annotations

import streamlit as st

from SMAI.core.data_yf import fetch_google_news_rss
from SMAI.ui.components import render_news_bullets


def render_news(ticker: str) -> None:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Stock News & Summaries")

    n1, n2 = st.tabs(["📢 Market news (US/EU)", f"📌 {ticker} news"])

    with n1:
        st.markdown("### Latest market headlines")
        items = fetch_google_news_rss("stock market finance economy", limit=18)
        render_news_bullets(items)

    with n2:
        st.markdown(f"### Latest news for {ticker}")
        items = fetch_google_news_rss(f"{ticker} stock", limit=18)
        render_news_bullets(items)

    st.markdown("</div>", unsafe_allow_html=True)
