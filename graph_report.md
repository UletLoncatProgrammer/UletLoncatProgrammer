# Stock Alert Automation — Architecture & Flow Report

## System overview

```mermaid
flowchart LR
    subgraph Triggers
        CRON[GitHub Actions schedule<br/>alert.yml: hourly, 09:00-16:00 WIB]
        EXT[cron-job.org<br/>POST every 5 min]
    end

    subgraph GitHub Repo
        CFG[config.json<br/>watchlist + thresholds]
        ALERT[stock_alert.py]
        BOT[telegram_bot.py]
        NOTIF[telegram_notif.py]
        STATE1[alert_state.json<br/>dedupe state]
        STATE2[telegram_offset.json<br/>last processed update_id]
    end

    subgraph External Services
        YF[Yahoo Finance<br/>via yfinance]
        CLAUDE[Claude API<br/>claude-sonnet-5]
        TG[Telegram Bot API]
    end

    GROUP[("Telegram group<br/>Yudha Saham")]

    CRON -->|workflow: alert.yml| ALERT
    EXT -->|workflow_dispatch: bot.yml| BOT

    ALERT --> CFG
    ALERT --> YF
    ALERT --> STATE1
    ALERT --> NOTIF
    NOTIF --> TG

    BOT --> TG
    BOT --> CLAUDE
    CLAUDE -.tool call: get_stock_quote.-> YF
    BOT --> STATE2

    TG <--> GROUP
```

## Flow 1 — Scheduled price alerts (`alert.yml` → `stock_alert.py`)

Runs hourly on weekdays. Checks every ticker in `config.json` against price
targets, daily volatility, RSI, and moving-average crossovers. Each
condition notifies once when it first triggers, then stays silent until it
clears (tracked in `alert_state.json`).

```mermaid
sequenceDiagram
    participant Cron as GitHub Actions Schedule
    participant Alert as stock_alert.py
    participant YF as Yahoo Finance
    participant State as alert_state.json
    participant Notif as telegram_notif.py
    participant TG as Telegram

    Cron->>Alert: run (hourly, weekdays)
    Alert->>Alert: load_config(config.json)
    Alert->>State: load_state()
    loop each ticker in watchlist
        Alert->>YF: fetch_history(ticker)
        YF-->>Alert: OHLC data
        Alert->>Alert: analyze() → RSI, MA, % change, targets
    end
    Alert->>Alert: dedupe_alerts() vs previous state
    alt new alerts triggered
        Alert->>Notif: send_message(alert text)
        Notif->>TG: POST sendMessage
    end
    Alert->>State: save_state() (git commit)
```

## Flow 2 — Conversational Q&A (`bot.yml` → `telegram_bot.py`)

Triggered every 5 minutes by an external cron (cron-job.org), since
GitHub's native schedule trigger proved unreliable for a 5-minute cadence.
Only messages from the configured chat (the group) are considered, and
within that group, only messages that `@mention` the bot or reply to one
of its messages are answered — enforced in code rather than relying on
Telegram's privacy-mode heuristics.

```mermaid
sequenceDiagram
    participant Ext as cron-job.org
    participant GH as GitHub Actions (bot.yml)
    participant Bot as telegram_bot.py
    participant TG as Telegram Bot API
    participant Offset as telegram_offset.json
    participant Claude as Claude API
    participant YF as Yahoo Finance

    Ext->>GH: POST /actions/workflows/bot.yml/dispatches (every 5 min)
    GH->>Bot: run
    Bot->>Offset: load_offset()
    Bot->>TG: GET getUpdates?offset=N
    TG-->>Bot: pending updates
    alt no updates
        Bot->>Bot: print "No new messages"
    else updates present
        loop each update
            Bot->>Bot: filter: allowed chat_id?
            Bot->>Bot: filter: is_addressed_to_bot()?
            alt passes both filters
                Bot->>Claude: messages.create(question, tools=[get_stock_quote])
                opt Claude requests tool
                    Claude-->>Bot: tool_use get_stock_quote
                    Bot->>YF: fetch_history(ticker)
                    YF-->>Bot: price/RSI
                    Bot->>Claude: tool_result
                end
                Claude-->>Bot: final answer text
                Bot->>TG: POST sendMessage(answer)
            end
        end
        Bot->>Offset: save_offset() (git commit)
    end
```

## Component reference

| File | Role |
|---|---|
| `config.json` | Watchlist (tickers, buy/sell targets) + alert thresholds |
| `stock_alert.py` | Fetches prices, computes indicators, dedupes, triggers alerts |
| `telegram_notif.py` | One-way Telegram `sendMessage` helper used by `stock_alert.py` |
| `telegram_bot.py` | Polls Telegram, filters by chat + mention/reply, answers via Claude |
| `alert_state.json` | Per-ticker per-condition dedupe flags (committed by `alert.yml`) |
| `telegram_offset.json` | Last processed Telegram `update_id` (committed by `bot.yml`) |
| `.github/workflows/alert.yml` | Hourly weekday schedule for `stock_alert.py` |
| `.github/workflows/bot.yml` | `workflow_dispatch`-triggered run of `telegram_bot.py` |
| cron-job.org (external) | Reliable 5-minute POST trigger for `bot.yml`, replacing GitHub's native schedule |
