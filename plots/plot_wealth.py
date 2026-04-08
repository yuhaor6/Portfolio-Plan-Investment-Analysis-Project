"""
plots/plot_wealth.py — Wealth fan chart and terminal wealth histogram.

Produces (saved to PLOTS_DIR):
  - wealth_fan_chart_<label>.png  : median path + percentile bands over 10 years
  - terminal_wealth_hist_<label>.png : histogram of terminal real wealth with goal line
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from models.simulation import SimulationResult, run_for_tangency  # noqa: E402


def _out(filename: str) -> Path:
    path = PROJECT_ROOT / config.PLOTS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _safe_label(label: str) -> str:
    return label.replace(" ", "_").replace("+", "").replace("/", "-")


# ── Fan chart ─────────────────────────────────────────────────────────────────

def plot_fan_chart(result: SimulationResult, label: str) -> Path:
    wp = result.wealth_paths          # (n_paths, years+1)
    years = wp.shape[1] - 1
    x = np.arange(config.START_YEAR - 1, config.START_YEAR + years)

    p5   = np.percentile(wp, 5,  axis=0)
    p25  = np.percentile(wp, 25, axis=0)
    p50  = np.percentile(wp, 50, axis=0)
    p75  = np.percentile(wp, 75, axis=0)
    p95  = np.percentile(wp, 95, axis=0)

    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.fill_between(x, p5,  p95, alpha=0.15, color="#4C72B0", label="5th–95th pct")
    ax.fill_between(x, p25, p75, alpha=0.30, color="#4C72B0", label="25th–75th pct")
    ax.plot(x, p50, color="#4C72B0", linewidth=2.5, label="Median path")
    ax.plot(x, p5,  color="#4C72B0", linewidth=0.8, linestyle="--")
    ax.plot(x, p95, color="#4C72B0", linewidth=0.8, linestyle="--")

    # Goal line
    goal = config.SAVINGS_GOAL_REAL
    ax.axhline(goal, color="red", linestyle="--", linewidth=1.5,
               label=f"Goal: ${goal:,.0f} real")

    ax.set_xlabel("Calendar Year")
    ax.set_ylabel("Portfolio Value (real $)")
    ax.set_title(f"Wealth Fan Chart — {label}\n"
                 f"({config.N_SIMULATIONS:,} paths, block bootstrap, real $)")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(fontsize=9)
    ax.set_xlim(x[0], x[-1])
    fig.tight_layout()

    path = _out(f"wealth_fan_chart_{_safe_label(label)}.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── Terminal wealth histogram ─────────────────────────────────────────────────

def plot_terminal_histogram(result: SimulationResult, label: str) -> Path:
    terminal = result.terminal_real
    goal = config.SAVINGS_GOAL_REAL
    attainment = result.summary["goal_attainment"]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    # Colour bars by side of goal
    n_bins = 60
    counts, edges = np.histogram(terminal, bins=n_bins)
    for left, right, count in zip(edges[:-1], edges[1:], counts):
        color = "#2ecc71" if right > goal else "#e74c3c"
        ax.bar(left, count, width=(right - left), color=color,
               alpha=0.75, edgecolor="white", linewidth=0.3)

    ax.axvline(goal, color="black", linewidth=2, linestyle="--",
               label=f"Goal ${goal:,.0f}")
    ax.axvline(result.summary["median"], color="#4C72B0", linewidth=1.8,
               linestyle="-", label=f"Median ${result.summary['median']:,.0f}")
    ax.axvline(result.summary["pct_5"], color="orange", linewidth=1.4,
               linestyle=":", label=f"5th pct ${result.summary['pct_5']:,.0f}")

    # Annotation
    ax.text(0.97, 0.95, f"P(goal) = {attainment:.1%}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=12, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gray"))

    ax.set_xlabel("Terminal Real Wealth ($)")
    ax.set_ylabel("Number of Paths")
    ax.set_title(f"Terminal Wealth Distribution — {label}\n(10-year horizon, real $)")
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(fontsize=9)
    fig.tight_layout()

    path = _out(f"terminal_hist_{_safe_label(label)}.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    for label, tickers in [("Layer A IVV-AGG-SHV", config.LAYER_A_TICKERS),
                             ("Layer B +QUAL-USMV",  config.LAYER_B_TICKERS)]:
        print(f"\nRunning simulation — {label} …")
        result = run_for_tangency(tickers)
        s = result.summary
        print(f"  Median: ${s['median']:,.0f}  |  P(goal): {s['goal_attainment']:.1%}  "
              f"|  5th pct: ${s['pct_5']:,.0f}")
        plot_fan_chart(result, label)
        plot_terminal_histogram(result, label)


if __name__ == "__main__":
    main()
