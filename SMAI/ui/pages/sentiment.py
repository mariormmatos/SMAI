from __future__ import annotations

import pandas as pd
import streamlit as st

from SMAI.core.sentiment import fetch_reddit_search, fetch_stocktwits, sentiment_summary
from SMAI.ui.charts import plot_area


def render_sentiment(ticker: str) -> None:
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
            plot_area(
                daily,
                "Date",
                ["Avg Sentiment"],
                title="Daily average sentiment (Reddit + Stocktwits)",
                yaxis_title="Score",
            )

        st.markdown("**Latest posts/messages**")
        show_cols = [
            c
            for c in ["source", "created_at", "user", "subreddit", "sentiment", "text", "permalink"]
            if c in all_sent.columns
        ]
        st.dataframe(all_sent[show_cols].head(60), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
