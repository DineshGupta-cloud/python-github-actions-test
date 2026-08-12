from app.config import get_settings
from app.services.scanner_service import run_scan
from app.utils.logger import configure_logging


def main() -> int:
    settings = get_settings()
    logger = configure_logging(settings.log_level)

    logger.info("Application started: %s", settings.app_name)
    logger.info("Environment: %s", settings.environment)

    result = run_scan()
    logger.info("Scanner status: %s", result.status)
    logger.info("%s", result.message)
    logger.info("Application completed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
