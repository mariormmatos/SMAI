from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class DcfInputs:
    years: int
    fcf_growth: float
    discount_rate: float
    terminal_growth: float
    net_debt: float
    shares_outstanding: float
    starting_fcf: float


def run_dcf(inp: DcfInputs) -> Dict[str, float]:
    years = max(1, int(inp.years))
    cashflows = []
    fcf = float(inp.starting_fcf)
    for _ in range(years):
        fcf = fcf * (1.0 + float(inp.fcf_growth))
        cashflows.append(fcf)

    dfs = [(1.0 / ((1.0 + inp.discount_rate) ** y)) for y in range(1, years + 1)]
    pv_fcfs = float(sum([cf * df for cf, df in zip(cashflows, dfs)]))

    terminal_cf = cashflows[-1] * (1.0 + float(inp.terminal_growth))
    r = float(inp.discount_rate)
    g = float(inp.terminal_growth)
    terminal_value = terminal_cf / (r - g) if (r - g) > 0 else np.nan
    pv_terminal = terminal_value / ((1.0 + r) ** years) if not np.isnan(terminal_value) else np.nan

    enterprise_value = pv_fcfs + (pv_terminal if not np.isnan(pv_terminal) else 0.0)
    equity_value = enterprise_value - float(inp.net_debt)

    intrinsic_per_share = (
        equity_value / float(inp.shares_outstanding)
        if inp.shares_outstanding else np.nan
    )

    return {
        "pv_fcfs": pv_fcfs,
        "pv_terminal": pv_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_per_share": intrinsic_per_share,
    }


def dcf_sensitivity(base: DcfInputs, discount_rates: List[float], terminal_growths: List[float]):
    rows = []
    for r in discount_rates:
        row = {"Discount Rate": float(r)}
        for g in terminal_growths:
            out = run_dcf(DcfInputs(**{**base.__dict__, "discount_rate": float(r), "terminal_growth": float(g)}))
            row[f"g={g:.1%}"] = out["intrinsic_per_share"]
        rows.append(row)
    return rows
