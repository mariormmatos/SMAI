"""PEG ratio with one explicit definition — mirror of FinanceResearchCenter/backend/peg.py.

The free sources each publish a PEG without saying which growth rate they
divide by. Measured on 100 companies @ 2026-09-30: yfinance and Finnhub differ
by more than 2x on 28 of 91, and yfinance never reports a negative PEG even
with falling earnings (Sanofi 27.6 vs Finnhub 2.8). So the source PEG is not
used; ours is computed:

    PEG = trailing P/E / annual EPS growth over 5 years, in %

Growth uses a two-year average at each end. There is no PEG when growth <= 0,
history < 7 years, or P/E <= 0 — dividing by falling earnings does not produce
an interpretable number. Finnhub's forwardPEG is shown alongside, labelled as
analyst estimates.

MIRROR: this app is deployed on Streamlit Cloud and cannot import the FRC
folder, so `historical()` and `eps_series()` are copies. The FRC module is the
reference; tests/test_peg.py pins the same cases. Change both or neither.

Why Finnhub: yfinance serves only 4 years of annual EPS (measured on NVDA,
MSFT, KO, SAN.PA, ASML.AS, RIO.L); the definition needs 7. Finnhub is used for
the EPS series only, and needs FINNHUB_API_KEY in the Streamlit secrets (or the
environment). Without a key every PEG is None — never an error.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests
import streamlit as st


def eps_series(metric_json: Any) -> dict:
    """Annual EPS by year from a Finnhub /stock/metric?metric=all payload."""
    if not isinstance(metric_json, dict):
        return {}
    rows = ((metric_json.get("series") or {}).get("annual") or {}).get("eps") or []
    out = {}
    for row in rows:
        try:
            out[int(str(row["period"])[:4])] = float(row["v"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def historical(eps: dict, pe: Any) -> tuple:
    """Return (growth_pct, peg). peg is None whenever PEG does not exist."""
    years = sorted(eps)
    if len(years) < 7:
        return None, None
    start = (eps[years[-7]] + eps[years[-6]]) / 2
    end = (eps[years[-2]] + eps[years[-1]]) / 2
    if start <= 0 or end <= 0:
        return None, None
    growth = ((end / start) ** (1 / 5) - 1) * 100
    if growth <= 0 or not isinstance(pe, (int, float)) or pe != pe or pe <= 0:
        return growth, None
    return growth, pe / growth


def _api_key() -> str | None:
    try:
        key = st.secrets.get("FINNHUB_API_KEY")
    except Exception:  # no secrets.toml locally raises, not returns None
        key = None
    key = key or os.environ.get("FINNHUB_API_KEY")
    return key.strip() if isinstance(key, str) and key.strip() else None


class _FetchFailed(Exception):
    """Raised inside the cached fetch so a failure is never cached (st.cache_data only
    stores return values). Otherwise one 429 or network blip would blank a ticker's
    PEG for 24h, and a run before the secret was set would stick until the TTL."""


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def _fetch_metric(ticker: str, _key: str) -> dict:
    """Successful Finnhub payloads only; `_key` is excluded from the cache hash."""
    for attempt in range(3):
        try:
            r = requests.get(
                "https://finnhub.io/api/v1/stock/metric",
                params={"symbol": ticker, "metric": "all", "token": _key},
                timeout=15,
            )
        except requests.RequestException:
            time.sleep(1 + attempt)
            continue
        if r.status_code == 429:  # 60 calls/min on the free tier
            time.sleep(2 + 2 * attempt)
            continue
        if r.status_code == 200:
            return r.json()
        break
    raise _FetchFailed(ticker)


def finnhub_metric(ticker: str) -> Any:
    """Finnhub /stock/metric payload (cached 24h on success). None without a key or on failure."""
    key = _api_key()
    if not key:
        return None
    try:
        return _fetch_metric(ticker, key)
    except _FetchFailed:
        return None


def peg_for(ticker: str, pe: Any) -> dict:
    """PEG, its growth basis and Finnhub's forward PEG for one ticker."""
    payload = finnhub_metric(ticker)
    growth, value = historical(eps_series(payload), pe)
    fwd = None
    if isinstance(payload, dict):
        raw = (payload.get("metric") or {}).get("forwardPEG")
        fwd = float(raw) if isinstance(raw, (int, float)) and raw > 0 else None
    return {"peg": value, "growth_5y": growth, "forward_peg": fwd}
