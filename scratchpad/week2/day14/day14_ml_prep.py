"""
Day 14: Documentation & ML Preparation
Create ML-ready dataset and comprehensive Week 2 summary
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def load_combined_data():
    """Load combined dataset with all indicators"""
    path = 'scratchpad/week2/day11/combined_with_rsi_trends.csv'
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    print(f"[OK] Loaded combined data: {len(df)} days")
    return df

def prepare_ml_dataset(df):
    """
    Create clean ML-ready dataset with engineered features

    Target: Will price go up in next 7 days?
    Features: All indicators + lag features + momentum features
    """
    print("\n" + "=" * 60)
    print("PREPARING ML-READY DATASET")
    print("=" * 60)

    ml_df = df.copy()
    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    # 1. Create target variable: Price increase in next 7 days
    print("\n[1] Creating target variable...")
    ml_df['price_7d_future'] = ml_df[price_col].shift(-7)
    ml_df['target'] = (ml_df['price_7d_future'] > ml_df[price_col]).astype(int)
    ml_df['target_return'] = ((ml_df['price_7d_future'] - ml_df[price_col]) / ml_df[price_col]) * 100

    print(f"    Target distribution:")
    print(f"    - Price UP (1): {(ml_df['target'] == 1).sum()} days")
    print(f"    - Price DOWN (0): {(ml_df['target'] == 0).sum()} days")

    # 2. Normalize features (0-1 scale)
    print("\n[2] Normalizing features...")
    ml_df['fg_normalized'] = ml_df['fear_greed_value'] / 100
    ml_df['rsi_normalized'] = ml_df['rsi'] / 100
    ml_df['trends_normalized'] = ml_df['trends_value'] / 100

    # Whale flow in millions (already scaled)
    ml_df['whale_flow_millions'] = ml_df['net_flow_millions']

    # 3. Add lag features (historical values)
    print("\n[3] Adding lag features...")
    for lag in [1, 3, 7]:
        ml_df[f'price_{lag}d_ago'] = ml_df[price_col].shift(lag)
        ml_df[f'fg_{lag}d_ago'] = ml_df['fear_greed_value'].shift(lag)
        ml_df[f'rsi_{lag}d_ago'] = ml_df['rsi'].shift(lag)
        ml_df[f'whale_flow_{lag}d_ago'] = ml_df['net_flow_millions'].shift(lag)

    # 4. Add momentum features (changes over time)
    print("\n[4] Adding momentum features...")

    # Price momentum
    ml_df['price_change_1d'] = ml_df[price_col].pct_change(1) * 100
    ml_df['price_change_3d'] = ml_df[price_col].pct_change(3) * 100
    ml_df['price_change_7d'] = ml_df[price_col].pct_change(7) * 100

    # Fear & Greed momentum
    ml_df['fg_change_1d'] = ml_df['fear_greed_value'].diff(1)
    ml_df['fg_change_3d'] = ml_df['fear_greed_value'].diff(3)
    ml_df['fg_change_7d'] = ml_df['fear_greed_value'].diff(7)

    # RSI momentum
    ml_df['rsi_change_1d'] = ml_df['rsi'].diff(1)
    ml_df['rsi_change_3d'] = ml_df['rsi'].diff(3)

    # Whale momentum
    ml_df['whale_flow_change_3d'] = ml_df['net_flow_millions'].diff(3)

    # 5. Add rolling statistics
    print("\n[5] Adding rolling statistics...")

    # 7-day moving averages
    ml_df['price_ma7'] = ml_df[price_col].rolling(window=7, min_periods=1).mean()
    ml_df['fg_ma7'] = ml_df['fear_greed_value'].rolling(window=7, min_periods=1).mean()
    ml_df['rsi_ma7'] = ml_df['rsi'].rolling(window=7, min_periods=1).mean()

    # Distance from moving average
    ml_df['price_vs_ma7'] = ((ml_df[price_col] - ml_df['price_ma7']) / ml_df['price_ma7']) * 100
    ml_df['fg_vs_ma7'] = ml_df['fear_greed_value'] - ml_df['fg_ma7']

    # 7-day volatility (standard deviation)
    ml_df['price_volatility_7d'] = ml_df[price_col].rolling(window=7, min_periods=1).std()
    ml_df['fg_volatility_7d'] = ml_df['fear_greed_value'].rolling(window=7, min_periods=1).std()

    # 6. Add signal indicators (from our strategies)
    print("\n[6] Adding strategy signals as features...")

    # Fear & Greed signals
    ml_df['fg_oversold'] = (ml_df['fear_greed_value'] < 25).astype(int)
    ml_df['fg_extreme_fear'] = (ml_df['fear_greed_value'] < 20).astype(int)
    ml_df['fg_overbought'] = (ml_df['fear_greed_value'] > 75).astype(int)

    # RSI signals
    ml_df['rsi_oversold'] = (ml_df['rsi'] < 30).astype(int)
    ml_df['rsi_extreme_oversold'] = (ml_df['rsi'] < 25).astype(int)
    ml_df['rsi_overbought'] = (ml_df['rsi'] > 70).astype(int)

    # Whale signals
    ml_df['whale_accumulation'] = (ml_df['signal'] == 'ACCUMULATION').astype(int)
    ml_df['whale_distribution'] = (ml_df['signal'] == 'DISTRIBUTION').astype(int)
    ml_df['whale_strong_accumulation'] = (ml_df['net_flow_millions'] > 20).astype(int)

    # Trends signals
    ml_df['trends_undervalued'] = (ml_df['trends_ratio'] < 0.5).astype(int)
    ml_df['trends_fomo'] = (ml_df['trends_ratio'] > 1.5).astype(int)

    # 7. Add voting features
    print("\n[7] Adding voting features...")

    # Simple voting count (how many indicators say BUY)
    ml_df['buy_votes'] = (
        ml_df['fg_oversold'] +
        ml_df['rsi_oversold'] +
        ml_df['whale_accumulation'] +
        ml_df['trends_undervalued']
    )

    ml_df['sell_votes'] = (
        ml_df['fg_overbought'] +
        ml_df['rsi_overbought'] +
        ml_df['whale_distribution'] +
        ml_df['trends_fomo']
    )

    # 8. Remove rows with NaN (due to shifting/rolling)
    print("\n[8] Cleaning data...")
    initial_rows = len(ml_df)
    ml_df = ml_df.dropna()
    final_rows = len(ml_df)
    removed_rows = initial_rows - final_rows

    print(f"    Removed {removed_rows} rows with missing values")
    print(f"    Final dataset: {final_rows} rows")

    # 9. Select final feature set
    print("\n[9] Selecting final features...")

    # Core features (current indicators)
    core_features = [
        'fg_normalized', 'rsi_normalized', 'whale_flow_millions', 'trends_normalized'
    ]

    # Lag features
    lag_features = [f for f in ml_df.columns if '_ago' in f]

    # Momentum features
    momentum_features = [f for f in ml_df.columns if '_change_' in f]

    # Rolling features
    rolling_features = [f for f in ml_df.columns if ('_ma7' in f or '_vs_ma7' in f or '_volatility_' in f)]

    # Signal features
    signal_features = [f for f in ml_df.columns if any(x in f for x in ['oversold', 'overbought', 'accumulation', 'distribution', 'undervalued', 'fomo', '_votes'])]

    # Target
    target_cols = ['target', 'target_return']

    # Metadata
    metadata_cols = ['date', price_col]

    # All ML features
    all_features = core_features + lag_features + momentum_features + rolling_features + signal_features

    # Final columns
    final_cols = metadata_cols + all_features + target_cols

    ml_ready = ml_df[final_cols].copy()

    print(f"\n[OK] ML dataset ready!")
    print(f"    Total features: {len(all_features)}")
    print(f"    - Core: {len(core_features)}")
    print(f"    - Lag: {len(lag_features)}")
    print(f"    - Momentum: {len(momentum_features)}")
    print(f"    - Rolling: {len(rolling_features)}")
    print(f"    - Signals: {len(signal_features)}")
    print(f"    Samples: {len(ml_ready)}")

    return ml_ready, all_features

def print_feature_summary(ml_df, features):
    """Print summary of ML features"""
    print("\n" + "=" * 60)
    print("FEATURE SUMMARY")
    print("=" * 60)

    print("\nTarget Variable Distribution:")
    target_counts = ml_df['target'].value_counts()
    for val, count in target_counts.items():
        pct = count / len(ml_df) * 100
        label = "Price UP" if val == 1 else "Price DOWN"
        print(f"  {label}: {count} samples ({pct:.1f}%)")

    print(f"\nAverage 7-day return: {ml_df['target_return'].mean():+.2f}%")
    print(f"Best 7-day return: {ml_df['target_return'].max():+.2f}%")
    print(f"Worst 7-day return: {ml_df['target_return'].min():+.2f}%")

    print("\nFeature Categories:")
    print(f"  Core Indicators: fg_normalized, rsi_normalized, whale_flow_millions, trends_normalized")
    print(f"  Lag Features: {len([f for f in features if '_ago' in f])} features (1d, 3d, 7d lags)")
    print(f"  Momentum: {len([f for f in features if '_change_' in f])} features (price/fg/rsi changes)")
    print(f"  Rolling Stats: {len([f for f in features if 'ma7' in f or 'volatility' in f])} features (MAs, volatility)")
    print(f"  Signal Flags: {len([f for f in features if any(x in f for x in ['oversold', 'overbought', 'accumulation'])])} features (binary signals)")
    print(f"  Voting: buy_votes, sell_votes")

def create_week2_summary():
    """Create comprehensive Week 2 summary"""
    summary = """
# Week 2 Summary: Multi-Indicator Trading System

## Overview
**Duration:** Days 8-14 (7 days)
**Goal:** Build a robust multi-indicator system and prepare for Week 3 ML optimization

## What We Built

### Indicators Implemented (4 total)
1. **Fear & Greed Index** (from Week 1)
   - Type: Sentiment indicator
   - Lag: 0 days (coincident)
   - Best return: +0.99% (after fees)

2. **Whale Movements** (Day 9)
   - Type: On-chain data
   - Lag: +7 days (LEADING indicator!)
   - Return: -0.46% (destroyed by fees)
   - Insight: Predicts price but too noisy

3. **RSI** (Day 11)
   - Type: Technical indicator
   - Lag: 0 days (coincident)
   - Best return: +2.20% (CHAMPION!)
   - Insight: Best single indicator

4. **Google Trends** (Day 11)
   - Type: Retail sentiment
   - Lag: -4 days (lagging)
   - Return: +0.00% (no signals)
   - Insight: Useful as veto filter

### Combination Strategies (4 total)
1. **Simple Voting (3/4)** - Democratic, need 3/4 votes
   - Return: +1.20%
   - Best Sharpe: 2.285 ⭐
   - Best Sortino: 2.970 ⭐
   - Best risk-adjusted performance

2. **Unanimous (4/4)** - All must agree
   - Return: +0.00%
   - Too conservative (0 trades)

3. **Weighted Voting (4/6)** - RSI & F&G get 2 votes
   - Return: +1.57%
   - Great balance of returns and risk
   - 2 trades only

4. **Confidence Scoring** - Score 0-2 based on strength
   - Return: +1.00%
   - Elegant but underperformed

## Key Discoveries

### 1. Leading vs Coincident vs Lagging
**Leading (+7d):** Whale movements
- Predicts future but too noisy
- Needs filtering

**Coincident (0d):** RSI, Fear & Greed
- Best performers!
- Clean signals, good timing

**Lagging (-4d):** Google Trends
- Retail reacts AFTER price moves
- Confirms contrarian edge

### 2. Transaction Costs Matter
**0.1% fee per trade changed everything:**
- Whale: +0.02% → -0.46% (lost 24× profit to fees!)
- High-frequency trading doesn't work
- Quality > Quantity

### 3. Risk-Adjusted Metrics Reveal Truth
**Absolute Return Winner:** RSI (+2.20%)
**Risk-Adjusted Winner:** Simple Voting (Sharpe 2.285)

Different optimization goals = different winners

### 4. Best Strategy: Simple Voting (3/4)
**Why it won:**
- Best Sharpe Ratio: 2.285
- Best Sortino Ratio: 2.970
- Best Calmar Ratio: 0.698
- Lowest drawdown: -1.72%
- Only 1 trade = $3 fees
- Perfect balance of return and risk

## Performance Summary

### All 9 Strategies Tested

| Rank | Strategy | Return | Sharpe | Sortino | Calmar | Trades |
|------|----------|--------|--------|---------|--------|--------|
| 1 | RSI | +2.20% | 1.666 | 2.141 | 0.486 | 6 |
| 2 | Weighted Voting | +1.57% | 1.775 | 2.516 | 0.547 | 2 |
| 3 | **Simple Voting** | **+1.20%** | **2.285** | **2.970** | **0.698** | **1** |
| 4 | Confidence Scoring | +1.00% | 2.278 | 2.958 | 0.695 | 1 |
| 5 | Fear & Greed | +0.99% | 0.743 | 1.267 | 0.217 | 11 |
| 6 | Google Trends | +0.00% | 0.000 | 0.000 | 0.000 | 0 |
| 7 | Unanimous | +0.00% | 0.000 | 0.000 | 0.000 | 0 |
| 8 | Whale | -0.46% | -0.471 | -0.504 | -0.123 | 21 |
| 9 | Buy & Hold | -9.36% | -2.758 | -3.729 | -0.637 | 1 |

**ALL active strategies beat buy & hold!**

## Lessons Learned

### 1. More Trades ≠ Better
- Whale: 21 trades → Lost money
- Simple Voting: 1 trade → Best risk-adjusted return

### 2. Predictive Power ≠ Profitability
- Whale predicts 7 days ahead but lost money
- RSI is coincident but made +2.20%
- Execution quality > prediction horizon

### 3. Signal Quality > Signal Quantity
- Focus on high-confidence setups
- Wait for confirmation
- Minimize trading costs

### 4. Risk Metrics Change Everything
- Sharpe/Sortino/Calmar reveal true performance
- Absolute returns can be misleading
- Smooth equity curves = better sleep!

### 5. Combination Strategies Reduce Risk
- Top 3 Sharpe ratios: All combinations
- Top 3 Sortino ratios: All combinations
- Diversification works

## Week 2 Achievements

✅ Implemented 4 indicators (F&G, Whale, RSI, Trends)
✅ Analyzed lag correlations (found whale is leading!)
✅ Created 4 combination strategies
✅ Added transaction cost modeling (0.1% fees)
✅ Calculated advanced risk metrics (Sharpe, Sortino, Calmar)
✅ Backtested all 9 strategies comprehensively
✅ Identified best strategy (Simple Voting)
✅ Prepared ML-ready dataset with 40+ features

## Ready for Week 3: Machine Learning

### ML Dataset Prepared
- **Samples:** ~17 rows (31 days - 14 for warmup/lookahead)
- **Features:** 40+ engineered features
- **Target:** Binary (price up/down in 7 days)

### Feature Categories:
1. **Core Indicators:** F&G, RSI, Whale, Trends (normalized)
2. **Lag Features:** 1d, 3d, 7d historical values
3. **Momentum:** Price changes, indicator changes
4. **Rolling Stats:** Moving averages, volatility
5. **Signals:** Binary flags (oversold, overbought, etc.)
6. **Voting:** Vote counts from our strategies

### Week 3 Goals:
1. Train ML models (Random Forest, XGBoost, Neural Network)
2. Compare ML vs rule-based strategies
3. Feature importance analysis
4. Ensemble models
5. Production-ready system

## Files & Documentation

### Week 2 Structure:
```
scratchpad/week2/
├── day8/    - Week 1 analysis
├── day9/    - Whale movements
├── day10/   - Integration & correlation
├── day11/   - Google Trends + RSI
├── day12/   - Combination strategies
├── day13/   - Comprehensive backtest
└── day14/   - ML prep & documentation
```

### Key Outputs:
- Combined dataset with all indicators
- Strategy comparison results
- Risk metrics analysis
- ML-ready dataset
- Comprehensive documentation

## Next: Week 3 - Machine Learning Optimization

**Can ML beat our best rule-based strategy (Simple Voting)?**

We'll find out in Week 3!
"""

    return summary

def main():
    """Day 14 Main: Documentation & ML Prep"""
    print("=" * 60)
    print("DAY 14: DOCUMENTATION & ML PREPARATION")
    print("=" * 60)

    # Create output directory
    output_dir = Path('scratchpad/week2/day14')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    print("\n[1] Loading combined data...")
    df = load_combined_data()

    # 2. Prepare ML dataset
    print("\n[2] Preparing ML-ready dataset...")
    ml_df, features = prepare_ml_dataset(df)

    # 3. Print feature summary
    print_feature_summary(ml_df, features)

    # 4. Save ML dataset
    ml_path = output_dir / 'ml_ready_dataset.csv'
    ml_df.to_csv(ml_path, index=False)
    print(f"\n[OK] Saved ML dataset: {ml_path}")

    # Also save to root for Week 3
    root_ml_path = Path('ml_ready_dataset.csv')
    ml_df.to_csv(root_ml_path, index=False)
    print(f"[OK] Saved ML dataset (root): {root_ml_path}")

    # 5. Save feature list
    features_path = output_dir / 'feature_list.txt'
    with open(features_path, 'w') as f:
        f.write("ML Features (" + str(len(features)) + " total)\n")
        f.write("=" * 60 + "\n\n")
        for i, feat in enumerate(features, 1):
            f.write(f"{i}. {feat}\n")
    print(f"[OK] Saved feature list: {features_path}")

    # 6. Create Week 2 summary
    print("\n[3] Creating Week 2 summary...")
    summary = create_week2_summary()

    summary_path = output_dir / 'WEEK2_SUMMARY.md'
    with open(summary_path, 'w') as f:
        f.write(summary)
    print(f"[OK] Saved summary: {summary_path}")

    # Also save to week2 root
    week2_summary_path = Path('scratchpad/week2/WEEK2_SUMMARY.md')
    with open(week2_summary_path, 'w') as f:
        f.write(summary)
    print(f"[OK] Saved summary (week2): {week2_summary_path}")

    print("\n" + "=" * 60)
    print("DAY 14 COMPLETE - WEEK 2 FINISHED!")
    print("=" * 60)
    print()
    print("[DATA] ML dataset: ml_ready_dataset.csv")
    print(f"[DATA] Features: {len(features)} total")
    print(f"[DATA] Samples: {len(ml_df)} rows")
    print("[DOCS] Week 2 summary: scratchpad/week2/WEEK2_SUMMARY.md")
    print()
    print("=" * 60)
    print("READY FOR WEEK 3: MACHINE LEARNING!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Train ML models (Random Forest, XGBoost, Neural Net)")
    print("2. Compare ML vs rule-based strategies")
    print("3. Feature importance analysis")
    print("4. Build production-ready system")
    print()
    print("Can ML beat Simple Voting (Sharpe 2.285)?")
    print("Let's find out!")

if __name__ == "__main__":
    main()