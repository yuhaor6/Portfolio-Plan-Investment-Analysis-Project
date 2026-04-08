"""
plots/plot_frontier.py — Efficient frontier, CAL, and correlation heatmap.

Produces (saved to PLOTS_DIR):
  - efficient_frontier_layerA.png
  - efficient_frontier_layerB.png
  - correlation_heatmap.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from models.efficient_frontier import build_frontier, cal_allocation, find_tangency  # noqa: E402
from models.portfolio_stats import compute_stats, load_returns  # noqa: E402


def _out(filename: str) -> Path:
    path = PROJECT_ROOT / config.PLOTS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_frontier(tickers: list[str], label: str) -> Path:
    returns = load_returns(tickers)
    s = compute_stats(returns)
    mu, cov, rf = s["mean_vec"], s["cov_mat"], s["rf_rate"]

    tangency = find_tangency(mu, cov, rf, tickers)
    frontier = build_frontier(mu, cov)
    cal = cal_allocation(tangency)

    vols = np.array([pt.expected_vol for pt in frontier])
    rets = np.array([pt.expected_return for pt in frontier])

    fig, ax = plt.subplots(figsize=(8, 5.5))

    # Efficient frontier
    ax.plot(vols, rets, color="#4C72B0", linewidth=2, label="Efficient frontier")

    # Individual assets
    for i, ticker in enumerate(tickers):
        ax.scatter(np.sqrt(cov[i, i]), mu[i],
                   s=80, zorder=5, label=ticker)
        ax.annotate(ticker, (np.sqrt(cov[i, i]), mu[i]),
                    textcoords="offset points", xytext=(6, 4), fontsize=9)

    # Tangency portfolio
    ax.scatter(tangency.expected_vol, tangency.expected_return,
               color="gold", edgecolors="black", s=150, zorder=6,
               marker="*", label=f"Tangency (Sharpe={tangency.sharpe_ratio:.2f})")

    # CAL — extend from rf to beyond tangency
    cal_vols = np.linspace(0, tangency.expected_vol * 1.6, 200)
    cal_rets = rf + tangency.sharpe_ratio * cal_vols
    ax.plot(cal_vols, cal_rets, "k--", linewidth=1.2, label="CAL")

    # Risk-free point
    ax.scatter(0, rf, color="black", s=60, zorder=6)
    ax.annotate(f"SHV (rf={rf:.2%})", (0, rf),
                textcoords="offset points", xytext=(6, -12), fontsize=8)

    # CAL allocation point
    ax.scatter(cal.portfolio_vol, cal.portfolio_return,
               color="tomato", edgecolors="black", s=100, zorder=7,
               marker="D", label=f"Client allocation ({cal.w_risky:.0%} risky)")

    ax.set_xlabel("Annual Volatility (σ)")
    ax.set_ylabel("Expected Annual Return (μ)")
    ax.set_title(f"Mean-Variance Efficient Frontier — {label}")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()

    path = _out(f"efficient_frontier_{label.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '')}.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


def plot_correlation_heatmap(tickers: list[str], label: str) -> Path:
    returns = load_returns(tickers)
    s = compute_stats(returns)
    corr = s["corr"]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn",
                vmin=-1, vmax=1, ax=ax, square=True, linewidths=0.5)
    ax.set_title(f"Return Correlation Matrix — {label}\n(monthly, 2005–2025)")
    fig.tight_layout()

    path = _out(f"correlation_heatmap_{label.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '')}.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")
    return path


def main() -> None:
    for label, tickers in [("Layer A IVV-AGG-SHV", config.LAYER_A_TICKERS),
                             ("Layer B +QUAL-USMV", config.LAYER_B_TICKERS)]:
        plot_frontier(tickers, label)
        plot_correlation_heatmap(tickers, label)


if __name__ == "__main__":
    main()
