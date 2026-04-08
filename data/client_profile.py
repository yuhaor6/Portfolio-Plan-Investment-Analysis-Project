"""
data/client_profile.py — Deterministic income / tax / expense / loan / savings projection.

Outputs:
  - data/client_cashflows.csv   (year-by-year schedule)
  - Prints the table and a quick sanity check
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402


# ── Income schedule ─────────────────────────────────────────────
def build_income(years: int = config.PLAN_YEARS) -> pd.DataFrame:
    salary = config.START_SALARY
    rows = []
    for yr in range(1, years + 1):
        rows.append({"year": yr, "salary": salary})
        growth = config.SALARY_GROWTH[min(yr - 1, len(config.SALARY_GROWTH) - 1)]
        salary *= 1 + growth
    return pd.DataFrame(rows)


# ── Expense schedule ────────────────────────────────────────────
def build_expenses(years: int = config.PLAN_YEARS) -> pd.DataFrame:
    base = config.MONTHLY_EXPENSES * 12
    rows = [
        {"year": yr, "expenses": base * (1 + config.INFLATION_RATE) ** (yr - 1)}
        for yr in range(1, years + 1)
    ]
    return pd.DataFrame(rows)


# ── Loan amortisation ──────────────────────────────────────────
def build_loan(years: int = config.PLAN_YEARS) -> pd.DataFrame:
    n_months = config.LOAN_TERM_YEARS * 12
    r = config.LOAN_RATE / 12
    pmt = config.LOAN_BALANCE * r / (1 - (1 + r) ** -n_months)
    balance = config.LOAN_BALANCE
    records = []
    for m in range(1, n_months + 1):
        interest = balance * r
        principal = pmt - interest
        balance = max(balance - principal, 0.0)
        records.append({"month": m, "payment": pmt, "interest": interest,
                        "principal": principal, "balance": balance})
    df = pd.DataFrame(records)
    df["year"] = (df["month"] - 1) // 12 + 1
    annual = df.groupby("year")["payment"].sum().reset_index()
    annual = annual.rename(columns={"payment": "loan_payment"})
    return annual[annual["year"] <= years].copy()


# ── Combined savings plan ──────────────────────────────────────
def build_savings_plan() -> pd.DataFrame:
    inc = build_income()
    exp = build_expenses()
    loan = build_loan()
    df = inc.merge(exp, on="year").merge(loan, on="year", how="left")
    df["loan_payment"] = df["loan_payment"].fillna(0.0)
    df["taxes"] = df["salary"] * config.EFFECTIVE_TAX_RATE
    df["net_income"] = df["salary"] - df["taxes"]
    df["savings"] = df["net_income"] - df["expenses"] - df["loan_payment"]
    df["savings"] = df["savings"].clip(lower=0.0)
    df["cumulative_savings"] = df["savings"].cumsum()
    df["calendar_year"] = config.START_YEAR + df["year"] - 1
    return df


# ── Plot: deterministic savings trajectory ─────────────────────
def plot_savings(df: pd.DataFrame, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(df["calendar_year"], df["savings"], color="#4C72B0", label="Annual savings")
    ax.plot(df["calendar_year"], df["cumulative_savings"], "o-", color="#DD8452",
            linewidth=2, label="Cumulative savings")
    ax.axhline(config.SAVINGS_GOAL_REAL, color="red", linestyle="--", label=f"Goal (real ${config.SAVINGS_GOAL_REAL:,.0f})")
    ax.set_xlabel("Year")
    ax.set_ylabel("Dollars ($)")
    ax.set_title("Deterministic Savings Trajectory (no investment returns)")
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.tight_layout()
    path = out_dir / "savings_trajectory.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ── Main entry point ───────────────────────────────────────────
def main() -> None:
    df = build_savings_plan()

    # Save CSV
    csv_path = PROJECT_ROOT / config.CASHFLOWS_CSV
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"Saved → {csv_path}\n")

    # Pretty-print the table
    display_cols = ["calendar_year", "salary", "taxes", "expenses",
                    "loan_payment", "net_income", "savings", "cumulative_savings"]
    fmt = df[display_cols].copy()
    for c in fmt.columns[1:]:
        fmt[c] = fmt[c].map(lambda v: f"${v:,.0f}")
    print(fmt.to_string(index=False))

    # Sanity check
    total = df["savings"].sum()
    print(f"\nTotal 10-year savings (no returns): ${total:,.0f}")
    print(f"Goal (real): ${config.SAVINGS_GOAL_REAL:,.0f}")
    shortfall = config.SAVINGS_GOAL_REAL - total
    if shortfall > 0:
        print(f"Shortfall without investment returns: ${shortfall:,.0f}  →  investing is essential")
    else:
        print("Savings alone exceed the goal — investing adds buffer")

    # Plot
    fig_path = plot_savings(df, PROJECT_ROOT / Path(config.PLOTS_DIR))
    print(f"\nPlot saved → {fig_path}")


if __name__ == "__main__":
    main()
