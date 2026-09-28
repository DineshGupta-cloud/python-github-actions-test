from __future__ import annotations

from app.services.telegram_service import TelegramService
from .data import NIFTY50, history


def build_signal(ticker: str) -> dict | None:
    df = history(ticker)
    if len(df) < 120:
        return None

    close = df["Close"]
    volume = df["Volume"]
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema25 = close.ewm(span=25, adjust=False).mean()
    ema99 = close.ewm(span=99, adjust=False).mean()

    price = float(close.iloc[-1])
    rsi_delta = close.diff()
    gain = rsi_delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-rsi_delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    avg_volume = float(volume.tail(20).mean())
    volume_ratio = float(volume.iloc[-1] / avg_volume) if avg_volume else 0.0
    high52 = float(close.tail(252).max())
    fall_pct = (1 - price / high52) * 100 if high52 else 0.0

    cross_up = ema9.iloc[-1] > ema25.iloc[-1] and ema9.iloc[-2] <= ema25.iloc[-2]
    cross_down = ema9.iloc[-1] < ema25.iloc[-1] and ema9.iloc[-2] >= ema25.iloc[-2]
    near_ema99 = abs(price - ema99.iloc[-1]) / ema99.iloc[-1] * 100 <= 2
    breakout_52w = price >= high52 * 0.995
    volume_surge = volume_ratio >= 1.5

    signals = []
    if cross_up:
        signals.append("EMA9 crossed above EMA25")
    if cross_down:
        signals.append("EMA9 crossed below EMA25")
    if breakout_52w:
        signals.append("Near 52W high")
    if near_ema99:
        signals.append("Near EMA99")
    if volume_surge:
        signals.append("Volume surge")

    if not signals:
        return None

    return {
        "symbol": ticker,
        "price": price,
        "change_pct": (price / float(close.iloc[-2]) - 1) * 100,
        "rsi": rsi,
        "ema9": float(ema9.iloc[-1]),
        "ema25": float(ema25.iloc[-1]),
        "ema99": float(ema99.iloc[-1]),
        "volume_ratio": volume_ratio,
        "high52": high52,
        "fall_pct": fall_pct,
        "signals": signals,
        "date": str(df.index[-1].date()),
    }


def build_message() -> str:
    rows = [build_signal(t) for t in NIFTY50]
    rows = [r for r in rows if r]
    rows.sort(key=lambda r: (len(r["signals"]), r["volume_ratio"]), reverse=True)

    if not rows:
        return "EQSIS-style EOD Terminal\nNo qualifying signals today."

    lines = [
        "📊 EQSIS-style EOD Market Terminal",
        f"Date: {rows[0]['date']}",
        "Signals are scanner conditions, not investment advice.",
        "",
    ]

    for r in rows[:20]:
        lines.extend([
            f"• {r['symbol']} ₹{r['price']:.2f} ({r['change_pct']:+.2f}%)",
            f"  RSI {r['rsi']:.1f} | EMA9 {r['ema9']:.2f} | EMA25 {r['ema25']:.2f} | EMA99 {r['ema99']:.2f}",
            f"  Vol {r['volume_ratio']:.1f}x | 52W high ₹{r['high52']:.2f} | fall {r['fall_pct']:.1f}%",
            f"  Signals: {', '.join(r['signals'])}",
            "",
        ])

    return "\n".join(lines)


def main() -> None:
    service = TelegramService()
    if not service.is_configured():
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    service.send_message(build_message())
    print("EQSIS-style Telegram notification sent.")


if __name__ == "__main__":
    main()
