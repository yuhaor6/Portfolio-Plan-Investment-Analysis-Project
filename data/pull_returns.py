"""
data/pull_returns.py — Download monthly total returns for all ETFs from Yahoo Finance.

Outputs: data/returns.csv  (columns = ticker symbols, rows = month-end dates)
"""
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

# Allow running as `python -m data.pull_returns` from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402


def download_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Download adjusted-close prices via yfinance."""
    raw = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"][tickers]
    else:
        prices = raw[["Close"]].rename(columns={"Close": tickers[0]})
    prices.index.name = "Date"
    return prices


def to_monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Resample daily prices to month-end and compute simple returns."""
    monthly_prices = prices.resample("ME").last()
    returns = monthly_prices.pct_change().dropna(how="all")
    return returns


def pull_and_save() -> Path:
    """Full pipeline: download → monthly returns → CSV."""
    output = PROJECT_ROOT / config.RETURNS_CSV
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {config.TICKERS} from {config.RETURN_START} to {config.RETURN_END} …")
    prices = download_prices(config.TICKERS, config.RETURN_START, config.RETURN_END)
    print(f"  Got {len(prices)} daily price rows, {prices.columns.tolist()} tickers")

    returns = to_monthly_returns(prices)
    returns.index.name = "Date"
    returns.to_csv(output)
    print(f"  Saved {len(returns)} monthly return rows → {output}")

    # Quick sanity stats
    print("\nSample annualised statistics (mean × 12, std × √12):")
    ann = pd.DataFrame({
        "ann_return": returns.mean() * 12,
        "ann_vol": returns.std() * (12 ** 0.5),
    })
    ann["sharpe"] = ann["ann_return"] / ann["ann_vol"]
    print(ann.round(4).to_string())

    return output


if __name__ == "__main__":
    pull_and_save()
