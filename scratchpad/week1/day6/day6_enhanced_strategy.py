"""
Day 6: Enhanced Strategy with Neutral Zones & Position Sizing
Implement tiered F&G signals with graduated position sizing
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append('..')
from day4.day4_backtest import SimpleBacktester


class ScaledBacktester:
    """
    Enhanced backtester with tiered F&G signals and position sizing

    Signal Tiers:
    - STRONG BUY:  F&G 0-20   → Buy 50% of available cash
    - BUY:         F&G 21-25  → Buy 25% of available cash
    - WEAK BUY:    F&G 26-40  → Buy 10% of available cash
    - HOLD:        F&G 41-59  → Do nothing
    - WEAK SELL:   F&G 60-69  → Sell 25% of BTC holdings
    - SELL:        F&G 70-74  → Sell 50% of BTC holdings
    - STRONG SELL: F&G 75+    → Sell 100% of BTC holdings
    """

    def __init__(self, starting_capital=10000):
        """Initialize scaled backtester"""
        self.starting_capital = starting_capital
        self.cash = starting_capital
        self.btc_holdings = 0
        self.portfolio_value = starting_capital

        # Track history
        self.trades = []
        self.portfolio_history = []

    def get_signal_tier(self, fg_value):
        """
        Determine signal tier based on F&G value

        Returns: (signal, action_size)
        """
        if fg_value <= 20:
            return 'STRONG_BUY', 0.50
        elif fg_value <= 25:
            return 'BUY', 0.25
        elif fg_value <= 40:
            return 'WEAK_BUY', 0.10
        elif fg_value <= 59:
            return 'HOLD', 0.0
        elif fg_value <= 69:
            return 'WEAK_SELL', 0.25
        elif fg_value <= 74:
            return 'SELL', 0.50
        else:
            return 'STRONG_SELL', 1.0

    def execute_trade(self, date, price, fg_value):
        """
        Execute trade based on tiered signal

        Args:
            date: Trade date
            price: Bitcoin price
            fg_value: Fear & Greed value
        """
        signal, action_size = self.get_signal_tier(fg_value)

        # Execute BUY signals
        if 'BUY' in signal and self.cash > 0:
            # Buy percentage of available cash
            usd_to_spend = self.cash * action_size
            btc_bought = usd_to_spend / price

            trade = {
                'date': date,
                'type': signal,
                'price': price,
                'btc_amount': btc_bought,
                'usd_amount': usd_to_spend,
                'fear_greed': fg_value,
                'cash_before': self.cash,
                'btc_before': self.btc_holdings,
                'action_size': action_size
            }

            self.btc_holdings += btc_bought
            self.cash -= usd_to_spend
            self.trades.append(trade)

        # Execute SELL signals
        elif 'SELL' in signal and self.btc_holdings > 0:
            # Sell percentage of BTC holdings
            btc_to_sell = self.btc_holdings * action_size
            usd_received = btc_to_sell * price

            trade = {
                'date': date,
                'type': signal,
                'price': price,
                'btc_amount': btc_to_sell,
                'usd_amount': usd_received,
                'fear_greed': fg_value,
                'cash_before': self.cash,
                'btc_before': self.btc_holdings,
                'action_size': action_size
            }

            self.cash += usd_received
            self.btc_holdings -= btc_to_sell
            self.trades.append(trade)

        # Calculate portfolio value
        self.portfolio_value = self.cash + (self.btc_holdings * price)

        # Record portfolio state
        self.portfolio_history.append({
            'date': date,
            'cash': self.cash,
            'btc_holdings': self.btc_holdings,
            'btc_price': price,
            'portfolio_value': self.portfolio_value,
            'signal': signal,
            'fear_greed': fg_value
        })

    def run_backtest(self, df):
        """Run backtest on data with F&G values"""
        print("="*80)
        print("RUNNING SCALED BACKTEST")
        print("="*80)
        print(f"Starting Capital: ${self.starting_capital:,.2f}")
        print(f"Strategy: Tiered position sizing based on F&G strength")
        print(f"Period: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        print()

        for idx, row in df.iterrows():
            self.execute_trade(
                date=row['date'],
                price=row['bitcoin_price_usd'],
                fg_value=row['fear_greed_value']
            )

        print(f"Backtest complete. Processed {len(df)} days.\n")

    def calculate_metrics(self):
        """Calculate performance metrics"""
        if len(self.trades) == 0:
            return {
                'starting_capital': self.starting_capital,
                'final_value': self.portfolio_value,
                'total_return': 0,
                'total_return_pct': 0,
                'num_trades': 0,
                'num_buys': 0,
                'num_sells': 0
            }

        # Count trades by type
        buys = [t for t in self.trades if 'BUY' in t['type']]
        sells = [t for t in self.trades if 'SELL' in t['type']]

        # Calculate returns
        total_return = self.portfolio_value - self.starting_capital
        total_return_pct = (total_return / self.starting_capital) * 100

        # Calculate weighted average entry price
        total_btc_bought = sum(t['btc_amount'] for t in buys)
        total_usd_spent = sum(t['usd_amount'] for t in buys)
        avg_entry_price = total_usd_spent / total_btc_bought if total_btc_bought > 0 else 0

        return {
            'starting_capital': self.starting_capital,
            'final_value': self.portfolio_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'num_trades': len(self.trades),
            'num_buys': len(buys),
            'num_sells': len(sells),
            'avg_entry_price': avg_entry_price,
            'total_btc_bought': total_btc_bought,
            'final_cash': self.cash,
            'final_btc': self.btc_holdings
        }

    def print_trade_log(self):
        """Print all executed trades"""
        print("="*80)
        print("TRADE LOG")
        print("="*80)

        if len(self.trades) == 0:
            print("No trades executed.")
            return

        print(f"\n{'Date':<12} {'Signal':<15} {'BTC':<12} {'Price':<12} {'USD':<12} {'F&G':<5} {'Size':<6}")
        print("-"*85)

        for trade in self.trades:
            date_str = trade['date'].strftime('%Y-%m-%d')
            signal_str = trade['type']
            btc_str = f"{trade['btc_amount']:.6f}"
            price_str = f"${trade['price']:,.0f}"
            usd_str = f"${trade['usd_amount']:,.2f}"
            fg_str = str(trade['fear_greed'])
            size_str = f"{trade['action_size']:.0%}"

            print(f"{date_str:<12} {signal_str:<15} {btc_str:<12} {price_str:<12} {usd_str:<12} {fg_str:<5} {size_str:<6}")

    def print_summary(self):
        """Print backtest summary"""
        metrics = self.calculate_metrics()

        print("\n" + "="*80)
        print("SCALED BACKTEST RESULTS")
        print("="*80)

        print(f"\n{'Starting Capital:':<30} ${metrics['starting_capital']:>12,.2f}")
        print(f"{'Final Portfolio Value:':<30} ${metrics['final_value']:>12,.2f}")
        print(f"{'Total Return:':<30} ${metrics['total_return']:>+12,.2f}")
        print(f"{'Return %:':<30} {metrics['total_return_pct']:>+12.2f}%")

        print(f"\n{'Total Trades Executed:':<30} {metrics['num_trades']:>12}")
        print(f"{'  - Buy Orders:':<30} {metrics['num_buys']:>12}")
        print(f"{'  - Sell Orders:':<30} {metrics['num_sells']:>12}")

        if metrics['avg_entry_price'] > 0:
            print(f"\n{'Weighted Avg Entry Price:':<30} ${metrics['avg_entry_price']:>12,.2f}")
            print(f"{'Total BTC Accumulated:':<30} {metrics['total_btc_bought']:>12.6f}")

        print(f"\n{'Final Position:':<30}")
        print(f"{'  - Cash:':<30} ${metrics['final_cash']:>12,.2f}")
        print(f"{'  - BTC Holdings:':<30} {metrics['final_btc']:>12.6f}")


def compare_strategies(df):
    """
    Compare 3 strategies:
    1. Original (all-in at F&G <= 25)
    2. Enhanced (tiered position sizing)
    3. Buy-and-hold
    """
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)
    print()

    results = {}

    # Strategy 1: Original (all-in)
    print("1. Running ORIGINAL strategy (all-in at F&G <= 25)...")
    test_df = df.copy()
    test_df['signal'] = 'HOLD'
    test_df.loc[test_df['fear_greed_value'] <= 25, 'signal'] = 'BUY'
    test_df.loc[test_df['fear_greed_value'] >= 75, 'signal'] = 'SELL'

    original = SimpleBacktester(starting_capital=10000)
    original.run_backtest(test_df)
    results['original'] = original.calculate_metrics()

    # Strategy 2: Enhanced (scaled)
    print("\n2. Running ENHANCED strategy (tiered position sizing)...")
    enhanced = ScaledBacktester(starting_capital=10000)
    enhanced.run_backtest(df)
    results['enhanced'] = enhanced.calculate_metrics()

    # Strategy 3: Buy-and-hold
    print("\n3. Calculating BUY-AND-HOLD baseline...")
    first_price = df.iloc[0]['bitcoin_price_usd']
    last_price = df.iloc[-1]['bitcoin_price_usd']
    btc_bought = 10000 / first_price
    final_value = btc_bought * last_price
    results['buy_hold'] = {
        'starting_capital': 10000,
        'final_value': final_value,
        'total_return': final_value - 10000,
        'total_return_pct': ((final_value - 10000) / 10000) * 100,
        'num_trades': 0
    }

    return results, original, enhanced


def print_comparison_table(results):
    """Print formatted comparison table"""
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print()

    print(f"{'Strategy':<20} {'Final Value':<15} {'Return %':<12} {'Trades':<10} {'vs B&H':<10}")
    print("-"*80)

    bh_return = results['buy_hold']['total_return_pct']

    for name, label in [('buy_hold', 'Buy-and-Hold'), ('original', 'Original (All-in)'), ('enhanced', 'Enhanced (Scaled)')]:
        metrics = results[name]
        final = f"${metrics['final_value']:,.2f}"
        ret = f"{metrics['total_return_pct']:+.2f}%"
        trades = f"{metrics.get('num_trades', 0)}"
        vs_bh = f"{metrics['total_return_pct'] - bh_return:+.2f}pp"

        print(f"{label:<20} {final:<15} {ret:<12} {trades:<10} {vs_bh:<10}")

    print("-"*80)

    # Winner
    best = max(results.items(), key=lambda x: x[1]['total_return_pct'])
    improvement = results['enhanced']['total_return_pct'] - results['original']['total_return_pct']

    print(f"\nBest Strategy: {best[0].upper()}")
    print(f"Enhanced vs Original: {improvement:+.2f}pp")


def plot_strategy_comparison(results, original, enhanced, save_path='enhanced_comparison.png'):
    """Create visualization comparing strategies"""
    print("\n" + "="*80)
    print("CREATING COMPARISON VISUALIZATION")
    print("="*80)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Left: Bar chart comparison
    strategies = ['Buy-and-Hold', 'Original\n(All-in)', 'Enhanced\n(Scaled)']
    returns = [
        results['buy_hold']['total_return_pct'],
        results['original']['total_return_pct'],
        results['enhanced']['total_return_pct']
    ]

    colors = ['gray', 'blue', 'green']
    bars = ax1.bar(strategies, returns, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax1.set_ylabel('Return %', fontsize=12, fontweight='bold')
    ax1.set_title('Strategy Performance Comparison', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar, ret in zip(bars, returns):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{ret:+.2f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=11, fontweight='bold')

    # Right: Portfolio value over time
    orig_df = pd.DataFrame(original.portfolio_history)
    enh_df = pd.DataFrame(enhanced.portfolio_history)

    ax2.plot(orig_df['date'], orig_df['portfolio_value'],
             label='Original (All-in)', color='blue', linewidth=2, alpha=0.7)
    ax2.plot(enh_df['date'], enh_df['portfolio_value'],
             label='Enhanced (Scaled)', color='green', linewidth=2, alpha=0.7)
    ax2.axhline(y=10000, color='gray', linestyle='--', alpha=0.7,
                label='Starting Capital')

    # Mark trades on enhanced
    buy_trades = [t for t in enhanced.trades if 'BUY' in t['type']]
    sell_trades = [t for t in enhanced.trades if 'SELL' in t['type']]

    if buy_trades:
        buy_dates = [t['date'] for t in buy_trades]
        buy_values = [enh_df[enh_df['date'] == d]['portfolio_value'].values[0] for d in buy_dates]
        ax2.scatter(buy_dates, buy_values, color='green', s=100, marker='^',
                   zorder=5, alpha=0.8, edgecolors='darkgreen')

    if sell_trades:
        sell_dates = [t['date'] for t in sell_trades]
        sell_values = [enh_df[enh_df['date'] == d]['portfolio_value'].values[0] for d in sell_dates]
        ax2.scatter(sell_dates, sell_values, color='red', s=100, marker='v',
                   zorder=5, alpha=0.8, edgecolors='darkred')

    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Portfolio Value (USD)', fontsize=12, fontweight='bold')
    ax2.set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {save_path}")
    plt.show()


def save_comparison_csv(results, filepath='comparison_results.csv'):
    """Save comparison results to CSV"""
    rows = []
    for name, metrics in results.items():
        rows.append({
            'strategy': name,
            'final_value': metrics['final_value'],
            'return_pct': metrics['total_return_pct'],
            'num_trades': metrics.get('num_trades', 0)
        })

    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False)
    print(f"Results saved to {filepath}")


def main():
    """Execute Day 6 enhanced strategy analysis"""
    print("="*80)
    print("DAY 6: ENHANCED STRATEGY WITH NEUTRAL ZONES")
    print("="*80)
    print()

    # Load data
    print("Loading data from Day 2...")
    df = pd.read_csv('../day2/combined_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    print(f"Loaded {len(df)} days of data\n")

    # Compare strategies
    results, original, enhanced = compare_strategies(df)

    # Print trade logs
    print("\n" + "="*80)
    print("ORIGINAL STRATEGY TRADES")
    print("="*80)
    original.print_trade_log()

    print("\n" + "="*80)
    print("ENHANCED STRATEGY TRADES")
    print("="*80)
    enhanced.print_trade_log()

    # Print summaries
    original.print_summary()
    enhanced.print_summary()

    # Print comparison
    print_comparison_table(results)

    # Create visualization
    plot_strategy_comparison(results, original, enhanced)

    # Save results
    save_comparison_csv(results)

    print("\n" + "="*80)
    print("DAY 6 COMPLETE!")
    print("="*80)
    print("\nOutput files:")
    print("  - enhanced_comparison.png (visualization)")
    print("  - comparison_results.csv (results table)")
    print("\nKey Findings:")

    improvement = results['enhanced']['total_return_pct'] - results['original']['total_return_pct']
    print(f"  - Enhanced strategy improved by {improvement:+.2f}pp vs original")
    print(f"  - Enhanced executed {results['enhanced']['num_trades']} trades vs {results['original']['num_trades']}")

    if improvement > 0:
        print(f"  - VALIDATED: Position sizing improves performance!")
    else:
        print(f"  - INTERESTING: More trades didn't improve returns in this period")


if __name__ == "__main__":
    main()
