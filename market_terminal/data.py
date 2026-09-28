from __future__ import annotations

from functools import lru_cache
from typing import Any
import pandas as pd
import yfinance as yf

NIFTY50 = [
    "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BEL","BHARTIARTL","BPCL","BRITANNIA","CIPLA",
    "COALINDIA","DRREDDY","EICHERMOT","ETERNAL","GRASIM","HCLTECH","HDFCBANK",
    "HDFCLIFE","HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK",
    "INFY","ITC","JIOFIN","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","MAXHEALTH",
    "NESTLEIND","NTPC","ONGC","POWERGRID","RELIANCE","SBILIFE","SBIN","SHRIRAMFIN",
    "SUNPHARMA","TATACONSUM","TATAMOTORS","TATASTEEL","TCS","TECHM","TITAN","TRENT",
    "ULTRACEMCO","WIPRO"
]

def symbol(ticker: str) -> str:
    return ticker if ticker.endswith(".NS") else f"{ticker}.NS"

def rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, pd.NA)
    return float((100 - (100 / (1 + rs))).iloc[-1])

@lru_cache(maxsize=128)
def history(ticker: str, period: str = "1y") -> pd.DataFrame:
    df = yf.download(symbol(ticker), period=period, interval="1d", auto_adjust=False, progress=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna(subset=["Close"])

def stock_snapshot(ticker: str) -> dict[str, Any] | None:
    df = history(ticker)
    if len(df) < 120:
        return None
    close, volume = df["Close"], df["Volume"]
    ema9, ema25, ema99 = close.ewm(span=9, adjust=False).mean(), close.ewm(span=25, adjust=False).mean(), close.ewm(span=99, adjust=False).mean()
    price=float(close.iloc[-1]); high52=float(close.max()); avgvol=float(volume.tail(20).mean())
    vol_ratio=float(volume.iloc[-1] / avgvol) if avgvol else 0
    return {
        "symbol": ticker, "price": round(price,2), "change_pct": round(float((price/close.iloc[-2]-1)*100),2),
        "high_52w": round(high52,2), "fall_pct": round((1-price/high52)*100,2),
        "ema9": round(float(ema9.iloc[-1]),2), "ema25": round(float(ema25.iloc[-1]),2),
        "ema99": round(float(ema99.iloc[-1]),2), "rsi": round(rsi(close),2),
        "volume_ratio": round(vol_ratio,2),
        "above_ema99": price >= float(ema99.iloc[-1]),
        "near_ema99_pct": round(abs(price-float(ema99.iloc[-1]))/float(ema99.iloc[-1])*100,2),
        "date": str(df.index[-1].date())
    }

def screener() -> list[dict[str, Any]]:
    rows=[x for t in NIFTY50 if (x:=stock_snapshot(t))]
    return sorted(rows, key=lambda x: x["change_pct"], reverse=True)
