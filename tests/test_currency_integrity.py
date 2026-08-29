"""Regression tests for the data-integrity defects found in the screener.

Reported symptom (2026-08-29): Novo Nordisk showed an EV/EBITDA of 1.7, which
cannot be true. Measuring the full 67-ticker screener universe turned up four
defects, three of which corrupted numbers silently.

All figures below were measured against the live yfinance API on 2026-08-29.
"""
from __future__ import annotations

import numpy as np
import pytest

from SMAI.core.fx import dividend_yield_fraction, normalise_currency
from SMAI.core.scoring import _ev_to_ebitda, compute_snapshot_ratios, enrich_info_from_stmts, scorecard


class TestDividendYield:
    """20 of 67 tickers displayed a yield roughly 100x too high.

    The old rule divided by 100 only above 1.0, and yfinance reports a percent,
    so every sub-1% yield passed through untouched and was multiplied by 100
    downstream: NVDA 0.46% became 44.0%, MSFT 0.71% became 72.0%.
    """

    def test_derived_from_rate_and_price(self):
        info = {"dividendRate": 1.00, "currentPrice": 217.55, "dividendYield": 0.44}
        assert dividend_yield_fraction(info) == pytest.approx(0.0046, abs=1e-4)

    def test_sub_one_percent_yield_is_not_inflated(self):
        """The exact NVDA case: 0.44 is 0.44%, not 44%."""
        info = {"dividendRate": 1.00, "currentPrice": 217.55, "dividendYield": 0.44}
        assert dividend_yield_fraction(info) * 100 < 1.0

    def test_falls_back_to_percent_when_no_rate(self):
        assert dividend_yield_fraction({"dividendYield": 4.27}) == pytest.approx(0.0427)

    def test_falls_back_to_fraction_when_no_rate_and_value_is_small(self):
        """XONA.DE returned 0.0298 meaning 2.98% — yfinance is not consistent
        between tickers, so a blanket divide-by-100 is wrong too."""
        assert dividend_yield_fraction({"dividendYield": 0.0298}) == pytest.approx(0.0298)

    def test_no_dividend_gives_nan(self):
        assert np.isnan(dividend_yield_fraction({"dividendYield": None}))
        assert np.isnan(dividend_yield_fraction({}))

    def test_inflated_yield_no_longer_inflates_the_scorecard(self):
        """Each of the 20 affected tickers scored +6, and the scorecard is the
        screener's sort key."""
        base = {"Trailing P/E": 28.8, "P/S (TTM)": 20.0, "P/B": 27.0, "ROE": 0.30,
                "Operating Margin": 0.60, "Beta": 2.1}
        true_yield, _ = scorecard({**base, "Dividend Yield": 0.0046})
        inflated, _ = scorecard({**base, "Dividend Yield": 0.44})
        assert inflated - true_yield == 6


class TestCurrencyNormalisation:
    """13 of 67 tickers quoted in one currency and reported in another."""

    @staticmethod
    def _nvo():
        # Real NVO figures: USD quote, DKK accounts.
        return {
            "currency": "USD",
            "financialCurrency": "DKK",
            "marketCap": 201_643_180_032,
            "ebitda": 175_300_000_000,
            "totalRevenue": 329_430_990_848,
            "freeCashflow": 37_673_250_816,
            "totalCash": 44_982_001_664,
            "totalDebt": 140_126_994_432,
            "enterpriseToEbitda": 1.711,
            "priceToSalesTrailing12Months": 0.612,
        }

    def test_noop_when_currencies_agree(self):
        info = {"currency": "USD", "financialCurrency": "USD", "ebitda": 100, "marketCap": 1000}
        assert normalise_currency(info) == info

    def test_noop_when_currency_unknown(self):
        info = {"currency": "USD", "ebitda": 100}
        assert normalise_currency(info) == info

    def test_accounting_figures_move_to_the_quote_currency(self, monkeypatch):
        import SMAI.core.fx as fx_mod

        monkeypatch.setattr(fx_mod, "fx_rate", lambda a, b: 0.155)
        out = normalise_currency(self._nvo())
        assert out["ebitda"] == pytest.approx(175_300_000_000 * 0.155)
        assert out["freeCashflow"] == pytest.approx(37_673_250_816 * 0.155)
        assert out["marketCap"] == 201_643_180_032  # already quote currency, untouched
        assert out["_fx_applied"]["from"] == "DKK"
        assert out["_fx_applied"]["to"] == "USD"

    def test_ev_ebitda_becomes_plausible(self, monkeypatch):
        """1.71 was USD enterprise value over DKK EBITDA. The coherent figure,
        cross-checked against the Copenhagen listing, is about 8."""
        import SMAI.core.fx as fx_mod

        monkeypatch.setattr(fx_mod, "fx_rate", lambda a, b: 0.155)
        out = normalise_currency(self._nvo())
        assert 7.0 < out["enterpriseToEbitda"] < 9.0

    def test_price_to_sales_becomes_plausible(self, monkeypatch):
        import SMAI.core.fx as fx_mod

        monkeypatch.setattr(fx_mod, "fx_rate", lambda a, b: 0.155)
        out = normalise_currency(self._nvo())
        assert 3.5 < out["priceToSalesTrailing12Months"] < 4.5

    def test_enterprise_value_is_rebuilt_not_converted(self, monkeypatch):
        """yfinance's enterpriseValue is itself a mixed sum — quote-currency
        market cap plus reporting-currency net debt — so scaling it by an FX
        rate would not repair it."""
        import SMAI.core.fx as fx_mod

        monkeypatch.setattr(fx_mod, "fx_rate", lambda a, b: 0.155)
        out = normalise_currency(self._nvo())
        expected = out["marketCap"] + (out["totalDebt"] - out["totalCash"])
        assert out["enterpriseValue"] == pytest.approx(expected)

    def test_mixed_ratios_are_dropped_when_no_rate_available(self, monkeypatch):
        """Never leave a currency-mixed multiple in place: absent is honest."""
        import SMAI.core.fx as fx_mod

        monkeypatch.setattr(fx_mod, "fx_rate", lambda a, b: float("nan"))
        out = normalise_currency(self._nvo())
        assert out["enterpriseToEbitda"] is None
        assert out["priceToSalesTrailing12Months"] is None
        assert "_currency_note" in out

    def test_book_value_is_left_alone(self, monkeypatch):
        """Verified against the balance sheets: yfinance already converts
        bookValue to the quote currency (NVO 7.80 is USD, not the 57.99 DKK the
        accounts imply), so P/B is correct and must not be touched."""
        import SMAI.core.fx as fx_mod

        monkeypatch.setattr(fx_mod, "fx_rate", lambda a, b: 0.155)
        info = {**self._nvo(), "bookValue": 7.8033, "priceToBook": 5.8449}
        out = normalise_currency(info)
        assert out["bookValue"] == 7.8033
        assert out["priceToBook"] == 5.8449


class TestEvEbitdaCrossCheck:
    """The old cross-check compared yfinance's enterpriseToEbitda against
    enterpriseValue/ebitda — both the same vendor figure, so the measured
    divergence was 0.0% for NVO, BABA and UL and the fallback could never fire.
    """

    def test_vendor_value_is_kept_when_the_reconstruction_agrees(self):
        info = {"enterpriseToEbitda": 27.18, "ebitda": 100.0,
                "marketCap": 2500.0, "totalDebt": 200.0, "totalCash": 100.0}
        assert _ev_to_ebitda(info) == 27.18  # rebuilt = 26.0, within 35%

    def test_reconstruction_overrules_a_wild_vendor_value(self):
        info = {"enterpriseToEbitda": 1.71, "ebitda": 100.0,
                "marketCap": 800.0, "totalDebt": 100.0, "totalCash": 50.0}
        assert _ev_to_ebitda(info) == pytest.approx(8.5)

    def test_reconstruction_is_independent_of_enterprise_value(self):
        """enterpriseValue is deliberately absurd; the result must ignore it."""
        info = {"enterpriseToEbitda": None, "enterpriseValue": 37_000_000_000_000,
                "ebitda": 100.0, "marketCap": 800.0, "totalDebt": 100.0, "totalCash": 50.0}
        assert _ev_to_ebitda(info) == pytest.approx(8.5)


class TestEnrichRespectsCurrency:
    def test_statement_ratios_are_converted_before_being_divided_by_price(self):
        import pandas as pd

        fin = pd.DataFrame({"2025": [10.0, 1000.0]}, index=["Diluted EPS", "Total Revenue"])
        stmts = {"financials": fin, "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame()}
        # Price 45.61 USD against EPS of 10 DKK is the mixed P/E the old code built.
        out = enrich_info_from_stmts({}, stmts, last_price=45.61, fx=0.155)
        assert out["trailingPE"] == pytest.approx(45.61 / (10.0 * 0.155))

    def test_pure_statement_ratios_are_unaffected_by_the_factor(self):
        """ROE and margins divide one accounting figure by another, so the
        conversion cancels — a useful invariant to hold the fix to."""
        import pandas as pd

        fin = pd.DataFrame({"2025": [100.0, 1000.0]}, index=["Net Income", "Total Revenue"])
        bs = pd.DataFrame({"2025": [500.0]}, index=["Stockholders Equity"])
        stmts = {"financials": fin, "balance_sheet": bs, "cashflow": pd.DataFrame()}
        a = enrich_info_from_stmts({}, stmts, last_price=50.0, fx=1.0)
        b = enrich_info_from_stmts({}, stmts, last_price=50.0, fx=0.155)
        assert a["returnOnEquity"] == pytest.approx(b["returnOnEquity"])
        assert a["profitMargins"] == pytest.approx(b["profitMargins"])


class TestSnapshotRatiosIntegration:
    def test_nvo_shaped_payload_produces_sane_ratios(self, monkeypatch):
        import SMAI.core.fx as fx_mod

        monkeypatch.setattr(fx_mod, "fx_rate", lambda a, b: 0.155)
        info = normalise_currency({
            **TestCurrencyNormalisation._nvo(),
            "currentPrice": 45.61,
            "dividendRate": 1.77,
            "trailingPE": 11.12,
            "priceToBook": 5.84,
        })
        r = compute_snapshot_ratios(info)
        assert 7.0 < r["EV/EBITDA"] < 9.0
        assert 0.0 < r["Dividend Yield"] < 0.10
        assert r["Trailing P/E"] == 11.12


class TestCallSiteStability:
    """The 2026-08-29 outage: an earlier fix added a required-by-callers `fx`
    argument, and Streamlit Cloud re-ran the updated app.py against a cached
    SMAI.core.scoring from sys.modules. The new call site met the old signature
    and raised TypeError at argument binding, before a single line could run.
    An import-only smoke test did not catch it — imports succeeded; the call
    was what failed.
    """

    def test_works_without_the_fx_argument(self):
        """Callers must never need to pass fx — that coupling caused the outage."""
        import pandas as pd

        stmts = {"financials": pd.DataFrame(), "balance_sheet": pd.DataFrame(),
                 "cashflow": pd.DataFrame()}
        assert enrich_info_from_stmts({}, stmts, 100.0) == {}

    def test_conversion_factor_is_read_from_the_payload(self):
        import pandas as pd

        fin = pd.DataFrame({"2025": [10.0]}, index=["Diluted EPS"])
        stmts = {"financials": fin, "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame()}
        info = {"_fx_applied": {"from": "DKK", "to": "USD", "rate": 0.155, "fields": []}}
        out = enrich_info_from_stmts(info, stmts, last_price=45.61)
        assert out["trailingPE"] == pytest.approx(45.61 / (10.0 * 0.155))

    def test_missing_or_broken_fx_metadata_degrades_to_no_conversion(self):
        import pandas as pd

        fin = pd.DataFrame({"2025": [10.0]}, index=["Diluted EPS"])
        stmts = {"financials": fin, "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame()}
        for info in ({}, {"_fx_applied": None}, {"_fx_applied": {}},
                     {"_fx_applied": {"rate": None}}, {"_fx_applied": {"rate": 0}}):
            out = enrich_info_from_stmts(dict(info), stmts, last_price=45.61)
            assert out["trailingPE"] == pytest.approx(4.561)


class TestEntryPointExecutes:
    """Import-only checks pass on a broken app. Exercise the real call chain."""

    def test_screener_row_runs_end_to_end(self, monkeypatch):
        import SMAI.ui.pages.screener as scr

        info = {"currency": "USD", "financialCurrency": "DKK", "shortName": "Novo Nordisk A/S",
                "currentPrice": 45.61, "marketCap": 201_643_180_032, "ebitda": 27_171_500_000,
                "totalRevenue": 51_061_803_581, "freeCashflow": 5_839_353_876,
                "totalCash": 6_972_210_258, "totalDebt": 21_719_684_137,
                "sharesOutstanding": 3_346_158_124, "dividendRate": 1.77,
                "trailingPE": 11.12, "priceToBook": 5.84,
                "_fx_applied": {"from": "DKK", "to": "USD", "rate": 0.155, "fields": []}}
        import pandas as pd

        monkeypatch.setattr(scr, "yf_info", lambda t: info)
        monkeypatch.setattr(scr, "yf_statements", lambda t: {
            "financials": pd.DataFrame(), "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame()})
        monkeypatch.setattr(scr, "yf_price_history",
                            lambda t, p, i: pd.DataFrame({"Close": [45.61]}))

        row = scr._valuation_screen_row("NVO")
        assert row["Ticker"] == "NVO"
        assert 5.0 < row["EV/EBITDA"] < 12.0          # not the 1.71 of the bug
        assert 0.0 < row["DivYield%"] < 10.0          # not 3.9 -> 390
        assert row["Upside %"] < 100.0                # not +341.9


class TestPriceToBook:
    """yfinance's priceToBook is wrong on a minority of tickers, and NOT for
    currency reasons: 11 of ~30 diverged >35% from the balance sheet on
    2026-08-29, and 8 of those quote and report in the same currency.
    ASML came back at 1423.2, Toyota at 15.7 against a real ~1, BRK-B at 0.0.
    """

    @staticmethod
    def _stmts(equity):
        import pandas as pd

        return {"financials": pd.DataFrame(),
                "balance_sheet": pd.DataFrame({"2025": [equity]}, index=["Stockholders Equity"]),
                "cashflow": pd.DataFrame()}

    def test_absurd_vendor_value_is_replaced(self):
        """The reported ASML case: EUR 19.61B of equity over 384.1M shares is
        about EUR 51/share, so a bookValue of 1.19 cannot be right."""
        info = {"priceToBook": 1423.2374, "sharesOutstanding": 384_100_000,
                "currentPrice": 1696.16,
                "_fx_applied": {"from": "EUR", "to": "USD", "rate": 1.1587, "fields": []}}
        out = enrich_info_from_stmts(info, self._stmts(19_612_200_000), 1696.16)
        assert 25.0 < out["priceToBook"] < 35.0

    def test_zero_vendor_value_is_replaced(self):
        info = {"priceToBook": 0.0, "sharesOutstanding": 1_000_000_000, "currentPrice": 100.0}
        out = enrich_info_from_stmts(info, self._stmts(100_000_000_000), 100.0)
        assert out["priceToBook"] == pytest.approx(1.0)

    def test_plausible_vendor_value_is_kept(self):
        """The reconstruction is a gross-error detector, not a better number:
        it uses annual equity and can include minority interests. It must not
        displace a vendor figure that merely differs a little."""
        info = {"priceToBook": 5.84, "sharesOutstanding": 1_000_000_000, "currentPrice": 100.0}
        out = enrich_info_from_stmts(info, self._stmts(20_000_000_000), 100.0)
        assert out["priceToBook"] == 5.84   # rebuilt = 5.0, within 35%

    def test_equity_is_converted_before_reconstructing(self):
        info = {"priceToBook": 9999.0, "sharesOutstanding": 100_000_000, "currentPrice": 50.0,
                "_fx_applied": {"from": "DKK", "to": "USD", "rate": 0.155, "fields": []}}
        out = enrich_info_from_stmts(info, self._stmts(10_000_000_000), 50.0)
        assert out["priceToBook"] == pytest.approx(50.0 / (10_000_000_000 * 0.155 / 100_000_000))


class TestOpenSessionPrice:
    """The newest daily bar carries a NaN close while a session is open — 13 of
    13 tickers on 2026-08-29 — which silently disabled every price-based branch
    of enrich_info_from_stmts. The whole function did nothing during market
    hours, and nothing reported it.
    """

    def test_nan_price_falls_back_to_the_quote(self):
        import pandas as pd

        stmts = {"financials": pd.DataFrame({"2025": [5.0]}, index=["Diluted EPS"]),
                 "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame()}
        out = enrich_info_from_stmts({"currentPrice": 100.0}, stmts, float("nan"))
        assert out["trailingPE"] == pytest.approx(20.0)

    def test_regular_market_price_is_the_second_fallback(self):
        import pandas as pd

        stmts = {"financials": pd.DataFrame({"2025": [5.0]}, index=["Diluted EPS"]),
                 "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame()}
        out = enrich_info_from_stmts({"regularMarketPrice": 100.0}, stmts, float("nan"))
        assert out["trailingPE"] == pytest.approx(20.0)

    def test_a_real_price_is_preferred_over_the_quote(self):
        import pandas as pd

        stmts = {"financials": pd.DataFrame({"2025": [5.0]}, index=["Diluted EPS"]),
                 "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame()}
        out = enrich_info_from_stmts({"currentPrice": 999.0}, stmts, 100.0)
        assert out["trailingPE"] == pytest.approx(20.0)


class TestNegativeMultiplesAreNotCheap:
    """Reviving the statement path exposed this: VOD's trailing P/E of -83 hit
    the `pe <= 15` band and collected the maximum 18 points. A loss is not a
    discount.
    """

    BASE = {"Trailing P/E": 20.0, "P/S (TTM)": 2.0, "P/B": 3.0, "ROE": 0.20,
            "Operating Margin": 0.30, "Beta": 1.0, "Dividend Yield": 0.02}

    def test_negative_pe_scores_as_unavailable(self):
        good, _ = scorecard(self.BASE)
        loss, _ = scorecard({**self.BASE, "Trailing P/E": -83.06})
        na, _ = scorecard({**self.BASE, "Trailing P/E": float("nan")})
        assert loss == na < good

    def test_negative_book_value_scores_as_unavailable(self):
        """BKNG carries negative equity; P/B -14.45 must not read as 'cheap'."""
        na, _ = scorecard({**self.BASE, "P/B": float("nan")})
        neg, _ = scorecard({**self.BASE, "P/B": -14.45})
        assert neg == na
