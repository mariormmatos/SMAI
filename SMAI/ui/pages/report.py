from __future__ import annotations

import numpy as np
import streamlit as st

from SMAI.core.formatting import fmt_num, fmt_pct, fmt_ratio


def render_report(
    ticker: str,
    name: str,
    currency: str,
    last_close: float,
    chg: float,
    info: dict,
    ratios: dict,
    score: int,
) -> None:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("One-page Report (Markdown export)")

    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")

    report_md = f"""# SMAI Report — {ticker}

**Company:** {name}  
**Sector/Industry:** {sector} / {industry}  
**Last:** {last_close:.2f} {currency}  ({fmt_pct(chg)})

## Snapshot (Yahoo)
- Market cap: {fmt_num(info.get('marketCap', np.nan))}
- Trailing P/E: {fmt_ratio(ratios.get('Trailing P/E'))}
- Forward P/E: {fmt_ratio(ratios.get('Forward P/E'))}
- EV/EBITDA: {fmt_ratio(ratios.get('EV/EBITDA'))}
- ROE: {fmt_pct(ratios.get('ROE', np.nan))}
- Operating margin: {fmt_pct(ratios.get('Operating Margin', np.nan))}
- Dividend yield: {fmt_pct(ratios.get('Dividend Yield', np.nan))}
- Scorecard: {score}/100

## Fundamental thesis (fill)
- Bull case:
- Bear case:
- Key risks:
- Catalysts:

## Buffett (DCF) — current assumptions
- Projection years: 10
- Intrinsic / share: (run in tab 6)

## Notes
- This report is generated from Yahoo Finance data via yfinance. Coverage can vary by ticker/region.
"""
    st.text_area("Report (Markdown)", value=report_md, height=360)
    st.download_button(
        "Download report.md",
        data=report_md.encode("utf-8"),
        file_name=f"SMAI_{ticker}_report.md",
        mime="text/markdown",
    )

    st.markdown("</div>", unsafe_allow_html=True)
