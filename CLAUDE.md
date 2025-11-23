# CLAUDE.md - AI Assistant Guide for buy_sell_pred

This file provides context and conventions for AI assistants working with this cryptocurrency trading signal repository.

---

## Quick Reference

```bash
# Run main trading analysis (requires API keys)
python test.py

# Run HuggingFace model query utility
python hf1.py

# Install dependencies
pip install -r requirements.txt
```

---

## Project Overview

**Repository:** buy_sell_pred (Crypto Trading Signal Tracker)

**Purpose:** Generate cryptocurrency buy/sell signals using a combination of:
- Technical analysis indicators (RSI, MACD, Bollinger Bands, etc.)
- Sentiment analysis (News via FinBERT, Fear & Greed Index)
- LLM-based decision making (LLaMA-2, Flan-T5)

**Primary Asset:** Bitcoin (BTC/USD)

**Core Philosophy:** Contrarian trading based on sentiment extremes
> "Be fearful when others are greedy, and greedy when others are fearful." - Warren Buffett

---

## Branch Structure

### Main Branch (Current)
The original implementation with LLM integration:
- `test.py` - Main trading analysis script (268 lines)
- `hf1.py` - HuggingFace inference utility (56 lines)
- Monolithic approach, runs end-to-end analysis

### `new_changes` Branch
Enhanced modular implementation with day-by-day learning structure:
- `scratchpad/week1/day1-6/` - Progressive feature implementations
- `scratchpad/week2/day8-9/` - Advanced features (whale tracking)
- Includes backtesting engine and strategy optimization

---

## Codebase Structure

### Current Directory Layout
```
buy_sell_pred/
├── .gitignore           # Git ignore rules
├── CLAUDE.md            # This file - AI assistant guide
├── DOCUMENTATION.md     # Detailed repository documentation
├── hf1.py               # HuggingFace model query utility
├── readme.md            # Basic project readme
├── requirements.txt     # Python dependencies (69 packages)
└── test.py              # Main trading analysis script
```

### Key Files Explained

#### `test.py` - Main Trading Script
**Structure (5 sections):**
1. **Data Aggregation** (lines 26-46): Fetches OHLCV from Coinbase via ccxt
2. **Technical Analysis** (lines 50-99): Computes 12+ indicators using `ta` library
3. **News Sentiment** (lines 106-191): GNews → Article extraction → FinBERT
4. **LLM Decision** (lines 193-257): LangChain + LLaMA-2 recommendation
5. **Output** (lines 262-268): Final trading advice

**Data Flow:**
```
Coinbase API → OHLCV Data → Technical Indicators ─┐
                                                   ├→ LLM Prompt → Trading Advice
GNews → Article URLs → Full Text → Summary → FinBERT ─┘
```

#### `hf1.py` - Model Query Utility
Simple wrapper for HuggingFace Inference API:
```python
def query_model(prompt, model_name="google/flan-t5-base", api_token=None) -> str
```
Parameters: `max_new_tokens=250`, `temperature=0.7`, `top_k=50`, `top_p=0.95`

---

## Technical Indicators Reference

| Indicator | Code Location | Purpose |
|-----------|---------------|---------|
| RSI (14) | `test.py:55` | Overbought/oversold detection |
| EMA (20) | `test.py:56` | Trend direction |
| MACD | `test.py:57-58` | Momentum |
| SMA (20) | `test.py:59` | Support/resistance |
| Bollinger Bands | `test.py:61-64` | Volatility bands |
| ATR (14) | `test.py:66` | Volatility measure |
| ADX (14) | `test.py:67` | Trend strength |
| Stochastic %K/%D | `test.py:69-71` | Momentum oscillator |
| OBV | `test.py:73` | Volume confirmation |
| Fibonacci | `test.py:75-82` | Retracement levels |

---

## Environment Variables Required

Create a `.env` file with:
```bash
# Required for test.py
HUGGINGFACE_API_TOKEN=hf_your_token_here
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret

# Optional (for new_changes branch whale tracking)
WHALE_ALERT_API_KEY=your_whale_alert_key
```

---

## Dependencies Overview

### Core Libraries
| Package | Version | Purpose |
|---------|---------|---------|
| pandas | 2.2.3 | Data manipulation |
| numpy | 2.2.2 | Numerical operations |
| ccxt | 4.4.52 | Exchange API wrapper |
| ta | 0.11.0 | Technical analysis |

### AI/ML Libraries
| Package | Purpose |
|---------|---------|
| transformers | 4.48.2 | Hugging Face transformers |
| huggingface-hub | 0.28.1 | Model access |
| langchain | LLM orchestration |

### News & Sentiment
| Package | Purpose |
|---------|---------|
| gnews | 0.4.0 | Google News fetcher |
| newspaper3k | 0.2.8 | Article extraction |

---

## Coding Conventions

### Style Guidelines
- **Python version:** 3.10+
- **Line length:** 100 characters max
- **Imports:** Group by stdlib, third-party, local
- **Naming:** snake_case for functions/variables, PascalCase for classes

### Documentation Requirements
```python
def fetch_historical_data(symbol: str = 'BTC/USD', timeframe: str = '1d', limit: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV data from exchange.

    Args:
        symbol: Trading pair (e.g., 'BTC/USD')
        timeframe: Candle timeframe ('1d', '1h', etc.)
        limit: Number of candles to fetch

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
```

### Error Handling Pattern
```python
try:
    result = api_call()
except SpecificException as e:
    logging.error(f"Descriptive message: {e}")
    return fallback_value
```

### Logging Convention
```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Operation completed")
logging.error("Error occurred: %s", error)
```

---

## Common Tasks for AI Assistants

### Adding a New Technical Indicator
1. Import from `ta` library in `test.py`
2. Add calculation after line 73
3. Add to `indicators` dict (line 85-99)
4. Update `prompt_template` (line 198-215) to include in LLM input
5. Add to `chain_inputs` dict (line 235-254)

### Modifying the LLM Prompt
- Location: `test.py:198-215` (prompt_template)
- Variables available: All items in `indicators` dict + `news_sentiment` + `target_duration`

### Adding a New Data Source
1. Create fetch function similar to `fetch_historical_data()`
2. Add API credentials to `.env`
3. Load with `os.getenv()` and `load_dotenv()`
4. Integrate data into the analysis pipeline

### Changing the Trading Model
- Summarization model: `test.py:144-148` (repo_id parameter)
- Decision model: `test.py:228-231` (repo_id parameter)
- Query utility model: `hf1.py:51` (model_name parameter)

---

## API Rate Limits

| API | Rate Limit | Notes |
|-----|------------|-------|
| Coinbase | Varies by endpoint | Use ccxt built-in rate limiting |
| HuggingFace Hub | 30 requests/hour (free) | Add `time.sleep(2)` between calls |
| GNews | 100 requests/day | Already limited to 5 articles |
| CoinGecko | 10-30 calls/min | Free tier, no key needed |
| WhaleAlert | 10 calls/min | Free tier requires key |

---

## Testing & Validation

### Manual Testing
```bash
# Test HuggingFace connection
python hf1.py

# Run full analysis (requires all API keys)
python test.py
```

### Expected Outputs
- `test.py`: Logs technical indicators, news sentiment, LLM recommendation
- `hf1.py`: Prints model response to BTC investment query

---

## Git Workflow

### Commit Message Format
```
type: short description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- refactor: Code restructuring
- test: Adding tests
```

### Files to Never Commit
- `.env` (API keys)
- `venv/` (virtual environment)
- `__pycache__/` (Python cache)
- `*.csv` (generated data files)
- `*.png` (generated charts)

---

## Common Issues & Solutions

### Issue: HuggingFace API Token Error
```
ValueError: Please set the HUGGINGFACE_API_TOKEN environment variable.
```
**Solution:** Create `.env` file with valid `HUGGINGFACE_API_TOKEN`

### Issue: Coinbase API Connection Failed
```
ccxt.AuthenticationError
```
**Solution:** Verify `COINBASE_API_KEY` and `COINBASE_API_SECRET` in `.env`

### Issue: News Extraction Failed
```
Error extracting article: ...
```
**Solution:** Some URLs block scraping. The code falls back to first 1000 chars.

### Issue: LangChain Deprecation Warnings
```
LangChainDeprecationWarning
```
**Solution:** Update imports to use `langchain_community` package (future task)

---

## Performance Considerations

### Memory Usage
- FinBERT model loads ~500MB into memory
- Consider using smaller models for testing

### API Costs
- HuggingFace free tier: Limited requests
- Coinbase: Free for market data
- Consider caching API responses during development

### Rate Limiting
- `time.sleep(2)` added between news sentiment calls
- Add delays when making multiple API requests

---

## Future Development Notes

### Planned Improvements (from new_changes branch)
1. Modular architecture with separate classes
2. Backtesting engine with position sizing
3. Strategy optimization framework
4. Whale movement tracking integration
5. Web dashboard for visualization

### Code Quality Goals
- Maximum 300 lines per file
- >80% test coverage on business logic
- Type hints on all function signatures
- Comprehensive docstrings

---

## Quick Command Reference

```bash
# Environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Run analysis
python test.py

# Check git status
git status
git log --oneline -5

# Update dependencies
pip freeze > requirements.txt
```

---

## Contact & Resources

- **Fear & Greed API:** https://api.alternative.me/fng/
- **CoinGecko API:** https://www.coingecko.com/en/api
- **HuggingFace Hub:** https://huggingface.co/
- **ccxt Documentation:** https://docs.ccxt.com/
- **ta Library:** https://technical-analysis-library-in-python.readthedocs.io/

---

*Last updated: November 2025*
