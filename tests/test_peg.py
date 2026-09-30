"""SMAI.core.peg — pins the same cases as FinanceResearchCenter/tests/unit/test_peg.py.

The formula is a mirror of the FRC module (this app cannot import it). If a case
here fails after a change, the two copies have drifted.
"""
from __future__ import annotations

import pytest

from SMAI.core import peg


def _series(values, first_year=2019):
    return {"series": {"annual": {"eps": [
        {"period": f"{first_year + i}-12-31", "v": v} for i, v in enumerate(values)
    ]}}}


def test_constant_growth_gives_exact_peg():
    g, p = peg.historical({2019 + i: 1.1 ** i for i in range(8)}, 20.0)
    assert g == pytest.approx(10.0)
    assert p == pytest.approx(2.0)


def test_falling_earnings_have_no_peg_but_report_growth():
    g, p = peg.historical({2019 + i: 1 / 1.05 ** i for i in range(8)}, 20.0)
    assert g < 0 and p is None


def test_short_history_has_no_peg():
    assert peg.historical({2020 + i: 1.0 for i in range(6)}, 20.0) == (None, None)


def test_loss_at_start_has_no_peg():
    eps = {2019 + i: v for i, v in enumerate([-1, -1, 1, 2, 3, 4, 5, 6])}
    assert peg.historical(eps, 20.0) == (None, None)


@pytest.mark.parametrize("pe", [None, 0, -5.0, float("nan")])
def test_non_positive_or_missing_pe_has_no_peg(pe):
    assert peg.historical({2019 + i: 1.1 ** i for i in range(8)}, pe)[1] is None


def test_isolated_spike_mid_series_does_not_change_peg():
    base = {2019 + i: 1.1 ** i for i in range(8)}
    assert peg.historical({**base, 2022: 99.0}, 20.0) == peg.historical(base, 20.0)


def test_eps_series_tolerates_garbage():
    for bad in (None, [], "x", {"series": None}, {"series": {"annual": {"eps": [{"v": 1}]}}}):
        assert peg.eps_series(bad) == {}


def test_peg_for_without_key_is_none_not_an_error(monkeypatch):
    monkeypatch.setattr(peg, "finnhub_metric", lambda t: None)
    assert peg.peg_for("MSFT", 28.5) == {"peg": None, "growth_5y": None, "forward_peg": None}


def test_peg_for_computes_and_keeps_only_positive_forward(monkeypatch):
    payload = {**_series([1.1 ** i for i in range(8)]), "metric": {"forwardPEG": 1.45}}
    monkeypatch.setattr(peg, "finnhub_metric", lambda t: payload)
    out = peg.peg_for("MSFT", 20.0)
    assert out["peg"] == pytest.approx(2.0) and out["forward_peg"] == 1.45
    payload["metric"]["forwardPEG"] = -0.4
    assert peg.peg_for("MSFT", 20.0)["forward_peg"] is None


def test_negative_source_peg_never_leaks(monkeypatch):
    """Novo Nordisk case: a negative pegTTM from the source must not become the PEG."""
    payload = {**_series([1 / 1.03 ** i for i in range(8)]), "metric": {"pegTTM": -11.56}}
    monkeypatch.setattr(peg, "finnhub_metric", lambda t: payload)
    assert peg.peg_for("NVO", 9.6)["peg"] is None


def test_no_key_means_no_network_call(monkeypatch):
    monkeypatch.setattr(peg, "_api_key", lambda: None)
    monkeypatch.setattr(peg.requests, "get", lambda *a, **k: pytest.fail("must not call the network"))
    assert peg.finnhub_metric("MSFT") is None


class _Resp:
    def __init__(self, code, payload=None):
        self.status_code, self._p = code, payload or {}

    def json(self):
        return self._p


def test_a_failure_is_not_cached(monkeypatch):
    """One failed call must not blank the ticker for 24h: the next call retries."""
    peg._fetch_metric.clear()
    monkeypatch.setattr(peg, "_api_key", lambda: "k")
    monkeypatch.setattr(peg.time, "sleep", lambda s: None)
    respostas = [_Resp(500), _Resp(200, {"metric": {"forwardPEG": 1.0}})]
    monkeypatch.setattr(peg.requests, "get", lambda *a, **k: respostas.pop(0))
    assert peg.finnhub_metric("ZZTEST") is None
    assert peg.finnhub_metric("ZZTEST") == {"metric": {"forwardPEG": 1.0}}
    peg._fetch_metric.clear()


def test_a_success_is_cached(monkeypatch):
    peg._fetch_metric.clear()
    monkeypatch.setattr(peg, "_api_key", lambda: "k")
    chamadas = []
    monkeypatch.setattr(peg.requests, "get", lambda *a, **k: chamadas.append(1) or _Resp(200, {"ok": 1}))
    peg.finnhub_metric("ZZOK")
    peg.finnhub_metric("ZZOK")
    assert len(chamadas) == 1
    peg._fetch_metric.clear()
