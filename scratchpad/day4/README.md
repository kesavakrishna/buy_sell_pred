# Day 4 - Simple Backtest

Simulate trading with $10,000 starting capital based on Fear & Greed signals.

## What This Does

1. **Loads signals** from Day 3
2. **Simulates trades:**
   - BUY: Use 100% of cash to buy BTC
   - SELL: Sell 100% of BTC holdings
   - HOLD: Do nothing
3. **Tracks portfolio** value over time
4. **Calculates metrics:**
   - Total return ($$ and %)
   - Number of trades
   - Win rate
   - Comparison vs buy-and-hold

## Trading Strategy

**All-in Strategy:**
- When BUY signal: Invest 100% of available cash
- When SELL signal: Sell 100% of BTC holdings
- Otherwise: Hold current position

## Running

```bash
# From project root
venv/Scripts/python scratchpad/day4/day4_backtest.py
```

## Results (Oct 4 - Nov 2, 2025)

### Performance Summary

| Metric | Value |
|--------|-------|
| **Starting Capital** | $10,000.00 |
| **Final Value** | $9,995.79 |
| **Total Return** | -$4.21 (-0.04%) |
| **Trades Executed** | 1 BUY, 0 SELL |
| **Win Rate** | N/A (no complete pairs) |

### vs Buy-and-Hold

| Strategy | Return | Final Value |
|----------|--------|-------------|
| **Our Strategy** | -0.04% | $9,995.79 |
| **Buy & Hold** | -9.36% | $9,063.91 |
| **Outperformance** | **+9.32pp** | **+$931.88** |

### Trade Log

Only 1 trade executed:

- **Oct 12, 2025:** BUY 0.090209 BTC at $110,853.12 (F&G: 24)
- Still holding at end of period

### Why Only 1 Trade?

**BUY signals (4 total):**
- Oct 12: ✅ Bought (had cash)
- Oct 17: ❌ No cash (already holding BTC)
- Oct 18: ❌ No cash (already holding BTC)
- Oct 22: ❌ No cash (already holding BTC)

**SELL signals:** None (F&G never reached ≥75)

**Strategy is currently:**
- Holding BTC bought on Oct 12
- Waiting for F&G to hit 75+ to sell
- Portfolio value changes with BTC price

## Key Findings

### 1. Strategy Beat Buy-and-Hold
Despite losing money, we lost LESS than buy-and-hold:
- **Timing advantage:** Waited until Oct 12 (after price dropped)
- **Buy-and-hold:** Would have bought on Oct 4 at peak ($122,250)

### 2. No Sell Signals is a Problem
- Never got exit signal (F&G peaked at 74)
- Strategy is "stuck" in position
- Need lower sell threshold or time-based exit

### 3. All-in Strategy Misses Opportunities
Once we buy, we can't buy more even when:
- Oct 17: F&G=22, Price=$108,076 (better than Oct 12!)
- Oct 18: F&G=23, Price=$106,443 (even better!)

**Better approach:** Scale into positions (buy 25% at a time)

## Output Files

- `backtest_results.csv` - Portfolio value history
- `backtest_results.png` - Visualization with trade markers

## Visualization

The plot shows:

**Top chart:** Bitcoin price with trade markers
- Blue line: BTC price
- Green triangle ▲: BUY executed
- Red triangle ▼: SELL executed (none in this period)

**Bottom chart:** Portfolio value over time
- Purple line: Portfolio value
- Gray dashed line: Starting capital ($10,000)
- Green area: Profit zone
- Red area: Loss zone

## Code Structure

### `SimpleBacktester` Class

**Attributes:**
- `cash` - Available USD
- `btc_holdings` - Amount of BTC owned
- `portfolio_value` - Total value (cash + BTC)
- `trades` - List of executed trades
- `portfolio_history` - Daily portfolio snapshots

**Methods:**
- `execute_trade()` - Process BUY/SELL/HOLD signal
- `run_backtest()` - Loop through all days
- `calculate_metrics()` - Compute performance stats
- `print_trade_log()` - Show all trades
- `print_summary()` - Display results

### Functions

- `plot_backtest_results()` - Create 2-panel visualization
- `save_results_to_csv()` - Export portfolio history
- `main()` - Orchestrate backtest execution

## Limitations

1. **All-in strategy** - Can't scale into positions
2. **No stop-loss** - Could lose more in bear market
3. **No sell signals** - Stuck holding if market doesn't reach 75
4. **No transaction fees** - Real trading has costs
5. **Single period** - Need more data to validate

## Improvements for Future

1. **Position sizing:**
   - Buy 25% on each signal
   - Allows 4 entries maximum

2. **Better exit rules:**
   - Lower sell threshold (65-70)
   - Time-based exit (30 days max hold)
   - Trailing stop-loss (10% below peak)

3. **Risk management:**
   - Max position size limits
   - Drawdown limits
   - Diversification

4. **More metrics:**
   - Sharpe ratio
   - Maximum drawdown
   - Average trade duration
   - Profit factor

## Next Steps

Day 5 will:
- Analyze what worked and what didn't
- Test different threshold values
- Compare multiple strategies
- Conclude if Fear & Greed is predictive