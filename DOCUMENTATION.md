# Comprehensive Repository Documentation

This document provides detailed documentation of the **buy_sell_pred** (Crypto Trading Signal Tracker) repository, covering both the main branch and the enhanced `new_changes` branch.

---

## Table of Contents

1. [Repository Overview](#1-repository-overview)
2. [Branch Structure](#2-branch-structure)
3. [Main Branch - Original Implementation](#3-main-branch---original-implementation)
4. [new_changes Branch - Enhanced Implementation](#4-new_changes-branch---enhanced-implementation)
5. [File-by-File Documentation](#5-file-by-file-documentation)
6. [Key Concepts & Trading Logic](#6-key-concepts--trading-logic)
7. [API Integrations](#7-api-integrations)
8. [Setup & Installation](#8-setup--installation)
9. [Dependencies](#9-dependencies)
10. [Project Evolution](#10-project-evolution)

---

## 1. Repository Overview

**Purpose:** This repository implements a cryptocurrency trading signal system that combines:
- **Sentiment Analysis** (Fear & Greed Index)
- **Technical Indicators** (RSI, MACD, Bollinger Bands, etc.)
- **AI/LLM Integration** (FinBERT, LLaMA, Hugging Face models)
- **Whale Movement Tracking** (Large transaction monitoring)

**Primary Use Case:** Generate buy/sell signals for Bitcoin trading based on contrarian sentiment analysis ("Buy when others are fearful, sell when others are greedy").

---

## 2. Branch Structure

### Main Branch (Original)
- Basic crypto trading script using LangChain and technical analysis
- Uses Coinbase API for price data
- Integrates FinBERT for news sentiment analysis
- LLaMA-2 for trading recommendations

### `new_changes` Branch (Enhanced)
- Complete refactored 6-day learning project
- Day-by-day structured implementation
- Fear & Greed Index contrarian strategy
- Backtesting engine with position sizing
- Whale movement tracking (Week 2)

---

## 3. Main Branch - Original Implementation

### 3.1 `test.py` - Main Trading Analysis Script

**Purpose:** Comprehensive crypto trading signal generator combining technical analysis, news sentiment, and LLM-based decision making.

#### Structure:

```
test.py (268 lines)
├── Data Aggregation (Lines 26-46)
│   └── fetch_historical_data() - Fetches OHLCV data from Coinbase
├── Technical Analysis (Lines 50-99)
│   └── Computes 12+ indicators using 'ta' library
├── News Sentiment Analysis (Lines 106-191)
│   └── GNews + Article extraction + FinBERT sentiment
├── LLM Decision Making (Lines 193-257)
│   └── LangChain + LLaMA-2 for trading recommendations
└── Trading Advice Generation (Lines 262-268)
    └── generate_trading_advice() - Final output
```

#### Components Explained:

**1. Data Aggregation (fetch_historical_data)**
```python
def fetch_historical_data(symbol='BTC/USD', timeframe='1d', limit=100):
```
- **Input:** Trading pair, timeframe, number of candles
- **Output:** DataFrame with OHLCV (Open, High, Low, Close, Volume)
- **API:** Coinbase via ccxt library

**2. Technical Indicators Computed:**

| Indicator | Description | Trading Signal |
|-----------|-------------|----------------|
| RSI (14) | Relative Strength Index | <30 oversold, >70 overbought |
| EMA (20) | Exponential Moving Average | Trend direction |
| MACD | Moving Average Convergence Divergence | Momentum |
| SMA (20) | Simple Moving Average | Support/resistance |
| Bollinger Bands | Volatility bands | Breakout signals |
| ATR (14) | Average True Range | Volatility measure |
| ADX (14) | Average Directional Index | Trend strength |
| Stochastic %K/%D | Momentum oscillator | Overbought/oversold |
| OBV | On-Balance Volume | Volume-price confirmation |
| Fibonacci Levels | Retracement levels | Support/resistance zones |

**3. News Sentiment Pipeline:**
```
GNews API → Article URLs → newspaper3k extraction →
LLaMA-2 Summarization → FinBERT Sentiment Analysis →
Aggregated Score (-1 to +1)
```

**4. LLM Decision Chain:**
- Uses `meta-llama/Llama-2-7B-Chat-hf` via HuggingFace Hub
- Prompt includes all technical indicators + sentiment score
- Outputs: Target price, Stop loss, Probability percentage

### 3.2 `hf1.py` - Hugging Face Inference Utility

**Purpose:** Simple utility for querying Hugging Face models.

```python
def query_model(prompt, model_name="google/flan-t5-base", api_token=None):
```

**Parameters:**
- `prompt`: Text input for the model
- `model_name`: HF model identifier (default: flan-t5-base)
- `api_token`: HuggingFace API token

**Configuration:**
- `max_new_tokens`: 250
- `temperature`: 0.7
- `top_k`: 50
- `top_p`: 0.95

---

## 4. new_changes Branch - Enhanced Implementation

### 4.1 Project Structure

```
buy_sell_pred/
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore rules
├── README.md              # Project overview & results
├── FINDINGS.md            # Research findings (813 lines)
├── WEEK2_PLAN.md          # Week 2 roadmap
├── claude.md              # Coding standards & context
├── requirements.txt       # Python dependencies
│
└── scratchpad/
    ├── week1/
    │   ├── day1/          # Fear & Greed API
    │   ├── day2/          # Bitcoin prices + visualization
    │   ├── day3/          # Signal generation
    │   ├── day4/          # Backtesting engine
    │   ├── day5/          # Threshold optimization
    │   └── day6/          # Enhanced position sizing
    │
    └── week2/
        ├── day8/          # Week 1 analysis
        └── day9/          # Whale tracking
```

### 4.2 Day-by-Day Implementation

---

#### **Day 1: Fear & Greed Index Fetching**

**File:** `scratchpad/week1/day1/day1_fear_greed.py`

**Purpose:** Fetch the Crypto Fear & Greed Index from Alternative.me API

**Key Function:**
```python
def fetch_fear_greed_index():
    """Fetch Fear & Greed Index from https://api.alternative.me/fng/"""
```

**Output:**
- Current Fear & Greed value (0-100)
- Classification (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
- Saved to `fear_greed_data.csv`

**Index Interpretation:**
| Value | Classification |
|-------|---------------|
| 0-24 | Extreme Fear |
| 25-49 | Fear |
| 50-50 | Neutral |
| 51-74 | Greed |
| 75-100 | Extreme Greed |

---

#### **Day 2: Bitcoin Prices & Data Combination**

**File:** `scratchpad/week1/day2/day2_bitcoin_prices.py`

**Purpose:** Fetch Bitcoin historical prices from CoinGecko and combine with Fear & Greed data

**Key Features:**
- Fetches 30+ days of Bitcoin price history
- Merges with Fear & Greed data by date
- Creates dual y-axis visualization (price vs. sentiment)

**Output:**
- `combined_data.csv` - Merged dataset
- `bitcoin_fear_greed_plot.png` - Visualization

---

#### **Day 3: Trading Signal Generation**

**File:** `scratchpad/week1/day3/day3_trading_signals.py`

**Purpose:** Generate buy/sell signals based on Fear & Greed thresholds

**Trading Rules:**
```python
BUY_THRESHOLD = 25   # Buy when F&G <= 25 (Extreme Fear)
SELL_THRESHOLD = 75  # Sell when F&G >= 75 (Extreme Greed)
```

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `load_data()` | Load combined data from Day 2 |
| `generate_signals()` | Apply threshold rules to generate BUY/SELL/HOLD |
| `analyze_signals()` | Count and summarize signal distribution |
| `plot_signals()` | Visualize signals on price chart |
| `generate_trading_summary()` | Calculate hypothetical returns |

**Signal Strength Calculation:**
- For BUY: `strength = buy_threshold - fear_greed_value`
- For SELL: `strength = fear_greed_value - sell_threshold`
- Higher strength = stronger conviction

**Output:**
- `signals_data.csv` - Data with signal columns
- `signals_plot.png` - Price chart with signal markers

---

#### **Day 4: Backtesting Engine**

**File:** `scratchpad/week1/day4/day4_backtest.py`

**Purpose:** Simulate trading with $10,000 starting capital

**Key Class: `SimpleBacktester`**

```python
class SimpleBacktester:
    """All-in strategy: 100% capital per trade"""

    def __init__(self, starting_capital=10000):
        self.cash = starting_capital
        self.btc_holdings = 0
        self.trades = []
        self.portfolio_history = []
```

**Methods:**

| Method | Purpose |
|--------|---------|
| `execute_trade()` | Execute BUY/SELL based on signal |
| `run_backtest()` | Process all dates in dataset |
| `calculate_metrics()` | Compute ROI, win rate, etc. |
| `print_trade_log()` | Display executed trades |
| `print_summary()` | Show final results + comparison |

**Metrics Calculated:**
- Total Return ($ and %)
- Number of trades (buys/sells)
- Win rate (% of profitable trades)
- Buy-and-hold comparison

**Output:**
- `backtest_results.csv` - Portfolio history
- `backtest_results.png` - Performance visualization

---

#### **Day 5: Threshold Optimization**

**File:** `scratchpad/week1/day5/day5_analysis.py`

**Purpose:** Test multiple threshold combinations to find optimal parameters

**Combinations Tested:**
```
Buy thresholds: [20, 25, 30]
Sell thresholds: [65, 70, 75]
Total: 9 combinations (3 x 3)
```

**Key Finding:** All 9 strategies outperformed buy-and-hold by +7.24pp to +9.36pp

**Output:**
- `final_analysis.txt` - Detailed results
- `strategy_comparison.png` - Visual comparison

---

#### **Day 6: Enhanced Strategy with Position Sizing**

**File:** `scratchpad/week1/day6/day6_enhanced_strategy.py`

**Purpose:** Implement tiered position sizing based on F&G strength

**Key Class: `ScaledBacktester`**

**Tiered Signal System:**
```
F&G Value → Signal → Position Size
0-20     → STRONG_BUY  → 50% of cash
21-25    → BUY         → 25% of cash
26-40    → WEAK_BUY    → 10% of cash
41-59    → HOLD        → 0%
60-69    → WEAK_SELL   → 25% of BTC
70-74    → SELL        → 50% of BTC
75+      → STRONG_SELL → 100% of BTC
```

**Key Method:**
```python
def get_signal_tier(self, fg_value):
    """Return (signal_name, position_size)"""
```

**Results:**
- Enhanced strategy: +0.11% return (only positive!)
- Original strategy: -0.04% return
- Buy-and-hold: -9.36% return
- **Enhanced beat buy-and-hold by +9.47pp**

---

#### **Day 8: Week 1 Analysis**

**File:** `scratchpad/week2/day8/day8_week1_analysis.py`

**Purpose:** Comprehensive analysis of Week 1 results

**Output:**
- `day8_week1_analysis.md` - Detailed markdown report
- `day8_analysis_charts.png` - Analysis visualizations

---

#### **Day 9: Whale Movement Tracking**

**File:** `scratchpad/week2/day9/day9_whale_tracker.py`

**Purpose:** Track large Bitcoin transactions to/from exchanges

**Key Class: `WhaleTracker`**

**Whale Logic:**
```
Transfers TO exchanges   → Bearish (whales selling)
Transfers FROM exchanges → Bullish (accumulation)
Net Flow = from_exchange - to_exchange
Positive = ACCUMULATION (bullish)
Negative = DISTRIBUTION (bearish)
```

**Signal Thresholds:**
```
Net Flow > $10M  → STRONG ACCUMULATION
Net Flow > $5M   → MODERATE ACCUMULATION
Net Flow < -$5M  → MODERATE DISTRIBUTION
Net Flow < -$10M → STRONG DISTRIBUTION
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `get_transactions()` | Fetch from WhaleAlert API |
| `calculate_whale_signal()` | Analyze flow direction |
| `fetch_historical_whale_data()` | Get 30 days of data |
| `backtest_whale_only()` | Test whale-only strategy |

**Output:**
- `whale_data_30days.csv` - Raw whale data
- `combined_with_whale.csv` - Merged with price data

---

## 5. File-by-File Documentation

### Configuration Files

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables (API keys) |
| `.gitignore` | Git ignore patterns (venv, .env, __pycache__, etc.) |
| `requirements.txt` | Python package dependencies |

### Documentation Files (new_changes branch)

| File | Purpose |
|------|---------|
| `README.md` | Project overview, features, quick start guide |
| `FINDINGS.md` | Detailed research findings and insights (813 lines) |
| `WEEK2_PLAN.md` | Week 2 roadmap and tasks |
| `claude.md` | Coding standards and AI prompting guide |

---

## 6. Key Concepts & Trading Logic

### 6.1 Fear & Greed Index Strategy

**The Hypothesis:**
> "Be fearful when others are greedy, and greedy when others are fearful." - Warren Buffett

**Implementation:**
1. Fetch daily Fear & Greed Index value
2. When F&G shows "Extreme Fear" (< 25) → BUY signal
3. When F&G shows "Extreme Greed" (> 75) → SELL signal
4. This is a **contrarian** strategy

### 6.2 Position Sizing Strategies

**All-in Strategy (Day 4):**
- Buy: Use 100% of available cash
- Sell: Sell 100% of BTC holdings
- Simple but misses accumulation opportunities

**Scaled Strategy (Day 6):**
- Buy/Sell based on signal strength
- Stronger fear = larger buy position
- Allows dollar-cost averaging during fear periods

### 6.3 Backtesting Methodology

**Process:**
1. Load historical data (prices + signals)
2. Iterate through each day chronologically
3. Execute trades based on signals
4. Track portfolio value over time
5. Calculate final metrics vs. buy-and-hold

**Metrics:**
- Total Return (%)
- Win Rate (% of profitable trades)
- Outperformance vs. Buy-and-Hold (percentage points)
- Number of trades executed

---

## 7. API Integrations

### 7.1 Fear & Greed Index API (Free)

**Endpoint:** `https://api.alternative.me/fng/`

**Features:**
- No API key required
- Historical data available
- Updated daily

### 7.2 CoinGecko API (Free)

**Purpose:** Bitcoin historical prices

**Rate Limits:**
- Free tier: 10-30 calls/minute
- No API key required for basic usage

### 7.3 WhaleAlert API (Freemium)

**Purpose:** Large cryptocurrency transactions

**Endpoint:** `https://api.whale-alert.io/v1`

**Rate Limits:**
- Free tier: 10 calls/minute

### 7.4 Coinbase API (Main Branch)

**Purpose:** OHLCV price data via ccxt

**Requirements:**
- API key and secret required
- Set via `COINBASE_API_KEY` and `COINBASE_API_SECRET`

### 7.5 Hugging Face Hub (Main Branch)

**Models Used:**
- `meta-llama/Llama-2-7B-Chat-hf` - Summarization and decision making
- `yiyanghkust/finbert-tone` - Financial sentiment analysis
- `google/flan-t5-base` - General text generation

---

## 8. Setup & Installation

### Prerequisites
- Python 3.10+
- pip (Python package manager)
- Git

### Installation Steps

```bash
# Clone repository
git clone <repository-url>
cd buy_sell_pred

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required for main branch
HUGGINGFACE_API_TOKEN=hf_your_token_here
COINBASE_API_KEY=your_coinbase_key
COINBASE_API_SECRET=your_coinbase_secret

# Optional for whale tracking (new_changes branch)
WHALE_ALERT_API_KEY=your_whale_alert_key
```

---

## 9. Dependencies

### Core Libraries

| Package | Version | Purpose |
|---------|---------|---------|
| pandas | 2.2.3 | Data manipulation |
| numpy | 2.2.2 | Numerical operations |
| matplotlib | 3.10.0 | Visualization |
| requests | 2.32.3 | HTTP requests |

### Trading & Analysis (Main Branch)

| Package | Purpose |
|---------|---------|
| ccxt | 4.4.52 | Crypto exchange API wrapper |
| ta | 0.11.0 | Technical analysis indicators |
| gnews | 0.4.0 | Google News fetcher |
| newspaper3k | 0.2.8 | Article content extraction |

### AI/ML (Main Branch)

| Package | Purpose |
|---------|---------|
| transformers | 4.48.2 | Hugging Face transformers |
| huggingface-hub | 0.28.1 | HF model access |
| langchain | - | LLM orchestration |

---

## 10. Project Evolution

### Phase 1: Original Implementation (Main Branch)
- Monolithic script approach
- Technical analysis + LLM integration
- News sentiment via FinBERT

### Phase 2: Refactored Learning Project (new_changes Branch)
- Day-by-day structured implementation
- Modular design with separate files
- Focus on Fear & Greed contrarian strategy
- Comprehensive backtesting

### Key Improvements in new_changes:
1. **Better Code Organization** - Separate files per day/feature
2. **Simpler Data Sources** - Free APIs (no exchange keys needed)
3. **Backtesting Framework** - Proper simulation with metrics
4. **Position Sizing** - Graduated entry based on signal strength
5. **Whale Tracking** - Additional sentiment indicator

### Future Enhancements (Planned)
- Risk management (stop-loss, take-profit)
- Real-time monitoring and alerts
- Multi-asset support (ETH, BNB, SOL)
- Machine learning predictions
- Web dashboard for visualization

---

## Quick Reference

### Run Fear & Greed Fetcher (new_changes)
```bash
python scratchpad/week1/day1/day1_fear_greed.py
```

### Run Full Backtest (new_changes)
```bash
python scratchpad/week1/day6/day6_enhanced_strategy.py
```

### Run Original Analysis (main)
```bash
python test.py
```

---

## Disclaimer

**This project is for educational purposes only.**
- Not financial advice
- Past performance does not guarantee future results
- Cryptocurrency trading involves significant risk
- Do your own research before investing

---

*Documentation last updated: November 2025*
