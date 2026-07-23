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


def analyze(stock: Stock, history: pd.DataFrame, thresholds: Thresholds) -> tuple[dict, list[str]]:
    close = history["Close"]
    ma_short = close.rolling(thresholds.ma_short).mean()
    ma_long = close.rolling(thresholds.ma_long).mean()
    rsi = compute_rsi(close)

    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else last_close
    change_pct = (last_close - prev_close) / prev_close * 100 if prev_close else 0.0
    last_rsi = float(rsi.iloc[-1])

    alerts: list[str] = []

    if stock.buy_below is not None and last_close <= stock.buy_below:
        alerts.append(f"{stock.ticker} at {last_close:.2f} has dropped to/below your buy target {stock.buy_below:.2f}")

    if stock.sell_above is not None and last_close >= stock.sell_above:
        alerts.append(f"{stock.ticker} at {last_close:.2f} has risen to/above your sell target {stock.sell_above:.2f}")

    if abs(change_pct) >= thresholds.daily_change_pct:
        direction = "up" if change_pct > 0 else "down"
        alerts.append(f"{stock.ticker} moved {direction} {abs(change_pct):.2f}% in a day (threshold {thresholds.daily_change_pct}%)")

    if last_rsi <= thresholds.rsi_oversold:
        alerts.append(f"{stock.ticker} RSI is {last_rsi:.1f} (oversold, <= {thresholds.rsi_oversold})")
    elif last_rsi >= thresholds.rsi_overbought:
        alerts.append(f"{stock.ticker} RSI is {last_rsi:.1f} (overbought, >= {thresholds.rsi_overbought})")

    prev_short, curr_short = ma_short.iloc[-2], ma_short.iloc[-1]
    prev_long, curr_long = ma_long.iloc[-2], ma_long.iloc[-1]
    if pd.notna(prev_short) and pd.notna(prev_long):
        if prev_short <= prev_long and curr_short > curr_long:
            alerts.append(f"{stock.ticker} MA{thresholds.ma_short} crossed above MA{thresholds.ma_long} (golden cross, bullish)")
        elif prev_short >= prev_long and curr_short < curr_long:
            alerts.append(f"{stock.ticker} MA{thresholds.ma_short} crossed below MA{thresholds.ma_long} (death cross, bearish)")

    summary = {"ticker": stock.ticker, "close": last_close, "change_pct": change_pct, "rsi": last_rsi}
    return summary, alerts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze a stock watchlist and send Telegram alerts.")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    args = parser.parse_args(argv)

    stocks, thresholds = load_config(args.config)

    all_alerts: list[str] = []
    print(f"{'Ticker':<10}{'Close':>10}{'Chg%':>8}{'RSI':>8}")
    for stock in stocks:
        try:
            history = fetch_history(stock.ticker)
        except Exception as exc:
            print(f"  ! failed to fetch {stock.ticker}: {exc}", file=sys.stderr)
            continue
        summary, alerts = analyze(stock, history, thresholds)
        print(f"{summary['ticker']:<10}{summary['close']:>10.2f}{summary['change_pct']:>7.2f}%{summary['rsi']:>8.1f}")
        all_alerts.extend(alerts)

    if all_alerts:
        for alert in all_alerts:
            print(f"[ALERT] {alert}")
        telegram_notif.send_message("\n".join(f"⚠️ {a}" for a in all_alerts))
    else:
        print("No alerts triggered.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
