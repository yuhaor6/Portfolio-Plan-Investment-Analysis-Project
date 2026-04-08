"""
models/portfolio_stats.py — Historical return statistics for all ETFs.

Produces:
  - Annualised mean return, volatility, Sharpe ratio per asset
  - Full covariance and correlation matrices
  - Risk-free rate (mean SHV return, annualised)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402


def load_returns(tickers: list[str] | None = None) -> pd.DataFrame:
    path = PROJECT_ROOT / config.RETURNS_CSV
    df = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
    if tickers:
        df = df[tickers]
    # Drop months where any ticker has missing data (e.g. QUAL pre-2013, USMV pre-2011)
    df = df.dropna(how="any")
    return df


def compute_stats(returns: pd.DataFrame) -> dict:
    """Return a dict with annualised stats, cov, corr, and risk-free rate."""
    mean_ann = returns.mean() * 12
    vol_ann  = returns.std() * np.sqrt(12)
    cov_ann  = returns.cov() * 12
    corr     = returns.corr()

    # Risk-free rate: average annualised SHV return (if available)
    rf = float(mean_ann["SHV"]) if "SHV" in mean_ann.index else 0.0

    sharpe = (mean_ann - rf) / vol_ann

    stats_df = pd.DataFrame({
        "ann_return":    mean_ann,
        "ann_vol":       vol_ann,
        "sharpe_ex_rf": sharpe,
    })

    return {
        "stats":   stats_df,
        "cov":     cov_ann,
        "corr":    corr,
        "rf_rate": rf,
        "mean_vec": mean_ann.values,
        "cov_mat":  cov_ann.values,
        "tickers":  returns.columns.tolist(),
    }


def main() -> None:
    for label, tickers in [("Layer A", config.LAYER_A_TICKERS),
                            ("Layer B", config.LAYER_B_TICKERS)]:
        returns = load_returns(tickers)
        s = compute_stats(returns)
        print(f"\n{'='*55}")
        print(f" {label} — Asset Statistics (2005–2025, annualised)")
        print(f"{'='*55}")
        print(s["stats"].round(4).to_string())
        print(f"\nRisk-free rate (avg SHV): {s['rf_rate']:.4f}")
        print(f"\nCorrelation matrix:")
        print(s["corr"].round(3).to_string())


if __name__ == "__main__":
    main()
