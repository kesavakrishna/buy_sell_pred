# 🚀 Crypto Trading Signal Tracker

A Python-based cryptocurrency trading signal tracker that uses the **Fear & Greed Index** as a contrarian indicator to identify potential buy and sell opportunities in Bitcoin.

**Project Type:** Learning Project | Algorithmic Trading | Sentiment Analysis

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Status](#project-status)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Key Findings](#key-findings)
- [Development](#development)
- [Contributing](#contributing)
- [Resources](#resources)
- [License](#license)

---

## 🎯 Overview

This project explores whether the **Crypto Fear & Greed Index** can be used as a reliable trading signal for Bitcoin. By combining sentiment data with historical price information, we aim to:

1. Identify optimal entry points (extreme fear)
2. Identify optimal exit points (extreme greed)
3. Backtest the strategy against historical data
4. Determine if sentiment-based trading outperforms buy-and-hold

### The Hypothesis

**"Be fearful when others are greedy, and greedy when others are fearful."** - Warren Buffett

We test whether this contrarian principle works in crypto markets by:
- **Buying when Fear & Greed Index < 25** (Extreme Fear)
- **Selling when Fear & Greed Index > 75** (Extreme Greed)

---

## ✨ Features

### Current (Days 1-2) ✅
- ✅ Fetch real-time Fear & Greed Index data
- ✅ Retrieve Bitcoin historical prices from CoinGecko
- ✅ Combine sentiment and price data by date
- ✅ Visualize correlation with dual y-axis charts
- ✅ Identify potential trading signals
- ✅ Export data to CSV for analysis

### Coming Soon (Days 3-5) 🚧
- 🚧 Generate buy/sell signals automatically
- 🚧 Backtest strategy with historical data
- 🚧 Calculate performance metrics (ROI, Sharpe ratio, drawdown)
- 🚧 Optimize threshold parameters
- 🚧 Compare against buy-and-hold strategy
- 🚧 Risk management implementation

---

## 📊 Project Status

**Current Progress:** Day 2 of 5 Complete

| Day | Task | Status | Completion Date |
|-----|------|--------|----------------|
| Day 1 | Environment Setup & Fear & Greed API | ✅ Complete | Nov 2, 2025 |
| Day 2 | Bitcoin Historical Data & Visualization | ✅ Complete | Nov 2, 2025 |
| Day 3 | Trading Signal Generation | 🚧 Pending | - |
| Day 4 | Backtesting Engine | 🚧 Pending | - |
| Day 5 | Analysis & Documentation | 🚧 Pending | - |

For detailed achievements, see [claude.md](claude.md).

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- pip (Python package manager)
- Git (for cloning)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trade
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Analysis

#### Day 1: Fetch Fear & Greed Index
```bash
python scratchpad/day1/day1_fear_greed.py
```

**Output:**
- Console: Current Fear & Greed value
- File: `fear_greed_data.csv`

#### Day 2: Fetch Bitcoin Prices & Combine Data
```bash
python scratchpad/day2/day2_bitcoin_prices.py
```

**Output:**
- Console: Combined data preview
- File: `combined_data.csv`
- File: `bitcoin_fear_greed_plot.png`

---

## 📁 Project Structure

```
trade/
├── venv/                          # Virtual environment (not in git)
├── scratchpad/                    # Learning implementations
│   ├── day1/                      # Day 1: Fear & Greed fetching
│   │   ├── day1_fear_greed.py     # Simple F&G fetcher
│   │   ├── fear_greed_data.csv    # Output data
│   │   └── README.md              # Day 1 notes
│   └── day2/                      # Day 2: Bitcoin data
│       ├── day2_bitcoin_prices.py # Bitcoin + F&G combiner
│       ├── combined_data.csv      # Combined dataset
│       ├── bitcoin_fear_greed_plot.png  # Visualization
│       └── README.md              # Day 2 notes
├── src/                           # Production code (coming soon)
│   ├── data/                      # Data fetching modules
│   ├── analysis/                  # Signal generation
│   ├── backtest/                  # Backtesting engine
│   └── utils/                     # Shared utilities
├── tests/                         # Unit tests (coming soon)
├── config/                        # Configuration files (coming soon)
├── .env                           # API keys (not in git)
├── .env.example                   # Template for environment variables
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── claude.md                      # Project context for AI assistant
├── FINDINGS.md                    # Research findings & insights
├── PROMPTING_GUIDE.md             # How to prompt for good code
└── plan.md                        # 5-day project roadmap
```

---

## 💻 Usage

### Viewing Results

After running Day 2 script, you can:

1. **View the CSV data**
   ```bash
   # On Windows
   start scratchpad/day2/combined_data.csv

   # On Mac
   open scratchpad/day2/combined_data.csv

   # On Linux
   xdg-open scratchpad/day2/combined_data.csv
   ```

2. **View the visualization**
   ```bash
   # On Windows
   start scratchpad/day2/bitcoin_fear_greed_plot.png

   # On Mac
   open scratchpad/day2/bitcoin_fear_greed_plot.png

   # On Linux
   xdg-open scratchpad/day2/bitcoin_fear_greed_plot.png
   ```

3. **Analyze in Python**
   ```python
   import pandas as pd

   # Load the data
   df = pd.read_csv('scratchpad/day2/combined_data.csv')

   # Show summary statistics
   print(df.describe())

   # Find all buy signals (F&G < 25)
   buy_signals = df[df['fear_greed_value'] < 25]
   print(buy_signals)
   ```

---

## 🔍 Key Findings

Based on 30 days of October 2025 data:

### Performance Highlights

| Metric | Value |
|--------|-------|
| **Data Period** | Oct 4 - Nov 2, 2025 (31 days) |
| **Bitcoin Range** | $106,443 - $124,773 (16.9% swing) |
| **F&G Range** | 22 (Extreme Fear) - 74 (Greed) |
| **Buy Signals Found** | 5 instances |
| **Sell Signals Found** | 0 instances |
| **Strategy Return** | +2.15% |
| **Buy & Hold Return** | -9.36% |
| **Outperformance** | +11.51 percentage points ✅ |

### Key Insights

1. **Sentiment is a Leading Indicator**
   - Fear & Greed dropped 52 points while Bitcoin only dropped 15%
   - Sentiment changes precede price movements

2. **Buy Signals Were Profitable**
   - Avg return per signal: +2.18%
   - Best entry (Oct 18): +4.10% in 15 days
   - Strategy outperformed buy-and-hold significantly

3. **Sell Threshold May Be Too High**
   - No sell signals occurred despite price being near peak
   - F&G reached 74 (just below 75 threshold) at price peak
   - May need to lower sell threshold to 70 or 65

4. **Extreme Fear Clusters**
   - F&G stayed below 30 for 14 consecutive days
   - Provides multiple accumulation opportunities
   - Don't need to time exact bottom

For detailed analysis, see [FINDINGS.md](FINDINGS.md).

---

## 🛠 Development

### Code Quality Standards

This project follows strict coding standards documented in [claude.md](claude.md):

- **File Size:** Maximum 300 lines per file
- **Modularity:** Single responsibility principle
- **Documentation:** Type hints and docstrings required
- **Testing:** >80% coverage goal
- **Style:** Follow PEP 8 conventions

### Development Workflow

1. **Experiment in scratchpad/**
   - Quick prototypes and learning
   - Test APIs and concepts
   - Throwaway code

2. **Refactor to src/**
   - Production-quality code
   - Modular classes and functions
   - Comprehensive testing

3. **Document findings**
   - Update [FINDINGS.md](FINDINGS.md) with insights
   - Update [claude.md](claude.md) with progress

### Adding Dependencies

```bash
# Install new package
pip install package_name

# Update requirements
pip freeze > requirements.txt
```

### Running Tests (Coming Soon)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/
```

---

## 🤝 Contributing

This is a learning project, but contributions are welcome!

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Follow coding standards in [claude.md](claude.md)
4. Add tests for new functionality
5. Commit changes (`git commit -m 'Add AmazingFeature'`)
6. Push to branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

### Contribution Ideas

- [ ] Add more technical indicators (RSI, MACD, etc.)
- [ ] Implement machine learning predictions
- [ ] Add support for other cryptocurrencies
- [ ] Create web dashboard for visualization
- [ ] Add real-time monitoring and alerts
- [ ] Implement paper trading mode
- [ ] Add more sophisticated risk management

---

## 📚 Resources

### APIs Used

- **Fear & Greed Index:** https://api.alternative.me/fng/
  - Free, no API key required
  - Historical data available
  - Updated daily

- **CoinGecko:** https://www.coingecko.com/en/api
  - Free tier: 10-30 calls/minute
  - No API key required for basic usage
  - Comprehensive cryptocurrency data

### Learning Resources

- [Algorithmic Trading Basics](https://www.investopedia.com/articles/active-trading/101014/basics-algorithmic-trading-concepts-and-examples.asp)
- [Fear & Greed Index Explained](https://alternative.me/crypto/fear-and-greed-index/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Tutorials](https://matplotlib.org/stable/tutorials/index.html)

### Related Projects

- [Backtrader](https://www.backtrader.com/) - Python backtesting framework
- [TA-Lib](https://github.com/mrjbq7/ta-lib) - Technical analysis library
- [ccxt](https://github.com/ccxt/ccxt) - Cryptocurrency exchange trading API

---

## 📖 Documentation

- **[claude.md](claude.md)** - Project context and coding standards
- **[FINDINGS.md](FINDINGS.md)** - Detailed research findings and insights
- **[PROMPTING_GUIDE.md](PROMPTING_GUIDE.md)** - How to prompt AI for good code
- **[plan.md](plan.md)** - 5-day implementation roadmap

---

## ⚠️ Disclaimer

**This project is for educational purposes only.**

- This is **NOT financial advice**
- Past performance does not guarantee future results
- Cryptocurrency trading involves significant risk
- Only trade with money you can afford to lose
- Do your own research before making any investment decisions
- The authors are not responsible for any financial losses

**Trading Risks:**
- High volatility
- Market manipulation
- Regulatory changes
- Technical failures
- Emotional decision-making

---

## 📊 Data Sources

All data is sourced from public APIs:

- **Bitcoin Prices:** CoinGecko (historical daily prices)
- **Fear & Greed Index:** Alternative.me (crypto market sentiment)

Data is retrieved via API calls and stored locally for analysis. No proprietary data is included.

---

## 🔐 Privacy & Security

- `.env` file (containing API keys) is gitignored
- No sensitive data is committed to the repository
- Use `.env.example` as a template for your own keys
- Keep API keys secure and never share them publicly

---

## 🎓 Learning Objectives

By completing this project, you will learn:

1. **Data Engineering**
   - Fetching data from RESTful APIs
   - Data cleaning and preprocessing
   - Time-series data alignment

2. **Financial Analysis**
   - Sentiment indicators
   - Trading signal generation
   - Backtesting methodologies
   - Performance metrics (ROI, Sharpe ratio, drawdown)

3. **Python Development**
   - Pandas for data manipulation
   - Matplotlib for visualization
   - Object-oriented programming
   - Testing and debugging

4. **Algorithmic Trading**
   - Strategy development
   - Risk management
   - Position sizing
   - Performance optimization

---

## 🎯 Next Steps

### Immediate (Today)
- [ ] Review [FINDINGS.md](FINDINGS.md) for insights
- [ ] Examine `combined_data.csv` and the visualization
- [ ] Identify patterns in the data

### Short-term (This Week)
- [ ] Complete Day 3: Signal generation
- [ ] Complete Day 4: Backtesting
- [ ] Complete Day 5: Final analysis

### Medium-term (Next Week)
- [ ] Refactor scratchpad code into modular `src/` structure
- [ ] Add comprehensive unit tests
- [ ] Optimize strategy parameters
- [ ] Test on longer time periods

### Long-term (Future)
- [ ] Implement real-time monitoring
- [ ] Add support for multiple cryptocurrencies
- [ ] Create interactive dashboard
- [ ] Explore machine learning enhancements

---

## 💬 Questions or Issues?

If you have questions about this project:

1. Check [claude.md](claude.md) for project context
2. Review [FINDINGS.md](FINDINGS.md) for analysis insights
3. See [PROMPTING_GUIDE.md](PROMPTING_GUIDE.md) for development patterns
4. Open an issue on GitHub

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- **Alternative.me** for the Fear & Greed Index API
- **CoinGecko** for cryptocurrency market data
- **Python community** for excellent data science libraries
- **Warren Buffett** for the contrarian wisdom

---

## 📈 Project Stats

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Started:** November 2, 2025
**Current Phase:** Day 2 Complete
**Next Milestone:** Day 3 Signal Generation

---

*"The stock market is a device for transferring money from the impatient to the patient."* - Warren Buffett

**Let's see if crypto markets follow the same pattern!** 🚀