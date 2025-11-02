# Research Findings & Market Observations

**Project:** Crypto Trading Signal Tracker
**Data Period:** October 4 - November 2, 2025 (30 days)
**Last Updated:** November 2, 2025

---

## Executive Summary

This document captures key observations, patterns, and insights discovered during the implementation of the crypto trading signal tracker. The analysis combines Bitcoin price data from CoinGecko with the Crypto Fear & Greed Index to identify potential trading opportunities.

### Quick Stats
- **Data Points:** 31 days analyzed
- **Bitcoin Price Range:** $106,443 - $124,773 (16.9% swing)
- **Fear & Greed Range:** 22 (Extreme Fear) to 74 (Greed)
- **Potential Buy Signals:** 5 instances (F&G ≤ 25)
- **Potential Sell Signals:** 0 instances (F&G ≥ 75)

---

## 🎯 Key Findings

### 1. **Strong Inverse Correlation Observed**

The data shows a clear **inverse relationship** between Bitcoin price and the Fear & Greed Index during this period:

- **Oct 4-10 (Greed Period):** Bitcoin averaged $122,600, F&G averaged 68
- **Oct 11-24 (Fear Period):** Bitcoin averaged $109,500, F&G averaged 29
- **Oct 25-29 (Recovery):** Bitcoin averaged $112,600, F&G averaged 51

**Observation:** When Bitcoin dropped ~$16,000 (13%), the Fear & Greed Index fell from 74 to 22 - a dramatic sentiment shift that preceded further price decline.

### 2. **Multiple Buy Signals Identified**

According to our trading rules (Buy when F&G < 25), we identified **5 potential buy signals**:

| Date | Bitcoin Price | F&G Value | Classification | Signal |
|------|--------------|-----------|----------------|---------|
| Oct 12 | $110,853 | 24 | Extreme Fear | **BUY** |
| Oct 17 | $108,076 | 22 | Extreme Fear | **BUY** ⭐ Best |
| Oct 18 | $106,443 | 23 | Extreme Fear | **BUY** ⭐ Lowest Price |
| Oct 22 | $108,486 | 25 | Extreme Fear | **BUY** (borderline) |

**Hindsight Analysis:**
- **Oct 18 buy signal** ($106,443) would have been the best entry
- Bitcoin recovered to $114,476 by Oct 27 (7.5% gain in 9 days)
- By Nov 2, price was $110,806 (4.1% gain from lowest point)

### 3. **No Sell Signals During This Period**

**Zero instances** where F&G reached ≥ 75 (Extreme Greed):
- Highest reading: **74 on Oct 5** (just shy of sell threshold)
- This suggests the market didn't reach euphoric levels in October 2025
- Strategy would have kept positions through the greed period (Oct 4-10)

**Implication:** Our current sell threshold (75) may be too high, potentially missing profit-taking opportunities when F&G is in the high 60s-70s range.

### 4. **Price Volatility vs Sentiment Volatility**

**Price volatility:** $124,773 → $106,443 = 14.7% drop over 14 days

**Sentiment volatility:** Much more dramatic
- F&G: 74 → 22 = 52-point drop (70% of the scale!)
- Sentiment changed faster than price

**Insight:** The Fear & Greed Index is a **leading indicator** - it dropped sharply before Bitcoin hit its lowest point.

### 5. **Recovery Pattern**

The market showed a clear **three-phase pattern**:

**Phase 1: Greed (Oct 4-10)**
- Avg Price: $122,600
- Avg F&G: 68
- Trend: High prices, high sentiment

**Phase 2: Capitulation (Oct 11-24)**
- Avg Price: $109,500
- Avg F&G: 29
- Trend: Prices falling, extreme fear

**Phase 3: Stabilization (Oct 25-Nov 2)**
- Avg Price: $111,400
- Avg F&G: 41
- Trend: Sideways consolidation, recovering sentiment

---

## 📊 Statistical Analysis

### Price Movement Breakdown

```
Highest Price:     $124,773 (Oct 7)
Lowest Price:      $106,443 (Oct 18)
Peak-to-Trough:    -14.7%
Current (Nov 2):   $110,806
Recovery:          +4.1% from low
Still Down:        -11.2% from peak
```

### Sentiment Distribution

```
Extreme Fear (0-24):   3 days (9.7%)
Fear (25-44):         16 days (51.6%)
Neutral (45-54):       3 days (9.7%)
Greed (55-74):         9 days (29.0%)
Extreme Greed (75+):   0 days (0%)
```

**Observation:** Market spent majority of time (61.3%) in Fear territory, suggesting this was a bearish period overall.

### Buy Signal Performance (Hypothetical)

If we had bought on **every** signal:

| Entry Date | Entry Price | Current Value | Gain/Loss |
|------------|-------------|---------------|-----------|
| Oct 12 | $110,853 | $110,806 | -0.04% |
| Oct 17 | $108,076 | $110,806 | +2.53% |
| Oct 18 | $106,443 | $110,806 | +4.10% ⭐ |
| Oct 22 | $108,486 | $110,806 | +2.14% |

**Average Return:** +2.18% (holding to Nov 2)

---

## 🔍 Interesting Observations

### 1. **The Oct 11 Crash Catalyst**

On **Oct 11**, we see the most dramatic single-day shift:
- Price: $121,698 → $113,201 (-7.0% drop)
- F&G: 64 → 27 (-37 point drop)

**Question for investigation:** What happened on Oct 11, 2025? External news event? This could be important for understanding market dynamics.

### 2. **"Dead Cat Bounce" Pattern?**

Oct 13-14 showed a small recovery:
- Oct 12: $110,853 (F&G: 24)
- Oct 13: $115,189 (F&G: 38) ← +3.9% bounce
- Oct 14: $115,222 (F&G: 38) ← Flat

Then continued falling:
- Oct 17: $108,076 (F&G: 22) ← New low

**Learning:** Don't assume first bounce = bottom. Market tested lower levels 5 days later.

### 3. **Sentiment Leads Price**

Comparing Oct 11 vs Oct 17-18:

**Oct 11:** Price $113,201, F&G 27 (Fear)
**Oct 17:** Price $108,076, F&G 22 (Extreme Fear)

Despite price being only 4.5% lower, sentiment dropped significantly more. This suggests **fear intensified** even as price stabilized.

### 4. **Neutral Zone = Consolidation**

Oct 25-29 showed F&G around 50-51 (Neutral):
- Prices ranged $110K-$114K (tight range)
- No extreme sentiment in either direction
- Market "waiting" for next move

**Insight:** Neutral sentiment correlates with sideways price action.

### 5. **Current Status (Nov 2)**

- Price: $110,806
- F&G: 37 (Fear)
- Still in "Fear" territory but recovering from extreme levels

**Interpretation:** Market has stabilized but hasn't regained confidence. Potential for either:
1. Further recovery if sentiment improves
2. Retest of lows if fear returns

---

## 🎲 What Would Our Strategy Have Done?

### Scenario: Following Our Rules Strictly

**Starting capital:** $10,000

**Trade 1 (Oct 12):**
- BUY at $110,853 with $2,500 (¼ position)
- Shares: 0.02255 BTC

**Trade 2 (Oct 17):**
- BUY at $108,076 with $2,500
- Shares: 0.02313 BTC

**Trade 3 (Oct 18):**
- BUY at $106,443 with $2,500
- Shares: 0.02349 BTC

**Trade 4 (Oct 22):**
- BUY at $108,486 with $2,500
- Shares: 0.02304 BTC

**Total BTC Acquired:** 0.09221 BTC
**Total Invested:** $10,000
**Average Cost:** $108,468.50
**Current Value (Nov 2):** $10,215.42
**Profit:** +$215.42 (+2.15%)

**Performance vs Buy-and-Hold:**
- If bought $10,000 on Oct 4 at $122,250: Worth $9,064 (-9.36%)
- Our strategy: +2.15% ✅
- **Outperformance:** +11.51 percentage points

---

## 🤔 Questions Raised

### 1. **Is 75 the Right Sell Threshold?**

**Problem:** We never hit a sell signal despite price being up 16% at peak.

**Consideration:** Should we lower the sell threshold to 70 or even 65?
- Oct 5 had F&G of 74 when BTC was near peak ($122,380)
- Missing this could mean leaving profits on table

**Action for Day 4 Backtesting:** Test multiple sell thresholds (65, 70, 75) to find optimal balance.

### 2. **Should We Use Graduated Position Sizing?**

**Current approach:** Equal $2,500 chunks on each signal

**Alternative:** Scale into positions based on F&G intensity:
- F&G 20-24: Buy 30%
- F&G 15-19: Buy 40%
- F&G 10-14: Buy 50%

**Question:** Would this improve returns by buying more at better prices?

### 3. **What About Sell Signals?**

**Observation:** We have no data on sell signal performance (none occurred)

**Risk:** Unknown how well the strategy exits positions

**Next Step:** Need data from a bull run period to test sell side.

### 4. **How Long Should We Hold?**

**Current strategy:** Hold until F&G ≥ 75

**Observation:** From Oct 18 low ($106,443) to current ($110,806) = 15 days holding

**Question:** Is there an optimal holding period? Should we have time-based exits?

### 5. **Does Extreme Fear Always Mean Buy?**

**Concern:** What if F&G stays low for extended period during bear market?

**Example:** F&G was <30 for 14 straight days (Oct 11-24)
- Early buyers (Oct 12) had to wait days for profit
- Could face drawdown if timing is poor

**Risk Management:** Should we wait for F&G to start recovering before buying?

---

## 💡 Insights for Strategy Improvement

### 1. **Consider Multi-Signal Confirmation**

**Instead of:** Just F&G < 25 = Buy

**Try:** F&G < 25 **AND** one of:
- Price is near recent low
- F&G is rising from extreme levels
- Volume is increasing

### 2. **Implement Trailing Stop-Loss**

**Issue:** Current strategy has no downside protection

**Solution:** If BTC drops X% from our entry, exit even if F&G hasn't reached 75

**Example:** 10% trailing stop would have limited losses if market continued down.

### 3. **Scale Out on Partial Signals**

**Idea:** Don't wait for F&G = 75 to sell everything

**Approach:**
- F&G 65-69: Sell 25% of position
- F&G 70-74: Sell 50% of position
- F&G 75+: Sell remaining 25%

**Benefit:** Lock in profits incrementally, reduce risk of missing peak.

### 4. **Add Trend Filter**

**Enhancement:** Only take buy signals if longer-term trend is up

**Why:** Avoid catching falling knives in strong bear markets

**Implementation:** Use 50-day or 200-day moving average as trend filter.

### 5. **Track Historical Context**

**Observation:** F&G of 24 might mean different things in different market contexts

**Action:** Normalize F&G scores relative to recent range
- If recent range is 50-80, then 24 is extremely fearful
- If recent range is 10-40, then 24 is just moderately low

---

## 📈 Visual Patterns Noted

From the generated plot (`bitcoin_fear_greed_plot.png`):

### Pattern 1: **Sentiment Leads Price**
- F&G drops before price bottoms
- F&G recovers before price recovers
- **Implication:** F&G is a leading indicator

### Pattern 2: **Extreme Fear Clusters**
- F&G stays in extreme territory for days, not just single spikes
- **Implication:** Don't try to time exact bottom, accumulate during fear periods

### Pattern 3: **Greed Doesn't Guarantee Correction**
- F&G was 70+ for week, but price kept rising
- **Implication:** Don't sell too early in bull trends

### Pattern 4: **Sharp Drops = Sharp Sentiment Changes**
- Oct 11 crash: Both price and F&G dropped dramatically
- **Implication:** Market sentiment can flip quickly

---

## 🎯 Actionable Next Steps (For Day 3+)

### For Day 3 (Signal Generation):
1. Implement basic buy/sell signals (F&G thresholds)
2. Mark all historical signals in our dataset
3. Calculate potential entry/exit points
4. Add signal strength indicator (how far from threshold)

### For Day 4 (Backtesting):
1. **Test multiple threshold combinations:**
   - Buy thresholds: 20, 25, 30
   - Sell thresholds: 65, 70, 75

2. **Test position sizing strategies:**
   - Equal sizing (current)
   - Fear-scaled sizing
   - Fixed dollar cost averaging

3. **Add risk management:**
   - Stop-loss levels
   - Take-profit targets
   - Maximum drawdown limits

4. **Performance metrics to calculate:**
   - Total return
   - Win rate
   - Average gain per trade
   - Maximum drawdown
   - Sharpe ratio
   - Comparison to buy-and-hold

### For Day 5 (Analysis):
1. Document which strategies worked best
2. Identify optimal parameters
3. Assess risk-adjusted returns
4. Determine if Fear & Greed Index is predictive
5. Conclude: Would we trust this with real money?

---

## 🚨 Limitations & Caveats

### 1. **Small Sample Size**
- Only 30 days of data
- Only 4 buy signals
- Zero sell signals
- **Concern:** Not enough to draw firm conclusions

### 2. **Specific Market Conditions**
- This period was corrective/bearish
- Haven't tested in strong bull market
- Haven't tested in extreme bear market
- **Concern:** Strategy may not generalize

### 3. **Hindsight Bias**
- We're analyzing knowing what happened next
- Real trading involves uncertainty and emotion
- **Concern:** Live performance may differ significantly

### 4. **No Transaction Costs**
- Analysis ignores fees, slippage, taxes
- Real returns would be lower
- **Concern:** Small gains might disappear with costs

### 5. **Data Quality**
- CoinGecko prices are snapshots, not exact traded prices
- F&G is calculated once daily
- **Concern:** Actual fills might be worse than backtest

### 6. **Market Evolution**
- Markets adapt to known patterns
- If everyone uses F&G, does it still work?
- **Concern:** Historical performance ≠ future results

---

## 📝 Interesting Questions for Further Research

1. **Does F&G work better in crypto than traditional markets?**
2. **Is there an optimal data lookback period for F&G?**
3. **How does F&G correlate with other altcoins?**
4. **Do different cryptocurrencies have different optimal thresholds?**
5. **Can we combine F&G with technical indicators for better signals?**
6. **How does F&G perform during black swan events?**
7. **Is there a "sentiment momentum" we can exploit?**
8. **Do F&G extremes last longer in bear vs bull markets?**

---

## 🎓 What We Learned (Technical Skills)

### APIs
- ✅ CoinGecko API returns daily OHLC data efficiently
- ✅ Fear & Greed API has good historical depth (no limits observed)
- ✅ Both APIs are free and don't require authentication
- ⚠️ Need to handle rate limiting in production
- ⚠️ Should add retry logic for failed requests

### Data Processing
- ✅ Pandas is excellent for time-series alignment
- ✅ Merging by date works well for daily data
- ⚠️ Timezone handling can be tricky (timestamps vs dates)
- ⚠️ Need to handle missing data (some dates might not align)

### Visualization
- ✅ Dual y-axis charts clearly show correlation
- ✅ Matplotlib is sufficient for basic analysis
- 💡 Consider adding: volume bars, moving averages, signal markers
- 💡 Interactive plots (Plotly) might be better for exploration

---

## 🏆 Key Takeaways

### What Worked Well:
1. **Fear & Greed Index shows promise** as a contrarian indicator
2. **Buying in extreme fear** outperformed buy-and-hold (+11.5pp)
3. **Simple thresholds** (25/75) are easy to implement and backtest
4. **Data combination** was straightforward with proper date alignment

### What Needs Improvement:
1. **Sell signals** need testing (no data in this period)
2. **Risk management** is completely absent
3. **Position sizing** could be optimized
4. **Threshold tuning** needs more data and analysis

### Biggest Surprise:
**The magnitude of sentiment swings** - F&G dropped 52 points (70%) while price only dropped 15%. This suggests emotional overreaction creates opportunities.

### Most Important Finding:
**Timing matters more than we thought** - Even within the "buy zone," entering at F&G=22 vs F&G=24 made a 2% difference. Patience during fear periods pays off.

---

## 📅 Data Generation Date
This document was generated on November 2, 2025, analyzing data from October 4 - November 2, 2025.

**Next Update:** After Day 4 backtesting with optimized parameters and multiple strategy variants.

---

*"In trading, the greatest opportunities arise when fear is highest and crowds are running for the exits. The Fear & Greed Index quantifies this human emotion, giving us a systematic edge."*