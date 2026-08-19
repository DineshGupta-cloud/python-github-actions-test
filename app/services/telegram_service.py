import os
from typing import Any

import requests


class TelegramService:
    """Send messages to Telegram safely within the Bot API message limit."""

    MAX_MESSAGE_LENGTH = 4000

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, message: str) -> bool:
        if not self.is_configured():
            raise RuntimeError(
                "Telegram is not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
            )

        message = str(message).strip()
        if not message:
            return True

        # Telegram allows up to 4096 characters. Keep a safety margin.
        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[: self.MAX_MESSAGE_LENGTH - 20].rstrip() + "\n...truncated"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        response = requests.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": message,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )

        if response.status_code != 200:
            try:
                details: Any = response.json()
                description = details.get("description", "Unknown Telegram API error")
            except ValueError:
                description = response.text[:200]
            raise RuntimeError(
                f"Telegram API returned HTTP {response.status_code}: {description}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("Telegram API returned invalid JSON") from exc

        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram API rejected the message: {data.get('description', 'Unknown error')}"
            )

        return True
