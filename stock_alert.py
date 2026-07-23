"""Analyzes a stock watchlist and sends Telegram alerts on price/technical triggers."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

import telegram_notif


@dataclass
class Stock:
    ticker: str
    name: str = ""
    buy_below: float | None = None
    sell_above: float | None = None


@dataclass
class Thresholds:
    daily_change_pct: float = 5.0
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    ma_short: int = 20
    ma_long: int = 50


def load_config(path: str) -> tuple[list[Stock], Thresholds]:
    data = json.loads(Path(path).read_text())
    stocks = [Stock(**item) for item in data.get("stocks", [])]
    thresholds = Thresholds(**data.get("thresholds", {}))
    return stocks, thresholds


def fetch_history(ticker: str) -> pd.DataFrame:
    history = yf.Ticker(ticker).history(period="6mo", interval="1d")
    if history.empty:
        raise ValueError(f"No price data returned for {ticker!r}")
    return history


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def analyze(stock: Stock, history: pd.DataFrame, thresholds: Thresholds) -> tuple[dict, list[tuple[str, str]]]:
    close = history["Close"]
    ma_short = close.rolling(thresholds.ma_short).mean()
    ma_long = close.rolling(thresholds.ma_long).mean()
    rsi = compute_rsi(close)

    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else last_close
    change_pct = (last_close - prev_close) / prev_close * 100 if prev_close else 0.0
    last_rsi = float(rsi.iloc[-1])

    alerts: list[tuple[str, str]] = []

    if stock.buy_below is not None and last_close <= stock.buy_below:
        alerts.append(("buy_target", f"{stock.ticker} at {last_close:.2f} has dropped to/below your buy target {stock.buy_below:.2f}"))

    if stock.sell_above is not None and last_close >= stock.sell_above:
        alerts.append(("sell_target", f"{stock.ticker} at {last_close:.2f} has risen to/above your sell target {stock.sell_above:.2f}"))

    if abs(change_pct) >= thresholds.daily_change_pct:
        direction = "up" if change_pct > 0 else "down"
        alerts.append(("volatility", f"{stock.ticker} moved {direction} {abs(change_pct):.2f}% in a day (threshold {thresholds.daily_change_pct}%)"))

    if last_rsi <= thresholds.rsi_oversold:
        alerts.append(("rsi_oversold", f"{stock.ticker} RSI is {last_rsi:.1f} (oversold, <= {thresholds.rsi_oversold})"))
    elif last_rsi >= thresholds.rsi_overbought:
        alerts.append(("rsi_overbought", f"{stock.ticker} RSI is {last_rsi:.1f} (overbought, >= {thresholds.rsi_overbought})"))

    prev_short, curr_short = ma_short.iloc[-2], ma_short.iloc[-1]
    prev_long, curr_long = ma_long.iloc[-2], ma_long.iloc[-1]
    if pd.notna(prev_short) and pd.notna(prev_long):
        if prev_short <= prev_long and curr_short > curr_long:
            alerts.append(("golden_cross", f"{stock.ticker} MA{thresholds.ma_short} crossed above MA{thresholds.ma_long} (golden cross, bullish)"))
        elif prev_short >= prev_long and curr_short < curr_long:
            alerts.append(("death_cross", f"{stock.ticker} MA{thresholds.ma_short} crossed below MA{thresholds.ma_long} (death cross, bearish)"))

    summary = {"ticker": stock.ticker, "close": last_close, "change_pct": change_pct, "rsi": last_rsi}
    return summary, alerts


def load_state(path: str) -> dict[str, bool]:
    if Path(path).exists():
        return json.loads(Path(path).read_text())
    return {}


def save_state(path: str, state: dict[str, bool]) -> None:
    Path(path).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def dedupe_alerts(
    ticker_alerts: list[tuple[str, list[tuple[str, str]]]],
    state: dict[str, bool],
) -> tuple[list[str], dict[str, bool]]:
    """Only surface an alert the moment its condition becomes active; suppress
    repeats while it stays active, and re-arm once the condition clears."""
    new_state = dict(state)
    to_notify: list[str] = []

    for ticker, alerts in ticker_alerts:
        active_kinds = {kind for kind, _ in alerts}

        for key in list(new_state.keys()):
            key_ticker, _, key_kind = key.partition(":")
            if key_ticker == ticker and key_kind not in active_kinds:
                new_state[key] = False

        for kind, message in alerts:
            key = f"{ticker}:{kind}"
            if not new_state.get(key, False):
                to_notify.append(message)
            new_state[key] = True

    return to_notify, new_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze a stock watchlist and send Telegram alerts.")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    parser.add_argument("--state", default="alert_state.json", help="Path to alert dedupe state JSON")
    args = parser.parse_args(argv)

    stocks, thresholds = load_config(args.config)
    state = load_state(args.state)

    ticker_alerts: list[tuple[str, list[tuple[str, str]]]] = []
    print(f"{'Ticker':<10}{'Close':>10}{'Chg%':>8}{'RSI':>8}")
    for stock in stocks:
        try:
            history = fetch_history(stock.ticker)
        except Exception as exc:
            print(f"  ! failed to fetch {stock.ticker}: {exc}", file=sys.stderr)
            continue
        summary, alerts = analyze(stock, history, thresholds)
        print(f"{summary['ticker']:<10}{summary['close']:>10.2f}{summary['change_pct']:>7.2f}%{summary['rsi']:>8.1f}")
        ticker_alerts.append((stock.ticker, alerts))

    to_notify, new_state = dedupe_alerts(ticker_alerts, state)
    save_state(args.state, new_state)

    if to_notify:
        for message in to_notify:
            print(f"[ALERT] {message}")
        telegram_notif.send_message("\n".join(f"⚠️ {m}" for m in to_notify))
    else:
        print("No new alerts triggered.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
