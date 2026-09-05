from app.config import get_settings
from app.services.high_52w_screener import run_high_52w_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def telegram_messages(result):
    candidates = result.candidates
    messages = []
    header = (
        "🚀 NSE 52W HIGH SCREENER\n"
        "📅 EOD\n"
        "🎯 Filter: Within 15% of 52W High\n"
        f"{result.message}\n"
    )

    for start in range(0, len(candidates), 5):
        lines = [header]
        for i, c in enumerate(candidates[start:start + 5], start + 1):
            lines.extend([
                f"{i}. {c.symbol}",
                f"Price: ₹{c.price} | 52W High: ₹{c.high_52w} | Below High: {c.below_high_pct}%",
                f"EMA9: ₹{c.ema9} | EMA25: ₹{c.ema25} | EMA99: ₹{c.ema99}",
                f"RSI: {c.rsi} | Volume: {c.volume_ratio}x",
                f"9/25 Cross: {'YES' if c.ema9_25_cross else 'NO'} | 25/99 Cross: {'YES' if c.ema25_99_cross else 'NO'}",
                f"EMA Trend: {'BULLISH' if c.ema9_above_25 and c.ema25_above_99 else 'MIXED'}",
                f"Score: {c.score}/100 | Signal: {c.signal}",
                "",
            ])
        messages.append("\n".join(lines)[:3500])

    return messages or [header + "\nNo matching stocks."]


def main() -> int:
    settings = get_settings()
    logger = configure_logging(settings.log_level)
    logger.info("52W High Screener started: %s", settings.app_name)

    result = run_high_52w_scan()
    logger.info("52W High Screener status: %s", result.status)
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

    logger.info("52W High Screener completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
