"""
plots/plot_comparison.py — Strategy comparison charts for Phase 4.

Produces (saved to PLOTS_DIR):
  - strategy_fan_overlay.png       : overlaid fan charts for all strategies
  - goal_attainment_bar.png        : P(goal) bar chart across strategies
  - strategy_summary_table.png     : publication-quality table as a figure
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
from analysis.compare_strategies import run_all_strategies  # noqa: E402


def _out(filename: str) -> Path:
    path = PROJECT_ROOT / config.PLOTS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# Colour palette — one colour per strategy
PALETTE = ["#7f8c8d", "#e74c3c", "#f39c12", "#2980b9", "#27ae60"]


# ── Overlaid fan charts ───────────────────────────────────────────────────────

def plot_fan_overlay(results: list, strategies: list, df: pd.DataFrame) -> Path:
    years  = results[0].wealth_paths.shape[1] - 1
    x      = np.arange(config.START_YEAR - 1, config.START_YEAR + years)
    goal   = config.SAVINGS_GOAL_REAL

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, (sim, strat) in enumerate(zip(results, strategies)):
        wp   = sim.wealth_paths
        p5   = np.percentile(wp, 5,  axis=0)
        p50  = np.percentile(wp, 50, axis=0)
        p95  = np.percentile(wp, 95, axis=0)
        col  = PALETTE[i]
        name = strat["name"]

        ax.fill_between(x, p5, p95, alpha=0.10, color=col)
        ax.plot(x, p50, color=col, linewidth=2.0, label=name)

    ax.axhline(goal, color="black", linestyle="--", linewidth=1.5,
               label=f"Goal ${goal:,.0f}")
    ax.set_xlabel("Calendar Year")
    ax.set_ylabel("Portfolio Value (real $)")
    ax.set_title(f"Wealth Trajectories by Strategy (median ± 5th–95th pct)\n"
                 f"{config.N_SIMULATIONS:,} paths, block bootstrap, real $")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(fontsize=8.5, loc="upper left")
    ax.set_xlim(x[0], x[-1])
    fig.tight_layout()

    path = _out("strategy_fan_overlay.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── Goal attainment bar chart ─────────────────────────────────────────────────

def plot_goal_attainment(df: pd.DataFrame) -> Path:
    names  = df["Strategy"].tolist()
    probs  = df["P(Goal) (%)"].tolist()
    colors = [PALETTE[i] for i in range(len(names))]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(names, probs, color=colors, edgecolor="white", width=0.55)

    # Value labels on bars
    for bar, val in zip(bars, probs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(50, color="black", linestyle=":", linewidth=1, alpha=0.5)
    ax.set_ylabel("Probability of Reaching Goal (%)")
    ax.set_title(f"Goal Attainment Probability by Strategy\n(Goal = ${config.SAVINGS_GOAL_REAL:,.0f} real)")
    ax.set_ylim(0, max(probs) * 1.18)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    plt.xticks(rotation=15, ha="right", fontsize=9)
    fig.tight_layout()

    path = _out("goal_attainment_bar.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── Summary table figure ──────────────────────────────────────────────────────

def plot_summary_table(df: pd.DataFrame) -> Path:
    display_cols = ["Strategy", "Median ($)", "5th Pct ($)", "95th Pct ($)",
                    "P(Goal) (%)", "Ann. Sharpe", "Med. Max DD (%)"]
    tbl = df[display_cols].copy()
    for c in ["Median ($)", "5th Pct ($)", "95th Pct ($)"]:
        tbl[c] = tbl[c].map(lambda v: f"${v:,.0f}")

    fig, ax = plt.subplots(figsize=(12, 2.8))
    ax.axis("off")

    col_labels = ["Strategy", "Median", "5th Pct", "95th Pct",
                  "P(Goal)", "Sharpe", "Max DD"]
    cell_data  = tbl.values.tolist()
    cell_colors = []
    for i in range(len(cell_data)):
        row_colors = ["#f0f0f0" if i % 2 == 0 else "white"] * len(col_labels)
        cell_colors.append(row_colors)

    table = ax.table(
        cellText=cell_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
        cellColours=cell_colors,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.6)

    # Bold header
    for j in range(len(col_labels)):
        table[(0, j)].set_facecolor("#2c3e50")
        table[(0, j)].get_text().set_color("white")
        table[(0, j)].get_text().set_fontweight("bold")

    ax.set_title("Strategy Comparison — Terminal Real Wealth (10-year horizon)",
                 fontsize=11, fontweight="bold", pad=12)
    fig.tight_layout()

    path = _out("strategy_summary_table.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Running all strategies …")
    df, results, strategies = run_all_strategies()
    plot_fan_overlay(results, strategies, df)
    plot_goal_attainment(df)
    plot_summary_table(df)
    print("\nDone. All comparison charts saved.")


if __name__ == "__main__":
    main()
