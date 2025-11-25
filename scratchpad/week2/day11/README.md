# Day 11: Add Google Trends + RSI

## Objectives
- Set up Google Trends tracking with daily resolution
- Add RSI (Relative Strength Index) technical indicator
- Test both indicators independently
- Analyze lag correlations to identify leading/lagging behavior

## Implementation

### 1. RSI (Relative Strength Index)
**Type:** Technical Indicator (Price-Based)
**Period:** 14 days
**No API needed** - Pure mathematical calculation on price data

**Formula:**
```
RSI = 100 - (100 / (1 + RS))
where RS = Average Gain / Average Loss over 14 days
```

**Signal Logic:**
- **RSI < 30:** OVERSOLD → BUY signal
- **RSI > 70:** OVERBOUGHT → SELL signal
- **30 ≤ RSI ≤ 70:** NEUTRAL → HOLD

**Position Sizing:**
- RSI < 25: 50% (STRONG oversold)
- RSI < 30: 25% (MODERATE oversold)
- RSI > 75: 50% (STRONG overbought)
- RSI > 70: 25% (MODERATE overbought)

### 2. Google Trends
**Type:** Retail Sentiment Indicator
**Keyword:** "bitcoin"
**Data:** 90 days of daily search interest (0-100 scale)

**Signal Logic (Contrarian):**
- **High search interest (ratio > 1.5):** FOMO_WARNING → SELL
  - Retail FOMO usually marks tops
  - When everyone is searching, it's often too late

- **Low search interest (ratio < 0.5):** UNDERVALUED → BUY
  - Lack of attention often marks bottoms
  - When nobody cares, it's often the best time to buy

**Position Sizing:**
- Ratio > 2.0: 50% SELL (STRONG FOMO)
- Ratio > 1.5: 25% SELL (MODERATE FOMO)
- Ratio < 0.3: 50% BUY (STRONG undervalued)
- Ratio < 0.5: 25% BUY (MODERATE undervalued)

## Key Findings

### 1. Backtest Results

**Test Period:** 31 days (October-November 2025)
**Starting Capital:** $10,000
**Buy & Hold Baseline:** -9.36%

#### RSI-Only Strategy: ✅ WINNER
- **Final Value:** $10,228.11
- **Total Return:** +2.28%
- **vs Buy & Hold:** +11.64pp
- **Number of Trades:** 6
- **Result:** BEST SINGLE INDICATOR SO FAR!

**Trade Analysis:**
- All 6 trades were BUYS (no sells - market was trending down)
- RSI correctly identified multiple oversold bounces
- Executed Oct 17-23 during correction (RSI 26-30)
- No SELL signals (RSI never hit 70+ in downtrend)

#### Google Trends Strategy:
- **Final Value:** $10,000.00
- **Total Return:** +0.00%
- **vs Buy & Hold:** +9.36pp (by not losing money!)
- **Number of Trades:** 0
- **Result:** No signals generated (no extreme FOMO or undervaluation)

**Why No Trades?**
- Trends ratio stayed in 0.5-1.5 range (neutral zone)
- No retail FOMO spikes (ratio > 1.5)
- No extreme low interest (ratio < 0.5)
- Shows trends are stable during this period

### 2. Lag Correlation Analysis

#### RSI:
- **Best correlation: 0.593 at lag 0 days**
- **Type:** COINCIDENT indicator
- **Interpretation:** RSI moves WITH price (same day)
  - Not surprising - RSI is calculated from price
  - It's a momentum indicator, not predictive
  - Useful for entry timing, not forecasting

#### Google Trends:
- **Best correlation: -0.343 at lag -4 days**
- **Type:** LAGGING indicator (4 days behind)
- **Interpretation:** Search interest FOLLOWS price changes
  - People search AFTER price moves (not before)
  - **Negative correlation:** High searches after price drops (fear)
  - Confirms retail is reactive, not predictive
  - **Contrarian approach validated:** Do opposite of retail sentiment

### 3. All Indicators Ranked (by Return)

|Rank|Indicator|Return|vs B&H|Trades|Type|Lag|
|---|---|---|---|---|---|---|
|1|**RSI**|**+2.28%**|**+11.64pp**|6|Coincident|0 days|
|2|Fear & Greed|+1.08%|+10.44pp|11|Coincident|0 days|
|3|Whale|+0.02%|+9.38pp|21|Leading|+7 days|
|4|Google Trends|+0.00%|+9.36pp|0|Lagging|-4 days|

**All beat buy & hold (-9.36%)!**

## Critical Insights

### 1. RSI is the NEW CHAMPION!
- **+2.28% return** beats all previous indicators
- Only 6 trades (very selective)
- Clean oversold signals during correction
- No false SELL signals in downtrend

### 2. Coincident Indicators Outperforming
- **RSI (lag 0):** +2.28%
- **Fear & Greed (lag 0):** +1.08%
- **Whale (lag +7):** +0.02%
- **Lesson:** Leading ≠ Better! Timing matters more than prediction

### 3. Why Leading Indicators Underperformed
**Whale (7-day lead):**
- Too noisy, 21 trades
- Predicts direction but timing is off
- Need filtering for stronger signals

**Google Trends (4-day lag):**
- Too stable, no extreme signals
- Retail wasn't panicking or FOMOing
- Better in volatile markets with sentiment extremes

### 4. Retail Sentiment Behavior
- **Negative correlation (-0.343):** Retail searches AFTER bad news
- **4-day lag:** Takes days for retail to react
- **Contrarian edge:** Retail sentiment is a lagging indicator
- **Implication:** Fade the crowd when extremes occur

### 5. Signal Quality > Predictive Power
- Whale has 7-day predictive lead → 21 trades → +0.02%
- RSI has 0-day lead (coincident) → 6 trades → +2.28%
- **Key:** Clean, high-quality signals beat noisy predictions

## Technical Details

### RSI Calculation
- **Valid values:** 18/31 days (first 13 days needed for warmup)
- **Period:** 14 days
- **Range:** 0-100
- **Oversold threshold:** 30 (with 25 for strong signals)
- **Overbought threshold:** 70 (with 75 for strong signals)

### Google Trends Data
- **Days fetched:** 91 days of real Google Trends data
- **Resolution:** Daily (achieved by 6-day chunks)
- **Keyword:** "bitcoin"
- **Range:** 0-100 (relative search interest)
- **Baseline:** 30-day moving average

## Deliverables

### Data:
- [trends_data_90days.csv](trends_data_90days.csv) - 91 days of Google Trends
- [combined_with_rsi_trends.csv](combined_with_rsi_trends.csv) - Full dataset with all 4 indicators

### Charts:
- [rsi_lag_correlation.png](rsi_lag_correlation.png) - RSI lag analysis (peak at 0)
- [trends_lag_correlation.png](trends_lag_correlation.png) - Trends lag analysis (peak at -4)

### Results:
- [indicators_comparison.csv](indicators_comparison.csv) - RSI vs Trends comparison

## Recommendations for Day 12

### 1. Use RSI as Primary Signal
- RSI has best performance (+2.28%)
- Use RSI oversold (< 30) as primary entry trigger
- Add Fear & Greed confirmation for stronger setups

### 2. Combine Leading + Coincident Indicators
**Strategy Framework:**
- **Step 1:** Whale accumulation (7-day leading signal)
- **Step 2:** Wait for RSI oversold (< 30) confirmation
- **Step 3:** Check Fear & Greed also shows fear (< 25)
- **Step 4:** Execute trade with high confidence

### 3. Use Google Trends as Veto Filter
- Don't buy during extreme FOMO (ratio > 2.0)
- Don't sell during extreme fear (ratio < 0.3)
- Use as confirmation, not primary signal

### 4. Multi-Indicator Voting Strategies
**Strategy A: Simple Voting (need 3/4)**
- Each indicator votes BUY/SELL/NEUTRAL
- Execute when 3+ agree

**Strategy B: Weighted Voting**
- RSI: 2 votes (best performer)
- Fear & Greed: 2 votes (proven track record)
- Whale: 1 vote (noisy but predictive)
- Trends: 1 vote (for extreme veto)
- Need 4/6 votes for signal

**Strategy C: Confidence Scoring**
- Each indicator scores 0-2 based on strength
- Combine scores for signal confidence
- Use confidence for position sizing

## Next Steps

**Day 12:** Multi-Indicator Signal Combination
- Implement 4 combination strategies
- Test simple voting (3/4 agree)
- Test unanimous (4/4 agree)
- Test weighted voting (RSI + F&G get more weight)
- Test confidence scoring with signal strength

**Goal:** Build the ultimate multi-indicator system that combines:
- **Best performer:** RSI (coincident, +2.28%)
- **Proven indicator:** Fear & Greed (coincident, +1.08%)
- **Leading signal:** Whale movements (7-day lead)
- **Sentiment filter:** Google Trends (contrarian veto)

## Code Location

**Script:** [day11_trends_rsi.py](day11_trends_rsi.py)

**Key Functions:**
- `calculate_rsi()` - Calculate 14-day RSI from prices
- `rsi_signal()` - Generate OVERSOLD/OVERBOUGHT signals
- `get_daily_trends()` - Fetch Google Trends with daily resolution
- `trends_signal()` - Generate FOMO/UNDERVALUED signals (contrarian)
- `backtest_rsi_only()` - Test RSI-only strategy
- `backtest_trends_only()` - Test Trends-only strategy
- `analyze_lag_correlation()` - Find leading/lagging behavior

---

**Status:** ✅ Complete
**Duration:** ~2.5 hours
**Next:** Day 12 - Multi-Indicator Signal Combination

## Summary Stats

**Indicators Tested:** 4 total
- Fear & Greed Index (Week 1)
- Whale Movements (Day 9)
- RSI (Day 11) ← NEW CHAMPION
- Google Trends (Day 11)

**Best Single Indicator:** RSI (+2.28%, 6 trades)
**All Beat Buy & Hold:** -9.36% baseline

**Ready for combination strategies!**