from app.config import get_settings
from app.services.scanner_service import run_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def telegram_messages(result):
    candidates = sorted(
        result.candidates,
        key=lambda c: (
            c.score,
            c.ema9_25_cross,
            c.ema25_99_cross,
            -(c.ema99_distance_pct),
            c.rsi,
        ),
        reverse=True,
    )[:20]

    messages = []
    header = f"📊 NSE TOP 20 REVERSAL SCANNER\n📅 EOD\n{result.message}\n"

    for start in range(0, len(candidates), 5):
        lines = [header]
        for i, c in enumerate(candidates[start:start + 5], start + 1):
            lines.extend([
                f"{i}. {c.symbol}",
                f"Price: ₹{c.price} | 52W High: ₹{c.high_52w} | Fall: {c.fall_pct}%",
                f"EMA9: ₹{c.ema9} | EMA25: ₹{c.ema25} | EMA99: ₹{c.ema99}",
                f"RSI: {c.rsi} | Volume: {c.volume_ratio}x",
                f"9/25 Cross: {'YES' if c.ema9_25_cross else 'NO'} | 25/99 Cross: {'YES' if c.ema25_99_cross else 'NO'}",
                f"Near EMA99: {'YES' if c.ema99_distance_pct <= 15 else 'NO'}",
                f"Score: {c.score}/100 | Signal: {c.signal}",
                "",
            ])
        messages.append("\n".join(lines)[:3500])

    return messages or [header + "\nNo matching stocks."]


def main() -> int:
    settings = get_settings()
    logger = configure_logging(settings.log_level)
    logger.info("Application started: %s", settings.app_name)
    logger.info("Environment: %s", settings.environment)

    result = run_scan()
    logger.info("Scanner status: %s", result.status)
    logger.info("%s", result.message)

    telegram = TelegramService()
    logger.info("Telegram configured: %s", telegram.is_configured())

    if telegram.is_configured():
        try:
            messages = telegram_messages(result)
            for message in messages:
                telegram.send_message(message)
            logger.info("Telegram notification sent successfully (%d messages)", len(messages))
        except Exception as exc:
            logger.warning("Telegram skipped: %s", exc)

    logger.info("Application completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
