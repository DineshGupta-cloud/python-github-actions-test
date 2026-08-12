from app.config import get_settings
from app.services.scanner_service import run_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def main() -> int:
    settings = get_settings()
    logger = configure_logging(settings.log_level)

    logger.info("Application started: %s", settings.app_name)
    logger.info("Environment: %s", settings.environment)

    result = run_scan()
    logger.info("Scanner status: %s", result.status)
    logger.info("%s", result.message)

    telegram = TelegramService()
    if telegram.is_configured():
        message = (
            "🤖 Python GitHub Actions\n\n"
            "✅ Application is running\n"
            f"Environment: {settings.environment}\n"
            f"Scanner: {result.status}\n"
            f"Message: {result.message}"
        )
        telegram.send_message(message)
        logger.info("Telegram notification sent successfully")
    else:
        logger.info("Telegram not configured; notification skipped")

    logger.info("Application completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
