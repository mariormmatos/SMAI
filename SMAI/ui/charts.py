from __future__ import annotations

import math
from typing import List

import plotly.graph_objects as go
import numpy as np
import pandas as pd
import streamlit as st

from SMAI.core.formatting import fmt_compact


def _nice_num(value: float, round_: bool) -> float:
    if value == 0:
        return 0.0
    exponent = math.floor(math.log10(abs(value)))
    fraction = abs(value) / (10**exponent)
    if round_:
        if fraction < 1.5:
            nice_fraction = 1.0
        elif fraction < 3:
            nice_fraction = 2.0
        elif fraction < 7:
            nice_fraction = 5.0
        else:
            nice_fraction = 10.0
    else:
        if fraction <= 1:
            nice_fraction = 1.0
        elif fraction <= 2:
            nice_fraction = 2.0
        elif fraction <= 5:
            nice_fraction = 5.0
        else:
            nice_fraction = 10.0
    return math.copysign(nice_fraction * (10**exponent), value)


def _nice_ticks(min_v: float, max_v: float, n: int = 5) -> list[float]:
    if min_v == max_v:
        return [min_v]
    span = _nice_num(max_v - min_v, round_=False)
    step = _nice_num(span / max(1, (n - 1)), round_=True)
    if step == 0:
        return [min_v, max_v]
    graph_min = math.floor(min_v / step) * step
    graph_max = math.ceil(max_v / step) * step
    ticks = np.arange(graph_min, graph_max + 0.5 * step, step)
    return ticks.tolist()


def plot_area(
    df,
    x_col: str,
    y_cols: List[str],
    title: str,
    yaxis_title: str = "",
    percent: bool = False,
) -> None:
    if df is None or df.empty:
        st.info("Sem dados para gráfico.")
        return

    fig = go.Figure()
    for i, col in enumerate(y_cols):
        if col not in df.columns:
            continue

        hover_fmt = ".2f" if percent else None
        customdata = None
        if not percent:
            series = pd.to_numeric(df[col], errors="coerce")
            customdata = series.map(lambda v: fmt_compact(v) if pd.notna(v) else "N/A")
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[col],
                mode="lines+markers",
                name=col,
                fill="tozeroy" if i == 0 else None,
                marker=dict(size=6),
                line=dict(width=2),
                customdata=customdata,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + (f"{col}: %{{y:{hover_fmt}}}%" if percent else f"{col}: %{{customdata}}")
                    + "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=16, r=16, t=60, b=14),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        font=dict(color="#e9eef6"),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.06)",
        showspikes=True,
        spikecolor="rgba(78,161,255,0.55)",
        spikethickness=1,
        spikesnap="cursor",
    )
    yaxis_kwargs = dict(
        title=yaxis_title,
        showgrid=True,
        gridcolor="rgba(255,255,255,0.08)",
        separatethousands=True,
        zerolinecolor="rgba(255,255,255,0.12)",
    )
    if percent:
        yaxis_kwargs["tickformat"] = ".1f"
    else:
        y_values = []
        for col in y_cols:
            if col in df.columns:
                y_values.append(pd.to_numeric(df[col], errors="coerce"))
        if y_values:
            y_all = pd.concat(y_values, axis=0).replace([np.inf, -np.inf], np.nan).dropna()
            if not y_all.empty:
                ticks = _nice_ticks(float(y_all.min()), float(y_all.max()))
                yaxis_kwargs.update(
                    {
                        "tickmode": "array",
                        "tickvals": ticks,
                        "ticktext": [fmt_compact(v) for v in ticks],
                    }
                )

    fig.update_yaxes(**yaxis_kwargs)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def plot_candles(df, title: str, currency: str) -> None:
    if df is None or df.empty:
        st.info("Sem dados para gráfico.")
        return
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
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        font=dict(color="#e9eef6"),
        title=title,
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=10, t=48, b=10),
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(title=f"Price ({currency})", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
