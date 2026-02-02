from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def safe_float(value: Any, default: float = np.nan) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def is_bad(value: float) -> bool:
    return value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value)))


def fmt_num(value: float) -> str:
    if is_bad(value):
        return "N/A"
    abs_v = abs(float(value))
    if abs_v >= 1e12:
        return f"{value/1e12:.2f}T"
    if abs_v >= 1e9:
        return f"{value/1e9:.2f}B"
    if abs_v >= 1e6:
        return f"{value/1e6:.2f}M"
    if abs_v >= 1e3:
        return f"{value/1e3:.2f}K"
    return f"{value:.2f}"


def fmt_pct(value: float, digits: int = 2) -> str:
    if is_bad(value):
        return "N/A"
    return f"{value*100:.{digits}f}%"


def fmt_ratio(value: float, digits: int = 2) -> str:
    return "N/A" if is_bad(value) else f"{value:.{digits}f}"


def fmt_compact(value: Any) -> str:
    try:
        v = float(value)
    except Exception:
        return "-"
    abs_v = abs(v)
    if abs_v >= 1e12:
        return f"{v/1e12:.2f}T"
    if abs_v >= 1e9:
        return f"{v/1e9:.2f}B"
    if abs_v >= 1e6:
        return f"{v/1e6:.2f}M"
    if abs_v >= 1e3:
        return f"{v/1e3:.2f}K"
    return f"{v:.2f}"


def coerce_dt_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=False)


def ensure_date_col(df: pd.DataFrame, idx_name: str = "Date") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if idx_name not in out.columns:
        if isinstance(out.index, pd.DatetimeIndex):
            out.insert(0, idx_name, out.index)
        else:
            out = out.reset_index()
            if "index" in out.columns:
                out.rename(columns={"index": idx_name}, inplace=True)
    out[idx_name] = pd.to_datetime(out[idx_name], errors="coerce")
    out = out.dropna(subset=[idx_name])
    return out
