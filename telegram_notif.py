"""Sends alert messages to Telegram via a bot."""
from __future__ import annotations

import os

import requests


def send_message(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram not configured (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing); skipping notification.")
        return False

    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    if not resp.ok:
        print(f"Telegram sendMessage failed ({resp.status_code}): {resp.text}")
        return False
    return True
