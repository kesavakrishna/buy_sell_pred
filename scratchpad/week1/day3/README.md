# Day 3 - Trading Signal Generation

Generate buy/sell trading signals based on Fear & Greed Index thresholds.

## What This Does

1. **Loads combined data** from Day 2 (Bitcoin prices + F&G Index)
2. **Applies trading rules:**
   - BUY when F&G ≤ 25 (Extreme Fear)
   - SELL when F&G ≥ 75 (Extreme Greed)
   - HOLD otherwise
3. **Calculates signal strength:** How far from threshold (stronger = better)
4. **Marks signals on visualization** with colored triangles
5. **Analyzes hypothetical performance:** What if we bought on each signal?

## Trading Rules

```
Buy Threshold:  F&G ≤ 25 (Extreme Fear)
Sell Threshold: F&G ≥ 75 (Extreme Greed)
Hold:           25 < F&G < 75
```

## Running

```bash
# From project root
venv/Scripts/python scratchpad/day3/day3_trading_signals.py
```

## Results (Oct 4 - Nov 2, 2025)

### Signal Distribution
- **HOLD:** 27 days (87.1%)
- **BUY:** 4 days (12.9%)
- **SELL:** 0 days (0%)

### Buy Signals Found

| Date | Bitcoin Price | F&G | Signal Strength | Current Return |
|------|--------------|-----|----------------|---------------|
| Oct 12 | $110,853 | 24 | 1.0 | -0.04% |
| Oct 17 | $108,076 | 22 | 3.0 | +2.53% |
| Oct 18 | $106,443 | 23 | 2.0 | +4.10% ⭐ |
| Oct 22 | $108,486 | 25 | 0.0 | +2.14% |

**Signal Strength:** How much below/above threshold
- Strength 3.0 = F&G is 3 points below 25 (very strong)
- Strength 0.0 = F&G is exactly at threshold (borderline)

### Hypothetical Performance

**Scenario:** Buy $1,000 on each signal, hold until Nov 2

- **Total Invested:** $4,000
- **Current Value:** $4,087.21
- **Profit:** +$87.21 (+2.18%)
- **Avg per trade:** +0.55%

### No Sell Signals

F&G never reached ≥ 75 during this period. Highest was 74 on Oct 5.

## Output Files

- `signals_data.csv` - Combined data with BUY/SELL/HOLD signals
- `signals_plot.png` - Visualization with signal markers

## Visualization

The plot shows:
- **Blue line:** Bitcoin price (left axis)
- **Gray line:** Fear & Greed Index (right axis)
- **Green dashed line:** Buy threshold (25)
- **Red dashed line:** Sell threshold (75)
- **Green triangles ▲:** BUY signals
- **Red triangles ▼:** SELL signals (none in this period)

## Key Findings

1. **4 buy opportunities** in October 2025
2. **Best entry:** Oct 18 at $106,443 (F&G: 23) → +4.10% gain
3. **No sell signals:** Market didn't reach extreme greed
4. **Strategy profitable:** +2.18% vs holding random entry
5. **Extreme fear clustered:** Oct 17-18 and Oct 22

## Code Structure

- `load_data()` - Load Day 2 combined CSV
- `generate_signals()` - Apply F&G threshold rules
- `analyze_signals()` - Count and summarize signals
- `generate_trading_summary()` - Calculate hypothetical P&L
- `plot_signals()` - Create visualization with markers
- `save_signals_to_csv()` - Export with signal columns

## Next Steps

Day 4 will backtest this strategy:
- Test different threshold combinations (20/25/30 buy, 65/70/75 sell)
- Implement position sizing strategies
- Add risk management (stop-loss, take-profit)
- Calculate metrics (Sharpe ratio, max drawdown)
- Compare vs buy-and-hold