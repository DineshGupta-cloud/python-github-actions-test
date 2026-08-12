import pytest

from app.services.telegram_service import TelegramService


def test_telegram_requires_configuration(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    service = TelegramService()

    assert service.is_configured() is False
    with pytest.raises(RuntimeError):
        service.send_message("test")


def test_telegram_configuration(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat")

    service = TelegramService()

    assert service.is_configured() is True
