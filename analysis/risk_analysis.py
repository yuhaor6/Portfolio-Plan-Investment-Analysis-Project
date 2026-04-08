"""
analysis/risk_analysis.py — Drawdown analysis and stress-test scenarios.

Stress scenarios (all use Layer B tangency as the proposed strategy):
  1. Market crash at year 3  — equity (IVV/QUAL/USMV) returns scaled to −35% that year
  2. Job loss at year 3      — zero new savings in year 3; draw 6-month emergency fund
  3. High inflation (4.5%)   — deflate with 4.5 % instead of 2.5 %

Outputs:
  - Prints drawdown stats and stress-scenario P(goal) comparison table
  - Saves analysis/stress_results.csv
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from data.client_profile import build_savings_plan  # noqa: E402
from models.efficient_frontier import run_phase2  # noqa: E402
from models.portfolio_stats import load_returns  # noqa: E402
from models.simulation import (  # noqa: E402
    SimulationResult,
    block_bootstrap_paths,
)


# ── Drawdown helpers ──────────────────────────────────────────────────────────

def path_max_drawdown(wealth_path: np.ndarray) -> float:
    """Max drawdown for a single (years+1,) wealth path."""
    peak = np.maximum.accumulate(wealth_path)
    with np.errstate(invalid="ignore", divide="ignore"):
        dd = np.where(peak > 0, (wealth_path - peak) / peak, 0.0)
    return float(dd.min())


def drawdown_stats(wealth_paths: np.ndarray) -> dict:
    """Summary drawdown stats over all simulation paths."""
    mdd_per_path = np.array([path_max_drawdown(wealth_paths[i]) for i in range(len(wealth_paths))])
    return {
        "mean_mdd":   float(np.mean(mdd_per_path)),
        "median_mdd": float(np.median(mdd_per_path)),
        "pct_5_mdd":  float(np.percentile(mdd_per_path, 5)),
        "mdd_per_path": mdd_per_path,
    }


# ── Stress simulation engine ──────────────────────────────────────────────────

# Tickers that count as "equity" for crash injection
_EQUITY_TICKERS = {"IVV", "QUAL", "USMV"}
_CRASH_YEAR_IDX = 2          # year 3 (0-indexed)
_CRASH_EQUITY_RETURN = -0.35 # −35 % annual


def _run_stress(
    tickers: list[str],
    weights: np.ndarray,
    annual_savings: list[float],
    inflation_rate: float = config.INFLATION_RATE,
    crash_year: int | None = None,
    job_loss_year: int | None = None,
    years: int = config.PLAN_YEARS,
    n_paths: int = config.N_SIMULATIONS,
    seed: int = config.RANDOM_SEED,
) -> SimulationResult:
    """
    Core stress simulation.  All interventions are optional:
      crash_year    : index of year where equity is forced to −35 %
      job_loss_year : index of year with 0 contribution + emergency-fund draw
      inflation_rate: override inflation deflation rate
    """
    returns = load_returns(tickers)
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()

    paths = block_bootstrap_paths(returns, n_paths, years, seed=seed)
    # paths shape: (n_paths, years, 12, n_assets)

    # Map each ticker to its column index
    ticker_idx = {t: i for i, t in enumerate(tickers)}
    equity_cols = [ticker_idx[t] for t in tickers if t in _EQUITY_TICKERS]

    # Emergency fund = 6 months of expenses (constant real value)
    emergency_fund = config.EMERGENCY_FUND_MONTHS * config.MONTHLY_EXPENSES

    wealth_paths = np.zeros((n_paths, years + 1))

    for p in range(n_paths):
        value = 0.0
        emg = emergency_fund  # remaining emergency fund

        for yr in range(years):
            # 1. Contribution
            if job_loss_year is not None and yr == job_loss_year:
                contrib = 0.0
                value = max(value - emergency_fund, 0.0)   # draw down emergency
            else:
                contrib = annual_savings[yr]
            value += contrib

            # 2. Monthly compounding
            monthly_rets = paths[p, yr].copy()   # (12, n_assets)

            if crash_year is not None and yr == crash_year and len(equity_cols) > 0:
                # Scale equity monthly returns so annual equity return ≈ −35 %
                # Each month: (1+r_crash)^12 = 1 − 0.35 → r_crash ≈ (0.65)^(1/12) − 1
                monthly_crash = (1 + _CRASH_EQUITY_RETURN) ** (1 / 12) - 1
                monthly_rets[:, equity_cols] = monthly_crash

            for m in range(12):
                value *= 1.0 + float(monthly_rets[m] @ w)

            wealth_paths[p, yr + 1] = value

    # Deflate with scenario inflation
    for yr in range(1, years + 1):
        wealth_paths[:, yr] /= (1 + inflation_rate) ** yr

    terminal_real = wealth_paths[:, -1]
    goal = config.SAVINGS_GOAL_REAL
    summary = {
        "mean":            float(np.mean(terminal_real)),
        "median":          float(np.median(terminal_real)),
        "pct_5":           float(np.percentile(terminal_real, 5)),
        "pct_95":          float(np.percentile(terminal_real, 95)),
        "goal_attainment": float(np.mean(terminal_real >= goal)),
        "goal":            goal,
    }
    return SimulationResult(wealth_paths, terminal_real, summary,
                             allocation=w, tickers=tickers)


# ── Run all scenarios ─────────────────────────────────────────────────────────

def run_all_stress(tickers: list[str], weights: np.ndarray,
                   annual_savings: list[float]) -> pd.DataFrame:
    """Run base + 3 stress scenarios and return comparison DataFrame."""

    scenarios = [
        ("Base case",           dict()),
        ("Crash at year 3",     dict(crash_year=_CRASH_YEAR_IDX)),
        ("Job loss at year 3",  dict(job_loss_year=_CRASH_YEAR_IDX)),
        ("High inflation 4.5%", dict(inflation_rate=0.045)),
    ]

    rows = []
    results = {}
    for name, kwargs in scenarios:
        sim = _run_stress(tickers, weights, annual_savings, **kwargs)
        s = sim.summary
        dd = drawdown_stats(sim.wealth_paths)
        rows.append({
            "Scenario":       name,
            "Median ($)":     s["median"],
            "5th Pct ($)":    s["pct_5"],
            "95th Pct ($)":   s["pct_95"],
            "P(Goal) (%)":    round(s["goal_attainment"] * 100, 1),
            "Median MDD (%)": round(dd["median_mdd"] * 100, 1),
        })
        results[name] = sim

    return pd.DataFrame(rows), results


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Use Layer B tangency as the proposed strategy
    tickers = config.LAYER_B_TICKERS
    out = run_phase2(tickers)
    t = out["tangency"]
    c = out["cal"]
    weights = c.w_risky * t.weights
    weights[tickers.index("SHV")] += c.w_rf
    weights = weights / weights.sum()

    savings_df = build_savings_plan()
    annual_savings = savings_df["savings"].tolist()

    print("Running stress scenarios …")
    df, results = run_all_stress(tickers, weights, annual_savings)

    # Pretty print
    display = df.copy()
    for c_col in ["Median ($)", "5th Pct ($)", "95th Pct ($)"]:
        display[c_col] = display[c_col].map(lambda v: f"${v:>10,.0f}")

    print("\n" + "=" * 75)
    print(" Stress Test Results — Layer B Tangency Portfolio")
    print("=" * 75)
    print(display.to_string(index=False))

    out_path = PROJECT_ROOT / "analysis" / "stress_results.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved → {out_path}")

    # Drawdown detail for base case
    base_dd = drawdown_stats(results["Base case"].wealth_paths)
    print(f"\nBase-case drawdown stats:")
    print(f"  Mean MDD:   {base_dd['mean_mdd']:.1%}")
    print(f"  Median MDD: {base_dd['median_mdd']:.1%}")
    print(f"  5th pct MDD:{base_dd['pct_5_mdd']:.1%}")


if __name__ == "__main__":
    main()
