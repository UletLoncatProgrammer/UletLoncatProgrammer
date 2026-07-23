# Stock Alert Automation

Analyzes a watchlist of stocks daily and sends a Telegram alert on price
targets, volatility spikes, RSI overbought/oversold levels, and
moving-average crossovers (golden/death cross).

## Structure

```
your-repo/
├── config.json          ← stocks, targets, thresholds
├── stock_alert.py       ← main script
├── telegram_notif.py    ← sends Telegram messages
├── requirements.txt     ← Python dependencies
├── .github/
│   └── workflows/
│       └── alert.yml    ← runs daily automatically
└── README.md            ← setup instructions
```

## Setup

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and get
   the bot token. Message the bot, then get your chat ID (e.g. via
   `https://api.telegram.org/bot<TOKEN>/getUpdates`).
2. In your GitHub repo, go to Settings → Secrets and variables → Actions
   and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Edit `config.json` with the tickers (Yahoo Finance symbols, e.g.
   `AAPL`, `BBCA.JK`, `BTC-USD`) and optional `buy_below` / `sell_above`
   price targets.

## Running locally

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=xxxx
export TELEGRAM_CHAT_ID=xxxx
python stock_alert.py --config config.json
```

## Automation

`.github/workflows/alert.yml` runs the analysis on weekdays at 08:00 UTC
and can also be triggered manually from the Actions tab
(`workflow_dispatch`).
