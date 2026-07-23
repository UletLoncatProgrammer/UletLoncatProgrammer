import pandas as pd

from stock_alerts.analysis import analyze
from stock_alerts.config import Thresholds, WatchlistItem


def _history(prices: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"Close": prices})


def test_buy_target_alert_triggers_below_threshold():
    item = WatchlistItem(ticker="TEST", buy_below=100.0)
    history = _history([110, 105, 95])
    snapshot = analyze(item, history, Thresholds())
    assert "buy_target" in {a.kind for a in snapshot.alerts}


def test_sell_target_alert_triggers_above_threshold():
    item = WatchlistItem(ticker="TEST", sell_above=100.0)
    history = _history([90, 95, 105])
    snapshot = analyze(item, history, Thresholds())
    assert "sell_target" in {a.kind for a in snapshot.alerts}


def test_volatility_alert_triggers_on_large_daily_move():
    item = WatchlistItem(ticker="TEST")
    history = _history([100, 100, 90])
    snapshot = analyze(item, history, Thresholds(daily_change_pct=5.0))
    assert "volatility" in {a.kind for a in snapshot.alerts}


def test_no_alerts_on_flat_stable_price():
    item = WatchlistItem(ticker="TEST")
    history = _history([100.0] * 60)
    snapshot = analyze(item, history, Thresholds())
    assert snapshot.alerts == []


def test_golden_cross_detected_when_short_ma_crosses_above_long_ma():
    item = WatchlistItem(ticker="TEST")
    prices = [100.0] * 55 + [90, 85, 80, 120, 130]
    history = _history(prices)
    snapshot = analyze(item, history, Thresholds(ma_short=5, ma_long=20))
    assert "golden_cross" in {a.kind for a in snapshot.alerts}
