"""
plots/plot_risk.py — Phase 5 risk and factor visualisations.

Produces:
  - drawdown_distribution.png   : histogram of per-path max drawdowns (base case)
  - stress_scenario_bar.png     : P(goal) and median wealth under each stress scenario
  - sensitivity_weights.png     : tangency weights by estimation window (stacked bars)
  - capm_alpha_bar.png          : annualised CAPM α with confidence intervals
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from analysis.factor_alpha import run_capm  # noqa: E402
from analysis.risk_analysis import (  # noqa: E402
    drawdown_stats,
    run_all_stress,
)
from analysis.sensitivity import run_sensitivity  # noqa: E402
from models.efficient_frontier import run_phase2  # noqa: E402
from models.portfolio_stats import load_returns  # noqa: E402


def _out(filename: str) -> Path:
    path = PROJECT_ROOT / config.PLOTS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _tangency_b_weights():
    """Return (tickers, weights) for Layer B CAL allocation."""
    tickers = config.LAYER_B_TICKERS
    out = run_phase2(tickers)
    t, c = out["tangency"], out["cal"]
    w = c.w_risky * t.weights
    w[tickers.index("SHV")] += c.w_rf
    return tickers, w / w.sum()


# ── 1. Drawdown distribution ──────────────────────────────────────────────────

def plot_drawdown_distribution(base_result) -> Path:
    dd = drawdown_stats(base_result.wealth_paths)
    mdd_vals = dd["mdd_per_path"] * 100   # convert to %

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(mdd_vals, bins=50, color="#e74c3c", alpha=0.75, edgecolor="white",
            linewidth=0.3)
    ax.axvline(dd["median_mdd"] * 100, color="black", linewidth=2,
               label=f"Median MDD {dd['median_mdd']:.1%}")
    ax.axvline(dd["pct_5_mdd"] * 100, color="orange", linewidth=1.5,
               linestyle="--", label=f"5th pct MDD {dd['pct_5_mdd']:.1%}")
    ax.axvline(-config.MAX_DRAWDOWN_TOLERANCE * 100, color="blue",
               linewidth=1.5, linestyle=":", label=f"Tolerance −{config.MAX_DRAWDOWN_TOLERANCE:.0%}")

    ax.set_xlabel("Max Drawdown (%)")
    ax.set_ylabel("Number of Paths")
    ax.set_title("Max Drawdown Distribution — Layer B Tangency\n"
                 f"({config.N_SIMULATIONS:,} paths, real-wealth basis)")
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.legend(fontsize=9)
    fig.tight_layout()

    path = _out("drawdown_distribution.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── 2. Stress scenario bar chart ──────────────────────────────────────────────

def plot_stress_scenarios(stress_df: pd.DataFrame) -> Path:
    scenarios = stress_df["Scenario"].tolist()
    p_goals   = stress_df["P(Goal) (%)"].tolist()
    medians   = stress_df["Median ($)"].tolist()

    x = np.arange(len(scenarios))
    width = 0.38
    colors = ["#27ae60", "#e74c3c", "#f39c12", "#8e44ad"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: P(goal)
    bars1 = ax1.bar(x, p_goals, width=width * 2, color=colors, edgecolor="white")
    for bar, val in zip(bars1, p_goals):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                 f"{val:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax1.axhline(p_goals[0], color="gray", linestyle="--", linewidth=1, label="Base case")
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, rotation=15, ha="right", fontsize=9)
    ax1.set_ylabel("P(Goal) (%)")
    ax1.set_title(f"Goal Attainment by Scenario\n(Goal = ${config.SAVINGS_GOAL_REAL:,.0f} real)")
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax1.set_ylim(0, max(p_goals) * 1.2)

    # Right: Median terminal wealth
    bars2 = ax2.bar(x, medians, width=width * 2, color=colors, edgecolor="white")
    for bar, val in zip(bars2, medians):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                 f"${val:,.0f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    ax2.axhline(config.SAVINGS_GOAL_REAL, color="black", linestyle="--",
                linewidth=1.5, label=f"Goal ${config.SAVINGS_GOAL_REAL:,.0f}")
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, rotation=15, ha="right", fontsize=9)
    ax2.set_ylabel("Median Terminal Real Wealth ($)")
    ax2.set_title("Median Terminal Wealth by Scenario")
    ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax2.legend(fontsize=8)

    fig.suptitle("Stress Test Analysis — Layer B Tangency Portfolio", fontweight="bold")
    fig.tight_layout()

    path = _out("stress_scenario_bar.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── 3. Sensitivity — tangency weights by window ───────────────────────────────

def plot_sensitivity_weights(weights_df: pd.DataFrame,
                              tickers: list[str]) -> Path:
    windows = weights_df["Window"].tolist()
    x = np.arange(len(windows))
    palette = ["#2980b9", "#27ae60", "#7f8c8d", "#e74c3c", "#f39c12"]

    fig, ax = plt.subplots(figsize=(10, 5))
    bottom = np.zeros(len(windows))

    asset_cols = [t for t in tickers if t in weights_df.columns]
    for i, ticker in enumerate(asset_cols):
        vals = weights_df[ticker].values.astype(float)
        ax.bar(x, vals, bottom=bottom, label=ticker,
               color=palette[i % len(palette)], edgecolor="white", width=0.5)
        # Label only non-trivial slices
        for xi, (v, b) in enumerate(zip(vals, bottom)):
            if v > 0.04:
                ax.text(xi, b + v / 2, f"{v:.0%}", ha="center", va="center",
                        fontsize=8.5, color="white", fontweight="bold")
        bottom += vals

    sharpes = weights_df["Sharpe"].tolist()
    for xi, sh in enumerate(sharpes):
        ax.text(xi, 1.03, f"Sharpe\n{sh:.2f}", ha="center", va="bottom",
                fontsize=8, color="#2c3e50")

    ax.set_xticks(x)
    ax.set_xticklabels(windows, rotation=10, ha="right", fontsize=9)
    ax.set_ylabel("Tangency Portfolio Weight")
    ax.set_ylim(0, 1.18)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_title("Tangency Portfolio Weights by Estimation Window\n"
                 "(shows sensitivity to sample-period choice)")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()

    path = _out("sensitivity_weights.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── 4. CAPM alpha bar chart ───────────────────────────────────────────────────

def plot_capm_alpha(capm_df: pd.DataFrame) -> Path:
    assets = capm_df["Asset"].tolist()
    alphas = (capm_df["Alpha (ann.)"] * 100).tolist()
    tstats = capm_df["t(alpha)"].tolist()

    colors = ["#27ae60" if a > 0 else "#e74c3c" for a in alphas]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(assets, alphas, color=colors, edgecolor="white", width=0.5)

    for bar, a, ts in zip(bars, alphas, tstats):
        sig = "**" if abs(ts) > 2 else ("*" if abs(ts) > 1.65 else "")
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (0.05 if a >= 0 else -0.25),
                f"{a:.2f}%{sig}", ha="center", va="bottom", fontsize=10,
                fontweight="bold")

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Annualised CAPM Alpha (%)")
    ax.set_title("Historical CAPM Alpha by Asset\n"
                 "(IVV = market; SHV = risk-free; * p<10%, ** p<5%)")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.1f}%"))
    fig.tight_layout()

    path = _out("capm_alpha_bar.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    from data.client_profile import build_savings_plan

    tickers, weights = _tangency_b_weights()
    savings_df = build_savings_plan()
    annual_savings = savings_df["savings"].tolist()

    # Stress
    print("Running stress scenarios …")
    stress_df, stress_results = run_all_stress(tickers, weights, annual_savings)
    plot_drawdown_distribution(stress_results["Base case"])
    plot_stress_scenarios(stress_df)

    # Sensitivity
    print("\nRunning sensitivity analysis …")
    weights_df, _ = run_sensitivity(tickers)
    plot_sensitivity_weights(weights_df, tickers)

    # CAPM alpha
    print("\nRunning CAPM regressions …")
    capm_df = run_capm(tickers)
    plot_capm_alpha(capm_df)

    print("\nAll Phase 5 plots saved.")


if __name__ == "__main__":
    main()
