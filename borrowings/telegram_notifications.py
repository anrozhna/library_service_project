import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(message: str) -> None:
    """Send a message to the configured Telegram chat."""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to send Telegram notification: %s", e)
