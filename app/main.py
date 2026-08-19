from app.config import get_settings
from app.services.scanner_service import run_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def build_telegram_message(result) -> str:
    lines = [
        "📈 NSE F&O REVERSAL SCANNER",
        "━━━━━━━━━━━━━━━━━━━━",
        f"{result.message}",
        "",
    ]

    # Telegram alert: send only the top 10 candidates to keep it concise.
    for index, candidate in enumerate(result.candidates[:10], start=1):
        lines.append(
            f"{index}. {candidate.symbol} {candidate.signal} | "
            f"₹{candidate.price} | Fall {candidate.fall_pct}% | "
            f"EMA {candidate.ema9}/{candidate.ema25}/{candidate.ema99} | "
            f"RSI {candidate.rsi} | Score {candidate.score}"
        )

    if not result.candidates:
        lines.append("No matching stocks found.")
    elif len(result.candidates) > 10:
        lines.append(f"\n+ {len(result.candidates) - 10} more candidates in logs.")

    lines.extend(["", "━━━━━━━━━━━━━━━━━━━━", "⚠️ Technical scanner only"])
    return "\n".join(lines)


def main() -> int:
    settings = get_settings()
    logger = configure_logging(settings.log_level)

    logger.info("Application started: %s", settings.app_name)
    logger.info("Environment: %s", settings.environment)

    result = run_scan()
    logger.info("Scanner status: %s", result.status)
    logger.info("%s", result.message)

    for candidate in result.candidates:
        logger.info(
            "%s | Price=%s | Fall=%s%% | EMA9=%s | EMA25=%s | EMA99=%s | RSI=%s | Score=%s | %s",
            candidate.symbol,
            candidate.price,
            candidate.fall_pct,
            candidate.ema9,
            candidate.ema25,
            candidate.ema99,
            candidate.rsi,
            candidate.score,
            candidate.signal,
        )

    telegram = TelegramService()
    logger.info("Telegram configured: %s", telegram.is_configured())

    if telegram.is_configured():
        try:
            telegram.send_message(build_telegram_message(result))
            logger.info("Telegram API: HTTP 200 / message accepted")
            logger.info("Telegram notification sent successfully")
        except Exception as exc:
            # Telegram failure must not make the scanner fail.
            logger.warning("Telegram notification skipped: %s", exc)
    else:
        logger.warning("Telegram not configured; notification skipped")

    logger.info("Application completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
