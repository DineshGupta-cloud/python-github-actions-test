from __future__ import annotations

import yfinance as yf
import pandas as pd


class MarketDataService:
    """Fetch daily OHLCV market data for an NSE symbol."""

    def fetch_daily(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
        data = yf.download(ticker, period=period, interval="1d", auto_adjust=False, progress=False)

        if data.empty:
            raise ValueError(f"No market data returned for {symbol}")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        required = {"Close", "High", "Volume"}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f"Missing market-data columns for {symbol}: {sorted(missing)}")

        return data.dropna(subset=["Close", "High"])
