from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from .formatting import is_bad, safe_float


def _normalize_fraction_metric(value: float, threshold: float = 1.0) -> float:
    """
    Yahoo fields are usually fractions (0.025 == 2.5%), but sometimes arrive in percent units (2.5).
    """
    v = safe_float(value)
    if is_bad(v):
        return np.nan
    if abs(v) > threshold and abs(v) <= 10000:
        return v / 100.0
    return v


def _ev_to_ebitda(info: Dict) -> float:
    raw_multiple = safe_float(info.get("enterpriseToEbitda"))
    ev = safe_float(info.get("enterpriseValue"))
    ebitda = safe_float(info.get("ebitda"))

    calc_multiple = np.nan
    if not is_bad(ev) and not is_bad(ebitda) and ebitda != 0:
        calc_multiple = ev / ebitda

    if is_bad(raw_multiple):
        return calc_multiple
    if is_bad(calc_multiple):
        return raw_multiple

    if raw_multiple > 0 and calc_multiple > 0:
        rel_diff = abs(raw_multiple - calc_multiple) / max(abs(raw_multiple), abs(calc_multiple))
        if rel_diff > 0.35:
            return calc_multiple

    return raw_multiple


def compute_snapshot_ratios(info: Dict) -> Dict[str, float]:
    return {
        "Trailing P/E": safe_float(info.get("trailingPE")),
        "Forward P/E": safe_float(info.get("forwardPE")),
        "P/B": safe_float(info.get("priceToBook")),
        "P/S (TTM)": safe_float(info.get("priceToSalesTrailing12Months")),
        "EV/EBITDA": _ev_to_ebitda(info),
        "ROE": _normalize_fraction_metric(info.get("returnOnEquity"), threshold=2.0),
        "ROA": _normalize_fraction_metric(info.get("returnOnAssets"), threshold=2.0),
        "Profit Margin": _normalize_fraction_metric(info.get("profitMargins"), threshold=2.0),
        "Operating Margin": _normalize_fraction_metric(info.get("operatingMargins"), threshold=2.0),
        "Dividend Yield": _normalize_fraction_metric(info.get("dividendYield"), threshold=1.0),
        "Payout Ratio": _normalize_fraction_metric(info.get("payoutRatio"), threshold=2.0),
        "Beta": safe_float(info.get("beta")),
        "Debt/Equity": safe_float(info.get("debtToEquity")),
    }


def scorecard(ratios: Dict[str, float]) -> Tuple[int, List[str]]:
    """
    Deterministic rubric (0-100). Not a recommendation—just a consistent diagnostic.
    """
    score = 0
    notes: List[str] = []

    pe = ratios.get("Trailing P/E", np.nan)
    ps = ratios.get("P/S (TTM)", np.nan)
    pb = ratios.get("P/B", np.nan)

    if not is_bad(pe):
        if pe <= 15:
            score += 18
            notes.append("Valuation: P/E <= 15 (+18)")
        elif pe <= 25:
            score += 10
            notes.append("Valuation: 15 < P/E <= 25 (+10)")
        else:
            score += 3
            notes.append("Valuation: P/E > 25 (+3)")
    else:
        notes.append("Valuation: P/E N/A (+0)")

    if not is_bad(ps):
        if ps <= 3:
            score += 10
            notes.append("Valuation: P/S <= 3 (+10)")
        elif ps <= 7:
            score += 6
            notes.append("Valuation: 3 < P/S <= 7 (+6)")
        else:
            score += 2
            notes.append("Valuation: P/S > 7 (+2)")
    else:
        notes.append("Valuation: P/S N/A (+0)")

    if not is_bad(pb):
        if pb <= 2:
            score += 6
            notes.append("Balance/Valuation: P/B <= 2 (+6)")
        elif pb <= 5:
            score += 4
            notes.append("Balance/Valuation: 2 < P/B <= 5 (+4)")
        else:
            score += 1
            notes.append("Balance/Valuation: P/B > 5 (+1)")
    else:
        notes.append("Balance/Valuation: P/B N/A (+0)")

    roe = ratios.get("ROE", np.nan)
    opm = ratios.get("Operating Margin", np.nan)

    if not is_bad(roe):
        if roe >= 0.20:
            score += 18
            notes.append("Quality: ROE >= 20% (+18)")
        elif roe >= 0.12:
            score += 12
            notes.append("Quality: 12% <= ROE < 20% (+12)")
        elif roe >= 0.06:
            score += 6
            notes.append("Quality: 6% <= ROE < 12% (+6)")
        else:
            score += 2
            notes.append("Quality: ROE < 6% (+2)")
    else:
        notes.append("Quality: ROE N/A (+0)")

    if not is_bad(opm):
        if opm >= 0.25:
            score += 14
            notes.append("Quality: Operating margin >= 25% (+14)")
        elif opm >= 0.12:
            score += 9
            notes.append("Quality: 12% <= operating margin < 25% (+9)")
        elif opm >= 0.05:
            score += 5
            notes.append("Quality: 5% <= operating margin < 12% (+5)")
        else:
            score += 1
            notes.append("Quality: operating margin < 5% (+1)")
    else:
        notes.append("Quality: operating margin N/A (+0)")

    beta = ratios.get("Beta", np.nan)
    if not is_bad(beta):
        if beta <= 1.0:
            score += 10
            notes.append("Risk: beta <= 1.0 (+10)")
        elif beta <= 1.5:
            score += 6
            notes.append("Risk: 1.0 < beta <= 1.5 (+6)")
        else:
            score += 2
            notes.append("Risk: beta > 1.5 (+2)")
    else:
        notes.append("Risk: beta N/A (+0)")

    dy = ratios.get("Dividend Yield", np.nan)
    if not is_bad(dy):
        if dy >= 0.03:
            score += 8
            notes.append("Shareholder return: dividend yield >= 3% (+8)")
        elif dy >= 0.015:
            score += 5
            notes.append("Shareholder return: 1.5%-3% (+5)")
        elif dy > 0:
            score += 2
            notes.append("Shareholder return: < 1.5% (+2)")
        else:
            score += 0
            notes.append("Shareholder return: no dividend (+0)")
    else:
        notes.append("Shareholder return: dividend yield N/A (+0)")

    score = max(0, min(100, score))
    return score, notes
