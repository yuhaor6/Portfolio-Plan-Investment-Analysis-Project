"""
analysis/factor_alpha.py — CAPM regressions and Fama-French 5-factor analysis.

CAPM per asset (using IVV as market proxy):
  r_i − r_f = α + β(r_mkt − r_f) + ε
  Reports α (annualised), β, R², t-stat(α), t-stat(β)

FF5 regression on the proposed Layer B tangency portfolio:
  r_p − r_f = α + β₁(Mkt-RF) + β₂SMB + β₃HML + β₄RMW + β₅CMA + ε
  FF5 data pulled from Ken French's data library via pandas_datareader.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from models.efficient_frontier import run_phase2  # noqa: E402
from models.portfolio_stats import load_returns  # noqa: E402


# ── CAPM regressions ──────────────────────────────────────────────────────────

def run_capm(tickers: list[str] | None = None) -> pd.DataFrame:
    """
    Run CAPM regression for each non-market, non-rf asset.
    IVV = market proxy; SHV = risk-free proxy.
    """
    if tickers is None:
        tickers = config.LAYER_B_TICKERS

    returns = load_returns(tickers)
    mkt_rf = returns["IVV"] - returns["SHV"]   # excess market return

    rows = []
    for ticker in tickers:
        if ticker in ("IVV", "SHV"):
            continue
        excess = returns[ticker] - returns["SHV"]
        X = sm.add_constant(mkt_rf.values)
        y = excess.values
        model = sm.OLS(y, X).fit()

        alpha_monthly = model.params[0]
        alpha_annual  = alpha_monthly * 12
        beta          = model.params[1]
        r2            = model.rsquared
        t_alpha       = model.tvalues[0]
        t_beta        = model.tvalues[1]
        p_alpha       = model.pvalues[0]

        rows.append({
            "Asset":           ticker,
            "Alpha (ann.)":    round(alpha_annual, 4),
            "Beta":            round(beta, 4),
            "R²":              round(r2, 4),
            "t(alpha)":        round(t_alpha, 3),
            "p(alpha)":        round(p_alpha, 4),
            "t(beta)":         round(t_beta, 3),
        })

    return pd.DataFrame(rows)


# ── FF5 regression ────────────────────────────────────────────────────────────

def fetch_ff5(start: str = config.RETURN_START,
              end:   str = config.RETURN_END) -> pd.DataFrame | None:
    """
    Download monthly FF5 factors directly from Ken French's website.
    Returns None if unavailable (no internet, URL changed, etc.).
    """
    import io
    import urllib.request
    import zipfile

    URL = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
        "F-F_Research_Data_5_Factors_2x3_CSV.zip"
    )
    try:
        with urllib.request.urlopen(URL, timeout=15) as resp:
            raw = resp.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
            content = zf.read(name).decode("utf-8", errors="replace")

        # Skip header lines until we hit the date column
        lines = content.splitlines()
        data_start = next(i for i, ln in enumerate(lines)
                          if ln.strip() and ln.strip()[0].isdigit())
        # Find the blank line that terminates the monthly section
        data_end = data_start
        for i in range(data_start, len(lines)):
            ln = lines[i].strip()
            if not ln:
                data_end = i
                break

        csv_block = "\n".join(lines[data_start:data_end])
        ff = pd.read_csv(
            io.StringIO(csv_block),
            header=None,
            names=["Date", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"],
        )
        ff["Date"] = pd.to_datetime(ff["Date"].astype(str), format="%Y%m")
        ff = ff.set_index("Date")
        ff = ff.apply(pd.to_numeric, errors="coerce") / 100.0
        ff = ff.dropna()
        # Filter to requested window
        ff = ff.loc[start:end]
        return ff

    except Exception as exc:
        print(f"  [FF5] Could not download French data: {exc}")
        return None


def run_ff5(tickers: list[str] | None = None) -> pd.DataFrame | None:
    """
    Run FF5 regression for the Layer B tangency portfolio.
    Returns DataFrame of factor loadings, or None if FF5 data unavailable.
    """
    if tickers is None:
        tickers = config.LAYER_B_TICKERS

    ff5 = fetch_ff5()
    if ff5 is None:
        return None

    returns = load_returns(tickers)
    out = run_phase2(tickers)
    t = out["tangency"]
    c = out["cal"]
    weights = c.w_risky * t.weights
    weights[tickers.index("SHV")] += c.w_rf
    weights = weights / weights.sum()

    # Portfolio monthly return
    port_ret = (returns * weights).sum(axis=1)

    # Align dates — FF5 uses month-start, returns uses month-end.
    # Normalise both to Period('M') for a robust join.
    ff5.index = ff5.index.to_period("M")
    port_ret.index = port_ret.index.to_period("M")
    common = port_ret.index.intersection(ff5.index)
    port_aligned = port_ret.loc[common]
    ff5_aligned  = ff5.loc[common]

    excess_port = port_aligned.values - ff5_aligned["RF"].values
    factors = ff5_aligned[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]].values
    X = sm.add_constant(factors)
    model = sm.OLS(excess_port, X).fit()

    factor_names = ["Alpha", "Mkt-RF", "SMB", "HML", "RMW", "CMA"]
    rows = []
    for name, coef, tval, pval in zip(
        factor_names, model.params, model.tvalues, model.pvalues
    ):
        ann_coef = coef * 12 if name == "Alpha" else coef
        rows.append({
            "Factor":        name,
            "Loading":       round(ann_coef if name == "Alpha" else coef, 4),
            "t-stat":        round(tval, 3),
            "p-value":       round(pval, 4),
        })

    rows.append({"Factor": "R²", "Loading": round(model.rsquared, 4),
                 "t-stat": None, "p-value": None})
    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print(" CAPM Regressions (IVV = market, SHV = risk-free)")
    print("=" * 60)
    capm_df = run_capm()
    print(capm_df.to_string(index=False))

    print("\n" + "=" * 60)
    print(" FF5 Regression — Layer B Tangency Portfolio")
    print("=" * 60)
    ff5_df = run_ff5()
    if ff5_df is not None:
        print(ff5_df.to_string(index=False))
    else:
        print("  FF5 data unavailable (no internet / pandas_datareader issue).")
        print("  CAPM results above are still valid.")

    # Save
    capm_df.to_csv(PROJECT_ROOT / "analysis" / "capm_results.csv", index=False)
    if ff5_df is not None:
        ff5_df.to_csv(PROJECT_ROOT / "analysis" / "ff5_results.csv", index=False)
    print(f"\nSaved CAPM results → analysis/capm_results.csv")


if __name__ == "__main__":
    main()
