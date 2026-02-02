from __future__ import annotations

import datetime as dt
from typing import Dict

import pandas as pd
import requests
import streamlit as st

POS_WORDS = {
    "beat", "beats", "strong", "upside", "bull", "bullish", "growth", "buy", "accumulate",
    "undervalued", "record", "profit", "surge", "upgrade", "outperform",
}
NEG_WORDS = {
    "miss", "missed", "weak", "downside", "bear", "bearish", "sell", "overvalued", "fraud",
    "drop", "plunge", "lawsuit", "warning", "downgrade", "underperform",
}


def lex_sentiment(text: str) -> float:
    if not text:
        return 0.0
    t = text.lower()
    pos = sum(w in t for w in POS_WORDS)
    neg = sum(w in t for w in NEG_WORDS)
    if pos == 0 and neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


@st.cache_data(ttl=60 * 20, show_spinner=False)
def fetch_stocktwits(ticker: str, limit: int = 40) -> pd.DataFrame:
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()
        j = r.json()
        msgs = (j.get("messages") or [])[:limit]
        rows = []
        for m in msgs:
            body = m.get("body", "")
            created = m.get("created_at", "")
            user = (m.get("user") or {}).get("username", "")
            rows.append({
                "source": "stocktwits",
                "created_at": created,
                "user": user,
                "text": body,
                "sentiment": lex_sentiment(body),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60 * 20, show_spinner=False)
def fetch_reddit_search(query: str, limit: int = 40) -> pd.DataFrame:
    """
    Public Reddit search endpoint (no auth). Rate-limits can happen; keep small & cached.
    """
    url = "https://www.reddit.com/search.json"
    headers = {"User-Agent": "SMAI/1.0 (Streamlit; personal analysis app)"}
    params = {"q": query, "sort": "new", "limit": min(limit, 50), "t": "week"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        if r.status_code != 200:
            return pd.DataFrame()
        j = r.json()
        children = (((j.get("data") or {}).get("children")) or [])[:limit]
        rows = []
        for c in children:
            d = c.get("data") or {}
            title = d.get("title", "")
            created_utc = d.get("created_utc")
            created_at = dt.datetime.utcfromtimestamp(created_utc).isoformat() if created_utc else ""
            rows.append({
                "source": "reddit",
                "created_at": created_at,
                "user": d.get("author", ""),
                "subreddit": d.get("subreddit", ""),
                "text": title,
                "sentiment": lex_sentiment(title + " " + (d.get("selftext") or "")),
                "permalink": "https://www.reddit.com" + (d.get("permalink") or ""),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def sentiment_summary(df: pd.DataFrame) -> Dict[str, float]:
    if df is None or df.empty:
        return {"count": 0, "avg": 0.0, "pos_share": 0.0, "neg_share": 0.0}
    s = df["sentiment"].fillna(0.0)
    return {
        "count": float(len(df)),
        "avg": float(s.mean()),
        "pos_share": float((s > 0.05).mean()),
        "neg_share": float((s < -0.05).mean()),
    }
