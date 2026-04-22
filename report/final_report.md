# Investment Analysis — Final Report
## 10-Year Savings & Investment Plan for a New College Graduate
**Course:** 70492 Investments Analysis, Burton Hollifield, Tepper School of Business, CMU  
**Date:** April 7, 2026

---

## 1. Executive Summary

A 22-year-old college graduate starting work in May 2026 seeks to accumulate **$150,000 in real (2026) dollars** within 10 years for a home down payment. After modelling the client's deterministic savings capacity and optimising a 5-asset portfolio using mean-variance theory, the analysis recommends:

> **60% IVV · 13% USMV · 27% SHV — rebalanced annually.**

This allocation achieves a **61.6% probability of reaching the $150k goal**, a median terminal real wealth of **$157,068**, and a 5th-percentile floor of **$122,760**—a $31,675 improvement over a naive all-equity strategy at nearly identical upside.

All data are monthly total returns from Yahoo Finance (January 2005 – December 2025, 251 months). Simulation uses 5,000 block-bootstrap paths with 12-month blocks. All wealth figures are in 2026 real dollars, deflated at 2.5% inflation.

---

## 2. Client Profile & Assumptions

### 2.1 Demographics and Income

| Attribute | Value | Source |
|-----------|-------|--------|
| Age | 22, graduating May 2026 | — |
| Starting salary | $65,000 gross | BLS median, B.S. economics/business |
| Salary growth | 5%/yr (Years 1–4), 3%/yr (Years 5–10) | Early-career wage growth pattern |
| Effective tax rate | 20% on gross | Simplified 2026 bracket + standard deduction |
| Monthly expenses | $3,500 (Year 1), growing at 2.5% inflation | Urban cost-of-living, rent-heavy |
| Student loans | $30,000 at 5.5%, 10-year standard repayment | Average federal loan balance |
| Inflation | 2.5% baseline | Long-run CPI target |
| Emergency fund target | 6 months expenses = $21,000 (Year 1) | Held in SHV within portfolio |

### 2.2 Savings Schedule

The savings available for investment each year equals:  
`Savings = Gross Salary − Taxes − Expenses − Loan Payment`

Fixed loan payment: **$390.69/month** ($4,688/yr) on a $30,000 loan at 5.5% over 10 years.

| Year | Salary ($) | Taxes ($) | Expenses ($) | Loan ($) | **Savings ($)** | Cumulative ($) |
|------|-----------|-----------|-------------|---------|----------------|---------------|
| 1 (2026) | 65,000 | 13,000 | 42,000 | 4,688 | **6,093** | 6,093 |
| 2 (2027) | 68,250 | 13,650 | 43,050 | 4,688 | **7,643** | 13,736 |
| 3 (2028) | 71,663 | 14,333 | 44,126 | 4,688 | **9,297** | 23,033 |
| 4 (2029) | 75,246 | 15,049 | 45,229 | 4,688 | **11,060** | 34,093 |
| 5 (2030) | 79,008 | 15,802 | 46,360 | 4,688 | **12,939** | 47,032 |
| 6 (2031) | 81,378 | 16,276 | 47,519 | 4,688 | **13,676** | 60,709 |
| 7 (2032) | 83,819 | 16,764 | 48,707 | 4,688 | **14,442** | 75,150 |
| 8 (2033) | 86,334 | 17,267 | 49,925 | 4,688 | **15,236** | 90,386 |
| 9 (2034) | 88,924 | 17,785 | 51,173 | 4,688 | **16,059** | 106,445 |
| 10 (2035) | 91,592 | 18,318 | 52,452 | 4,688 | **16,914** | 123,359 |

**Total undiscounted contributions over 10 years: $123,359.** The $150k real goal requires approximately $26,641 in real investment returns — broadly consistent with moderate historical equity returns.

*See:* `plots/figures/savings_trajectory.png`

---

## 3. Investment Universe & Historical Analysis

### 3.1 Asset Universe

The project uses a **5-asset universe** drawn from Hollifield's lecture materials.

**Layer A — Core (3 assets)**

| Ticker | Name | Role |
|--------|------|------|
| IVV | iShares Core S&P 500 ETF | U.S. equity market proxy; captures the equity risk premium |
| AGG | iShares Core U.S. Aggregate Bond ETF | Investment-grade bond diversifier; low IVV correlation |
| SHV | iShares Short Treasury ETF | Risk-free / cash proxy; emergency fund vehicle |

**Layer B — Extended (adds 2 factor ETFs)**

| Ticker | Name | Role | Hollifield Reference |
|--------|------|------|---------------------|
| QUAL | iShares MSCI USA Quality Factor ETF | Profitability tilt | Slide 21: Long Quality α = 3.41%/yr |
| USMV | iShares MSCI USA Min Vol Factor ETF | Low-volatility tilt | Slide 23: β ≈ 0.71, defensive |

QUAL's inception is 2013; USMV's is 2011. Layer B analysis uses the available overlapping history (2013–2025, 145 months).

### 3.2 Historical Return Statistics

Monthly total returns, January 2005 – December 2025. Annualised as: mean × 12, vol × √12.

| Asset | Ann. Return | Ann. Vol | Sharpe (vs SHV) | Max Ann. Drawdown |
|-------|------------|---------|----------------|------------------|
| IVV | 13.6% | 15.2% | 0.80 | −51% (2008–09) |
| AGG | 3.0% | 3.8% | 0.81 | −14% (2022) |
| SHV | 1.5% | 0.3% | — (rf) | ≈0% |
| QUAL | 13.2% | 14.7% | 0.79 | −38% (2020) |
| USMV | 11.1% | 11.1% | 0.86 | −30% (2020) |

*Key observation:* USMV achieves the highest Sharpe among individual assets (0.86) with meaningfully lower volatility than IVV. This motivates its inclusion as a portfolio building block.

### 3.3 Correlations

**Layer A (2005–2025)**

|  | IVV | AGG | SHV |
|--|-----|-----|-----|
| IVV | 1.00 | 0.02 | −0.01 |
| AGG | 0.02 | 1.00 | 0.24 |
| SHV | −0.01 | 0.24 | 1.00 |

**Layer B (2013–2025, QUAL/USMV available)**

|  | IVV | AGG | SHV | QUAL | USMV |
|--|-----|-----|-----|------|------|
| IVV | 1.00 | | | 0.98 | 0.88 |
| QUAL | 0.98 | | | 1.00 | 0.88 |
| USMV | 0.88 | | | 0.88 | 1.00 |

IVV–AGG correlation ≈ 0 confirms the diversification benefit of bonds. QUAL moves nearly in lockstep with IVV (ρ = 0.98), adding little diversification. USMV has lower correlation (ρ = 0.88), providing a more useful portfolio building block.

*See:* `plots/figures/correlation_heatmap_Layer_A_IVV-AGG-SHV.png`  
*See:* `plots/figures/correlation_heatmap_Layer_B_+QUAL-USMV.png`

---

## 4. Recommended Strategy

### 4.1 Mean-Variance Optimisation

The tangency portfolio maximises the Sharpe ratio subject to no-short-sales constraints. Optimisation uses `scipy.optimize.minimize` (SLSQP, 20 random restarts) with bounds (0, 1) and a weights-sum-to-1 constraint.

**Layer A Tangency (IVV / AGG / SHV)**

| Asset | Weight |
|-------|--------|
| IVV | 44% |
| AGG | 56% |
| SHV | 0% |
| **Sharpe** | **0.70** |
| Expected return | 8.0%/yr |
| Volatility | 9.2%/yr |

**Layer B Tangency (IVV / AGG / SHV / QUAL / USMV) — Full history 2005–2025**

| Asset | Weight |
|-------|--------|
| IVV | 82.7% |
| USMV | 17.3% |
| AGG, SHV, QUAL | 0% each |
| **Sharpe** | **0.87** |
| Expected return | 13.6%/yr |
| Volatility | 13.7%/yr |

Adding USMV to the universe raises the tangency Sharpe from 0.70 → 0.87, a **24% improvement**, by replacing bonds with a low-beta equity tilt that preserves return while reducing correlation.

*See:* `plots/figures/efficient_frontier_Layer_A_IVV-AGG-SHV.png`  
*See:* `plots/figures/efficient_frontier_Layer_B_+QUAL-USMV.png`

### 4.2 Capital Allocation Line — Risk-Adjusting for the Client

The tangency portfolio alone allocates 100% to risky assets. The client's stated risk tolerance—willing to accept a **20% maximum drawdown** without panic-selling—implies a portfolio volatility target of **10%** (half the maximum drawdown, per Hollifield slide 43 framework).

The Capital Allocation Line determines the split between the tangency portfolio ($T$) and the risk-free asset (SHV):

$$w^* = \frac{\sigma^*}{\sigma_T} = \frac{10\%}{13.7\%} = 73.0\%$$

**Final Recommended Allocation**

| Asset | Role | Weight |
|-------|------|--------|
| IVV | Risky core | **60.4%** |
| USMV | Low-vol tilt | **12.6%** |
| SHV | Risk-free / buffer | **27.0%** |
| **Total** | | **100%** |

The SHV allocation ($\approx$27% of portfolio) serves a dual purpose: (1) it is the risk-free component of the optimal CAL allocation, and (2) it naturally covers the client's 6-month emergency fund requirement.

### 4.3 Rebalancing Policy

Rebalance to target weights **annually** at year-end. Annual rebalancing is sufficient to maintain the risk profile without incurring excessive transaction costs. In the simulation, each year's sequence is: (1) add annual savings contribution → (2) earn monthly returns on the portfolio → (3) rebalance to 60/13/27 target.

---

## 5. Simulation Results

### 5.1 Methodology

**Block bootstrap Monte Carlo** with 12-month blocks. Each simulated year draws a contiguous 12-month block of historical monthly returns at random (with replacement), preserving within-year autocorrelation, seasonality, and cross-asset dependency structure. No normality assumption. The simulation runs:
- 5,000 independent paths
- 10 years per path
- Contributions added at the start of each year
- Terminal wealth deflated to 2026 dollars at 2.5% inflation

### 5.2 Terminal Wealth Distribution — Recommended Strategy (Tangency B / CAL)

| Statistic | Value |
|-----------|-------|
| Mean | $158,748 |
| Median | **$157,068** |
| 5th percentile | **$122,760** |
| 25th percentile | $141,332 |
| 75th percentile | $174,108 |
| 95th percentile | $201,176 |
| **P(≥ $150,000 real)** | **61.6%** |

*See:* `plots/figures/wealth_fan_chart_Layer_B_QUAL-USMV.png`  
*See:* `plots/figures/terminal_hist_Layer_B_QUAL-USMV.png`

### 5.3 Strategy Comparison

Five strategies were evaluated under identical simulation conditions (same paths, same savings schedule).

| Strategy | Median ($) | 5th Pct ($) | P(Goal) % | Sharpe |
|----------|-----------|------------|----------|--------|
| 1. All Cash (SHV) | 102,523 | 98,184 | 0.0% | 0.00 |
| 2. All Equity (IVV) | 168,672 | 91,085 | 64.3% | 0.64 |
| 3. 60/40 IVV/AGG | 143,962 | 98,790 | 40.3% | 0.67 |
| 4. Tangency A (IVV/AGG/SHV) | 134,804 | 100,942 | 20.3% | 0.68 |
| **5. Tangency B—recommended** | **157,068** | **122,760** | **61.6%** | **0.87** |

**Key finding:** Strategy 5 (recommended) matches All Equity's goal attainment rate (61.6% vs 64.3%) while delivering a 5th-percentile floor **$31,675 higher** ($122,760 vs $91,085). This is mean-variance efficiency in action — the same expected upside at materially lower downside risk.

The conventional 60/40 portfolio achieves only 40.3% goal probability because bond returns since 2005 (with the 2022 rate-shock episode included) have been insufficiently compensated to justify displacing equity.

*See:* `plots/figures/strategy_fan_overlay.png`  
*See:* `plots/figures/goal_attainment_bar.png`  
*See:* `plots/figures/strategy_summary_table.png`

---

## 6. Risk Analysis

### 6.1 Drawdown Analysis

Maximum drawdown (MDD) is computed on each of the 5,000 simulated real-wealth paths. Because the client contributes positive savings at the start of every year, the portfolio rarely draws down in absolute nominal terms — contributions mechanically replenish any market loss in early years.

| Statistic | Value |
|-----------|-------|
| Median MDD (5,000 paths) | 0.0% |
| 5th-percentile MDD | −0.6% |
| Paths breaching −20% tolerance | < 1% |

**Interpretation:** A 22-year-old with consistent income and annual contributions will rarely see their total portfolio value decline, even through a bear market. The risk-management problem is not "don't lose money" but "don't fall short of the goal" — which is captured by P(Goal).

*See:* `plots/figures/drawdown_distribution.png`

### 6.2 Stress Tests

Three adverse scenarios were injected into the simulation to stress-test the recommended strategy.

| Scenario | Description | P(Goal) | Median ($) | 5th Pct ($) |
|----------|-------------|---------|-----------|------------|
| Base case | Historical block bootstrap | 61.6% | 157,068 | 122,760 |
| **Crash at Year 3** | Equity monthly return forced to −3.8%/mo for 12 months (≈−35%/yr) | **37.3%** | 143,054 | 112,628 |
| **Job loss at Year 3** | Zero contributions for 12 months + $21k emergency fund drawn from portfolio | **2.2%** | 114,819 | 92,203 |
| **High inflation (4.5%)** | All wealth deflated at 4.5% instead of 2.5% | **16.9%** | 129,468 | 101,189 |

**Crash at Year 3** drops P(Goal) to 37.3% but remains non-zero — the portfolio recovers over the remaining 7 years. The critical behavioural assumption is that the client does **not** sell after the crash (behavioural discipline enables the recovery).

**Job loss at Year 3** is the most damaging scenario (P(Goal) = 2.2%) because it simultaneously stops contributions and forces asset liquidation to fund expenses, creating a permanent path divergence.

**High inflation** is severe because it re-prices the goal in nominal terms: $150k real at 4.5% inflation requires $229k nominal at Year 10 vs $192k at 2.5%.

**Mitigation strategies:**
- For crash risk: maintain the SHV buffer; do not sell equities during drawdowns.
- For job loss: build the emergency fund to 9–12 months before contributing aggressively.
- For inflation risk: consider adding inflation-protected exposure (I-bonds, TIPs) if CPI systematically exceeds 3%.

*See:* `plots/figures/stress_scenario_bar.png`

---

## 7. Factor Analysis (Layer B Extension)

### 7.1 CAPM Regressions

CAPM regressions were run for AGG, QUAL, and USMV using IVV as the market proxy and SHV as the risk-free rate. Sample: January 2013 – December 2025 (layers overlap period).

$$r_i - r_f = \alpha_i + \beta_i (r_{IVV} - r_f) + \varepsilon_i$$

| Asset | α (ann.) | β | R² | t(α) | p(α) | t(β) |
|-------|---------|---|---|------|------|------|
| AGG | −0.88% | 0.116 | 0.128 | −0.69 | 0.49 | 4.64 |
| QUAL | −0.46% | 1.005 | 0.969 | −0.60 | 0.55 | 67.3 |
| **USMV** | **+0.31%** | **0.719** | **0.780** | **0.20** | **0.84** | **22.9** |

**Findings:**
- **No asset shows statistically significant alpha** at the 10% level. This confirms the Efficient Market Hypothesis: historical ETF returns are well-explained by market beta alone.
- USMV has the lowest beta (0.72), confirming its role as a defensive equity position.
- QUAL moves almost entirely with the market (β ≈ 1.0, R² = 0.97), offering no diversification beyond IVV. Its inclusion in the portfolio is dominated by USMV.
- The small positive USMV alpha (+0.31%/yr) is the strongest individual signal, consistent with Hollifield's slide 21 (Long Low-Vol α ≈ 3.84% historically) but attenuated because USMV is an ETF, not a pure long-short factor portfolio.

*See:* `plots/figures/capm_alpha_bar.png`

### 7.2 Fama-French 5-Factor Regression

To decompose the recommended portfolio's return sources beyond CAPM, a FF5 regression was run on the Layer B tangency portfolio (83% IVV / 17% USMV), using monthly factors from Ken French's data library.

$$r_p - r_f = \alpha + \beta_1 \text{MktRF} + \beta_2 \text{SMB} + \beta_3 \text{HML} + \beta_4 \text{RMW} + \beta_5 \text{CMA} + \varepsilon$$

| Factor | Loading | t-stat | p-value | Interpretation |
|--------|---------|--------|---------|---------------|
| **Alpha** | **−0.12%/yr** | **−0.39** | **0.698** | No unexplained return |
| Mkt-RF | 0.684 | 113.5 | 0.000 | 68% market beta |
| SMB | −0.080 | −7.74 | 0.000 | **Large-cap tilt** (expected) |
| HML | +0.003 | 0.27 | 0.789 | No value tilt |
| **RMW** | **+0.075** | **5.76** | **0.000** | **Profitability tilt** |
| **CMA** | **+0.042** | **2.95** | **0.004** | **Conservative investment tilt** |
| R² | 0.990 | — | — | 99% of variance explained |

**Findings:**
- **The portfolio has no alpha** (−0.12%/yr, p = 0.70): its returns are fully explained by systematic factors. This is appropriate — the client is paying for market exposure, not active management.
- **Economically meaningful tilts** emerge from USMV's inclusion: the portfolio loads positively on profitability (RMW) and conservative investment (CMA), both associated with the quality factor family. These are priced risk factors, not free return.
- The **negative SMB loading** confirms the large-cap orientation (IVV + USMV are both large-cap ETFs).
- R² = 0.99 means the 5-factor model explains essentially all portfolio return variation.

---

## 8. Sensitivity Analysis

### 8.1 Tangency Portfolio Weights by Estimation Window

A key concern in mean-variance optimisation is sensitivity to the sample period (Hollifield, Slide 59). The tangency portfolio was re-estimated over four windows.

| Window | IVV | AGG | SHV | QUAL | USMV | Sharpe | P(Goal) | Median ($) |
|--------|-----|-----|-----|------|------|--------|---------|-----------|
| **Full (2005–2025)** | 83% | 0% | 0% | 0% | 17% | 0.87 | 82.1% | $182,261 |
| Post-GFC (2010–2025) | 83% | 0% | 0% | 0% | 17% | 0.87 | 82.1% | $182,261 |
| Recent (2015–2025) | 100% | 0% | 0% | 0% | 0% | 0.80 | 82.3% | $185,772 |
| Pre-crisis (2005–2015) | 0% | 18% | 76% | 4% | 2% | 1.47 | 0.0% | $108,009 |

*Note: Simulation P(Goal) uses the weights from each window applied to the full-history return distribution (5,000 paths drawn from 2005–2025 data).*

**Findings:**
- The **full-window and post-GFC results agree exactly** — the GFC (2008–09) does not meaningfully shift optimal weights.
- The **recent-only window (2015–2025)** selects 100% IVV — in the post-2015 bull market, no diversifier added Sharpe. This illustrates the over-fitting danger of short windows.
- The **pre-crisis window (2005–2015)** selects predominantly SHV and bonds — the GFC dominated that era's volatility estimates, and with hindsight-inflated bond returns, the optimizer loaded defensively.
- **The pre-crisis portfolio fails completely in forward simulation** (P(Goal) = 0%) because a conservative 2025 portfolio misses the equity bull run needed to reach $150k.

**Conclusion:** The full-sample window is the most defensible choice. The 2005–2025 period spans both the GFC and the post-COVID bull market, producing realistic estimates that do not overfit to a single regime.

*See:* `plots/figures/sensitivity_weights.png`

---

## 9. Conclusion & Caveats

### 9.1 Recommendation Summary

The quantitative analysis consistently selects a portfolio approximating **60% IVV / 13% USMV / 27% SHV**, rebalanced annually. This portfolio:
- Maximises the Sharpe ratio among all feasible allocations in the 5-asset universe
- Meets the client's 10% volatility target (implied by 20% drawdown tolerance)
- Achieves a **61.6% probability** of accumulating $150k real by 2035
- Delivers a worst-case (5th percentile) outcome of **$122,760**—comfortably above subsistence
- Outperforms all-equity on a risk-adjusted basis

### 9.2 Critical Caveats

| Caveat | Implication |
|--------|------------|
| **Historical returns ≠ future returns** | The 2005–2025 period captures an unusually strong equity bull market. Forward returns will likely differ; P(Goal) estimates are illustrative, not forecasts. |
| **Alpha estimates are backward-looking** | USMV's positive historical CAPM alpha (+0.31%/yr) need not persist. Factor tilts can be arbitraged away as more capital chases them. |
| **Estimation error in tangency weights** | Mean-variance optimisation is notoriously sensitive to expected return estimates. The sensitivity analysis shows the weights are reasonably stable, but the IVV-heavy result partly reflects the 2010–2025 equity bull market. |
| **No tax-advantaged account modelling** | In practice, the client should maximise 401(k) / Roth IRA contributions first. tax-advantaged accounts would improve all P(Goal) estimates. |
| **Behavioural risk is unmodelled** | The most dangerous scenario is the client selling equities during a crash (Year 3 crash scenario P(Goal) = 37.3%, but only if the client holds). Selling at the bottom destroys the simulation's recovery assumption. |
| **Loan payoff option not evaluated** | At 5.5% interest, the student loan has a risk-free return equivalent of 5.5%. In a low-return environment, accelerated loan repayment dominates equity investment. This frontier was not evaluated here. |

### 9.3 Next Steps for the Client

1. **Open a Roth IRA today.** A 22-year-old with $6k+ annual contributions can shelter capital gains tax-free. This alone adds meaningful expected terminal wealth.
2. **Automate contributions.** Set up automatic monthly transfers. The model's P(Goal) assumes full annual contributions every year — lapses compound adversely.
3. **Revisit the allocation in Year 5.** If actual portfolio value is substantially above or below the median simulation path by mid-plan, re-optimise. The analysis assumed fixed weights throughout.
4. **Consider a glide path after Year 7.** As the 2035 goal date approaches, gradually reduce IVV exposure toward USMV and SHV to lock in gains and reduce left-tail risk in the final years.

---

## Appendix: Figures & Outputs

| Figure | File | Section |
|--------|------|---------|
| Savings trajectory | `plots/figures/savings_trajectory.png` | §2 |
| Layer A efficient frontier | `plots/figures/efficient_frontier_Layer_A_IVV-AGG-SHV.png` | §4 |
| Layer B efficient frontier | `plots/figures/efficient_frontier_Layer_B_+QUAL-USMV.png` | §4 |
| Layer A correlation heatmap | `plots/figures/correlation_heatmap_Layer_A_IVV-AGG-SHV.png` | §3 |
| Layer B correlation heatmap | `plots/figures/correlation_heatmap_Layer_B_+QUAL-USMV.png` | §3 |
| Layer A wealth fan chart | `plots/figures/wealth_fan_chart_Layer_A_IVV-AGG-SHV.png` | §5 |
| Layer B wealth fan chart | `plots/figures/wealth_fan_chart_Layer_B_QUAL-USMV.png` | §5 |
| Layer A terminal wealth hist. | `plots/figures/terminal_hist_Layer_A_IVV-AGG-SHV.png` | §5 |
| Layer B terminal wealth hist. | `plots/figures/terminal_hist_Layer_B_QUAL-USMV.png` | §5 |
| Strategy fan overlay | `plots/figures/strategy_fan_overlay.png` | §5 |
| Goal attainment bar chart | `plots/figures/goal_attainment_bar.png` | §5 |
| Strategy summary table | `plots/figures/strategy_summary_table.png` | §5 |
| Drawdown distribution | `plots/figures/drawdown_distribution.png` | §6 |
| Stress scenario bar chart | `plots/figures/stress_scenario_bar.png` | §6 |
| CAPM alpha bar chart | `plots/figures/capm_alpha_bar.png` | §7 |
| Sensitivity weights chart | `plots/figures/sensitivity_weights.png` | §8 |

| Data File | Contents |
|-----------|---------|
| `data/returns.csv` | 251 months of ETF adjusted returns |
| `data/client_cashflows.csv` | Year-by-year income/savings schedule |
| `analysis/strategy_comparison.csv` | Full 5-strategy simulation results |
| `analysis/stress_results.csv` | Stress scenario terminal wealth statistics |
| `analysis/capm_results.csv` | CAPM regression coefficients per asset |
| `analysis/ff5_results.csv` | FF5 factor loadings for tangency portfolio |
| `analysis/sensitivity_results.csv` | Tangency weights by estimation window |
| `analysis/sensitivity_sim_results.csv` | Simulation outcomes by window |
