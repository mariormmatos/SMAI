from __future__ import annotations

import pandas as pd
import streamlit as st

from SMAI.core.sentiment import fetch_reddit_search, sentiment_summary
from SMAI.ui.charts import plot_area


def render_sentiment(ticker: str) -> None:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Sentiment — Reddit")
    st.caption("Heurística simples (lexicon). Stocktwits removido (API bloqueada). Para produção, usa VADER/FinBERT.")

    rd_df = fetch_reddit_search(ticker, limit=50)
    rd_sum = sentiment_summary(rd_df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reddit posts", int(rd_sum["count"]))
    c2.metric("Avg sentiment", f"{rd_sum['avg']:+.3f}")
    c3.metric("Positive share", f"{rd_sum['pos_share']*100:.1f}%")
    c4.metric("Negative share", f"{rd_sum['neg_share']*100:.1f}%")

    st.write("")
    if rd_df.empty:
        st.info("Sem dados de sentimento (Reddit sem resultados para este ticker).")
    else:
        tmp = rd_df.copy()
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
                title="Daily average sentiment (Reddit)",
                yaxis_title="Score",
            )

        st.markdown("**Latest posts**")
        show_cols = [c for c in ["created_at", "user", "subreddit", "sentiment", "text", "permalink"] if c in rd_df.columns]
        st.dataframe(rd_df[show_cols].head(50), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
