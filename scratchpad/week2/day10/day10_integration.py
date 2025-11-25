"""
Day 10: Integration & Correlation Analysis
Merge all datasets and analyze correlations including lag analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_bitcoin_and_fg_data():
    """Load Bitcoin + Fear & Greed data from Week 1"""
    # Try both scratchpad locations (Week 1 structure)
    paths = [
        'scratchpad/day2/combined_data.csv',
        'scratchpad/week1/day2/combined_data.csv'
    ]

    for path in paths:
        try:
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date']).dt.date
            print(f"[OK] Loaded Bitcoin + F&G data from: {path}")
            return df
        except FileNotFoundError:
            continue

    raise FileNotFoundError(
        "Could not find combined_data.csv. Please run Day 2 script first."
    )

def load_whale_data():
    """Load whale movement data from Day 9"""
    path = 'scratchpad/week2/day9/whale_data_30days.csv'
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date']).dt.date
    print(f"[OK] Loaded whale data from: {path}")
    return df

def merge_all_datasets(btc_df, whale_df):
    """
    Merge all indicators into one DataFrame

    Args:
        btc_df: Bitcoin + Fear & Greed DataFrame
        whale_df: Whale movements DataFrame

    Returns:
        Combined DataFrame with all indicators
    """
    # Ensure date columns are the same type
    btc_df['date'] = pd.to_datetime(btc_df['date']).dt.date
    whale_df['date'] = pd.to_datetime(whale_df['date']).dt.date

    # Merge on date (left join to keep all Bitcoin dates)
    combined = btc_df.merge(whale_df, on='date', how='left')

    # Fill missing whale data with neutral values
    combined['signal'] = combined['signal'].fillna('NEUTRAL')
    combined['net_flow'] = combined['net_flow'].fillna(0)
    combined['net_flow_millions'] = combined['net_flow_millions'].fillna(0)
    combined['total_volume'] = combined['total_volume'].fillna(0)
    combined['num_transactions'] = combined['num_transactions'].fillna(0)

    print(f"\n[OK] Merged datasets: {len(combined)} days")
    print(f"Columns: {list(combined.columns)}")

    return combined

def analyze_standard_correlation(df):
    """
    Analyze correlation between indicators (same-day)

    Args:
        df: Combined DataFrame with all indicators

    Returns:
        Correlation matrix
    """
    print("\n" + "=" * 60)
    print("STANDARD CORRELATION ANALYSIS")
    print("=" * 60)

    # Select relevant numeric columns
    # Use the correct column name from the combined data
    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    indicators = df[[price_col, 'fear_greed_value', 'net_flow_millions']].copy()
    indicators.columns = ['Price', 'Fear & Greed', 'Whale Net Flow (M)']

    # Calculate correlation
    correlation = indicators.corr()

    print("\nCorrelation Matrix:")
    print(correlation)

    # Create heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0,
                fmt='.3f', square=True, linewidths=1)
    plt.title('Indicator Correlation Matrix (Same Day)', fontsize=14, fontweight='bold')
    plt.tight_layout()

    return correlation

def analyze_lag_correlation(df, indicator_col, indicator_name, max_lag=7):
    """
    Analyze correlation at different time lags
    This reveals if an indicator LEADS or LAGS price movements

    Args:
        df: Combined DataFrame
        indicator_col: Name of indicator column
        indicator_name: Display name for indicator
        max_lag: Maximum lag in days to test (default 7)

    Returns:
        Dictionary of lag -> correlation values
    """
    print(f"\n{'=' * 60}")
    print(f"LAG CORRELATION: {indicator_name}")
    print("=" * 60)

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    # Test both directions: -max_lag to +max_lag
    lags = range(-max_lag, max_lag + 1)
    correlations = {}

    for lag in lags:
        # Positive lag: indicator shifted forward (indicator predicts future price)
        # Negative lag: indicator shifted backward (indicator lags behind price)
        correlations[lag] = df[price_col].corr(df[indicator_col].shift(lag))

    # Find best correlation
    best_lag = max(correlations.items(), key=lambda x: abs(x[1]))

    print(f"\nBest correlation: {best_lag[1]:.3f} at lag {best_lag[0]} days")

    if best_lag[0] > 0:
        print(f"-> {indicator_name} PREDICTS price {best_lag[0]} days ahead")
    elif best_lag[0] < 0:
        print(f"-> {indicator_name} LAGS behind price by {abs(best_lag[0])} days")
    else:
        print(f"-> {indicator_name} moves WITH price (same day)")

    # Plot lag correlation
    plt.figure(figsize=(10, 6))
    plt.plot(list(correlations.keys()), list(correlations.values()),
             marker='o', linewidth=2, markersize=6)
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    plt.xlabel('Lag (days)', fontsize=12)
    plt.ylabel('Correlation', fontsize=12)
    plt.title(f'{indicator_name} Correlation at Different Lags',
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)

    # Add annotation for best lag
    plt.annotate(f'Best: {best_lag[0]}d ({best_lag[1]:.3f})',
                xy=(best_lag[0], best_lag[1]),
                xytext=(best_lag[0] + 1, best_lag[1] + 0.05),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10, color='red', fontweight='bold')

    plt.tight_layout()

    return correlations

def backtest_whale_only(df, starting_capital=10000):
    """
    Backtest using ONLY whale signals

    Args:
        df: Combined DataFrame with whale data
        starting_capital: Starting capital in USD

    Returns:
        Dictionary with backtest results
    """
    print("\n" + "=" * 60)
    print("WHALE-ONLY BACKTEST")
    print("=" * 60)

    capital = starting_capital
    btc_holdings = 0
    trades = []

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    for idx, row in df.iterrows():
        signal = row.get('signal', 'NEUTRAL')
        price = row[price_col]

        if pd.isna(price) or price == 0:
            continue

        # BUY on ACCUMULATION signal
        if signal == 'ACCUMULATION' and capital > 0:
            # Buy 50% of available capital
            amount_to_invest = capital * 0.5
            btc_bought = amount_to_invest / price
            btc_holdings += btc_bought
            capital -= amount_to_invest

            trades.append({
                'date': row['date'],
                'action': 'BUY',
                'price': price,
                'amount': btc_bought,
                'usd_amount': amount_to_invest,
                'signal_strength': row.get('strength', 'UNKNOWN')
            })

        # SELL on DISTRIBUTION signal
        elif signal == 'DISTRIBUTION' and btc_holdings > 0:
            # Sell 50% of holdings
            btc_to_sell = btc_holdings * 0.5
            usd_received = btc_to_sell * price
            btc_holdings -= btc_to_sell
            capital += usd_received

            trades.append({
                'date': row['date'],
                'action': 'SELL',
                'price': price,
                'amount': btc_to_sell,
                'usd_amount': usd_received,
                'signal_strength': row.get('strength', 'UNKNOWN')
            })

    # Calculate final value
    final_price = df[price_col].iloc[-1]
    final_value = capital + (btc_holdings * final_price)
    total_return = ((final_value / starting_capital) - 1) * 100

    # Buy & hold comparison
    initial_price = df[price_col].iloc[0]
    buy_hold_btc = starting_capital / initial_price
    buy_hold_final = buy_hold_btc * final_price
    buy_hold_return = ((buy_hold_final / starting_capital) - 1) * 100

    results = {
        'final_value': final_value,
        'total_return': total_return,
        'num_trades': len(trades),
        'trades': trades,
        'final_btc': btc_holdings,
        'final_cash': capital,
        'buy_hold_return': buy_hold_return,
        'vs_buy_hold': total_return - buy_hold_return
    }

    print(f"\nStarting Capital: ${starting_capital:,.2f}")
    print(f"Final Value: ${final_value:,.2f}")
    print(f"Total Return: {total_return:+.2f}%")
    print(f"Number of Trades: {len(trades)}")
    print(f"Final BTC Holdings: {btc_holdings:.6f}")
    print(f"Final Cash: ${capital:,.2f}")
    print(f"\nBuy & Hold Return: {buy_hold_return:+.2f}%")
    print(f"Strategy vs B&H: {total_return - buy_hold_return:+.2f}pp")

    if len(trades) > 0:
        print(f"\nTRADE LOG:")
        for trade in trades:
            print(f"  {trade['date']} {trade['action']:4s} {trade['amount']:.6f} BTC @ "
                  f"${trade['price']:,.0f} (${trade['usd_amount']:,.0f}) [{trade['signal_strength']}]")

    return results

def backtest_fg_only(df, starting_capital=10000):
    """
    Backtest using ONLY Fear & Greed signals (for comparison)
    Using Day 6 enhanced strategy thresholds

    Args:
        df: Combined DataFrame with F&G data
        starting_capital: Starting capital in USD

    Returns:
        Dictionary with backtest results
    """
    print("\n" + "=" * 60)
    print("FEAR & GREED ONLY BACKTEST")
    print("=" * 60)

    capital = starting_capital
    btc_holdings = 0
    trades = []

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    for idx, row in df.iterrows():
        fg = row['fear_greed_value']
        price = row[price_col]

        if pd.isna(price) or pd.isna(fg) or price == 0:
            continue

        # Generate F&G signal (7-tier system from Day 6)
        if fg <= 20:
            position_size = 0.5  # STRONG_BUY
        elif fg <= 25:
            position_size = 0.25  # BUY
        elif fg <= 30:
            position_size = 0.1  # WEAK_BUY
        elif fg >= 80:
            position_size = 0.5  # STRONG_SELL
        elif fg >= 75:
            position_size = 0.25  # SELL
        elif fg >= 70:
            position_size = 0.1  # WEAK_SELL
        else:
            position_size = 0  # HOLD

        # Execute BUY
        if position_size > 0 and fg <= 30 and capital > 0:
            amount_to_invest = capital * position_size
            btc_bought = amount_to_invest / price
            btc_holdings += btc_bought
            capital -= amount_to_invest

            trades.append({
                'date': row['date'],
                'action': 'BUY',
                'price': price,
                'amount': btc_bought,
                'usd_amount': amount_to_invest,
                'fg_value': fg
            })

        # Execute SELL
        elif position_size > 0 and fg >= 70 and btc_holdings > 0:
            btc_to_sell = btc_holdings * position_size
            usd_received = btc_to_sell * price
            btc_holdings -= btc_to_sell
            capital += usd_received

            trades.append({
                'date': row['date'],
                'action': 'SELL',
                'price': price,
                'amount': btc_to_sell,
                'usd_amount': usd_received,
                'fg_value': fg
            })

    # Calculate final value
    final_price = df[price_col].iloc[-1]
    final_value = capital + (btc_holdings * final_price)
    total_return = ((final_value / starting_capital) - 1) * 100

    # Buy & hold comparison
    initial_price = df[price_col].iloc[0]
    buy_hold_btc = starting_capital / initial_price
    buy_hold_final = buy_hold_btc * final_price
    buy_hold_return = ((buy_hold_final / starting_capital) - 1) * 100

    results = {
        'final_value': final_value,
        'total_return': total_return,
        'num_trades': len(trades),
        'trades': trades,
        'final_btc': btc_holdings,
        'final_cash': capital,
        'buy_hold_return': buy_hold_return,
        'vs_buy_hold': total_return - buy_hold_return
    }

    print(f"\nStarting Capital: ${starting_capital:,.2f}")
    print(f"Final Value: ${final_value:,.2f}")
    print(f"Total Return: {total_return:+.2f}%")
    print(f"Number of Trades: {len(trades)}")
    print(f"Final BTC Holdings: {btc_holdings:.6f}")
    print(f"Final Cash: ${capital:,.2f}")
    print(f"\nBuy & Hold Return: {buy_hold_return:+.2f}%")
    print(f"Strategy vs B&H: {total_return - buy_hold_return:+.2f}pp")

    if len(trades) > 0:
        print(f"\nTRADE LOG:")
        for trade in trades[:10]:  # Show first 10 trades
            print(f"  {trade['date']} {trade['action']:4s} {trade['amount']:.6f} BTC @ "
                  f"${trade['price']:,.0f} (${trade['usd_amount']:,.0f}) [F&G={trade['fg_value']}]")
        if len(trades) > 10:
            print(f"  ... and {len(trades) - 10} more trades")

    return results

def compare_strategies(whale_results, fg_results):
    """
    Compare Whale vs Fear & Greed performance

    Args:
        whale_results: Whale-only backtest results
        fg_results: Fear & Greed only backtest results

    Returns:
        Comparison summary
    """
    print("\n" + "=" * 60)
    print("STRATEGY COMPARISON: WHALE vs FEAR & GREED")
    print("=" * 60)

    comparison = pd.DataFrame({
        'Metric': [
            'Final Value',
            'Total Return (%)',
            'vs Buy & Hold (pp)',
            'Number of Trades',
            'Avg Return per Trade (%)'
        ],
        'Whale Only': [
            f"${whale_results['final_value']:,.2f}",
            f"{whale_results['total_return']:+.2f}%",
            f"{whale_results['vs_buy_hold']:+.2f}pp",
            whale_results['num_trades'],
            f"{whale_results['total_return'] / max(whale_results['num_trades'], 1):.2f}%" if whale_results['num_trades'] > 0 else "N/A"
        ],
        'Fear & Greed': [
            f"${fg_results['final_value']:,.2f}",
            f"{fg_results['total_return']:+.2f}%",
            f"{fg_results['vs_buy_hold']:+.2f}pp",
            fg_results['num_trades'],
            f"{fg_results['total_return'] / max(fg_results['num_trades'], 1):.2f}%" if fg_results['num_trades'] > 0 else "N/A"
        ]
    })

    print("\n" + comparison.to_string(index=False))

    # Determine winner
    print("\n" + "=" * 60)
    if whale_results['total_return'] > fg_results['total_return']:
        winner = 'Whale'
        diff = whale_results['total_return'] - fg_results['total_return']
        print(f"WINNER: Whale signals (+{diff:.2f}pp better)")
    else:
        winner = 'Fear & Greed'
        diff = fg_results['total_return'] - whale_results['total_return']
        print(f"WINNER: Fear & Greed signals (+{diff:.2f}pp better)")
    print("=" * 60)

    return comparison

def main():
    """Day 10 Main: Integration & Correlation Analysis"""
    print("=" * 60)
    print("DAY 10: INTEGRATION & CORRELATION ANALYSIS")
    print("=" * 60)

    # Create output directory
    output_dir = Path('scratchpad/week2/day10')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load all datasets
    print("\n[1] Loading datasets...")
    btc_df = load_bitcoin_and_fg_data()
    whale_df = load_whale_data()

    # 2. Merge datasets
    print("\n[2] Merging datasets...")
    combined_df = merge_all_datasets(btc_df, whale_df)

    # Save combined dataset
    combined_path = output_dir / 'combined_data.csv'
    combined_df.to_csv(combined_path, index=False)
    print(f"[OK] Saved combined dataset: {combined_path}")

    # 3. Standard correlation analysis
    print("\n[3] Analyzing standard correlations...")
    correlation_matrix = analyze_standard_correlation(combined_df)

    # Save correlation heatmap
    plt.savefig(output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"[OK] Saved correlation heatmap: {output_dir / 'correlation_heatmap.png'}")

    # 4. Lag correlation analysis
    print("\n[4] Analyzing lag correlations...")

    # Fear & Greed lag analysis
    fg_lag_corr = analyze_lag_correlation(
        combined_df,
        'fear_greed_value',
        'Fear & Greed Index',
        max_lag=7
    )
    plt.savefig(output_dir / 'fg_lag_correlation.png', dpi=300, bbox_inches='tight')

    # Whale lag analysis
    whale_lag_corr = analyze_lag_correlation(
        combined_df,
        'net_flow_millions',
        'Whale Net Flow',
        max_lag=7
    )
    plt.savefig(output_dir / 'whale_lag_correlation.png', dpi=300, bbox_inches='tight')

    print(f"[OK] Saved lag correlation charts")

    # 5. Independent backtests
    print("\n[5] Running independent backtests...")
    whale_results = backtest_whale_only(combined_df, starting_capital=10000)
    fg_results = backtest_fg_only(combined_df, starting_capital=10000)

    # 6. Compare strategies
    print("\n[6] Comparing strategies...")
    comparison = compare_strategies(whale_results, fg_results)

    # Save comparison
    comparison.to_csv(output_dir / 'strategy_comparison.csv', index=False)
    print(f"[OK] Saved comparison: {output_dir / 'strategy_comparison.csv'}")

    print("\n" + "=" * 60)
    print("DAY 10 COMPLETE")
    print("=" * 60)
    print()
    print(f"[DATA] Combined dataset: {combined_path}")
    print(f"[CHARTS] Correlation heatmap: {output_dir / 'correlation_heatmap.png'}")
    print(f"[CHARTS] F&G lag correlation: {output_dir / 'fg_lag_correlation.png'}")
    print(f"[CHARTS] Whale lag correlation: {output_dir / 'whale_lag_correlation.png'}")
    print(f"[RESULTS] Strategy comparison: {output_dir / 'strategy_comparison.csv'}")
    print()
    print("Next: Day 11 - Add Google Trends + RSI")

if __name__ == "__main__":
    main()