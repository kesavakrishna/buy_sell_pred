# Crypto Trading Signal Tracker - Project Context

## Project Overview
A 5-day learning project to build a crypto trading signal tracker using the Fear & Greed Index and Bitcoin price data. This project emphasizes learning algorithmic trading concepts through hands-on implementation.

## Current Status
- **Day 1**: ✅ Complete - Environment setup, Fear & Greed Index data fetching
- **Day 2**: ✅ Complete - Bitcoin historical prices, data combination, visualization
- **Day 3**: Pending - Signal generation
- **Day 4**: Pending - Backtesting
- **Day 5**: Pending - Analysis and documentation

### Day 2 Achievements
- Successfully fetched 31 days of Bitcoin historical prices from CoinGecko API
- Retrieved 30 days of Fear & Greed Index historical data
- Combined both datasets by date (31 matching rows)
- Created dual y-axis visualization showing price vs sentiment correlation
- Identified several potential buy signals (F&G < 25) during Oct 2025 price dip
- Output: `scratchpad/day2/combined_data.csv` and visualization plot

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
│   └── day2/                  # Day 2: Bitcoin prices + data combination
├── src/                       # Production-quality modular code
│   ├── data/                  # Data fetching modules
│   ├── analysis/              # Signal generation and analysis
│   ├── backtest/              # Backtesting engine
│   └── utils/                 # Shared utilities
├── tests/                     # Unit tests
├── config/                    # Configuration files
├── .env                       # API keys and secrets (not committed)
├── requirements.txt           # Python dependencies
├── claude.md                  # This file - project context
├── FINDINGS.md                # Key observations and insights
├── PROMPTING_GUIDE.md         # How to prompt for good code
└── plan.md                    # 5-day project roadmap
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
