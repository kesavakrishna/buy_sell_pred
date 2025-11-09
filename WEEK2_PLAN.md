# Week 2 Enhanced Plan: Multi-Indicator Trading System

**Duration:** Days 8-14 (7 days)
**Total Time:** ~20 hours (2.5-3 hours/day)
**Goal:** Build a robust multi-indicator trading system and prepare for Week 3 ML optimization

---

## Overview

Build on Week 1's Fear & Greed Index foundation by adding 3 more indicators (Whale Movements, Google Trends, RSI), test multiple combination strategies, and prepare clean data for machine learning in Week 3.

### Key Improvements vs Original Plan:
- ✅ Added RSI as 4th indicator (free, no API needed)
- ✅ Included lag correlation analysis to identify leading indicators
- ✅ Added risk-adjusted metrics (Sharpe, Sortino, Calmar ratios)
- ✅ Incorporated transaction cost modeling for realistic backtesting
- ✅ Enhanced time estimates (padded by 20%)
- ✅ Improved signal combination with confidence scoring

---

## Day 8 (Monday): Deep Analysis of Week 1 Results

**Time: ~2.5 hours** (originally 2h)

### Objectives:
- Thoroughly analyze Day 6 enhanced strategy performance
- Identify specific strengths and weaknesses
- Create foundation for multi-indicator improvements

### Tasks:

1. **Calculate Comprehensive Metrics**:
   ```python
   def analyze_week1_results(backtest_results, df):
       """Deep dive into Fear & Greed strategy"""
       analysis = {}

       # Win rate
       trades = backtest_results['trades']
       profitable_trades = [t for t in trades if t['profit'] > 0]
       analysis['win_rate'] = len(profitable_trades) / len(trades)

       # Signal frequency
       buy_signals = len(df[df['signal'] == 'BUY'])
       sell_signals = len(df[df['signal'] == 'SELL'])
       analysis['signal_frequency'] = (buy_signals + sell_signals) / len(df)

       # Time in market
       analysis['days_in_market'] = df[df['signal'] != 'HOLD'].shape[0]

       # Drawdown analysis
       df['cumulative_return'] = (df['price'] / df['price'].iloc[0] - 1) * 100
       analysis['max_drawdown'] = df['cumulative_return'].min()

       return analysis
   ```

2. **Identify Weaknesses**:
   - Too many signals? (Over-trading)
   - Too few signals? (Missing opportunities)
   - Wrong timing? (Signals lag the move)
   - False signals? (Says buy, then price drops)

3. **Create Findings Document**:
   - 5-10 specific insights about what worked and what didn't
   - Market conditions where F&G excelled
   - Areas for improvement

### Deliverables:
- `scratchpad/week2/day8_week1_analysis.py`
- `scratchpad/week2/day8_week1_analysis.md`

### Success Metric:
Written document with 5-10 specific actionable insights

---

## Day 9 (Tuesday): Add Whale Movements Indicator

**Time: ~3 hours** (originally 2.5h)

### Objectives:
- Set up WhaleAlert API
- Fetch and analyze 30 days of whale transaction data
- Create whale-based trading signal

### Tasks:

1. **Set up WhaleAlert API**:
   - Sign up at https://whale-alert.io/
   - Get free API key (10 calls/minute limit)

2. **Fetch Historical Whale Data** (with rate limiting):
   ```python
   import time

   def fetch_historical_whale_data(days=30):
       """Fetch with rate limiting"""
       all_transactions = []

       for i in range(days):
           date = datetime.now() - timedelta(days=i)
           start = date.replace(hour=0, minute=0)
           end = date.replace(hour=23, minute=59)

           transactions = whale.get_transactions(start, end)
           all_transactions.extend(transactions)

           # Rate limiting: 10 calls/min = 6 seconds between calls
           if i < days - 1:
               time.sleep(6)

       return all_transactions  # ~3 minutes total
   ```

3. **Create Whale Signal Logic**:
   ```python
   class WhaleTracker:
       def calculate_whale_signal(self, transactions):
           """
           Analyze whale movements:
           - Transfers TO exchanges = Bearish (might sell)
           - Transfers FROM exchanges = Bullish (accumulation)
           """
           to_exchange = sum([tx['amount_usd'] for tx in transactions
                             if tx['to']['owner_type'] == 'exchange'])
           from_exchange = sum([tx['amount_usd'] for tx in transactions
                               if tx['from']['owner_type'] == 'exchange'])

           net_flow = from_exchange - to_exchange

           if net_flow > 10_000_000:
               return 'ACCUMULATION'
           elif net_flow < -10_000_000:
               return 'DISTRIBUTION'
           else:
               return 'NEUTRAL'
   ```

4. **Test whale signal independently**

### Deliverables:
- `scratchpad/week2/day9_whale_tracker.py`
- `scratchpad/week2/whale_data_30days.csv`

### Success Metric:
30 days of whale movement data stored and whale signal generator working

---

## Day 10 (Wednesday): Integration & Correlation Analysis

**Time: ~2.5 hours** (originally 2h)

### Objectives:
- Merge all datasets (BTC + F&G + Whale)
- Analyze correlations including lag analysis
- Test whale signal independently

### Tasks:

1. **Merge All Datasets**:
   ```python
   def create_combined_dataset(btc_df, fg_df, whale_df):
       """Merge all indicators into one DataFrame"""
       # Ensure all have date column
       btc_df['date'] = pd.to_datetime(btc_df['date']).dt.date
       fg_df['date'] = pd.to_datetime(fg_df['date']).dt.date
       whale_df['date'] = pd.to_datetime(whale_df['date']).dt.date

       # Merge
       combined = btc_df.merge(fg_df, on='date', how='left')
       combined = combined.merge(whale_df, on='date', how='left')

       # Fill missing values
       combined = combined.fillna(method='ffill')

       return combined
   ```

2. **Standard Correlation Analysis**:
   ```python
   import seaborn as sns

   def analyze_indicator_correlation(df):
       """See which indicators move together"""
       indicators = df[['price', 'fear_greed', 'whale_net_flow']].copy()

       # Normalize to 0-100 scale
       for col in indicators.columns:
           indicators[col] = (indicators[col] - indicators[col].min()) / \
                            (indicators[col].max() - indicators[col].min()) * 100

       correlation = indicators.corr()

       # Plot heatmap
       plt.figure(figsize=(8, 6))
       sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
       plt.title('Indicator Correlation Matrix')
       plt.show()

       return correlation
   ```

3. **NEW: Lag Correlation Analysis**:
   ```python
   def analyze_correlation_with_lag(df):
       """
       Check if indicators LEAD or LAG price movements
       This is more useful than same-day correlation
       """
       lags = range(-7, 8)  # Check 7 days before/after
       correlations = {}

       for lag in lags:
           correlations[lag] = df['price'].corr(df['fear_greed'].shift(lag))

       # Plot
       plt.figure(figsize=(10, 6))
       plt.plot(list(correlations.keys()), list(correlations.values()))
       plt.axhline(y=0, color='r', linestyle='--')
       plt.xlabel('Lag (days)')
       plt.ylabel('Correlation')
       plt.title('Fear & Greed Correlation at Different Lags')
       plt.show()

       best_lag = max(correlations, key=correlations.get)
       print(f"\nBest correlation at lag: {best_lag} days")
       print(f"If positive lag: F&G PREDICTS price that many days ahead")
   ```

4. **Independent Whale Backtest**:
   - Test whale-only strategy
   - Compare to F&G performance

### Deliverables:
- `scratchpad/week2/day10_integration.py`
- `scratchpad/week2/combined_data.csv`
- Correlation analysis insights document

### Success Metric:
Know which indicator performs better (F&G or Whale) and whether any indicator leads price movements

---

## Day 11 (Thursday): Add Google Trends + RSI

**Time: ~2.5 hours** (originally 2h)

### Objectives:
- Set up Google Trends tracking with DAILY resolution
- Add RSI technical indicator (no API needed)
- Test both independently

### Tasks:

1. **Set up Google Trends** (Daily Data):
   ```python
   from pytrends.request import TrendReq
   import time

   def get_daily_trends(days=90):
       """
       Get daily resolution by requesting smaller chunks
       Google Trends gives daily data for requests < 7 days
       """
       pytrends = TrendReq()
       all_data = []

       for i in range(0, days, 6):  # 6-day chunks
           end_date = datetime.now() - timedelta(days=i)
           start_date = end_date - timedelta(days=6)

           timeframe = f'{start_date.strftime("%Y-%m-%d")} {end_date.strftime("%Y-%m-%d")}'
           pytrends.build_payload(['bitcoin'], timeframe=timeframe)
           data = pytrends.interest_over_time()
           all_data.append(data)

           time.sleep(2)  # Rate limiting

       return pd.concat(all_data)
   ```

2. **Create Trends Signal**:
   ```python
   class TrendsTracker:
       def generate_signal(self, current_interest, historical_avg):
           """
           High search = Retail FOMO = Potential top (contrarian)
           Low search = Lack of attention = Potential bottom
           """
           if current_interest > historical_avg * 1.5:
               return 'FOMO_WARNING'  # Too much hype - SELL
           elif current_interest < historical_avg * 0.5:
               return 'UNDERVALUED'  # Nobody cares - BUY
           else:
               return 'NEUTRAL'
   ```

3. **NEW: Add RSI Indicator**:
   ```python
   def calculate_rsi(prices, period=14):
       """
       RSI (Relative Strength Index) - Classic technical indicator
       No API needed - pure math on price data
       """
       delta = prices.diff()
       gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
       loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
       rs = gain / loss
       rsi = 100 - (100 / (1 + rs))
       return rsi

   # RSI Signal Logic
   def rsi_signal(rsi_value):
       if rsi_value < 30:
           return 'OVERSOLD'  # BUY
       elif rsi_value > 70:
           return 'OVERBOUGHT'  # SELL
       else:
           return 'NEUTRAL'
   ```

4. **Test both independently**

### Deliverables:
- `scratchpad/week2/day11_trends_rsi.py`
- `scratchpad/week2/trends_data_90days.csv`
- RSI calculated and added to combined dataset

### Success Metric:
90 days of Google Trends data + RSI calculated for all price data

---

## Day 12 (Friday): Multi-Indicator Signal Combination

**Time: ~3 hours** (originally 2.5h)

### Objectives:
- Design 4 different combination strategies
- Implement all strategies
- Test each on paper (no full backtest yet)

### Tasks:

1. **Strategy A: Simple Voting** (need 3/4 votes):
   ```python
   class SimpleVotingStrategy:
       def generate_signal(self, fg, whale, trends, rsi):
           """Each indicator votes BUY/SELL/NEUTRAL"""
           votes = {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0}

           # F&G vote
           if fg < 25:
               votes['BUY'] += 1
           elif fg > 75:
               votes['SELL'] += 1
           else:
               votes['NEUTRAL'] += 1

           # Whale vote
           if whale == 'ACCUMULATION':
               votes['BUY'] += 1
           elif whale == 'DISTRIBUTION':
               votes['SELL'] += 1
           else:
               votes['NEUTRAL'] += 1

           # Trends vote (contrarian)
           if trends == 'UNDERVALUED':
               votes['BUY'] += 1
           elif trends == 'FOMO_WARNING':
               votes['SELL'] += 1
           else:
               votes['NEUTRAL'] += 1

           # RSI vote
           if rsi < 30:
               votes['BUY'] += 1
           elif rsi > 70:
               votes['SELL'] += 1
           else:
               votes['NEUTRAL'] += 1

           # Need 3/4 votes for signal
           if votes['BUY'] >= 3:
               return 'BUY'
           elif votes['SELL'] >= 3:
               return 'SELL'
           else:
               return 'HOLD'
   ```

2. **Strategy B: Unanimous** (all 4 must agree):
   ```python
   if votes['BUY'] == 4:
       return 'STRONG_BUY'
   elif votes['SELL'] == 4:
       return 'STRONG_SELL'
   else:
       return 'HOLD'
   ```

3. **Strategy C: Weighted Voting** (F&G gets 2 votes):
   ```python
   weighted_votes = {
       'BUY': (fg_buy * 2) + whale_buy + trends_buy + rsi_buy,
       'SELL': (fg_sell * 2) + whale_sell + trends_sell + rsi_sell
   }
   # Total possible: 7 votes
   # Need 4/7 for signal
   ```

4. **Strategy D: NEW - Confidence Scoring**:
   ```python
   def generate_combined_signal_v2(fg, whale_flow, trends, trends_avg, rsi):
       """
       Enhanced with confidence scoring
       Each indicator scores 0-2 based on signal strength
       """
       scores = {'BUY': 0, 'SELL': 0}

       # F&G (weighted by extremity)
       if fg <= 20:
           scores['BUY'] += 2  # Strong
       elif fg <= 25:
           scores['BUY'] += 1  # Moderate
       elif fg >= 80:
           scores['SELL'] += 2
       elif fg >= 75:
           scores['SELL'] += 1

       # Whale (weighted by volume)
       if whale_flow > 20_000_000:
           scores['BUY'] += 2
       elif whale_flow > 10_000_000:
           scores['BUY'] += 1
       elif whale_flow < -20_000_000:
           scores['SELL'] += 2
       elif whale_flow < -10_000_000:
           scores['SELL'] += 1

       # Trends (contrarian with strength)
       deviation = trends / trends_avg
       if deviation > 2.0:
           scores['SELL'] += 2
       elif deviation > 1.5:
           scores['SELL'] += 1
       elif deviation < 0.3:
           scores['BUY'] += 2
       elif deviation < 0.5:
           scores['BUY'] += 1

       # RSI (strength-based)
       if rsi < 25:
           scores['BUY'] += 2
       elif rsi < 30:
           scores['BUY'] += 1
       elif rsi > 75:
           scores['SELL'] += 2
       elif rsi > 70:
           scores['SELL'] += 1

       # Determine signal with confidence (max score: 8)
       if scores['BUY'] >= 5:
           return {'signal': 'STRONG_BUY', 'confidence': scores['BUY']/8}
       elif scores['BUY'] >= 3:
           return {'signal': 'BUY', 'confidence': scores['BUY']/8}
       elif scores['SELL'] >= 5:
           return {'signal': 'STRONG_SELL', 'confidence': scores['SELL']/8}
       elif scores['SELL'] >= 3:
           return {'signal': 'SELL', 'confidence': scores['SELL']/8}
       else:
           return {'signal': 'HOLD', 'confidence': 0}
   ```

### Deliverables:
- `scratchpad/week2/day12_combination_strategies.py`

### Success Metric:
4 different combination strategies coded and ready to backtest

---

## Day 13 (Saturday): Comprehensive Backtest Comparison

**Time: ~4 hours** (originally 3h)

### Objectives:
- Backtest all 9 strategies with transaction costs
- Calculate risk-adjusted metrics
- Identify best strategy

### Tasks:

1. **Backtest All Strategies**:
   - Fear & Greed only
   - Whale only
   - Trends only
   - RSI only
   - Simple Voting (4 indicators)
   - Unanimous (4 indicators)
   - Weighted (4 indicators)
   - Confidence Scoring (4 indicators)
   - Buy & Hold baseline

2. **NEW: Add Transaction Costs**:
   ```python
   class RealisticBacktester:
       def __init__(self, starting_capital=10000, fee_rate=0.001):
           self.fee_rate = fee_rate  # 0.1% per trade

       def execute_trade(self, action, price, capital):
           if action == 'BUY':
               fee = capital * self.fee_rate
               btc_bought = (capital - fee) / price
               return btc_bought
           elif action == 'SELL':
               gross_proceeds = btc_amount * price
               fee = gross_proceeds * self.fee_rate
               net_proceeds = gross_proceeds - fee
               return net_proceeds
   ```

3. **Calculate Advanced Metrics**:
   ```python
   def calculate_advanced_metrics(results):
       """Beyond return % - measure quality of returns"""

       # Sharpe Ratio (return per unit of risk)
       returns = results['daily_returns']
       sharpe = (returns.mean() / returns.std()) * np.sqrt(365)

       # Sortino Ratio (only penalizes downside volatility)
       downside_returns = returns[returns < 0]
       sortino = (returns.mean() / downside_returns.std()) * np.sqrt(365)

       # Calmar Ratio (return / max drawdown)
       calmar = results['total_return'] / abs(results['max_drawdown'])

       # Win/Loss Ratio
       avg_win = results['winning_trades'].mean()
       avg_loss = abs(results['losing_trades'].mean())
       win_loss_ratio = avg_win / avg_loss

       return {
           'sharpe': sharpe,
           'sortino': sortino,
           'calmar': calmar,
           'win_loss_ratio': win_loss_ratio
       }
   ```

4. **Create Comparison Table**:
   ```python
   comparison = pd.DataFrame({
       'Strategy': results.keys(),
       'Final Value': [r['final_value'] for r in results.values()],
       'Return %': [r['return_pct'] for r in results.values()],
       'Return % (Net)': [r['return_pct_after_fees'] for r in results.values()],
       'Win Rate': [r['win_rate'] for r in results.values()],
       'Num Trades': [r['num_trades'] for r in results.values()],
       'Max Drawdown': [r['max_drawdown'] for r in results.values()],
       'Sharpe Ratio': [r['sharpe'] for r in results.values()],
       'Sortino Ratio': [r['sortino'] for r in results.values()],
       'Calmar Ratio': [r['calmar'] for r in results.values()],
       'Win/Loss Ratio': [r['win_loss_ratio'] for r in results.values()]
   })
   ```

5. **Visualize Performance**:
   - Return comparison bar chart
   - Win rate comparison
   - Risk-adjusted return comparison
   - Drawdown comparison
   - Equity curves over time

6. **Identify Best Strategy** (using risk-adjusted metrics)

### Deliverables:
- `scratchpad/week2/day13_comprehensive_backtest.py`
- `scratchpad/week2/strategy_comparison_results.csv`
- `scratchpad/week2/strategy_comparison_charts.png`

### Success Metric:
Know definitively which strategy performs best on risk-adjusted basis

---

## Day 14 (Sunday): Documentation & ML Prep

**Time: ~2.5 hours** (originally 2h)

### Objectives:
- Create comprehensive Week 2 summary
- Prepare ML-ready dataset for Week 3
- Update project documentation

### Tasks:

1. **Create Week 2 Summary Report**:
   ```markdown
   # Week 2 Results Summary

   ## Indicators Implemented
   1. Fear & Greed Index (from Week 1)
   2. Whale Movements (WhaleAlert API)
   3. Google Trends Search Volume
   4. RSI (Relative Strength Index)

   ## Individual Performance
   - F&G Only: X% return, Y% win rate
   - Whale Only: X% return, Y% win rate
   - Trends Only: X% return, Y% win rate
   - RSI Only: X% return, Y% win rate

   ## Combined Strategy Performance
   - Voting Strategy: X% return, Y% Sharpe
   - Unanimous Strategy: X% return, Y% Sharpe
   - Weighted Strategy: X% return, Y% Sharpe
   - Confidence Scoring: X% return, Y% Sharpe

   ## Best Strategy: [Name]
   - Return: X% (net of fees)
   - Sharpe Ratio: X.XX
   - Win Rate: Y%
   - Why it works: [Your insight]

   ## Key Learnings
   1. [What surprised you?]
   2. [Which indicator was most useful?]
   3. [Did lag correlation reveal leading indicators?]
   4. [Impact of transaction costs?]

   ## Ready for Week 3?
   - [x] 4 working indicators
   - [x] 30+ days of combined data
   - [x] Best combination strategy identified
   - [x] ML-ready dataset prepared
   ```

2. **Prepare ML-Ready Dataset**:
   ```python
   def prepare_ml_dataset(df):
       """Create clean dataset for machine learning"""
       ml_df = df.copy()

       # Create target variable: Did price go up in next 7 days?
       ml_df['price_7d_future'] = ml_df['price'].shift(-7)
       ml_df['target'] = (ml_df['price_7d_future'] > ml_df['price']).astype(int)

       # Feature engineering
       ml_df['fg_normalized'] = ml_df['fear_greed'] / 100
       ml_df['whale_flow_millions'] = ml_df['whale_net_flow'] / 1_000_000
       ml_df['trends_relative'] = ml_df['trends_value'] / ml_df['trends_value'].rolling(30).mean()
       ml_df['rsi_normalized'] = ml_df['rsi'] / 100

       # Add lag features (past values)
       ml_df['price_7d_ago'] = ml_df['price'].shift(7)
       ml_df['fg_7d_ago'] = ml_df['fear_greed'].shift(7)
       ml_df['rsi_7d_ago'] = ml_df['rsi'].shift(7)

       # Add momentum features
       ml_df['price_change_7d'] = (ml_df['price'] - ml_df['price_7d_ago']) / ml_df['price_7d_ago']
       ml_df['fg_change_7d'] = ml_df['fear_greed'] - ml_df['fg_7d_ago']

       # Remove rows with NaN
       ml_df = ml_df.dropna()

       # Save for Week 3
       ml_df.to_csv('ml_ready_dataset.csv', index=False)

       print(f"\n✅ ML Dataset Ready")
       print(f"Total samples: {len(ml_df)}")
       print(f"Features: {len(ml_df.columns)}")
       print(f"Target distribution: {ml_df['target'].value_counts().to_dict()}")

       return ml_df
   ```

3. **Set Week 3 Goals**:
   - Can ML beat best rule-based strategy?
   - Which features will be most important?
   - Will feature engineering help?

4. **Update Project Documentation**:
   - Update README.md with Week 2 status
   - Update claude.md with new indicators
   - Commit Week 2 work to git

### Deliverables:
- `scratchpad/week2/WEEK2_SUMMARY.md`
- `ml_ready_dataset.csv`
- Updated README.md and claude.md

### Success Metric:
Clean ML-ready dataset saved and comprehensive summary document completed

---

## Total Time Estimate

**Total: ~20 hours** (2.5-3 hours/day average)

Breakdown:
- Day 8: 2.5 hours
- Day 9: 3 hours
- Day 10: 2.5 hours
- Day 11: 2.5 hours
- Day 12: 3 hours
- Day 13: 4 hours
- Day 14: 2.5 hours

---

## Key Additions vs Original Plan

1. ✅ **RSI as 4th indicator** (no API needed, pure technical analysis)
2. ✅ **Lag correlation analysis** (find leading indicators)
3. ✅ **Risk-adjusted metrics** (Sharpe, Sortino, Calmar ratios)
4. ✅ **Transaction cost modeling** (0.1% fee per trade)
5. ✅ **Confidence scoring strategy** (gradual position sizing)
6. ✅ **Padded time estimates** (+20% buffer)
7. ✅ **Rate limiting code** for API calls
8. ✅ **Daily resolution** for Google Trends

---

## Success Criteria

By end of Week 2, you should have:
- [ ] 4 working indicators (F&G, Whale, Trends, RSI)
- [ ] 30+ days of combined indicator data
- [ ] 9 strategies tested (4 single + 4 combined + baseline)
- [ ] Transaction costs modeled (realistic returns)
- [ ] Best strategy identified using risk-adjusted metrics
- [ ] ML-ready dataset with engineered features
- [ ] Comprehensive Week 2 summary document
- [ ] Updated project documentation

---

## What You'll Learn

### Technical Skills:
- Multi-indicator strategy design
- Lag correlation analysis
- Risk-adjusted performance metrics
- Transaction cost modeling
- Feature engineering for ML

### Trading Concepts:
- How different data sources complement each other
- Signal combination approaches
- Impact of trading costs on returns
- Risk vs return tradeoffs
- Leading vs lagging indicators

### Research Methodology:
- Systematic strategy comparison
- Identifying what makes a strategy work
- Preparing data for machine learning
- Documenting findings for future reference

---

## Ready to Begin?

Start with **Day 8** and analyze your Week 1 results thoroughly. This foundation will guide all your Week 2 decisions!
