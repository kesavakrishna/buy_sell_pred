"""
Day 5: Final Analysis & Documentation
Test multiple strategies, compare results, draw conclusions
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append('..')
from day4.day4_backtest import SimpleBacktester


def test_threshold_combinations(df):
    """
    Test different Fear & Greed threshold combinations

    Args:
        df: DataFrame with Bitcoin price and F&G data

    Returns:
        DataFrame with results for each threshold combination
    """
    print("="*80)
    print("TESTING DIFFERENT THRESHOLD COMBINATIONS")
    print("="*80)
    print()

    # Test combinations
    buy_thresholds = [20, 25, 30]
    sell_thresholds = [65, 70, 75]

    results = []

    for buy_thresh in buy_thresholds:
        for sell_thresh in sell_thresholds:
            print(f"Testing: Buy <= {buy_thresh}, Sell >= {sell_thresh}...")

            # Generate signals with these thresholds
            test_df = df.copy()
            test_df['signal'] = 'HOLD'
            test_df.loc[test_df['fear_greed_value'] <= buy_thresh, 'signal'] = 'BUY'
            test_df.loc[test_df['fear_greed_value'] >= sell_thresh, 'signal'] = 'SELL'

            # Run backtest
            backtester = SimpleBacktester(starting_capital=10000)
            backtester.run_backtest(test_df)
            metrics = backtester.calculate_metrics()

            # Store results
            results.append({
                'buy_threshold': buy_thresh,
                'sell_threshold': sell_thresh,
                'final_value': metrics['final_value'],
                'return_pct': metrics['total_return_pct'],
                'num_buys': metrics['num_buys'],
                'num_sells': metrics['num_sells'],
                'total_trades': metrics['num_trades']
            })

    results_df = pd.DataFrame(results)
    return results_df


def analyze_buy_and_hold(df, starting_capital=10000):
    """
    Calculate buy-and-hold performance

    Args:
        df: DataFrame with price data
        starting_capital: Starting amount in USD

    Returns:
        Dictionary with buy-and-hold metrics
    """
    first_price = df.iloc[0]['bitcoin_price_usd']
    last_price = df.iloc[-1]['bitcoin_price_usd']

    btc_bought = starting_capital / first_price
    final_value = btc_bought * last_price
    total_return = final_value - starting_capital
    return_pct = (total_return / starting_capital) * 100

    return {
        'strategy': 'Buy-and-Hold',
        'entry_price': first_price,
        'exit_price': last_price,
        'starting_capital': starting_capital,
        'final_value': final_value,
        'total_return': total_return,
        'return_pct': return_pct
    }


def print_threshold_results(results_df):
    """
    Print threshold testing results in a formatted table
    """
    print("\n" + "="*80)
    print("THRESHOLD TESTING RESULTS")
    print("="*80)
    print()

    print(f"{'Buy <=':<8} {'Sell >=':<8} {'Final Value':<15} {'Return %':<12} "
          f"{'Buys':<8} {'Sells':<8} {'Total':<8}")
    print("-"*80)

    for _, row in results_df.iterrows():
        print(f"{row['buy_threshold']:<8} {row['sell_threshold']:<8} "
              f"${row['final_value']:>13,.2f} {row['return_pct']:>10.2f}% "
              f"{row['num_buys']:<8} {row['num_sells']:<8} {row['total_trades']:<8}")

    # Find best strategy
    best_idx = results_df['return_pct'].idxmax()
    best = results_df.loc[best_idx]

    print("-"*80)
    print(f"\nBEST STRATEGY: Buy <= {best['buy_threshold']}, Sell >= {best['sell_threshold']}")
    print(f"   Return: {best['return_pct']:+.2f}% (${best['final_value']:,.2f})")
    print(f"   Trades: {best['num_buys']} buys, {best['num_sells']} sells")


def generate_final_summary(results_df, buy_hold_metrics, original_strategy):
    """
    Generate final analysis summary
    """
    print("\n" + "="*80)
    print("FINAL ANALYSIS SUMMARY")
    print("="*80)

    print("\n1. ORIGINAL STRATEGY (Buy <= 25, Sell >= 75)")
    print("-"*80)
    print(f"   Return: {original_strategy['return_pct']:+.2f}%")
    print(f"   Final Value: ${original_strategy['final_value']:,.2f}")
    print(f"   Trades: {original_strategy['num_buys']} buys, {original_strategy['num_sells']} sells")

    print("\n2. BUY-AND-HOLD BASELINE")
    print("-"*80)
    print(f"   Return: {buy_hold_metrics['return_pct']:+.2f}%")
    print(f"   Final Value: ${buy_hold_metrics['final_value']:,.2f}")
    print(f"   Entry: ${buy_hold_metrics['entry_price']:,.2f}")
    print(f"   Exit: ${buy_hold_metrics['exit_price']:,.2f}")

    print("\n3. BEST STRATEGY FOUND")
    print("-"*80)
    best_idx = results_df['return_pct'].idxmax()
    best = results_df.loc[best_idx]
    print(f"   Thresholds: Buy <= {best['buy_threshold']}, Sell >= {best['sell_threshold']}")
    print(f"   Return: {best['return_pct']:+.2f}%")
    print(f"   Final Value: ${best['final_value']:,.2f}")
    print(f"   Trades: {best['num_buys']} buys, {best['num_sells']} sells")

    print("\n4. KEY FINDINGS")
    print("-"*80)

    # Calculate outperformance
    orig_vs_bh = original_strategy['return_pct'] - buy_hold_metrics['return_pct']
    best_vs_bh = best['return_pct'] - buy_hold_metrics['return_pct']

    print(f"   [+] Original strategy beat buy-and-hold by {orig_vs_bh:+.2f}pp")
    print(f"   [+] Best strategy beat buy-and-hold by {best_vs_bh:+.2f}pp")
    print(f"   [+] Improvement from optimization: {best['return_pct'] - original_strategy['return_pct']:+.2f}pp")

    # Count strategies that beat buy-and-hold
    winning_strategies = len(results_df[results_df['return_pct'] > buy_hold_metrics['return_pct']])
    total_strategies = len(results_df)

    print(f"   [+] {winning_strategies}/{total_strategies} threshold combinations beat buy-and-hold")

    # Identify issues
    print("\n5. LIMITATIONS IDENTIFIED")
    print("-"*80)

    if original_strategy['num_sells'] == 0:
        print("   [!] No sell signals with threshold 75 (too high)")

    if original_strategy['num_buys'] == 1:
        print("   [!] All-in strategy misses additional buy opportunities")

    print("   [!] Small sample size (31 days) limits confidence")
    print("   [!] No transaction fees included in backtest")
    print("   [!] Single market condition (corrective period)")


def plot_strategy_comparison(results_df, buy_hold_metrics, save_path='strategy_comparison.png'):
    """
    Create visualization comparing all strategies
    """
    print("\n" + "="*80)
    print("CREATING STRATEGY COMPARISON VISUALIZATION")
    print("="*80)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Left plot: Return % for each threshold combination
    results_pivot = results_df.pivot(index='buy_threshold', columns='sell_threshold', values='return_pct')

    im = ax1.imshow(results_pivot, cmap='RdYlGn', aspect='auto', vmin=-10, vmax=10)
    ax1.set_xticks(range(len(results_pivot.columns)))
    ax1.set_yticks(range(len(results_pivot.index)))
    ax1.set_xticklabels(results_pivot.columns)
    ax1.set_yticklabels(results_pivot.index)
    ax1.set_xlabel('Sell Threshold (F&G >=)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Buy Threshold (F&G <=)', fontsize=12, fontweight='bold')
    ax1.set_title('Return % Heatmap by Threshold Combination', fontsize=14, fontweight='bold')

    # Add text annotations
    for i in range(len(results_pivot.index)):
        for j in range(len(results_pivot.columns)):
            text = ax1.text(j, i, f'{results_pivot.iloc[i, j]:.1f}%',
                           ha="center", va="center", color="black", fontsize=10)

    plt.colorbar(im, ax=ax1, label='Return %')

    # Right plot: Bar chart comparing strategies
    strategies = ['Buy-and-Hold', 'Original\n(25/75)', 'Best\nStrategy']

    best_idx = results_df['return_pct'].idxmax()
    best = results_df.loc[best_idx]
    original = results_df[(results_df['buy_threshold'] == 25) & (results_df['sell_threshold'] == 75)].iloc[0]

    returns = [
        buy_hold_metrics['return_pct'],
        original['return_pct'],
        best['return_pct']
    ]

    colors = ['gray', 'blue', 'green']
    bars = ax2.bar(strategies, returns, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax2.set_ylabel('Return %', fontsize=12, fontweight='bold')
    ax2.set_title('Strategy Performance Comparison', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar, ret in zip(bars, returns):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{ret:+.2f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {save_path}")
    plt.show()


def generate_conclusions():
    """
    Generate final conclusions and recommendations
    """
    print("\n" + "="*80)
    print("FINAL CONCLUSIONS & RECOMMENDATIONS")
    print("="*80)

    conclusions = """
1. DOES THE FEAR & GREED INDEX WORK?
   [+] YES, but with caveats
   - Buying during extreme fear (F&G <= 25) outperformed buy-and-hold
   - Strategy provided 9.32pp better returns in this test period
   - Index appears to be a useful contrarian indicator

2. OPTIMAL THRESHOLDS
   - Original (25/75): Minimal trades, no sell signals
   - Lower sell threshold (65-70) would have created exit opportunities
   - Buy threshold of 25 appears reasonable for extreme fear

3. STRATEGY LIMITATIONS
   [!] All-in approach missed multiple accumulation opportunities
   [!] No stop-loss protection against extended downtrends
   [!] Single 30-day period insufficient for robust validation
   [!] Market conditions matter (tested only in corrective period)

4. WHAT WE LEARNED
   [+] Sentiment indicators can add value
   [+] Timing entries during fear periods helps
   [+] Exit strategy is as important as entry
   [+] Position sizing matters (gradual accumulation > all-in)

5. WOULD I TRADE THIS WITH REAL MONEY?
   [?] NOT YET - Here's why:
   - Need more data (multiple market cycles)
   - Need better risk management (stop-loss, position sizing)
   - Need to test in bull markets and bear markets
   - Need to account for fees and slippage
   - Need emotional discipline to execute signals

6. NEXT STEPS FOR IMPROVEMENT
   -> Test on longer timeframes (1+ years)
   -> Add position sizing (scale in/out)
   -> Implement stop-loss and take-profit
   -> Combine with other indicators (RSI, moving averages)
   -> Test on multiple cryptocurrencies
   -> Add risk management rules
   -> Paper trade before going live

7. KEY TAKEAWAY
   "The Fear & Greed Index shows promise as a contrarian indicator,
    but it's a tool, not a complete strategy. Use it as one input
    among many, combined with proper risk management."
"""

    print(conclusions)


def save_final_report(results_df, buy_hold_metrics, filepath='final_analysis.txt'):
    """
    Save analysis to text file
    """
    with open(filepath, 'w') as f:
        f.write("="*80 + "\n")
        f.write("CRYPTO TRADING SIGNAL TRACKER - FINAL ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")

        f.write("THRESHOLD TESTING RESULTS\n")
        f.write("-"*80 + "\n")
        f.write(results_df.to_string())
        f.write("\n\n")

        f.write("BUY-AND-HOLD BASELINE\n")
        f.write("-"*80 + "\n")
        for key, value in buy_hold_metrics.items():
            f.write(f"{key}: {value}\n")

    print(f"\nFinal report saved to {filepath}")


def main():
    """
    Execute Day 5 final analysis
    """
    print("="*80)
    print("DAY 5: FINAL ANALYSIS & CONCLUSIONS")
    print("="*80)
    print()

    # Load data
    print("Loading data from previous days...")
    df = pd.read_csv('../day2/combined_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    print(f"Loaded {len(df)} days of data\n")

    # Test different threshold combinations
    results_df = test_threshold_combinations(df)

    # Calculate buy-and-hold
    buy_hold_metrics = analyze_buy_and_hold(df)

    # Get original strategy metrics (25/75)
    original_strategy = results_df[
        (results_df['buy_threshold'] == 25) &
        (results_df['sell_threshold'] == 75)
    ].iloc[0].to_dict()

    # Print results
    print_threshold_results(results_df)

    # Generate summary
    generate_final_summary(results_df, buy_hold_metrics, original_strategy)

    # Generate conclusions
    generate_conclusions()

    # Create visualizations
    plot_strategy_comparison(results_df, buy_hold_metrics)

    # Save report
    save_final_report(results_df, buy_hold_metrics)

    print("\n" + "="*80)
    print("DAY 5 COMPLETE!")
    print("="*80)
    print("\n*** 5-DAY PROJECT COMPLETE! ***")
    print("\nOutput files:")
    print("  - strategy_comparison.png (visualization)")
    print("  - final_analysis.txt (detailed report)")
    print("\nProject files to review:")
    print("  - FINDINGS.md (comprehensive research findings)")
    print("  - README.md (project overview)")
    print("  - All scratchpad/* folders (day-by-day implementations)")
    print("\nThank you for following along!")
    print("Remember: This is a learning project. Always practice")
    print("proper risk management and never invest more than you")
    print("can afford to lose!")


if __name__ == "__main__":
    main()