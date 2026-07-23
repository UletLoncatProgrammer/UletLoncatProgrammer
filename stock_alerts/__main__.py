from __future__ import annotations

import argparse
import sys

from .analysis import analyze
from .config import load_config
from .data import fetch_history
from .notify import send_notifications


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze a stock watchlist and send alerts.")
    parser.add_argument("--config", default="config/watchlist.json", help="Path to watchlist config JSON")
    args = parser.parse_args(argv)

    config = load_config(args.config)

    all_alerts = []
    print(f"{'Ticker':<10}{'Close':>10}{'Chg%':>8}{'RSI':>8}")
    for item in config.watchlist:
        try:
            history = fetch_history(item.ticker)
        except Exception as exc:
            print(f"  ! failed to fetch {item.ticker}: {exc}", file=sys.stderr)
            continue
        snapshot = analyze(item, history, config.thresholds)
        print(f"{snapshot.ticker:<10}{snapshot.close:>10.2f}{snapshot.change_pct:>7.2f}%{snapshot.rsi:>8.1f}")
        all_alerts.extend(snapshot.alerts)

    send_notifications(all_alerts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
