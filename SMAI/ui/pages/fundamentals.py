from __future__ import annotations

import datetime as dt
from typing import Dict

import numpy as np
import pandas as pd
import streamlit as st

from SMAI.core.data_yf import statement_to_timeseries, yf_news
from SMAI.core.formatting import ensure_date_col, fmt_num, fmt_pct, fmt_ratio, is_bad, safe_float
from SMAI.ui.charts import plot_area
from SMAI.ui.components import render_news_bullets

INCOME_ROWS = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Diluted EPS"]
CASHFLOW_ROWS = ["Total Cash From Operating Activities", "Capital Expenditures", "Free Cash Flow"]
BALANCE_ROWS = ["Total Assets", "Total Liab", "Total Stockholder Equity", "Cash", "Long Term Debt"]
STAT_POINTS_MAP = {"1Y": 4, "5Y": 5, "10Y": 10}


def render_fundamentals(
    ticker: str,
    name: str,
    currency: str,
    px: pd.DataFrame,
    stmts: Dict[str, pd.DataFrame],
    info: Dict,
    ratios: Dict[str, float],
    score: int,
    score_notes: list[str],
    stmt_mode: str,
    stmt_span: str,
    timeframe: str,
) -> None:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader(f"Fundamental Analysis — {name} ({ticker})")
    st.caption("Fonte: Yahoo Finance (yfinance). A disponibilidade/labels podem variar por ticker.")

    areas = st.tabs(
        [
            "1️⃣ Financial Statements Analysis",
            "2️⃣ Valuation Metrics",
            "3️⃣ Growth Potential & Competitive Positioning",
            "4️⃣ Risk Analysis",
            "5️⃣ Recent News & Catalysts",
        ]
    )

    with areas[0]:
        st.markdown("### Financial Statements Analysis (charts)")
        st.caption(
            "Inclui: Revenue, profitability, EPS, debt levels (proxy), cash flow. Display por 'span' (10Y/5Y/1Y) e frequência (annual/quarterly)."
        )

        if stmt_mode == "Annual":
            inc = stmts.get("financials", pd.DataFrame())
            cf = stmts.get("cashflow", pd.DataFrame())
            bs = stmts.get("balance_sheet", pd.DataFrame())
        else:
            inc = stmts.get("quarterly_financials", pd.DataFrame())
            cf = stmts.get("quarterly_cashflow", pd.DataFrame())
            bs = stmts.get("quarterly_balance_sheet", pd.DataFrame())

        n_points = STAT_POINTS_MAP.get(stmt_span, 10)

        inc_ts = statement_to_timeseries(inc, INCOME_ROWS)
        if inc_ts.empty:
            st.info("Sem Income Statement suficiente no Yahoo Finance para este ticker.")
        else:
            inc_ts = inc_ts.sort_values("Date").tail(n_points)
            plot_area(
                inc_ts,
                "Date",
                [c for c in INCOME_ROWS if c in inc_ts.columns],
                title=f"Income Statement ({stmt_mode}, last {stmt_span})",
                yaxis_title=f"Amount ({currency})",
            )

        cf_ts = statement_to_timeseries(cf, CASHFLOW_ROWS)
        if not cf_ts.empty and "Free Cash Flow" not in cf_ts.columns:
            if "Total Cash From Operating Activities" in cf_ts.columns and "Capital Expenditures" in cf_ts.columns:
                cf_ts["Free Cash Flow"] = cf_ts["Total Cash From Operating Activities"] + cf_ts["Capital Expenditures"]
        if cf_ts.empty:
            st.info("Sem Cash Flow suficiente no Yahoo Finance para este ticker.")
        else:
            cf_ts = cf_ts.sort_values("Date").tail(n_points)
            plot_area(
                cf_ts,
                "Date",
                [
                    c
                    for c in ["Total Cash From Operating Activities", "Capital Expenditures", "Free Cash Flow"]
                    if c in cf_ts.columns
                ],
                title=f"Cash Flow ({stmt_mode}, last {stmt_span})",
                yaxis_title=f"Amount ({currency})",
            )

        bs_ts = statement_to_timeseries(bs, BALANCE_ROWS)
        if bs_ts.empty:
            st.info("Sem Balance Sheet suficiente no Yahoo Finance para este ticker.")
        else:
            bs_ts = bs_ts.sort_values("Date").tail(n_points)
            plot_area(
                bs_ts,
                "Date",
                [c for c in BALANCE_ROWS if c in bs_ts.columns],
                title=f"Balance Sheet ({stmt_mode}, last {stmt_span})",
                yaxis_title=f"Amount ({currency})",
            )

        st.markdown("### Debt & Liquidity (snapshot)")
        cA, cB, cC, cD = st.columns(4)
        cA.metric("Debt/Equity", fmt_ratio(ratios.get("Debt/Equity")))
        cB.metric("Total Debt", fmt_num(safe_float(info.get("totalDebt"))))
        cC.metric("Total Cash", fmt_num(safe_float(info.get("totalCash"))))
        nd = safe_float(info.get("totalDebt")) - safe_float(info.get("totalCash"))
        cD.metric("Net Debt", fmt_num(nd))

    with areas[1]:
        st.markdown("### Valuation Metrics (charts)")
        st.caption(
            "Como o Yahoo não fornece séries históricas completas de múltiplos, aqui combinamos: preço (série) + snapshot de múltiplos e alguns proxies com base em statements anuais."
        )

        px2 = ensure_date_col(px.reset_index().rename(columns={"index": "Date"}), "Date")
        px2 = px2[["Date", "Close"]].dropna()
        plot_area(px2, "Date", ["Close"], title=f"{ticker} price ({timeframe})", yaxis_title=f"Price ({currency})")

        income_annual = stmts.get("financials", pd.DataFrame())
        inc_ts = statement_to_timeseries(income_annual, ["Total Revenue", "Net Income", "Operating Income", "Diluted EPS"])
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
                plot_area(vdf, "Date", cols, title="Profitability margins (annual)", yaxis_title="%", percent=True)

            if "EPS" in vdf.columns:
                plot_area(vdf, "Date", ["EPS"], title="Diluted EPS (annual)", yaxis_title=f"EPS ({currency})")

        st.markdown("### Valuation Snapshot (Yahoo info)")
        snap = [
            ("Trailing P/E", fmt_ratio(ratios.get("Trailing P/E"))),
            ("Forward P/E", fmt_ratio(ratios.get("Forward P/E"))),
            ("P/B", fmt_ratio(ratios.get("P/B"))),
            ("P/S (TTM)", fmt_ratio(ratios.get("P/S (TTM)"))),
            ("EV/EBITDA", fmt_ratio(ratios.get("EV/EBITDA"))),
            ("Dividend Yield", fmt_pct(ratios.get("Dividend Yield", np.nan))),
        ]
        st.dataframe(pd.DataFrame(snap, columns=["Metric", "Value"]), use_container_width=True, hide_index=True)

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
        st.write(f"- **Revenue (TTM, proxy)**: {fmt_num(safe_float(info.get('totalRevenue')))}")
        st.write(f"- **Operating margin (snapshot)**: {fmt_pct(ratios.get('Operating Margin', np.nan))}")
        st.write(f"- **ROE (snapshot)**: {fmt_pct(ratios.get('ROE', np.nan))}")

        st.markdown("**Your notes (session)**")
        st.text_area("Pontos sobre crescimento/competição", height=160)

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

        st.markdown("**Snapshot signals (Yahoo info)**")
        st.write(f"- **Beta**: {fmt_ratio(ratios.get('Beta'))}")
        st.write(f"- **Debt/Equity**: {fmt_ratio(ratios.get('Debt/Equity'))}")
        st.write(
            f"- **52W range**: {info.get('fiftyTwoWeekLow','N/A')} → {info.get('fiftyTwoWeekHigh','N/A')} {currency}"
        )
        st.write(
            f"- **Recommendation mean (Yahoo)**: {info.get('recommendationMean','N/A')} (quanto menor, mais bullish)"
        )

        st.markdown("**Your risk notes (session)**")
        st.text_area("Riscos específicos (tese bearish)", height=170)

    with areas[4]:
        st.markdown("### Recent News & Catalysts")
        st.caption(
            "Este bloco puxa notícias via yfinance (quando disponível). Para contexto global do mercado, usa o módulo 2."
        )

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
            render_news_bullets(items, title_key="title", link_key="link")

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

    st.divider()
    st.markdown("## 🔍 If you were Warren Buffett, would you invest in this stock?")
    st.caption("Este é um framework + alguns sinais automáticos. A decisão final é tua.")

    buff_cols = st.columns([1, 1, 1, 1])
    buff_cols[0].metric("Quality (ROE)", fmt_pct(ratios.get("ROE", np.nan)))
    buff_cols[1].metric("Operating Margin", fmt_pct(ratios.get("Operating Margin", np.nan)))
    buff_cols[2].metric("Valuation (P/E)", fmt_ratio(ratios.get("Trailing P/E")))
    buff_cols[3].metric("Scorecard", f"{score}/100")

    with st.expander("Rubric details (how scorecard was computed)"):
        st.write("\n".join([f"- {n}" for n in score_notes]))

    st.text_area(
        "A tua conclusão (estilo Buffett): moat, previsibilidade, gestão, preço e margem de segurança.",
        height=160,
    )

    st.markdown("</div>", unsafe_allow_html=True)
