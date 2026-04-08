"""
models/simulation.py — Monte Carlo block-bootstrap wealth simulation engine.

Algorithm per path:
  1. Draw `years` consecutive 12-month blocks (with replacement) from history.
  2. For each year:
       a. Add that year's savings contribution at the START of the year.
       b. Compound through 12 monthly portfolio returns.
       c. Rebalance back to target weights at year-end.
  3. Deflate terminal nominal value by (1 + inflation)^years → real wealth.

Outputs a SimulationResult with:
  - wealth_paths  : (n_paths × years+1) array of real wealth at each year-end
  - terminal_real : (n_paths,) array of terminal real wealth
  - summary       : key quantile stats + goal attainment probability
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from models.portfolio_stats import load_returns  # noqa: E402


# ── Data class ────────────────────────────────────────────────────────────────

@dataclass
class SimulationResult:
    wealth_paths: np.ndarray     # shape (n_paths, years + 1); col 0 = year 0 = $0
    terminal_real: np.ndarray    # shape (n_paths,); inflation-adjusted terminal wealth
    summary: dict = field(default_factory=dict)
    allocation: np.ndarray = field(default_factory=lambda: np.array([]))
    tickers: list = field(default_factory=list)


# ── Block bootstrap sampler ───────────────────────────────────────────────────

def _build_blocks(monthly_returns: np.ndarray, block_size: int) -> list[np.ndarray]:
    """All overlapping blocks of length `block_size` months."""
    n = len(monthly_returns)
    return [monthly_returns[i: i + block_size] for i in range(n - block_size + 1)]


def block_bootstrap_paths(
    returns: pd.DataFrame,
    n_paths: int,
    years: int,
    block_size: int = config.BLOCK_SIZE_MONTHS,
    seed: int = config.RANDOM_SEED,
) -> np.ndarray:
    """
    Returns array of shape (n_paths, years * block_size, n_assets).
    Each path is `years` randomly drawn non-overlapping annual blocks.
    """
    rng = np.random.default_rng(seed)
    monthly = returns.values.astype(float)          # (T, n_assets)
    blocks = _build_blocks(monthly, block_size)     # list of (12, n_assets) arrays
    n_blocks = len(blocks)
    # Draw indices: (n_paths, years)
    idx = rng.integers(0, n_blocks, size=(n_paths, years))
    # Stack into (n_paths, years * 12, n_assets)
    paths = np.stack(
        [[blocks[idx[p, y]] for y in range(years)] for p in range(n_paths)]
    )  # (n_paths, years, 12, n_assets)
    return paths  # keep as (n_paths, years, 12, n_assets) for easy indexing


# ── Core simulation ───────────────────────────────────────────────────────────

def run_simulation(
    tickers: list[str],
    allocation: np.ndarray,
    annual_savings: list[float],
    years: int = config.PLAN_YEARS,
    n_paths: int = config.N_SIMULATIONS,
    seed: int = config.RANDOM_SEED,
) -> SimulationResult:
    """
    Parameters
    ----------
    tickers        : asset tickers (must match returns.csv columns)
    allocation     : portfolio weights summing to 1, length == len(tickers)
    annual_savings : list of length `years` with each year's savings contribution
    """
    returns = load_returns(tickers)
    w = np.asarray(allocation, dtype=float)
    w = w / w.sum()   # normalise (safety)

    paths = block_bootstrap_paths(returns, n_paths, years, seed=seed)
    # paths shape: (n_paths, years, 12, n_assets)

    inflation_deflator = (1 + config.INFLATION_RATE) ** years
    wealth_paths = np.zeros((n_paths, years + 1))

    for p in range(n_paths):
        value = 0.0
        for yr in range(years):
            # 1. Contribute at start of year
            value += annual_savings[yr]
            # 2. Compound 12 monthly returns
            monthly_rets = paths[p, yr]  # (12, n_assets)
            for m in range(12):
                value *= 1.0 + float(monthly_rets[m] @ w)
            # 3. Record year-end nominal wealth (rebalancing is implicit — weights held fixed)
            wealth_paths[p, yr + 1] = value

    # Deflate entire matrix to real wealth
    for yr in range(1, years + 1):
        deflator = (1 + config.INFLATION_RATE) ** yr
        wealth_paths[:, yr] /= deflator

    terminal_real = wealth_paths[:, -1]

    goal = config.SAVINGS_GOAL_REAL
    summary = {
        "mean":             float(np.mean(terminal_real)),
        "median":           float(np.median(terminal_real)),
        "pct_5":            float(np.percentile(terminal_real, 5)),
        "pct_25":           float(np.percentile(terminal_real, 25)),
        "pct_75":           float(np.percentile(terminal_real, 75)),
        "pct_95":           float(np.percentile(terminal_real, 95)),
        "goal_attainment":  float(np.mean(terminal_real >= goal)),
        "goal":             goal,
    }
    return SimulationResult(wealth_paths, terminal_real, summary,
                             allocation=w, tickers=tickers)


# ── Convenience: run for tangency portfolio ───────────────────────────────────

def run_for_tangency(tickers: list[str] | None = None) -> SimulationResult:
    """Run simulation using the tangency portfolio weights for given tickers."""
    from models.efficient_frontier import run_phase2  # lazy to avoid circular

    if tickers is None:
        tickers = config.LAYER_A_TICKERS
    out = run_phase2(tickers)
    tangency = out["tangency"]
    cal = out["cal"]

    # Build full allocation including SHV at CAL weight
    alloc = cal.w_risky * tangency.weights
    if "SHV" in tickers:
        shv_idx = tickers.index("SHV")
        alloc[shv_idx] += cal.w_rf
    alloc = alloc / alloc.sum()

    from data.client_profile import build_savings_plan  # lazy
    savings_df = build_savings_plan()
    annual_savings = savings_df["savings"].tolist()

    return run_simulation(tickers, alloc, annual_savings)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    for label, tickers in [("Layer A", config.LAYER_A_TICKERS),
                             ("Layer B", config.LAYER_B_TICKERS)]:
        print(f"\n{'='*55}")
        print(f" {label} Tangency — Monte Carlo ({config.N_SIMULATIONS:,} paths)")
        print(f"{'='*55}")
        result = run_for_tangency(tickers)
        s = result.summary
        print(f"  Allocation:         {dict(zip(result.tickers, result.allocation.round(3)))}")
        print(f"  Mean terminal:      ${s['mean']:>10,.0f}")
        print(f"  Median terminal:    ${s['median']:>10,.0f}")
        print(f"  5th  percentile:    ${s['pct_5']:>10,.0f}")
        print(f"  95th percentile:    ${s['pct_95']:>10,.0f}")
        print(f"  Goal (${s['goal']:,.0f}):   {s['goal_attainment']:.1%} probability")


if __name__ == "__main__":
    main()
