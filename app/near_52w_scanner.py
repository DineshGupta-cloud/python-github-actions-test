import logging
from datetime import datetime

import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("near_52w_scanner")

# Keep this scanner independent from the EMA 9/25/99 scanner.
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "AXISBANK.NS",
    "KOTAKBANK.NS", "MARUTI.NS", "M&M.NS", "SUNPHARMA.NS", "NTPC.NS",
    "TITAN.NS", "ADANIENT.NS", "BAJFINANCE.NS", "HINDUNILVR.NS", "TATASTEEL.NS",
]

NEAR_HIGH_PCT = 5.0


def scan_stock(ticker: str):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=False)
        if df.empty:
            return None

        close = float(df["Close"].iloc[-1].item())
        high_52w = float(df["High"].max().item())
        distance_pct = ((high_52w - close) / high_52w) * 100

        if distance_pct <= NEAR_HIGH_PCT:
            return {
                "symbol": ticker.replace(".NS", ""),
                "price": round(close, 2),
                "high_52w": round(high_52w, 2),
                "distance_pct": round(distance_pct, 2),
            }
    except Exception as exc:
        logger.warning("%s failed: %s", ticker, exc)

    return None


def main():
    logger.info("Near 52-week high scanner started: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    results = []

    for ticker in TICKERS:
        result = scan_stock(ticker)
        if result:
            results.append(result)

    results.sort(key=lambda x: x["distance_pct"])

    print("\n🔥 STOCKS NEAR 52-WEEK HIGH")
    print(f"Within {NEAR_HIGH_PCT}% of 52-week high\n")

    if not results:
        print("No stocks found.")
        return

    for i, stock in enumerate(results, 1):
        print(
            f"{i}. {stock['symbol']} | "
            f"Price: ₹{stock['price']} | "
            f"52W High: ₹{stock['high_52w']} | "
            f"Distance: {stock['distance_pct']}%"
        )


if __name__ == "__main__":
    main()
