from app.config import get_settings
from app.services.high_52w_screener import run_high_52w_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def telegram_messages(result):
    candidates = result.candidates
    messages = []
    header = (
        "🚀 NSE 52W HIGH MOMENTUM SCREENER\n"
        "📅 EOD\n"
        "🎯 ALL filters must pass\n"
        "• Distance from 52W High <= 15%\n"
        "• Price > EMA20 > EMA50\n"
        "• RSI > 55\n"
        "• Volume Ratio > 1.2x\n"
        f"{result.message}\n"
    )

    for start in range(0, len(candidates), 5):
        lines = [header]
        for i, c in enumerate(candidates[start:start + 5], start + 1):
            lines.extend([
                f"{i}. {c.symbol}",
                f"Price: ₹{c.price} | 52W High: ₹{c.high_52w} | Below High: {c.below_high_pct}%",
                f"EMA20: ₹{c.ema20} | EMA50: ₹{c.ema50}",
                f"RSI: {c.rsi} | Volume Ratio: {c.volume_ratio}x",
                f"Score: {c.score}/100 | Signal: {c.signal}",
                "",
            ])
        messages.append("\n".join(lines)[:3500])

    return messages or [header + "\nNo matching stocks."]


def main() -> int:
    settings = get_settings()
    logger = configure_logging(settings.log_level)
    logger.info("52W High Momentum Screener started: %s", settings.app_name)

    result = run_high_52w_scan()
    logger.info("52W High Momentum Screener status: %s", result.status)
    logger.info("%s", result.message)

    telegram = TelegramService()
    logger.info("Telegram configured: %s", telegram.is_configured())

    if telegram.is_configured():
        try:
            messages = telegram_messages(result)
            for message in messages:
                telegram.send_message(message)
            logger.info("52W High Telegram notification sent (%d messages)", len(messages))
        except Exception as exc:
            logger.warning("Telegram skipped: %s", exc)

    logger.info("52W High Momentum Screener completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
