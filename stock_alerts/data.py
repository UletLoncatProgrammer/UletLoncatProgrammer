from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    history = yf.Ticker(ticker).history(period=period, interval=interval)
    if history.empty:
        raise ValueError(f"No price data returned for {ticker!r}")
    return history
