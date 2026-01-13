# Crypto Trading Signal Tracker - Project Context

## Project Overview
A 6-day learning project (originally planned as 5 days, extended with Day 6 enhancement) to build a crypto trading signal tracker using the Fear & Greed Index and Bitcoin price data. This project emphasizes learning algorithmic trading concepts through hands-on implementation.

## Current Status
- **Day 1**: ✅ Complete - Environment setup, Fear & Greed Index data fetching
- **Day 2**: ✅ Complete - Bitcoin historical prices, data combination, visualization
- **Day 3**: ✅ Complete - Signal generation with threshold-based rules
- **Day 4**: ✅ Complete - Backtesting with $10,000 starting capital
- **Day 5**: ✅ Complete - Threshold optimization (9 combinations tested)
- **Day 6**: ✅ Complete - Enhanced strategy with position sizing
- **Day 7**: 📝 Noted for future - Daily tracking script (deferred until project matures)

### Project Achievements Summary

**Day 1-2: Data Pipeline**
- Successfully fetched 31 days of Bitcoin historical prices from CoinGecko API
- Retrieved 30 days of Fear & Greed Index historical data
- Combined both datasets by date (31 matching rows)
- Created dual y-axis visualization showing price vs sentiment correlation
- Output: `scratchpad/day2/combined_data.csv` and visualization plot

**Day 3: Signal Generation**
- Implemented threshold-based trading rules (Buy F&G ≤ 25, Sell F&G ≥ 75)
- Fixed critical bug: Changed `<` to `<=` for inclusive thresholds
- Found 4 BUY signals in October 2025 corrective period
- Generated signals_data.csv with signal strength indicators
- Hypothetical performance: +2.18% avg return on fear signals

**Day 4: Backtesting**
- Built SimpleBacktester class with all-in position sizing
- Simulated trading with $10,000 starting capital
- Result: -0.04% return BUT beat buy-and-hold by +9.32pp
- Buy-and-hold lost -9.36% in same period
- Key finding: Only 1 BUY executed (Oct 12), no SELL signals (F&G never reached 75)

**Day 5: Threshold Optimization**
- Tested 9 threshold combinations (buy: 20/25/30, sell: 65/70/75)
- ALL 9 strategies beat buy-and-hold (+7.24pp to +9.36pp)
- Best active strategy: Buy ≤ 25, Sell ≥ 75 (-0.04%, +9.32pp vs B&H)
- Identified limitations: All-in approach missed 3 better entry opportunities
- Estimated opportunity cost: +2.2% if used position sizing

**Day 6: Enhanced Strategy**
- Implemented ScaledBacktester with 7-tier F&G signal system
- Tiered position sizing: STRONG_BUY (50%), BUY (25%), WEAK_BUY (10%)
- Result: +0.11% return (only positive return across all strategies!)
- Enhanced beat original by +0.15pp, executed 21 trades vs 1
- VALIDATED: Position sizing improves performance
- Captured all 4 major buy signals (Oct 12, 17, 18, 22)

## Tech Stack
- Python 3.13
- pandas (data manipulation)
- requests (API calls)
- matplotlib (visualization)

## Project Structure
```
trade/
├── venv/                      # Virtual environment
├── scratchpad/                # Experimental/learning implementations
│   ├── day1/                  # Day 1: Fear & Greed Index fetching
│   ├── day2/                  # Day 2: Bitcoin prices + data combination
│   ├── day3/                  # Day 3: Signal generation with thresholds
│   ├── day4/                  # Day 4: Backtesting with SimpleBacktester
│   ├── day5/                  # Day 5: Threshold optimization (9 combos)
│   └── day6/                  # Day 6: Enhanced strategy with position sizing
├── src/                       # Production-quality modular code (future)
│   ├── data/                  # Data fetching modules
│   ├── analysis/              # Signal generation and analysis
│   ├── backtest/              # Backtesting engine
│   └── utils/                 # Shared utilities
├── tests/                     # Unit tests (future)
├── config/                    # Configuration files (future)
├── .env                       # API keys and secrets (not committed)
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore patterns
├── claude.md                  # This file - project context
├── FINDINGS.md                # Comprehensive research findings (813 lines!)
├── PROMPTING_GUIDE.md         # How to prompt for good code
├── README.md                  # Project overview and results
└── plan.md                    # Original 7-day project roadmap
```

## Coding Standards & Best Practices

### 1. **File Organization**
- **Maximum 300 lines per file** - If a file grows beyond this, refactor into smaller modules
- **Single Responsibility Principle** - Each module/class should have one clear purpose
- **Meaningful names** - Use descriptive names like `fetch_fear_greed_data()` not `get_data()`

### 2. **Code Modularity**
- **Reusable functions** - Extract common logic into utility functions
- **Configuration over hardcoding** - Use config files for API URLs, constants, defaults
- **Dependency injection** - Pass dependencies as parameters rather than hardcoding

### 3. **OOP Principles**
- **Classes for entities** - Use classes for: DataFetcher, TradingSignal, Backtester, etc.
- **Inheritance for specialization** - Base classes for common behavior
- **Composition over inheritance** - Favor has-a over is-a relationships
- **Encapsulation** - Keep internal state private, expose public interfaces

### 4. **Documentation**
- **Docstrings** - Every function/class must have a docstring explaining:
  - What it does
  - Parameters and their types
  - Return value and type
  - Example usage (for complex functions)
- **Type hints** - Use Python type hints for all function parameters and returns
- **Comments** - Explain WHY, not WHAT (code should be self-explanatory)

### 5. **Error Handling**
- **Explicit exceptions** - Catch specific exceptions, not bare `except:`
- **Fail gracefully** - Log errors and provide meaningful messages
- **Validate inputs** - Check parameters at function boundaries

### 6. **Testing**
- **Unit tests** - Test individual functions in isolation
- **Test edge cases** - Empty data, invalid inputs, network failures
- **Test coverage** - Aim for >80% coverage on business logic

## Example Code Structure

### Bad (monolithic):
```python
# day1.py - 500 lines, does everything
def main():
    # fetch data
    # process data
    # save data
    # plot data
```

### Good (modular):
```python
# src/data/fear_greed_fetcher.py
class FearGreedFetcher:
    """Fetches Fear & Greed Index data from API."""

    def fetch(self) -> dict:
        """Fetch current Fear & Greed data."""
        pass

# src/data/bitcoin_fetcher.py
class BitcoinPriceFetcher:
    """Fetches Bitcoin price data."""
    pass

# src/utils/csv_storage.py
class CSVStorage:
    """Handles CSV file operations."""
    pass

# main.py
from src.data.fear_greed_fetcher import FearGreedFetcher
from src.utils.csv_storage import CSVStorage

def main():
    fetcher = FearGreedFetcher()
    storage = CSVStorage('data/')
    data = fetcher.fetch()
    storage.save(data)
```

## API Keys & Configuration
- Store sensitive data in `.env` file (already gitignored)
- Use `python-dotenv` to load environment variables
- Create `config/api_config.py` for API endpoints and constants

## Data Flow
1. **Fetch** → Get data from external APIs
2. **Transform** → Clean and process data
3. **Store** → Save to CSV/database
4. **Analyze** → Generate trading signals
5. **Backtest** → Simulate trades
6. **Visualize** → Create charts and reports

## How to Prompt Claude for Good Code

### ✅ DO prompt like this:
- "Create a modular FearGreedFetcher class following SOLID principles"
- "Refactor this into smaller functions, each doing one thing"
- "Add type hints and docstrings to all functions"
- "This file is getting large, split it into separate modules"
- "Extract this logic into a reusable utility function"

### ❌ DON'T prompt like this:
- "Write all the code in one file"
- "Make it work quickly" (without mentioning quality)
- "Just hack it together"

## Scratchpad vs src/

### **scratchpad/** - Use for:
- Quick experiments and proof-of-concepts
- Learning new APIs or libraries
- Throwaway code
- Day-by-day learning implementations
- Code that doesn't need to be maintained

### **src/** - Use for:
- Production-quality code
- Code that will be reused
- Code that needs testing
- Code that will be maintained long-term
- Final implementations after learning

### **Workflow**:
1. **Experiment** in `scratchpad/day1/` → Learn how the API works
2. **Refactor** into `src/data/` → Create clean, modular version
3. **Test** in `tests/` → Ensure it works correctly
4. **Use** in main application

## Dependencies
See `requirements.txt` for current dependencies. When adding new packages:
1. Install in venv: `venv/Scripts/pip install package_name`
2. Update requirements: `venv/Scripts/pip freeze > requirements.txt`

## Git Workflow
- Commit after completing each day's work
- Use meaningful commit messages: "feat: add Fear & Greed data fetcher"
- Don't commit `.env`, `venv/`, `__pycache__/`, or CSV data files

## Resources
- Fear & Greed API: https://api.alternative.me/fng/
- CoinGecko API: https://www.coingecko.com/en/api
- Project Plan: See `plan.md` for 5-day roadmap
