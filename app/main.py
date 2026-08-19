from app.config import get_settings
from app.services.scanner_service import run_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def build_telegram_message(result) -> str:
    lines = ["NSE F&O SCANNER", "", str(result.message), ""]
    for index, candidate in enumerate(result.candidates[:5], start=1):
        lines.append(
            f"{index}. {candidate.symbol} | {candidate.price} | "
            f"Fall {candidate.fall_pct}% | Score {candidate.score}"
        )
    if not result.candidates:
        lines.append("No matching stocks.")
    return "\n".join(lines)[:3000]


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
            candidate.symbol, candidate.price, candidate.fall_pct,
            candidate.ema9, candidate.ema25, candidate.ema99,
            candidate.rsi, candidate.score, candidate.signal,
        )

    telegram = TelegramService()
    logger.info("Telegram configured: %s", telegram.is_configured())

    if telegram.is_configured():
        try:
            message = build_telegram_message(result)
            logger.info("Telegram message length: %d", len(message))
            telegram.send_message(message)
            logger.info("Telegram notification sent successfully")
        except Exception as exc:
            logger.warning("Telegram notification skipped: %s", exc)
    else:
        logger.warning("Telegram not configured; notification skipped")

    logger.info("Application completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
