"""
config.py — Single source of truth for all project assumptions.

Change parameters here and every downstream module picks them up.
"""

# ── Client profile ──────────────────────────────────────────────
START_YEAR = 2026
START_AGE = 22
START_SALARY = 65_000.0                      # gross annual
SALARY_GROWTH = [0.05] * 4 + [0.03] * 6     # per-year nominal growth
EFFECTIVE_TAX_RATE = 0.20                    # simplified federal + state
MONTHLY_EXPENSES = 3_500.0                   # rent-heavy, urban
INFLATION_RATE = 0.025                       # long-run CPI target

# ── Student loans ───────────────────────────────────────────────
LOAN_BALANCE = 30_000.0
LOAN_RATE = 0.055                            # federal direct rate
LOAN_TERM_YEARS = 10                         # standard repayment

# ── 10-year goal ────────────────────────────────────────────────
SAVINGS_GOAL_REAL = 150_000.0                # real (inflation-adjusted)
PLAN_YEARS = 10

# ── Asset universe ──────────────────────────────────────────────
LAYER_A_TICKERS = ["IVV", "AGG", "SHV"]
LAYER_B_TICKERS = ["IVV", "AGG", "SHV", "QUAL", "USMV"]
TICKERS = LAYER_B_TICKERS                   # pull all; filter later

# ── Historical data window ──────────────────────────────────────
RETURN_START = "2005-01-01"
RETURN_END   = "2025-12-31"

# ── Simulation parameters ───────────────────────────────────────
N_SIMULATIONS = 5_000
BLOCK_SIZE_MONTHS = 12                       # block-bootstrap block length
RANDOM_SEED = 42

# ── Risk tolerance ──────────────────────────────────────────────
MAX_DRAWDOWN_TOLERANCE = 0.20                # can stomach 20 % drawdown
EMERGENCY_FUND_MONTHS = 6                    # months of expenses in SHV/cash

# ── Output paths (relative to project root) ─────────────────────
DATA_DIR = "data"
RETURNS_CSV = f"{DATA_DIR}/returns.csv"
CASHFLOWS_CSV = f"{DATA_DIR}/client_cashflows.csv"
PLOTS_DIR = "plots/figures"
