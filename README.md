# Stock Alert Automation

Analyzes a watchlist of stocks daily and raises alerts on price targets,
volatility spikes, RSI overbought/oversold levels, and moving-average
crossovers (golden/death cross).

## Watchlist config

Edit `config/watchlist.json`:

```json
{
  "watchlist": [
    {"ticker": "BBCA.JK", "name": "Bank Central Asia", "buy_below": 9000, "sell_above": 11000}
  ],
  "thresholds": {
    "daily_change_pct": 5.0,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "ma_short": 20,
    "ma_long": 50
  }
}
```

`ticker` uses Yahoo Finance symbols (e.g. `AAPL`, `BBCA.JK`, `BTC-USD`).
`buy_below` / `sell_above` are optional price targets; set to `null` to skip.

## Running locally

```bash
pip install -r requirements.txt
python -m stock_alerts --config config/watchlist.json
```

## Notifications

Alerts always print to the console. If any of these secrets/env vars are
set, alerts are also sent there:

- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
- `DISCORD_WEBHOOK_URL`
- `SLACK_WEBHOOK_URL`

If none of those are configured and the run happens inside GitHub Actions,
a GitHub issue is opened automatically instead — no secrets required.

## Automation

`.github/workflows/stock-alert.yml` runs the analysis on weekdays at
08:00 UTC and can also be triggered manually from the Actions tab
(`workflow_dispatch`). Add any of the notification secrets above under
repo Settings → Secrets and variables → Actions to enable that channel.

## Tests

```bash
pip install -r requirements.txt pytest
pytest
```
