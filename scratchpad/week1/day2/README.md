# Day 2 - Bitcoin Historical Prices

Quick proof-of-concept to test CoinGecko API and combine with Fear & Greed data.

## What This Does

1. **Fetches Bitcoin historical prices** (30 days) from CoinGecko API (free, no key needed)
2. **Fetches Fear & Greed Index** historical data (30 days)
3. **Combines both datasets** by matching dates
4. **Saves to CSV** for later use
5. **Creates visualization** showing Bitcoin price vs Fear & Greed Index

## Running

```bash
# From project root
venv/Scripts/python scratchpad/day2/day2_bitcoin_prices.py
```

## Output Files

- `combined_data.csv` - Combined Bitcoin + Fear & Greed data
- `bitcoin_fear_greed_plot.png` - Visualization

## API Info

**CoinGecko API:**
- Endpoint: `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart`
- Free, no API key required
- Returns: prices, market caps, volumes
- Format: `[[timestamp_ms, price], ...]`

**Fear & Greed API:**
- Endpoint: `https://api.alternative.me/fng/?limit=30`
- Free, no API key required
- Returns: historical values with timestamps

## Next Steps

Production refactor should create:
- `src/data/bitcoin_fetcher.py` - BitcoinPriceFetcher class
- `src/data/fear_greed_fetcher.py` - FearGreedFetcher class
- `src/utils/data_combiner.py` - Reusable data merging
- `src/visualization/plotter.py` - Reusable plotting functions
