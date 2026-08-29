from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .formatting import is_bad, safe_float
from .fx import dividend_yield_fraction


def _stmt_val(df: pd.DataFrame, candidates: List[str]) -> float:
    """Most recent non-NaN value from a statement DataFrame, trying multiple row names."""
    if df is None or df.empty:
        return np.nan
    for name in candidates:
        if name in df.index:
            valid = df.loc[name].dropna()
            if not valid.empty:
                return float(valid.iloc[0])
    return np.nan


def enrich_info_from_stmts(info: Dict, stmts: Dict, last_price: float, fx: float | None = None) -> Dict:
    """Fill missing ratios in info using financial statements (annual).

    The statements are in the reporting currency and `last_price` is in the
    quote currency, so several ratios below would otherwise divide a price in
    USD by a per-share figure in DKK. The conversion factor is read from
    `info["_fx_applied"]`, which SMAI.core.fx.normalise_currency already
    attached — deliberately NOT from a new required argument.

    That choice is not cosmetic: an earlier version made `fx` a caller-supplied
    parameter, and on 2026-08-29 that took the deployed app down. Streamlit
    Cloud re-ran the updated entry script against a still-cached
    `SMAI.core.scoring` in `sys.modules`, so the new call site met the old
    signature and raised TypeError before any of it could run. Reading the
    factor off the payload keeps callers and this function independently
    upgradable: a stale module now merely skips the conversion instead of
    crashing.

    Pure statement-over-statement ratios (ROE, margins, debt/equity) are
    unaffected by the factor either way — it cancels.
    """
    result = dict(info)

    fin = stmts.get("financials", pd.DataFrame())
    bs = stmts.get("balance_sheet", pd.DataFrame())
    cf = stmts.get("cashflow", pd.DataFrame())

    if fx is None:
        applied = info.get("_fx_applied") or {}
        fx = applied.get("rate")
    fx = safe_float(fx, default=1.0)
    if is_bad(fx) or fx <= 0:
        fx = 1.0

    def _money(df: pd.DataFrame, candidates: List[str]) -> float:
        """Statement value converted to the quote currency."""
        v = _stmt_val(df, candidates)
        return v if is_bad(v) else v * fx

    net_income = _money(fin, ["Net Income", "Net Income Common Stockholders"])
    revenue = _money(fin, ["Total Revenue", "Operating Revenue"])
    op_income = _money(fin, ["Operating Income", "EBIT"])
    ebitda = _money(fin, ["EBITDA", "Normalized EBITDA"])
    gross_profit = _money(fin, ["Gross Profit"])
    diluted_eps = _money(fin, ["Diluted EPS", "Basic EPS"])
    shares = _stmt_val(fin, ["Diluted Average Shares", "Basic Average Shares"])  # a count, not money

    equity = _money(bs, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
    total_debt = _money(bs, ["Total Debt"])
    total_assets = _money(bs, ["Total Assets"])
    cash = _money(bs, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"])
    shares_bs = _stmt_val(bs, ["Ordinary Shares Number", "Share Issued"])  # a count, not money

    free_cash_flow = _money(cf, ["Free Cash Flow"])

    shares_count = shares if not is_bad(shares) else shares_bs

    def _fill(key: str, value: float) -> None:
        if is_bad(safe_float(result.get(key))) and not is_bad(value):
            result[key] = value

    # Profitability
    if not is_bad(equity) and equity != 0 and not is_bad(net_income):
        _fill("returnOnEquity", net_income / equity)
    if not is_bad(total_assets) and total_assets != 0 and not is_bad(net_income):
        _fill("returnOnAssets", net_income / total_assets)
    if not is_bad(revenue) and revenue != 0:
        if not is_bad(op_income):
            _fill("operatingMargins", op_income / revenue)
        if not is_bad(net_income):
            _fill("profitMargins", net_income / revenue)
        if not is_bad(gross_profit):
            _fill("grossMargins", gross_profit / revenue)

    # Valuation
    if not is_bad(diluted_eps) and diluted_eps != 0 and not is_bad(last_price):
        _fill("trailingPE", last_price / diluted_eps)
    if not is_bad(revenue) and revenue != 0 and not is_bad(shares_count) and not is_bad(last_price):
        mcap = last_price * shares_count
        _fill("marketCap", mcap)
        _fill("priceToSalesTrailing12Months", mcap / revenue)
    if not is_bad(equity) and equity != 0 and not is_bad(shares_count) and not is_bad(last_price):
        bvps = equity / shares_count
        if bvps > 0:
            _fill("priceToBook", last_price / bvps)

    # Leverage
    if not is_bad(total_debt) and not is_bad(equity) and equity != 0:
        _fill("debtToEquity", (total_debt / equity) * 100)

    # EV/EBITDA
    mcap_val = safe_float(result.get("marketCap"), default=None)
    if mcap_val is None and not is_bad(shares_count) and not is_bad(last_price):
        mcap_val = last_price * shares_count
    if not is_bad(ebitda) and ebitda != 0 and mcap_val is not None:
        ev = mcap_val + (total_debt if not is_bad(total_debt) else 0) - (cash if not is_bad(cash) else 0)
        _fill("enterpriseToEbitda", ev / ebitda)

    # Free cash flow
    if not is_bad(free_cash_flow):
        _fill("freeCashflow", free_cash_flow)

    return result


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
    """EV/EBITDA, preferring a value rebuilt from market cap and net debt.

    The previous version cross-checked yfinance's `enterpriseToEbitda` against
    `enterpriseValue / ebitda` and fell back to the latter when they diverged
    by more than 35%. Measured 2026-08-29: the divergence is 0.0% for NVO, BABA
    and UL, because both sides are the same yfinance figure — the check was
    comparing a number with itself and could never fire. It looked like
    validation while validating nothing.

    Market cap plus net debt over EBITDA is a real independent reconstruction,
    and after SMAI.core.fx.normalise_currency every input is in the quote
    currency, so it is also the currency-coherent one.
    """
    raw_multiple = safe_float(info.get("enterpriseToEbitda"))
    ebitda = safe_float(info.get("ebitda"))
    mcap = safe_float(info.get("marketCap"))
    cash = safe_float(info.get("totalCash"))
    debt = safe_float(info.get("totalDebt"))

    rebuilt = np.nan
    if not is_bad(mcap) and not is_bad(ebitda) and ebitda != 0:
        net_debt = (0.0 if is_bad(debt) else debt) - (0.0 if is_bad(cash) else cash)
        rebuilt = (mcap + net_debt) / ebitda

    if is_bad(raw_multiple):
        return rebuilt
    if is_bad(rebuilt):
        return raw_multiple

    # Keep the vendor's figure — it accounts for minority interest and
    # preferred stock, which the reconstruction above does not — but let the
    # reconstruction overrule it when they genuinely disagree.
    if raw_multiple > 0 and rebuilt > 0:
        rel_diff = abs(raw_multiple - rebuilt) / max(abs(raw_multiple), abs(rebuilt))
        if rel_diff > 0.35:
            return rebuilt

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
        # Derived from dividendRate/price, not from the ambiguous dividendYield
        # field — see SMAI.core.fx.dividend_yield_fraction.
        "Dividend Yield": dividend_yield_fraction(info),
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
