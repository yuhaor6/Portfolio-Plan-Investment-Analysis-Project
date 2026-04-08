"""
analysis/compare_strategies.py — Side-by-side comparison of all portfolio strategies.

Strategies compared:
  1. 100% SHV          — all-cash baseline
  2. 100% IVV          — all-equity (maximum aggression)
  3. 60/40 IVV/AGG     — conventional wisdom
  4. Tangency A        — MV-optimal (IVV/AGG/SHV universe)
  5. Tangency B        — Factor-tilted MV-optimal (+QUAL/USMV)

For each strategy computes:
  Mean, Median, 5th/25th/75th/95th percentile terminal real wealth,
  P(goal), Sharpe ratio (from historical stats), Max Drawdown (median path).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config                                              # noqa: E402
from data.client_profile import build_savings_plan        # noqa: E402
from models.efficient_frontier import run_phase2          # noqa: E402
from models.portfolio_stats import compute_stats, load_returns  # noqa: E402
from models.simulation import run_simulation              # noqa: E402


# ── Max-drawdown on the median wealth path ────────────────────────────────────

def max_drawdown_median(wealth_paths: np.ndarray) -> float:
    """Maximum drawdown of the median path across years."""
    median_path = np.median(wealth_paths, axis=0)
    peak = np.maximum.accumulate(median_path)
    # skip year-0 where wealth == 0 to avoid divide-by-zero
    with np.errstate(invalid="ignore", divide="ignore"):
        drawdown = np.where(peak > 0, (median_path - peak) / peak, 0.0)
    return float(drawdown.min())


# ── Strategy definitions ──────────────────────────────────────────────────────

def _tangency_weights(tickers: list[str]) -> np.ndarray:
    out = run_phase2(tickers)
    t = out["tangency"]
    c = out["cal"]
    w = c.w_risky * t.weights
    if "SHV" in tickers:
        w[tickers.index("SHV")] += c.w_rf
    return w / w.sum()


def build_strategies() -> list[dict]:
    """
    Returns a list of dicts with keys:
      name, tickers, weights, label
    """
    # All Layer-A tickers needed for fixed-mix strategies
    a_tickers = config.LAYER_A_TICKERS   # ["IVV", "AGG", "SHV"]
    b_tickers = config.LAYER_B_TICKERS   # ["IVV", "AGG", "SHV", "QUAL", "USMV"]

    def w_a(ivv=0, agg=0, shv=0):
        arr = np.array([ivv, agg, shv], dtype=float)
        return arr / arr.sum()

    strategies = [
        {
            "name":    "1. All Cash (SHV)",
            "tickers": a_tickers,
            "weights": w_a(shv=1.0),
        },
        {
            "name":    "2. All Equity (IVV)",
            "tickers": a_tickers,
            "weights": w_a(ivv=1.0),
        },
        {
            "name":    "3. 60/40 IVV/AGG",
            "tickers": a_tickers,
            "weights": w_a(ivv=0.6, agg=0.4),
        },
        {
            "name":    "4. Tangency A (IVV/AGG/SHV)",
            "tickers": a_tickers,
            "weights": _tangency_weights(a_tickers),
        },
        {
            "name":    "5. Tangency B (+QUAL/USMV)",
            "tickers": b_tickers,
            "weights": _tangency_weights(b_tickers),
        },
    ]
    return strategies


# ── Run all strategies ────────────────────────────────────────────────────────

def run_all_strategies() -> tuple[pd.DataFrame, list]:
    """
    Returns (summary_df, results_list).
    results_list[i] is the SimulationResult for strategy i.
    """
    savings_df = build_savings_plan()
    annual_savings = savings_df["savings"].tolist()

    strategies = build_strategies()
    rows = []
    results = []

    for strat in strategies:
        tickers  = strat["tickers"]
        weights  = strat["weights"]

        sim = run_simulation(tickers, weights, annual_savings)
        results.append(sim)
        s = sim.summary

        # Historical Sharpe from stats (excess over SHV)
        rets = load_returns(tickers)
        stats = compute_stats(rets)
        port_ret = float(weights @ stats["mean_vec"])
        port_vol = float(np.sqrt(weights @ stats["cov_mat"] @ weights))
        sharpe   = (port_ret - stats["rf_rate"]) / port_vol if port_vol > 0 else 0.0

        mdd = max_drawdown_median(sim.wealth_paths)

        rows.append({
            "Strategy":        strat["name"],
            "Mean ($)":        s["mean"],
            "Median ($)":      s["median"],
            "5th Pct ($)":     s["pct_5"],
            "25th Pct ($)":    s["pct_25"],
            "75th Pct ($)":    s["pct_75"],
            "95th Pct ($)":    s["pct_95"],
            "P(Goal) (%)":     round(s["goal_attainment"] * 100, 1),
            "Ann. Sharpe":     round(sharpe, 3),
            "Med. Max DD (%)": round(mdd * 100, 1),
        })

    return pd.DataFrame(rows), results, strategies


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Running strategy comparison …")
    df, _, _ = run_all_strategies()

    # Pretty-print
    money_cols = ["Mean ($)", "Median ($)", "5th Pct ($)", "25th Pct ($)",
                  "75th Pct ($)", "95th Pct ($)"]
    display = df.copy()
    for c in money_cols:
        display[c] = display[c].map(lambda v: f"${v:>10,.0f}")

    print("\n" + "=" * 90)
    print(" Strategy Comparison — Terminal Real Wealth (10-year, real $)")
    print("=" * 90)
    print(display.to_string(index=False))

    # Save CSV
    out = PROJECT_ROOT / "analysis" / "strategy_comparison.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved → {out}")


if __name__ == "__main__":
    main()
