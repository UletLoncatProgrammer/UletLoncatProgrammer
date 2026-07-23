from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WatchlistItem:
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


@dataclass
class Config:
    watchlist: list[WatchlistItem]
    thresholds: Thresholds


def load_config(path: str | Path) -> Config:
    data = json.loads(Path(path).read_text())
    watchlist = [WatchlistItem(**item) for item in data.get("watchlist", [])]
    thresholds = Thresholds(**data.get("thresholds", {}))
    return Config(watchlist=watchlist, thresholds=thresholds)
