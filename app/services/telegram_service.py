import os

import requests


class TelegramService:
    """Send short Telegram notifications safely."""

    MAX_LENGTH = 3000

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, message: str) -> bool:
        if not self.is_configured():
            raise RuntimeError("Telegram is not configured")

        message = str(message).strip()[: self.MAX_LENGTH]

        if not message:
            return True

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        response = requests.post(
            url,
            data={
                "chat_id": self.chat_id,
                "text": message,
            },
            timeout=15,
        )

        if response.status_code != 200:
            try:
                description = response.json().get("description", response.text)
            except ValueError:
                description = response.text

            raise RuntimeError(
                f"Telegram API returned HTTP {response.status_code}: {description}"
            )

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram API rejected message: {data.get('description', 'Unknown error')}"
            )

        return True
