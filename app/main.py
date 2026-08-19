from app.config import get_settings
from app.services.scanner_service import run_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def build_telegram_message(result):
    # Intentionally tiny: one line only.
    return f"NSE SCANNER: {result.message[:500]}"


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
            telegram.send_message(build_telegram_message(result))
            logger.info("Telegram notification sent successfully")
        except Exception as exc:
            logger.warning("Telegram skipped: %s", exc)

    logger.info("Application completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
