# Investment Analysis Final Project — Design Document
## Savings & Investment Plan for a New College Graduate
### Burton Hollifield, Tepper School of Business, CMU — Spring 2026

---

## 1. Project Architecture

### 1.1 Research Question

**Central question:** Given a new college graduate's projected income, expenses, and a 10-year savings goal, what combination of savings rates, asset allocation, rebalancing policy, and risk management produces the highest probability of reaching the goal while keeping downside risk tolerable?

**Subsidiary questions (that the project answers quantitatively):**
- How much should the graduate save each year, and how should savings change as income grows?
- What risky portfolio maximizes the Sharpe ratio using investable ETFs?
- How much cash / risk-free allocation is needed as crisis protection?
- Does tilting toward factor exposures (quality, low volatility) improve the risk-return tradeoff?
- How sensitive are results to different market environments?

### 1.2 Client Profile

| Attribute | Assumption | Justification |
|-----------|-----------|---------------|
| Age | 22, graduating May 2026 | Standard 4-year college |
| Starting salary | $65,000 gross | Median for B.S. holder in economics/business (BLS data) |
| Salary growth | 5% nominal years 1–4, 3% years 5–10 | Early-career wage growth higher, flattens |
| Federal tax | Simplified effective rate schedule (~18–22%) | Standard deduction + 2026 brackets |
| Monthly expenses | $3,500 initially, growing with inflation | Rent-heavy, urban cost of living |
| Inflation | 2.5% annually (baseline) | Long-run CPI target |
| Student loans | $30,000 at 5.5%, 10-year standard repayment | Average federal loan balance |
| 10-year goal | $80,000 in real (inflation-adjusted) terms | Down payment on a home |
| Risk tolerance | Moderate — can tolerate 20% drawdown without selling, but not 40% | Young with long horizon, but needs liquidity |

**Why this profile works:** It's realistic, it creates binding constraints (loan payments reduce early savings capacity), and it makes the savings-rate decision non-trivial. The goal is ambitious but achievable — the project's value lies in showing *how* achievable under different strategies.

### 1.3 Ten-Year Goal

Accumulate **$80,000 in real purchasing power** (roughly $100k+ nominal by year 10 at 2.5% inflation) for a home down payment. This is measured as the terminal real wealth of the investment portfolio.

### 1.4 Main Modeling Choices

| Choice | Decision | Rationale |
|--------|----------|-----------|
| Return estimation | Historical sample moments (monthly, 2005–2025) | Long enough to span GFC + COVID; matches Hollifield's approach |
| Portfolio construction | Mean-variance optimization, maximize Sharpe ratio | Directly from lecture (slides 51, 56–58) |
| Risk-free proxy | SHV (iShares Short Treasury Bond ETF) | Course-aligned; Hollifield uses SHV as risk-free |
| Cash allocation | Spending-needs based: 6 months expenses in SHV | Hollifield's slide 43 approach |
| Rebalancing | Annual, back to target weights | Simple, realistic, discussed in lecture |
| Simulation | Monte Carlo with block bootstrap (12-month blocks) | Preserves autocorrelation and fat tails; more credible than parametric normal |
| Risk metrics | Sharpe ratio, max drawdown, 5th percentile terminal wealth | Sharpe from lecture; drawdown from slide 64–65 |
| Factor tilts | Add QUAL and USMV as alpha-generating extensions | Hollifield's CAPM alpha slides; performance table (slide 21) |

### 1.5 Baseline vs. Extension

**Layer A (Baseline — "Definitely Sufficient"):**
- Deterministic income/expense/savings projection
- 3-asset universe: IVV, AGG, SHV
- Mean-variance efficient frontier + tangency portfolio
- Capital allocation line (how much in tangency vs. SHV)
- Annual rebalancing simulation over 10 years
- Monte Carlo: 5,000 paths, terminal wealth distribution
- Goal attainment probability
- Key charts: efficient frontier, wealth fan chart, savings schedule
- Client-facing summary report

**Layer B (Extension — "Intellectually Stronger"):**
- Expanded to 5-asset universe: add QUAL and USMV (factor tilts)
- CAPM alpha estimation for each asset
- Show Sharpe improvement from factor tilts
- Glide path (de-risking as goal date approaches)
- Stress tests: 2008-style crash at year 3, inflation spike, job loss
- Sensitivity analysis: different estimation windows
- Drawdown analysis and behavioral framing
- Fama-French 5-factor regression on proposed portfolio

---

## 2. Phased Implementation Plan

### Phase 1: Data Collection & Client Setup
**Objective:** Build the income/expense model and pull all historical return data.

**Deliverables:**
- `data/client_profile.py` — deterministic income, tax, expense, loan payment, and savings projection for years 1–10
- `data/pull_returns.py` — download monthly total returns for IVV, AGG, SHV, QUAL, USMV from Yahoo Finance (2005–2025)
- `data/returns.csv` — cleaned monthly return dataset
- `data/client_cashflows.csv` — year-by-year savings schedule

**Key Decisions:**
- Start date for historical returns: January 2005 (captures GFC)
- Tax model: simplified effective rate, not full bracket simulation (good enough, avoids rabbit hole)
- Loan repayment: fixed monthly payment, pre-tax deduction not modeled (simplicity)

**Data Needed:**
- Yahoo Finance: IVV, AGG, SHV, QUAL, USMV adjusted close prices
- BLS: median earnings by education for calibration (can hardcode)
- Federal tax brackets 2026 (can hardcode simplified schedule)

**Outputs/Tables:**
- Table: Year-by-year income, taxes, expenses, loan payment, savings, cumulative savings
- Plot: Savings trajectory over 10 years (deterministic, no market returns yet)

**What Could Go Wrong:**
- Yahoo Finance API changes or data gaps → use `yfinance` library, which is stable
- SHV has limited history pre-2007 → supplement with 3-month T-bill rate from FRED for early years
- QUAL inception is 2013, USMV is 2011 → for Layer A this doesn't matter (only IVV/AGG/SHV); for Layer B use available history

---

### Phase 2: Portfolio Analytics (Layer A Core)
**Objective:** Compute historical statistics, build efficient frontier, find tangency portfolio.

**Deliverables:**
- `models/portfolio_stats.py` — compute mean returns, covariance matrix, correlations, Sharpe ratios
- `models/efficient_frontier.py` — mean-variance optimization (no short sales), tangency portfolio
- Summary statistics table
- Efficient frontier plot with individual assets and tangency portfolio
- Capital allocation line plot

**Key Decisions:**
- Annualize monthly statistics: multiply mean by 12, std by √12
- Optimization: `scipy.optimize.minimize` with SLSQP, bounds=(0,1), constraint sum=1
- Risk-free rate for Sharpe: use average SHV return over sample period
- No short sales constraint (matches Hollifield slide 56, right panel)

**Outputs/Tables:**
- Table: Asset-level statistics (mean return, vol, Sharpe, pairwise correlations) — matches Hollifield's slide 54 format
- Table: Tangency portfolio weights, expected return, vol, Sharpe
- Plot 1: Efficient frontier (σ vs E[r]) with individual assets labeled, tangency point marked, CAL drawn
- Plot 2: Correlation heatmap

**What Could Go Wrong:**
- Optimizer converges to corner solution (100% IVV) → this is possible and actually fine; document it as a finding
- Sample period matters a lot (Hollifield's slide 59 point) → acknowledge this, and in Layer B do robustness check

---

### Phase 3: Simulation Engine
**Objective:** Monte Carlo simulation of 10-year wealth accumulation under proposed strategy.

**Deliverables:**
- `models/simulation.py` — Monte Carlo engine with annual contributions and rebalancing
- Terminal wealth distribution
- Goal attainment probability
- Wealth fan chart

**Key Decisions:**
- Simulation method: **Block bootstrap** (resample 12-month blocks from historical monthly returns with replacement). This preserves within-year autocorrelation and cross-asset dependence without assuming normality. Each simulated year = one randomly drawn historical year of monthly returns.
- Number of paths: 5,000 (sufficient for stable quantiles; 10,000 is fine too but slower)
- Each year: (1) add annual savings, (2) earn monthly returns on portfolio, (3) rebalance to target at year-end
- Terminal wealth measured in real terms: deflate by (1.025)^10

**Outputs/Tables:**
- Table: Terminal wealth distribution — mean, median, 5th/25th/75th/95th percentiles
- Table: Goal attainment probability (P[real wealth ≥ $80k])
- Plot 1: Wealth fan chart — median path with 5th–95th percentile bands
- Plot 2: Histogram of terminal real wealth with $80k goal line marked

**What Could Go Wrong:**
- Block bootstrap can repeat extreme years (2008, 2020) → this is a feature, not a bug; it shows tail risk
- Need to handle contributions correctly: savings are added at start of year, then earn returns through the year
- Inflation adjustment: be consistent about whether returns are nominal or real

---

### Phase 4: Strategy Comparison
**Objective:** Compare multiple strategies to demonstrate the value of each modeling choice.

**Deliverables:**
- `analysis/compare_strategies.py` — run simulation for each strategy variant
- Comparison table and plots

**Strategies to Compare:**
1. **100% SHV (all cash)** — baseline "do nothing risky"
2. **100% IVV (all equity)** — maximum aggression
3. **60/40 IVV/AGG** — conventional wisdom
4. **Tangency portfolio** — MV-optimal from Phase 2
5. **Tangency + SHV (risk-adjusted)** — CAL allocation matching client risk tolerance
6. **(Layer B) Factor-tilted tangency** — adding QUAL/USMV

**Outputs/Tables:**
- Table: Side-by-side comparison — E[terminal wealth], P[goal], median, 5th percentile, max drawdown, Sharpe
- Plot: Overlaid wealth fan charts for 3–4 key strategies
- Plot: Goal attainment probability bar chart across strategies

**What Could Go Wrong:**
- Too many strategies → keep it to 4–5 meaningful comparisons, not a combinatorial explosion
- Need to tell a clear narrative: "here's why the tangency portfolio dominates, here's the cost of being too conservative or too aggressive"

---

### Phase 5: Risk Analysis & Stress Testing (Layer B)
**Objective:** Deeper risk analysis — drawdown, stress scenarios, sensitivity.

**Deliverables:**
- `analysis/risk_analysis.py` — drawdown computation, stress scenarios
- `analysis/sensitivity.py` — vary estimation window, inflation, salary growth
- `analysis/factor_alpha.py` — CAPM regressions, alpha estimation, FF5 regression

**Stress Scenarios:**
1. **Market crash at year 3:** Force a −35% equity return in simulation year 3, then resume normal draws
2. **Job loss at year 3:** Zero savings for 12 months, draw down emergency fund
3. **High inflation (4.5%):** Raise inflation assumption, eroding real value of goal and cash

**Factor Analysis (connects to CAPM lecture):**
- Run CAPM regression for each asset: r_i − r_f = α + β(r_mkt − r_f) + ε
- Report α, β, R² for IVV, AGG, QUAL, USMV
- Show that QUAL and USMV have historically positive α (connects to slide 21)
- Run FF5 regression on the proposed portfolio to decompose returns

**Sensitivity Analysis:**
- Re-estimate tangency portfolio using 2010–2025 vs 2015–2025 vs 2005–2015 data
- Show how weights and Sharpe shift (Hollifield's slide 59 point about sample dependence)

**Outputs/Tables:**
- Table: CAPM α, β for each asset
- Table: Stress scenario impact on goal attainment probability
- Plot: Drawdown chart for proposed strategy (à la Hollifield slide 65)
- Plot: Sensitivity — tangency weights under different estimation windows

**What Could Go Wrong:**
- Alpha estimates are backward-looking; emphasize this is historical, not a forecast
- FF5 data: pull from Ken French's data library via `pandas_datareader` (Hollifield uses this, slide 15)

---

### Phase 6: Report & Presentation
**Objective:** Produce client-facing deliverable and Q&A preparation.

**Deliverables:**
- `report/final_report.md` or `.pdf` — 8–12 page client report
- `report/executive_summary.md` — 1-page recommendation
- Key exhibit figures saved as high-res PNGs

**Report Structure:**
1. Executive Summary (1 page): who is the client, what's the goal, what's the recommendation
2. Client Profile & Assumptions (1 page)
3. Investment Universe & Historical Analysis (2 pages): stats table, correlations, efficient frontier
4. Recommended Strategy (2 pages): tangency portfolio, capital allocation, savings schedule, rebalancing
5. Simulation Results (2 pages): wealth fan chart, goal probability, comparison table
6. Risk Analysis (1–2 pages): drawdown, stress tests, sensitivity
7. Factor Analysis Extension (1 page, if Layer B): alpha, FF5, factor tilts
8. Conclusion & Caveats (0.5 page)

---

## 3. Two-Layer Design Summary

### Layer A: Clean, Class-Aligned, Sufficient
- 3-asset universe (IVV, AGG, SHV)
- Deterministic savings model
- Mean-variance frontier + tangency portfolio
- Capital allocation line
- Monte Carlo simulation (5,000 paths, block bootstrap)
- Goal attainment probability
- Strategy comparison (4 strategies)
- Core risk metrics: Sharpe, vol, 5th-percentile wealth
- Client report with 6–8 key exhibits

**Estimated effort:** 60–70% of total work. Covers all project questions. Would earn a strong grade.

### Layer B: Intellectually Deeper Extension
- 5-asset universe (add QUAL, USMV)
- CAPM alpha regressions
- Fama-French 5-factor decomposition
- Factor-tilted tangency portfolio
- Glide path (time-varying allocation)
- Stress testing (crash, job loss, inflation spike)
- Estimation-window sensitivity
- Drawdown analysis
- Enhanced visualizations

**Estimated effort:** Additional 30–40%. Differentiates from other groups. Shows research maturity.

**The key principle:** Layer A is self-contained and complete. Layer B adds depth without breaking Layer A. You can stop at any point in Layer B and still have a strong project.

---

## 4. Modeling Stack Recommendation

| Component | Approach | Worth It? |
|-----------|----------|-----------|
| Savings projection | Deterministic year-by-year (income − tax − expenses − loan payment) | **Yes, essential.** Simple and clear. |
| Tax model | Simplified effective rate schedule | **Yes.** Full bracket sim is overkill for this project. |
| Return estimation | Sample mean and covariance from monthly data, annualized | **Yes, essential.** Exactly what Hollifield does. |
| MV optimization | `scipy.optimize.minimize` (SLSQP), no short sales | **Yes, essential.** Core of the course. |
| Sharpe ratio comparison | Compute for each asset and for portfolios | **Yes, essential.** Central metric in lectures. |
| Capital allocation | Choose w along CAL based on client risk tolerance | **Yes, essential.** Directly answers "how much risk." |
| Annual rebalancing | Simulate rebalancing back to target weights each year | **Yes.** Shows you understand the concept; easy to implement. |
| Monte Carlo (block bootstrap) | Resample historical 12-month blocks, 5,000 paths | **Yes, essential.** This is what makes the project quantitative. |
| Goal attainment probability | P[real terminal wealth ≥ $80k] | **Yes, essential.** Key deliverable. |
| Drawdown | Compute max drawdown on simulated paths | **Yes.** Easy to add, directly from lecture. |
| Strategy comparison | 4–5 strategies side by side | **Yes.** Shows analytical judgment. |
| CAPM alpha regression | OLS: r_i − r_f on r_mkt − r_f | **Yes for Layer B.** Quick, connects to lecture. |
| FF5 regression | OLS with 5 factors from French library | **Yes for Layer B.** 20 lines of code, impressive. |
| Glide path | Linear de-risking schedule | **Maybe.** Adds depth but is less central to course. Include if time permits. |
| Stress testing | Inject crash/job loss into simulation | **Yes for Layer B.** Very practical, impressive to client. |
| Sensitivity to estimation window | Re-run with different historical periods | **Yes for Layer B.** Directly addresses Hollifield's slide 59. |
| Consumption optimization (lifecycle model) | Optimize consumption path via `scipy.minimize` | **No — overkill.** Interesting but not in the course, hard to explain in Q&A. |
| Regime-switching model | Hamilton regime model for returns | **No — overkill.** Too complex, not in course, hard to defend. |
| Individual stock selection | Pick stocks, estimate individual betas | **No.** Hollifield explicitly says stock-picking is hard (slide 22). Use ETFs. |

---

## 5. Asset Universe

### Layer A: Core (3 Assets)

| Ticker | Full Name | Role | Why It Belongs |
|--------|-----------|------|---------------|
| **IVV** | iShares Core S&P 500 ETF | U.S. equity market | Hollifield's primary equity building block (slides 8–9, 53). Proxy for the market portfolio in CAPM. Captures the equity risk premium. |
| **AGG** | iShares Core U.S. Aggregate Bond ETF | Investment-grade bond | Hollifield uses AGG as the diversified bond exposure (slide 52). Low correlation with IVV provides diversification benefit. Intermediate duration — less rate-sensitive than TLT. |
| **SHV** | iShares Short Treasury Bond ETF | Risk-free / cash proxy | Hollifield's risk-free proxy (slides 8–9). Near-zero volatility. Used for the emergency fund and the risk-free component of the capital allocation. |

**Why not TLT?** TLT (20+ year Treasuries) has high interest-rate sensitivity. Hollifield shows it looked great in 2017–2021 but warns about sample-period dependence (slide 59). For a 10-year plan starting in 2026, with rates potentially staying elevated, AGG is a more defensible bond choice. You can mention TLT in the report as an alternative and show what happens if you swap it in.

### Layer B: Extended (Add 2 Factor ETFs)

| Ticker | Full Name | Role | Why It Belongs |
|--------|-----------|------|---------------|
| **QUAL** | iShares MSCI USA Quality Factor ETF | Quality/profitability tilt | Hollifield shows "Long Quality" had α = 3.41% and Sharpe = 0.19 vs. market's 0.14 (slide 21). Listed explicitly on slide 22. |
| **USMV** | iShares MSCI USA Min Vol Factor ETF | Low-volatility tilt | "Long Low Volatility" had α = 3.84% and Sharpe = 0.20 (slide 21). Lower beta (0.71), beneficial for a client who can't tolerate large drawdowns. Listed on slide 23. |

**Why these two and not MTUM/VLUE/SIZE?** Quality and low-vol had the strongest historical risk-adjusted performance in Hollifield's own data. Momentum is high-turnover and crashed in 2009. Value has been inconsistent post-GFC. Quality and low-vol are also the most defensible for a conservative client.

---

## 6. Folder Structure & File Roadmap

```
investment_project/
│
├── config.py                  # All assumptions in one place
│                                (salary, growth rates, tax rates,
│                                 inflation, goal, asset tickers,
│                                 date range, n_simulations)
│
├── data/
│   ├── pull_returns.py        # Download & clean ETF returns
│   ├── client_cashflows.py    # Deterministic savings projection
│   └── returns.csv            # [generated] cleaned monthly returns
│
├── models/
│   ├── portfolio_stats.py     # Mean, vol, cov, corr, Sharpe
│   ├── efficient_frontier.py  # MV optimization, tangency portfolio
│   └── simulation.py          # Monte Carlo block bootstrap engine
│
├── analysis/
│   ├── compare_strategies.py  # Run all strategies, produce comparison
│   ├── risk_analysis.py       # Drawdown, stress tests
│   ├── factor_alpha.py        # CAPM alpha, FF5 regressions (Layer B)
│   └── sensitivity.py         # Estimation window robustness (Layer B)
│
├── plots/
│   ├── plot_frontier.py       # Efficient frontier + CAL
│   ├── plot_wealth.py         # Fan chart, histograms
│   ├── plot_comparison.py     # Strategy comparison exhibits
│   └── plot_risk.py           # Drawdown, stress test charts
│
├── report/
│   ├── final_report.md        # Full report text
│   └── figures/               # All saved figures
│
├── notebooks/                 # (optional) Jupyter for exploration
│   └── exploration.ipynb
│
└── requirements.txt           # numpy, pandas, scipy, matplotlib,
                                 yfinance, pandas_datareader
```

### File-by-File Purpose

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `config.py` | 40–50 | Single source of truth for all parameters. Change assumptions here, everything downstream updates. |
| `data/pull_returns.py` | 30–40 | Uses `yfinance` to pull adjusted close, compute monthly returns, merge into one DataFrame, save to CSV. |
| `data/client_cashflows.py` | 60–80 | Year-by-year: gross income → after-tax income → subtract expenses → subtract loan payment → annual savings. Returns DataFrame. |
| `models/portfolio_stats.py` | 40–50 | Compute annualized mean, vol, Sharpe for each asset. Compute covariance and correlation matrices. |
| `models/efficient_frontier.py` | 80–100 | `scipy.optimize.minimize` to find min-variance portfolios for a grid of target returns. Find tangency portfolio (max Sharpe). |
| `models/simulation.py` | 100–120 | Block bootstrap Monte Carlo. For each path: sample a sequence of historical years, apply monthly returns to portfolio + contributions, rebalance annually. Return array of terminal wealth values. |
| `analysis/compare_strategies.py` | 60–80 | Define 4–6 strategy weight vectors. Call `simulation.py` for each. Compute summary stats. Produce comparison table. |
| `analysis/risk_analysis.py` | 60–80 | Max drawdown calculation. Stress scenario injection (override year 3 returns). |
| `analysis/factor_alpha.py` | 50–60 | CAPM regression for each asset. FF5 regression using French library data. Report α, β, R², t-stats. |
| `analysis/sensitivity.py` | 40–50 | Re-run frontier estimation with different date ranges. Show tangency weight shifts. |
| `plots/plot_*.py` | 40–60 each | Matplotlib/Plotly figures. Each file produces 1–2 publication-quality plots. |

---

## 7. Execution Order for Claude Code

### Build Order (what to implement first)

**Sprint 1: Foundation (do first, test immediately)**
1. `config.py` — define all parameters
2. `data/pull_returns.py` — pull data, verify it's clean
3. `data/client_cashflows.py` — savings projection, print table, sanity check
4. **Test:** Does the savings schedule make sense? Does the grad have positive savings by year 2–3?

**Sprint 2: Portfolio Core (the heart of the project)**
5. `models/portfolio_stats.py` — compute stats, print summary table
6. `models/efficient_frontier.py` — frontier + tangency portfolio
7. `plots/plot_frontier.py` — efficient frontier chart
8. **Test:** Does the tangency portfolio have reasonable weights? Is the Sharpe higher than any individual asset?

**Sprint 3: Simulation (the quantitative engine)**
9. `models/simulation.py` — Monte Carlo engine
10. `plots/plot_wealth.py` — fan chart and histogram
11. **Test:** Run 100 paths first (fast). Check: does median terminal wealth grow over time? Are tails reasonable?

**Sprint 4: Strategy Comparison (the analytical payoff)**
12. `analysis/compare_strategies.py` — run all strategies
13. `plots/plot_comparison.py` — comparison exhibits
14. **Test:** Does the tangency strategy dominate? Is all-cash clearly inferior?

**→ At this point, Layer A is complete. Pause, review, decide whether to proceed.**

**Sprint 5: Layer B Extensions (if time permits)**
15. `analysis/factor_alpha.py` — CAPM and FF5 regressions
16. Re-run efficient frontier with 5 assets (add QUAL, USMV)
17. `analysis/risk_analysis.py` — drawdown + stress tests
18. `analysis/sensitivity.py` — estimation window robustness
19. Update comparison with factor-tilted strategy

**Sprint 6: Report**
20. Write `report/final_report.md`
21. Polish all figures
22. Prepare Q&A talking points

### What to Postpone
- Glide path optimization — only add if Sprints 1–5 are done and clean
- Jupyter notebook — only for personal exploration; the report should be standalone
- Any web dashboard or interactive tool — impressive but not what Hollifield is grading

### What to Avoid Overengineering
- **Tax model:** A simplified effective rate is fine. Don't model marginal brackets, FICA separately, state taxes, etc.
- **Rebalancing frequency:** Annual is sufficient. Monthly or threshold-based rebalancing adds complexity with minimal insight gain.
- **Number of simulations:** 5,000 is plenty. Going to 100,000 doesn't change the story and just slows debugging.
- **Asset universe:** 3–5 ETFs is the sweet spot. Adding 10+ assets leads to overfitting and unclear narratives.
- **Optimization method:** SLSQP is fine. Don't implement custom quadratic programming or use CVXPY unless you already know it.

---

## 8. Final Recommendations

### Recommended Project Design (Summary)

**Client:** 22-year-old college graduate, $65k starting salary, $30k student loans, saving for an $80k real-dollar home down payment in 10 years.

**Strategy:** Invest in a Sharpe-maximizing portfolio of IVV + AGG (+ optionally QUAL/USMV), combined with an SHV cash buffer sized to 6 months of expenses. Rebalance annually. Increase savings rate as income grows and loans are paid off.

**Analysis:** Monte Carlo simulation (5,000 paths, block bootstrap from 20 years of history) to estimate goal attainment probability, expected terminal wealth, and downside risk under multiple strategies.

**Key result to target:** Show that the MV-optimal strategy achieves ~75–85% goal attainment probability, compared to ~40% for all-cash and ~85%+ but with large drawdown risk for all-equity. The recommended strategy balances probability and downside protection.

---

### Week-by-Week Implementation Plan

| Week | Focus | Deliverables | Layer |
|------|-------|-------------|-------|
| **Week 1** | Data + Client Model | `config.py`, `pull_returns.py`, `client_cashflows.py`, savings table | A |
| **Week 2** | Portfolio Analytics | `portfolio_stats.py`, `efficient_frontier.py`, frontier plot, stats table | A |
| **Week 3** | Simulation Engine | `simulation.py`, wealth fan chart, goal attainment probability | A |
| **Week 4** | Strategy Comparison + Core Report | `compare_strategies.py`, comparison table, draft report sections 1–5 | A |
| **Week 5** | Extensions + Polish | Factor alpha, stress tests, sensitivity, final report, Q&A prep | B |

---

### Minimum Viable Excellent Project (stop here if needed)

- Deterministic savings schedule (table + plot)
- 3-asset efficient frontier with tangency portfolio
- Capital allocation recommendation
- 5,000-path Monte Carlo simulation
- Goal attainment probability for 4 strategies
- Wealth fan chart + comparison table
- 8-page client report with clear recommendation
- **Estimated total code: ~500–600 lines across all files**

### Ambitious Version (full Layer B)

All of the above, plus:
- 5-asset frontier with factor-tilted tangency
- CAPM α and FF5 regression table
- 3 stress scenarios with impact analysis
- Estimation-window sensitivity
- Drawdown analysis with behavioral interpretation
- 10–12 page report with risk analysis appendix
- **Estimated total code: ~800–1000 lines across all files**

---

### What Makes This Project Stand Out

1. **It answers all five project questions quantitatively**, not qualitatively
2. **It uses the exact analytical framework from class** (Sharpe, MV frontier, CAPM α, rebalancing, risk-free allocation)
3. **The Monte Carlo simulation converts backward-looking statistics into forward-looking probabilities** — this is what most student projects will lack
4. **The strategy comparison shows analytical judgment** — not "here's one answer" but "here's why this answer dominates alternatives"
5. **The factor-tilt extension connects CAPM theory to practical implementation** using the same ETFs Hollifield put on slide 22–23
6. **The stress tests answer the client's real fear:** "what happens if the market crashes?"
7. **The estimation-window sensitivity shows intellectual honesty** about the limits of historical estimation — exactly the lesson from Hollifield's slide 59
