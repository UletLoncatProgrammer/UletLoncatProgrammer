from __future__ import annotations

import os

import requests

from .analysis import Alert


def notify_console(alerts: list[Alert]) -> None:
    for alert in alerts:
        print(f"[ALERT] {alert.ticker}: {alert.message}")


def notify_telegram(alerts: list[Alert]) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    text = "\n".join(f"⚠️ {a.message}" for a in alerts)
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    resp.raise_for_status()
    return True


def notify_webhook(alerts: list[Alert], env_var: str) -> bool:
    url = os.environ.get(env_var)
    if not url:
        return False
    text = "\n".join(f"⚠️ {a.message}" for a in alerts)
    resp = requests.post(url, json={"content": text, "text": text}, timeout=15)
    resp.raise_for_status()
    return True


def notify_github_issue(alerts: list[Alert]) -> bool:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return False
    body = "\n".join(f"- {a.message}" for a in alerts)
    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"title": f"Stock alerts — {len(alerts)} triggered", "body": body, "labels": ["stock-alert"]},
        timeout=15,
    )
    resp.raise_for_status()
    return True


def send_notifications(alerts: list[Alert]) -> None:
    if not alerts:
        print("No alerts triggered.")
        return

    notify_console(alerts)

    sent_externally = False
    sent_externally |= notify_telegram(alerts)
    sent_externally |= notify_webhook(alerts, "DISCORD_WEBHOOK_URL")
    sent_externally |= notify_webhook(alerts, "SLACK_WEBHOOK_URL")

    if not sent_externally and os.environ.get("GITHUB_ACTIONS") == "true":
        notify_github_issue(alerts)
