from app.config import get_settings
from app.services.scanner_service import run_scan
from app.services.telegram_service import TelegramService
from app.utils.logger import configure_logging


def build_telegram_message(result) -> str:
    lines = [
        "📈 *NSE F&O REVERSAL SCANNER*",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"*{result.message}*",
        "",
    ]

    for index, candidate in enumerate(result.candidates, start=1):
        lines.extend(
            [
                f"{index}. *{candidate.symbol}* {candidate.signal}",
                f"💰 Price: ₹{candidate.price}",
                f"📉 52W High: ₹{candidate.high_52w}",
                f"📉 Fall: {candidate.fall_pct}%",
                f"📈 EMA9: ₹{candidate.ema9}",
                f"📈 EMA25: ₹{candidate.ema25}",
                f"📈 EMA99: ₹{candidate.ema99}",
                f"📊 RSI: {candidate.rsi}",
                f"📊 Volume Ratio: {candidate.volume_ratio}x",
                f"⭐ Score: {candidate.score}/100",
                f"🔄 9/25 Cross: {'YES' if candidate.ema9_25_cross else 'NO'}",
                f"🔄 25/99 Cross: {'YES' if candidate.ema25_99_cross else 'NO'}",
                f"📐 Near EMA99: {'YES' if candidate.ema99_distance_pct <= 15 else 'NO'}",
                "",
            ]
        )

    lines.extend(["━━━━━━━━━━━━━━━━━━━━", "⚠️ Technical scanner only"])
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
            logger.error("Telegram notification failed: %s", exc)
            return 1
    else:
        logger.warning("Telegram not configured; notification skipped")

    logger.info("Application completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
