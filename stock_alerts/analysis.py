from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import Thresholds, WatchlistItem


@dataclass
class Alert:
    ticker: str
    kind: str
    message: str


@dataclass
class StockSnapshot:
    ticker: str
    name: str
    close: float
    change_pct: float
    rsi: float
    ma_short: float
    ma_long: float
    alerts: list[Alert] = field(default_factory=list)


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def analyze(item: WatchlistItem, history: pd.DataFrame, thresholds: Thresholds) -> StockSnapshot:
    close = history["Close"]
    ma_short = close.rolling(thresholds.ma_short).mean()
    ma_long = close.rolling(thresholds.ma_long).mean()
    rsi = compute_rsi(close)

    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else last_close
    change_pct = (last_close - prev_close) / prev_close * 100 if prev_close else 0.0

    alerts: list[Alert] = []

    if item.buy_below is not None and last_close <= item.buy_below:
        alerts.append(Alert(
            item.ticker, "buy_target",
            f"{item.ticker} at {last_close:.2f} has dropped to/below your buy target {item.buy_below:.2f}",
        ))

    if item.sell_above is not None and last_close >= item.sell_above:
        alerts.append(Alert(
            item.ticker, "sell_target",
            f"{item.ticker} at {last_close:.2f} has risen to/above your sell target {item.sell_above:.2f}",
        ))

    if abs(change_pct) >= thresholds.daily_change_pct:
        direction = "up" if change_pct > 0 else "down"
        alerts.append(Alert(
            item.ticker, "volatility",
            f"{item.ticker} moved {direction} {abs(change_pct):.2f}% in a day (threshold {thresholds.daily_change_pct}%)",
        ))

    last_rsi = float(rsi.iloc[-1])
    if last_rsi <= thresholds.rsi_oversold:
        alerts.append(Alert(
            item.ticker, "rsi_oversold",
            f"{item.ticker} RSI is {last_rsi:.1f} (oversold, <= {thresholds.rsi_oversold})",
        ))
    elif last_rsi >= thresholds.rsi_overbought:
        alerts.append(Alert(
            item.ticker, "rsi_overbought",
            f"{item.ticker} RSI is {last_rsi:.1f} (overbought, >= {thresholds.rsi_overbought})",
        ))

    ma_short_clean = ma_short.dropna()
    ma_long_clean = ma_long.dropna()
    if len(ma_short_clean) > 1 and len(ma_long_clean) > 1:
        prev_short, curr_short = ma_short.iloc[-2], ma_short.iloc[-1]
        prev_long, curr_long = ma_long.iloc[-2], ma_long.iloc[-1]
        if pd.notna(prev_short) and pd.notna(prev_long):
            if prev_short <= prev_long and curr_short > curr_long:
                alerts.append(Alert(
                    item.ticker, "golden_cross",
                    f"{item.ticker} MA{thresholds.ma_short} crossed above MA{thresholds.ma_long} (golden cross, bullish)",
                ))
            elif prev_short >= prev_long and curr_short < curr_long:
                alerts.append(Alert(
                    item.ticker, "death_cross",
                    f"{item.ticker} MA{thresholds.ma_short} crossed below MA{thresholds.ma_long} (death cross, bearish)",
                ))

    return StockSnapshot(
        ticker=item.ticker,
        name=item.name or item.ticker,
        close=last_close,
        change_pct=change_pct,
        rsi=last_rsi,
        ma_short=float(ma_short.iloc[-1]) if pd.notna(ma_short.iloc[-1]) else float("nan"),
        ma_long=float(ma_long.iloc[-1]) if pd.notna(ma_long.iloc[-1]) else float("nan"),
        alerts=alerts,
    )
