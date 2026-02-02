from __future__ import annotations

import pandas as pd
import streamlit as st

from SMAI.core.dcf import DcfInputs, dcf_sensitivity, run_dcf
from SMAI.core.data_yf import statement_to_timeseries
from SMAI.core.formatting import fmt_num, fmt_pct, is_bad, safe_float


def render_buffett(
    info: dict,
    stmts: dict,
    last_close: float,
    currency: str,
) -> None:
    st.markdown('<div class="smai-card">', unsafe_allow_html=True)
    st.subheader("Warren Buffett Module — DCF Intrinsic Value")

    fcf = safe_float(info.get("freeCashflow"))
    if is_bad(fcf):
        cf_a = stmts.get("cashflow", pd.DataFrame())
        cf_ts = statement_to_timeseries(cf_a, ["Total Cash From Operating Activities", "Capital Expenditures"])
        if not cf_ts.empty and "Total Cash From Operating Activities" in cf_ts.columns and "Capital Expenditures" in cf_ts.columns:
            fcf = float((cf_ts["Total Cash From Operating Activities"] + cf_ts["Capital Expenditures"]).dropna().tail(1).iloc[0])

    cash = safe_float(info.get("totalCash"))
    debt = safe_float(info.get("totalDebt"))
    shares = safe_float(info.get("sharesOutstanding"))
    net_debt = (debt - cash) if (not is_bad(debt) and not is_bad(cash)) else 0.0

    st.caption("O DCF é sensível a crescimento, desconto e crescimento terminal. Mantém conservador.")
    cL, cM, cR = st.columns([1, 1, 1])
    with cL:
        years = st.slider("Projection years", 5, 15, 10, 1)
        fcf_growth = st.slider("FCF growth (annual)", 0.00, 0.30, 0.08, 0.01)
        terminal_growth = st.slider("Terminal growth", 0.00, 0.06, 0.025, 0.005)
    with cM:
        discount_rate = st.slider("Discount rate (required return)", 0.05, 0.18, 0.10, 0.005)
        st.write("")
    with cR:
        starting_fcf = st.number_input(
            "Starting FCF (base year)",
            value=float(0.0 if is_bad(fcf) else fcf),
            step=1e8,
            format="%.2f",
        )
        shares_out = st.number_input(
            "Shares outstanding",
            value=float(0.0 if is_bad(shares) else shares),
            step=1e7,
            format="%.0f",
        )
        net_debt_in = st.number_input("Net debt (Debt - Cash)", value=float(net_debt), step=1e8, format="%.2f")

    base = DcfInputs(
        years=int(years),
        fcf_growth=float(fcf_growth),
        discount_rate=float(discount_rate),
        terminal_growth=float(terminal_growth),
        net_debt=float(net_debt_in),
        shares_outstanding=float(shares_out),
        starting_fcf=float(starting_fcf),
    )

    out = run_dcf(base)
    intrinsic = out["intrinsic_per_share"]
    mos = (intrinsic / last_close - 1.0) if (last_close and not is_bad(intrinsic)) else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("PV projected FCF", fmt_num(out["pv_fcfs"]))
    k2.metric("PV terminal value", fmt_num(out["pv_terminal"]))
    k3.metric("Equity value (DCF)", fmt_num(out["equity_value"]))
    k4.metric("Intrinsic / share", "N/A" if is_bad(intrinsic) else f"{intrinsic:.2f} {currency}")

    st.write("")
    if mos is not None:
        if mos >= 0.25:
            st.success(f"Margin of safety: {fmt_pct(mos)}")
        elif mos >= 0.05:
            st.warning(f"Margin of safety: {fmt_pct(mos)} (sensível aos inputs)")
        else:
            st.error(f"Margin of safety: {fmt_pct(mos)} (pouca folga)")

    st.markdown("### Sensitivity (intrinsic / share)")
    dr_grid = [max(0.03, discount_rate - 0.02), max(0.03, discount_rate - 0.01), discount_rate, discount_rate + 0.01, discount_rate + 0.02]
    tg_grid = [max(0.0, terminal_growth - 0.01), terminal_growth, terminal_growth + 0.01]
    sens_rows = dcf_sensitivity(base, dr_grid, tg_grid)
    sens = pd.DataFrame(sens_rows)

    disp = sens.copy()
    for c in disp.columns:
        if c.startswith("g="):
            disp[c] = disp[c].apply(lambda v: "N/A" if is_bad(v) else f"{float(v):.2f}")
    disp["Discount Rate"] = disp["Discount Rate"].apply(lambda x: f"{float(x)*100:.1f}%")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
