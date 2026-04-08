"""
analysis/sensitivity.py — Estimation-window robustness check.

Re-estimates the tangency portfolio on three sub-periods:
  - Full sample   : 2005–2025
  - Pre-GFC-to-now: 2010–2025
  - Recent        : 2015–2025
  - Pre-crisis    : 2005–2015

For each window reports tangency weights, E[return], vol, Sharpe,
and runs the Monte Carlo simulation (using the full-sample returns
for simulation, but window-specific weights).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from data.client_profile import build_savings_plan  # noqa: E402
from models.efficient_frontier import find_tangency  # noqa: E402
from models.portfolio_stats import compute_stats, load_returns  # noqa: E402
from models.simulation import run_simulation  # noqa: E402


WINDOWS = {
    "Full (2005–2025)":   ("2005-01-01", "2025-12-31"),
    "Post-GFC (2010–2025)": ("2010-01-01", "2025-12-31"),
    "Recent (2015–2025)": ("2015-01-01", "2025-12-31"),
    "Pre-crisis (2005–2015)": ("2005-01-01", "2015-12-31"),
}


def run_sensitivity(tickers: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (weights_df, sim_df).
      weights_df : tangency weights per window
      sim_df     : simulation summary per window
    """
    if tickers is None:
        tickers = config.LAYER_B_TICKERS

    savings_df = build_savings_plan()
    annual_savings = savings_df["savings"].tolist()

    weights_rows = []
    sim_rows = []

    for label, (start, end) in WINDOWS.items():
        # Load window-specific returns for estimation
        path = PROJECT_ROOT / config.RETURNS_CSV
        all_ret = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
        all_ret = all_ret[tickers].dropna(how="any")
        window_ret = all_ret.loc[start:end]

        if len(window_ret) < 24:
            print(f"  Skipping {label}: only {len(window_ret)} months available")
            continue

        s = compute_stats(window_ret)
        tangency = find_tangency(s["mean_vec"], s["cov_mat"], s["rf_rate"], tickers)

        row_w = {"Window": label}
        for ticker, w in zip(tickers, tangency.weights):
            row_w[ticker] = round(w, 4)
        row_w["E[r]"]   = round(tangency.expected_return, 4)
        row_w["Vol"]    = round(tangency.expected_vol, 4)
        row_w["Sharpe"] = round(tangency.sharpe_ratio, 4)
        weights_rows.append(row_w)

        # Run simulation with these weights on full-period returns
        sim = run_simulation(tickers, tangency.weights, annual_savings)
        sim_rows.append({
            "Window":      label,
            "Median ($)":  sim.summary["median"],
            "5th Pct ($)": sim.summary["pct_5"],
            "P(Goal) (%)": round(sim.summary["goal_attainment"] * 100, 1),
            "Sharpe":      round(tangency.sharpe_ratio, 4),
        })

    return pd.DataFrame(weights_rows), pd.DataFrame(sim_rows)


def main() -> None:
    print("Running sensitivity analysis …\n")
    weights_df, sim_df = run_sensitivity()

    print("=" * 70)
    print(" Tangency Weights by Estimation Window")
    print("=" * 70)
    print(weights_df.to_string(index=False))

    print("\n" + "=" * 70)
    print(" Simulation Outcomes by Estimation Window (weights only change)")
    print("=" * 70)
    display = sim_df.copy()
    for c in ["Median ($)", "5th Pct ($)"]:
        display[c] = display[c].map(lambda v: f"${v:>10,.0f}")
    print(display.to_string(index=False))

    out = PROJECT_ROOT / "analysis" / "sensitivity_results.csv"
    weights_df.to_csv(out, index=False)
    sim_df.to_csv(PROJECT_ROOT / "analysis" / "sensitivity_sim_results.csv", index=False)
    print(f"\nSaved → {out}")


if __name__ == "__main__":
    main()
