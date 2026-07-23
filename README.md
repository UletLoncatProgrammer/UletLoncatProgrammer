# Stock Alert Automation

Analyzes a watchlist of stocks hourly during Jakarta trading hours and
sends a Telegram alert on price targets, volatility spikes, RSI
overbought/oversold levels, and moving-average crossovers (golden/death
cross). Each condition alerts once when it first triggers, then stays
quiet until it clears and re-triggers later — no repeated pings every
hour for the same still-active condition.

A companion bot also lets you *ask* it questions in Telegram (e.g. "what's
BBCA doing?" or "should I be worried about my portfolio right now?") and
get a reply from Claude, which can pull live price/RSI data on demand.

## Structure

```
your-repo/
├── config.json           ← stocks, targets, thresholds
├── alert_state.json      ← tracks which alerts are already active (dedupe)
├── telegram_offset.json  ← tracks which Telegram messages are already answered
├── stock_alert.py        ← scheduled analysis + alert script
├── telegram_bot.py        ← polls Telegram, answers questions via Claude
├── telegram_notif.py      ← sends Telegram messages
├── requirements.txt      ← Python dependencies
├── .github/
│   └── workflows/
│       ├── alert.yml     ← runs stock_alert.py hourly
│       └── bot.yml       ← runs telegram_bot.py every 5 minutes
└── README.md             ← setup instructions
```

## Setup

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and get
   the bot token. Message the bot, then get your chat ID (e.g. via
   `https://api.telegram.org/bot<TOKEN>/getUpdates`).
2. Get an Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
   (needed for the Q&A bot only, not for scheduled alerts).
3. In your GitHub repo, go to Settings → Secrets and variables → Actions
   and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `ANTHROPIC_API_KEY`
4. Edit `config.json` with the tickers (Yahoo Finance symbols, e.g.
   `AAPL`, `BBCA.JK`, `BTC-USD`) and optional `buy_below` / `sell_above`
   price targets.

## Current watchlist

- `BBCA.JK`, `BBRI.JK`, `AMMN.JK`, `WIIM.JK`, `WIFI.JK` — requested tickers
- `BMRI.JK`, `TLKM.JK`, `ASII.JK`, `UNVR.JK`, `ICBP.JK` — added as widely
  cited stable, large-cap IDX picks (banking, telecom, conglomerate,
  consumer staples) with consistent dividends across market cycles

This is not financial advice — set your own `buy_below`/`sell_above`
targets and do your own research before investing.

## Running locally

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=xxxx
export TELEGRAM_CHAT_ID=xxxx
python stock_alert.py --config config.json
```

## Automation

`.github/workflows/alert.yml` runs the analysis every hour from 09:00 to
16:00 WIB (Jakarta time) on weekdays, and can also be triggered manually
from the Actions tab (`workflow_dispatch`). After each run it commits
`alert_state.json` back to the repo if it changed, so dedupe state
carries over between runs.

## Asking the bot questions

`.github/workflows/bot.yml` polls Telegram for new messages every ~5
minutes (so replies aren't instant, but arrive quickly). Only messages
from the chat ID in `TELEGRAM_CHAT_ID` are answered — messages from
anyone else are ignored, so a stranger who finds your bot's username
can't run up your API bill. Each question is answered independently
(no memory of earlier messages yet). Claude can call a `get_stock_quote`
tool for live price/RSI on any ticker; anything else is answered from
its own general knowledge, which may not reflect the very latest news.
