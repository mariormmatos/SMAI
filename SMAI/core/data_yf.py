from __future__ import annotations

from typing import Dict, List

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

from .formatting import ensure_date_col


@st.cache_data(ttl=60 * 20, show_spinner=False)
def yf_price_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60 * 60, show_spinner=False)
def yf_info(ticker: str) -> Dict:
    t = yf.Ticker(ticker)
    result: Dict = {}
    try:
        result = t.info or {}
    except Exception:
        pass

    if not result:
        try:
            fi = t.fast_info
            result = {
                "currency": getattr(fi, "currency", None),
                "currentPrice": getattr(fi, "lastPrice", None),
                "previousClose": getattr(fi, "previousClose", None),
                "regularMarketPreviousClose": getattr(fi, "regularMarketPreviousClose", None),
                "marketCap": getattr(fi, "marketCap", None),
                "dayHigh": getattr(fi, "dayHigh", None),
                "dayLow": getattr(fi, "dayLow", None),
                "fiftyTwoWeekHigh": getattr(fi, "yearHigh", None),
                "fiftyTwoWeekLow": getattr(fi, "yearLow", None),
                "fiftyDayAverage": getattr(fi, "fiftyDayAverage", None),
                "twoHundredDayAverage": getattr(fi, "twoHundredDayAverage", None),
                "regularMarketVolume": getattr(fi, "lastVolume", None),
                "sharesOutstanding": getattr(fi, "shares", None),
            }
            result = {k: v for k, v in result.items() if v is not None}
        except Exception:
            pass

    return result


@st.cache_data(ttl=60 * 60, show_spinner=False)
def yf_statements(ticker: str) -> Dict[str, pd.DataFrame]:
    t = yf.Ticker(ticker)
    out: Dict[str, pd.DataFrame] = {}
    for key, attr in [
        ("financials", "financials"),
        ("quarterly_financials", "quarterly_financials"),
        ("balance_sheet", "balance_sheet"),
        ("quarterly_balance_sheet", "quarterly_balance_sheet"),
        ("cashflow", "cashflow"),
        ("quarterly_cashflow", "quarterly_cashflow"),
    ]:
        try:
            out[key] = getattr(t, attr)
        except Exception:
            out[key] = pd.DataFrame()
    return out


@st.cache_data(ttl=60 * 30, show_spinner=False)
def yf_news(ticker: str) -> List[Dict]:
    """Fetch ticker news — falls back to Google News RSS if Yahoo Finance is blocked."""
    try:
        t = yf.Ticker(ticker)
        news = t.news or []
        if news and isinstance(news, list):
            return news[:30]
    except Exception:
        pass
    return []


@st.cache_data(ttl=60 * 20, show_spinner=False)
def fetch_google_news_rss(query: str, limit: int = 20) -> List[Dict]:
    """Fetch news from Google News RSS — reliable from cloud IPs."""
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return []
        txt = r.text
    except Exception:
        return []

    items: List[Dict] = []
    for chunk in txt.split("<item>")[1:]:
        if "</item>" not in chunk:
            continue
        item = chunk.split("</item>")[0]
        title = _extract_tag(item, "title")
        link = _extract_tag(item, "link") or _extract_tag(item, "guid")
        pub = _extract_tag(item, "pubDate")
        source = _extract_tag(item, "source")
        if title:
            items.append({"title": title, "link": link, "published": pub, "publisher": source})
        if len(items) >= limit:
            break
    return items


def _extract_tag(text: str, tag: str) -> str:
    start = f"<{tag}"
    end = f"</{tag}>"
    if start in text and end in text:
        block = text.split(start)[1]
        # skip attributes inside the opening tag
        if ">" in block:
            block = block.split(">", 1)[1]
        return _clean_xml(block.split(end)[0].strip())
    return ""


def _clean_xml(text: str) -> str:
    return (
        (text or "")
        .replace("&amp;", "&")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .strip()
    )


def statement_to_timeseries(df: pd.DataFrame, rows: List[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out = out.loc[[r for r in rows if r in out.index]]
    if out.empty:
        return pd.DataFrame()
    out = out.transpose().reset_index().rename(columns={"index": "Date"})
    out = ensure_date_col(out, "Date")
    return out
