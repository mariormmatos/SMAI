from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from SMAI.core.formatting import ensure_date_col
from SMAI.ui.charts import plot_area, plot_candles


def render_technical(px: pd.DataFrame, ticker: str, timeframe: str, currency: str) -> None:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Technical Analysis")
    t_tabs = st.tabs(["Price (candles)", "Indicators", "Levels & Volatility"])

    with t_tabs[0]:
        plot_candles(px, f"{ticker} candlestick ({timeframe})", currency)

    with t_tabs[1]:
        df = px.copy()
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()

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
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=48, b=10),
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

        rsi_df = pd.DataFrame({"Date": df.index, "RSI14": df["RSI14"].values}).dropna()
        rsi_df = ensure_date_col(rsi_df, "Date")
        plot_area(rsi_df, "Date", ["RSI14"], title="RSI(14)", yaxis_title="RSI")

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
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=48, b=10),
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

        win = st.slider("Level window (days)", 20, 260, 60, 10)
        df2 = df.copy()
        df2["Rolling Low"] = df2["Low"].rolling(win).min()
        df2["Rolling High"] = df2["High"].rolling(win).max()
        lvl_df = ensure_date_col(df2.reset_index().rename(columns={"index": "Date"}), "Date")
        plot_area(
            lvl_df,
            "Date",
            ["Rolling Low", "Rolling High"],
            title=f"Rolling support/resistance proxy ({win}d)",
            yaxis_title=f"Price ({currency})",
        )

    st.markdown("</div>", unsafe_allow_html=True)
