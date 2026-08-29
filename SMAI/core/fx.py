"""Currency coherence for yfinance payloads.

yfinance mixes two currencies in a single `info` dict whenever a company is
quoted in one currency and reports its accounts in another — every ADR, plus
cases like SHELL.AS (EUR quote, USD accounts). Price and market cap come in the
QUOTE currency; revenue, EBITDA, cash, debt and free cash flow come in the
REPORTING currency. Ratios built across the two are meaningless.

Measured on the 67-ticker screener universe, 2026-08-29:

    NVO   EV/EBITDA  1.71  (USD enterprise value over DKK EBITDA; true ~8.0)
    BABA  EV/EBITDA  2.24  (true ~15)
    XIACY EV/EBITDA  0.32
    NVO   P/S        0.61  (true ~3.97)
    NVO   DCF upside +341.9%  (DKK intrinsic value against a USD price;
                               correctly converted it is about -32%)

13 of 67 tickers were affected.

What is NOT mixed, verified against the balance sheets rather than assumed:
  * `bookValue` is already converted to the quote currency (NVO 7.80 is USD,
    not the 57.99 DKK the accounts imply), so P/B is fine and must be left
    alone.
  * `trailingEps` is likewise in the quote currency, so P/E is fine.
  * `enterpriseValue` is neither: it is a MIXED SUM of quote-currency market
    cap and reporting-currency net debt, so it is recomputed rather than
    converted.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import streamlit as st
import yfinance as yf

from .formatting import is_bad, safe_float

# Monetary fields yfinance reports in the ACCOUNTING currency. Verified field
# by field before being listed here; anything unverified stays out.
_REPORTING_CURRENCY_FIELDS: Tuple[str, ...] = (
    "ebitda",
    "totalRevenue",
    "grossProfits",
    "freeCashflow",
    "operatingCashflow",
    "totalCash",
    "totalDebt",
    "netIncomeToCommon",
)


@st.cache_data(ttl=60 * 60, show_spinner=False)
def fx_rate(from_ccy: str, to_ccy: str) -> float:
    """Units of `to_ccy` per one unit of `from_ccy`. NaN when unavailable.

    Uses Yahoo's own FX pairs (e.g. DKKUSD=X) — free, no API key, and the same
    source as the rest of the data, so no third provider is introduced.
    """
    f = (from_ccy or "").strip().upper()
    t = (to_ccy or "").strip().upper()
    if not f or not t:
        return float("nan")
    if f == t:
        return 1.0
    # GBp/GBX are pence, not pounds.
    pence_factor = 1.0
    if f == "GBX":
        f, pence_factor = "GBP", 0.01
    if t == "GBX":
        t = "GBP"
        pence_factor *= 100.0
    if f == t:
        return pence_factor
    try:
        hist = yf.Ticker(f"{f}{t}=X").history(period="5d", interval="1d")
        if hist is None or hist.empty or "Close" not in hist.columns:
            return float("nan")
        rate = float(hist["Close"].iloc[-1])
    except Exception:
        return float("nan")
    if rate <= 0 or rate != rate:
        return float("nan")
    return rate * pence_factor


def normalise_currency(info: Dict) -> Dict:
    """Return `info` with accounting figures expressed in the quote currency.

    No-op when both currencies agree (the common case, 54 of 67 tickers). When
    they differ and no rate is available, the corrupted ratios are removed
    rather than left in place — an absent multiple is honest, a mixed one is
    not.
    """
    if not info:
        return info

    quote_ccy = str(info.get("currency") or "").strip().upper()
    fin_ccy = str(info.get("financialCurrency") or "").strip().upper()
    if not quote_ccy or not fin_ccy or quote_ccy == fin_ccy:
        return info

    out = dict(info)
    rate = fx_rate(fin_ccy, quote_ccy)
    converted: List[str] = []

    if is_bad(rate):
        # Cannot fix them; make sure we do not serve them either.
        for field in ("enterpriseToEbitda", "enterpriseValue", "priceToSalesTrailing12Months"):
            out[field] = None
        out["_currency_note"] = (
            f"Quote in {quote_ccy} but accounts in {fin_ccy}, and no {fin_ccy}->{quote_ccy} "
            f"rate was available. Currency-mixed multiples were removed."
        )
        return out

    for field in _REPORTING_CURRENCY_FIELDS:
        value = safe_float(out.get(field), default=None)
        if value is not None and not is_bad(value):
            out[field] = value * rate
            converted.append(field)

    # enterpriseValue is a mixed SUM (quote-currency market cap + reporting-
    # currency net debt), so rebuild it from parts now expressed in one currency.
    mcap = safe_float(out.get("marketCap"), default=None)
    cash = safe_float(out.get("totalCash"), default=None)
    debt = safe_float(out.get("totalDebt"), default=None)
    if mcap is not None and not is_bad(mcap):
        net_debt = (debt or 0.0) - (cash or 0.0)
        out["enterpriseValue"] = mcap + net_debt

    ev = safe_float(out.get("enterpriseValue"), default=None)
    ebitda = safe_float(out.get("ebitda"), default=None)
    if ev is not None and ebitda not in (None, 0) and not is_bad(ebitda):
        out["enterpriseToEbitda"] = ev / ebitda
    else:
        out["enterpriseToEbitda"] = None

    revenue = safe_float(out.get("totalRevenue"), default=None)
    if mcap is not None and revenue not in (None, 0) and not is_bad(revenue):
        out["priceToSalesTrailing12Months"] = mcap / revenue

    out["_fx_applied"] = {
        "from": fin_ccy,
        "to": quote_ccy,
        "rate": rate,
        "fields": converted,
    }
    return out


def dividend_yield_fraction(info: Dict) -> float:
    """Dividend yield as a fraction (0.0046 == 0.46%).

    yfinance is not self-consistent here: across the screener universe it
    returned a PERCENT for 46 of 47 payers (NKE 4.27 == 4.27%) and a FRACTION
    for one (XONA.DE 0.0298 == 2.98%). Any threshold rule therefore misreads
    one group or the other — the old `>1.0 means percent` heuristic silently
    turned every sub-1% yield into a sub-100% one (NVDA 0.46% -> 44%).

    So derive it instead: `dividendRate` and the price are both per share in
    the quote currency, which makes the units unambiguous. The stored field is
    only a fallback, and then only within a plausible range.
    """
    price = safe_float(info.get("currentPrice"), default=None)
    if price is None or is_bad(price) or price <= 0:
        price = safe_float(info.get("regularMarketPrice"), default=None)
    rate = safe_float(info.get("dividendRate"), default=None)

    if (
        rate is not None
        and not is_bad(rate)
        and rate > 0
        and price is not None
        and not is_bad(price)
        and price > 0
    ):
        return rate / price

    raw = safe_float(info.get("dividendYield"), default=None)
    if raw is None or is_bad(raw) or raw <= 0:
        return float("nan")
    # No rate to derive from. A yield above 0.35 as a fraction (35%) is far
    # outside anything real, so such a value must be a percent.
    return raw / 100.0 if raw > 0.35 else raw
