"""Polls Telegram for new messages and answers them with Claude, including live stock quotes."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anthropic
import requests

from stock_alert import compute_rsi, fetch_history

MODEL = "claude-sonnet-5"
BOT_USERNAME = "SahamUletBot"

SYSTEM_PROMPT = (
    "You are a private financial assistant for the user's Indonesian stock watchlist. "
    "Use the get_stock_quote tool to fetch live price/RSI data whenever asked about a "
    "specific ticker. Yahoo Finance ticker format: Indonesian stocks need a .JK suffix "
    "(e.g. BBCA.JK), US stocks don't (e.g. AAPL). Answer other questions from your own "
    "knowledge, and say clearly when you're not certain or when data may be outdated. "
    "Keep replies short and suited for a Telegram chat."
)

TOOLS = [
    {
        "name": "get_stock_quote",
        "description": "Get the latest close price, daily percent change, and RSI(14) for a stock ticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Yahoo Finance ticker, e.g. BBCA.JK or AAPL"},
            },
            "required": ["ticker"],
        },
    }
]


def get_stock_quote(ticker: str) -> dict:
    history = fetch_history(ticker)
    close = history["Close"]
    rsi = compute_rsi(close)
    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else last_close
    change_pct = (last_close - prev_close) / prev_close * 100 if prev_close else 0.0
    return {
        "ticker": ticker,
        "close": round(last_close, 2),
        "change_pct": round(change_pct, 2),
        "rsi": round(float(rsi.iloc[-1]), 1),
    }


def run_tool(name: str, tool_input: dict) -> dict:
    if name == "get_stock_quote":
        try:
            return get_stock_quote(tool_input["ticker"])
        except Exception as exc:
            return {"error": str(exc)}
    return {"error": f"unknown tool {name}"}


def ask_claude(client: anthropic.Anthropic, question: str) -> str:
    messages: list[dict] = [{"role": "user", "content": question}]

    for _ in range(5):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text").strip()

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })
        messages.append({"role": "user", "content": tool_results})

    return "Sorry, I couldn't finish thinking about that in time."


def load_offset(path: str) -> int:
    if Path(path).exists():
        return json.loads(Path(path).read_text()).get("offset", 0)
    return 0


def save_offset(path: str, offset: int) -> None:
    Path(path).write_text(json.dumps({"offset": offset}) + "\n")


def send_message(token: str, chat_id: str, text: str) -> None:
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    if not resp.ok:
        print(f"Telegram sendMessage failed ({resp.status_code}): {resp.text}")


def is_addressed_to_bot(message: dict) -> bool:
    if message.get("chat", {}).get("type") == "private":
        return True
    text = message.get("text", "")
    if f"@{BOT_USERNAME}".lower() in text.lower():
        return True
    reply = message.get("reply_to_message")
    return bool(reply and reply.get("from", {}).get("username", "").lower() == BOT_USERNAME.lower())


def strip_mention(text: str) -> str:
    return text.replace(f"@{BOT_USERNAME}", "").strip()


def fetch_updates(token: str, offset: int) -> list[dict]:
    resp = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        params={"offset": offset, "timeout": 0},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def main(argv: list[str] | None = None) -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    allowed_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not allowed_chat_id:
        print("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not configured", file=sys.stderr)
        return 1

    state_path = "telegram_offset.json"
    offset = load_offset(state_path)
    updates = fetch_updates(token, offset)

    if not updates:
        print("No new messages.")
        return 0

    client = anthropic.Anthropic()

    max_update_id = offset - 1
    for update in updates:
        max_update_id = max(max_update_id, update["update_id"])
        message = update.get("message")
        if not message or "text" not in message:
            continue

        chat_id = str(message["chat"]["id"])
        if chat_id != str(allowed_chat_id):
            print(f"Ignoring message from unauthorized chat {chat_id}")
            continue

        if not is_addressed_to_bot(message):
            print("Ignoring message not addressed to the bot")
            continue

        text = strip_mention(message["text"])
        print(f"Received: {text}")
        reply = ask_claude(client, text)
        print(f"Replying: {reply}")
        send_message(token, chat_id, reply)

    save_offset(state_path, max_update_id + 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
