# Investment Analysis Final Project

This repository contains the scaffolding for the investment analysis project described in `project_design.md`.

## Project structure

- `data/`
  - `client_profile.py`: deterministic income, expense, tax, loan, and savings schedule model
  - `pull_returns.py`: download ETF historical returns from Yahoo Finance
- `models/`
  - `portfolio_stats.py`: return and risk statistics
  - `efficient_frontier.py`: mean-variance optimization and tangency portfolio
  - `simulation.py`: Monte Carlo simulation and block bootstrap engine
- `analysis/`
  - `compare_strategies.py`: compare multiple portfolio strategies
- `.vscode/`
  - VS Code settings, recommended extensions, and tasks
- `requirements.txt`: Python dependency list

## Getting started

1. Open this folder in VS Code.
2. Install recommended extensions if prompted: Python, Pylance, Jupyter.
3. Create a Python virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Run a starter script:

```powershell
python -m data.pull_returns
python -m data.client_profile
python -m models.portfolio_stats
```

## Notes

- Most modules are currently scaffolds with placeholder logic. Use them to implement the phases defined in `project_design.md`.
- The file `project_design.md` is the design document for the full analytics plan.
- Add your own notebooks or scripts if you want interactive exploration.
