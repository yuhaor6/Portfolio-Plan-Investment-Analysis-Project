"""
models/efficient_frontier.py — Mean-variance optimisation.

Produces:
  - Minimum-variance frontier (grid of target returns)
  - Tangency portfolio (max Sharpe, no short sales)
  - Capital allocation line (CAL) given client risk tolerance
  - CAL allocation: fraction in tangency vs SHV matching 20 % max-drawdown
"""
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from models.portfolio_stats import compute_stats, load_returns  # noqa: E402


@dataclass
class FrontierPoint:
    weights: np.ndarray
    expected_return: float
    expected_vol: float


@dataclass
class TangencyResult:
    weights: np.ndarray
    tickers: list[str]
    expected_return: float
    expected_vol: float
    sharpe_ratio: float
    rf_rate: float


@dataclass
class CALAllocation:
    tangency: TangencyResult
    w_risky: float          # fraction in tangency portfolio
    w_rf: float             # fraction in SHV / risk-free
    portfolio_return: float
    portfolio_vol: float


# ── Helpers ──────────────────────────────────────────────────────

def _port_return(w: np.ndarray, mu: np.ndarray) -> float:
    return float(w @ mu)


def _port_vol(w: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(w @ cov @ w))


# ── Tangency portfolio ────────────────────────────────────────────

def find_tangency(mu: np.ndarray, cov: np.ndarray, rf: float,
                  tickers: list[str]) -> TangencyResult:
    """Maximise Sharpe ratio subject to long-only + sum-to-one constraints."""
    n = len(mu)
    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    best = None
    best_sharpe = -np.inf
    # Multiple random restarts for robustness
    rng = np.random.default_rng(config.RANDOM_SEED)
    for _ in range(20):
        w0 = rng.dirichlet(np.ones(n))
        res = minimize(
            lambda w: -((w @ mu - rf) / np.sqrt(w @ cov @ w)),
            w0, method="SLSQP", bounds=bounds, constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        if res.success and -res.fun > best_sharpe:
            best_sharpe = -res.fun
            best = res.x
    w = best
    ret = _port_return(w, mu)
    vol = _port_vol(w, cov)
    return TangencyResult(w, tickers, ret, vol, (ret - rf) / vol, rf)


# ── Minimum variance frontier ─────────────────────────────────────

def build_frontier(mu: np.ndarray, cov: np.ndarray,
                   n_points: int = 200) -> list[FrontierPoint]:
    """Trace out the efficient frontier (min-var for each target return)."""
    n = len(mu)
    mu_min = mu.min()
    mu_max = mu.max()
    targets = np.linspace(mu_min, mu_max, n_points)
    frontier = []
    for target in targets:
        bounds = [(0.0, 1.0)] * n
        constraints = [
            {"type": "eq", "fun": lambda w: w.sum() - 1.0},
            {"type": "eq", "fun": lambda w, t=target: w @ mu - t},
        ]
        res = minimize(
            lambda w: w @ cov @ w,
            np.repeat(1 / n, n), method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        if res.success:
            vol = np.sqrt(res.fun)
            frontier.append(FrontierPoint(res.x, float(target), float(vol)))
    return frontier


# ── Capital Allocation Line ───────────────────────────────────────

def cal_allocation(tangency: TangencyResult) -> CALAllocation:
    """
    Choose the weight w in the tangency portfolio along the CAL so that
    portfolio vol = MAX_DRAWDOWN_TOLERANCE (proxy: treat max drawdown ≈ 2 × vol).
    Target vol = MAX_DRAWDOWN_TOLERANCE / 2.
    """
    target_vol = config.MAX_DRAWDOWN_TOLERANCE / 2.0
    w_risky = min(target_vol / tangency.expected_vol, 1.0)
    w_rf    = 1.0 - w_risky
    port_ret = w_risky * tangency.expected_return + w_rf * tangency.rf_rate
    port_vol = w_risky * tangency.expected_vol
    return CALAllocation(tangency, w_risky, w_rf, port_ret, port_vol)


# ── Main entry ────────────────────────────────────────────────────

def run_phase2(tickers: list[str]) -> dict:
    """Full Phase 2 pipeline for a given ticker universe."""
    returns = load_returns(tickers)
    s = compute_stats(returns)
    tangency = find_tangency(s["mean_vec"], s["cov_mat"], s["rf_rate"], tickers)
    frontier = build_frontier(s["mean_vec"], s["cov_mat"])
    cal = cal_allocation(tangency)
    return {"stats": s, "tangency": tangency, "frontier": frontier, "cal": cal}


def main() -> None:
    for label, tickers in [("Layer A (IVV/AGG/SHV)", config.LAYER_A_TICKERS),
                            ("Layer B (+QUAL/USMV)", config.LAYER_B_TICKERS)]:
        print(f"\n{'='*55}")
        print(f" {label}")
        print(f"{'='*55}")
        out = run_phase2(tickers)
        t = out["tangency"]
        c = out["cal"]

        print("\nTangency portfolio weights:")
        for ticker, w in zip(t.tickers, t.weights):
            print(f"  {ticker}: {w:.4f}")
        print(f"  E[return]:    {t.expected_return:.4f}")
        print(f"  Volatility:   {t.expected_vol:.4f}")
        print(f"  Sharpe ratio: {t.sharpe_ratio:.4f}")
        print(f"  Risk-free:    {t.rf_rate:.4f}")

        print(f"\nCAL allocation (target vol ≤ {config.MAX_DRAWDOWN_TOLERANCE/2:.0%}):")
        print(f"  {c.w_risky:.2%} in tangency  |  {c.w_rf:.2%} in SHV")
        print(f"  Portfolio E[return]: {c.portfolio_return:.4f}")
        print(f"  Portfolio vol:       {c.portfolio_vol:.4f}")


if __name__ == "__main__":
    main()
