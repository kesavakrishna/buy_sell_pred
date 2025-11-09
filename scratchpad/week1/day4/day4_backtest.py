"""
Day 4: Simple Backtest
Simulate trading based on signals with $10,000 starting capital
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


# Backtest Configuration
STARTING_CAPITAL = 10000  # $10,000 fake money
POSITION_SIZE = 1.0       # Use 100% of available cash per trade (all-in strategy)


class SimpleBacktester:
    """
    Simple backtesting engine for crypto trading strategy

    Simulates buying when signal is BUY and selling when signal is SELL
    """

    def __init__(self, starting_capital=STARTING_CAPITAL):
        """
        Initialize backtester

        Args:
            starting_capital: Starting cash in USD
        """
        self.starting_capital = starting_capital
        self.cash = starting_capital
        self.btc_holdings = 0
        self.portfolio_value = starting_capital

        # Track history
        self.trades = []
        self.portfolio_history = []

    def execute_trade(self, date, price, signal, fg_value):
        """
        Execute a trade based on the signal

        Args:
            date: Trade date
            price: Bitcoin price
            signal: BUY, SELL, or HOLD
            fg_value: Fear & Greed value at this date
        """
        if signal == 'BUY' and self.cash > 0:
            # Buy BTC with all available cash
            btc_bought = self.cash / price

            trade = {
                'date': date,
                'type': 'BUY',
                'price': price,
                'btc_amount': btc_bought,
                'usd_amount': self.cash,
                'fear_greed': fg_value,
                'cash_before': self.cash,
                'btc_before': self.btc_holdings
            }

            self.btc_holdings += btc_bought
            self.cash = 0

            self.trades.append(trade)

        elif signal == 'SELL' and self.btc_holdings > 0:
            # Sell all BTC holdings
            usd_received = self.btc_holdings * price

            trade = {
                'date': date,
                'type': 'SELL',
                'price': price,
                'btc_amount': self.btc_holdings,
                'usd_amount': usd_received,
                'fear_greed': fg_value,
                'cash_before': self.cash,
                'btc_before': self.btc_holdings
            }

            self.cash += usd_received
            self.btc_holdings = 0

            self.trades.append(trade)

        # Calculate current portfolio value
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
        """
        Run backtest on signal data

        Args:
            df: DataFrame with columns: date, bitcoin_price_usd, signal, fear_greed_value
        """
        print("="*60)
        print("RUNNING BACKTEST")
        print("="*60)
        print(f"Starting Capital: ${self.starting_capital:,.2f}")
        print(f"Strategy: All-in (use 100% cash on BUY, sell 100% on SELL)")
        print(f"Period: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        print()

        for idx, row in df.iterrows():
            self.execute_trade(
                date=row['date'],
                price=row['bitcoin_price_usd'],
                signal=row['signal'],
                fg_value=row['fear_greed_value']
            )

        print(f"Backtest complete. Processed {len(df)} days.\n")

    def calculate_metrics(self):
        """
        Calculate performance metrics

        Returns:
            Dictionary with performance metrics
        """
        if len(self.trades) == 0:
            return {
                'total_return': 0,
                'total_return_pct': 0,
                'num_trades': 0,
                'num_buys': 0,
                'num_sells': 0,
                'win_rate': 0,
                'final_value': self.portfolio_value
            }

        # Count trades
        buys = [t for t in self.trades if t['type'] == 'BUY']
        sells = [t for t in self.trades if t['type'] == 'SELL']

        # Calculate win rate (only if we have complete buy-sell pairs)
        winning_trades = 0
        total_trades = 0

        for i in range(min(len(buys), len(sells))):
            buy_price = buys[i]['price']
            sell_price = sells[i]['price']

            if sell_price > buy_price:
                winning_trades += 1
            total_trades += 1

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Calculate returns
        total_return = self.portfolio_value - self.starting_capital
        total_return_pct = (total_return / self.starting_capital) * 100

        metrics = {
            'starting_capital': self.starting_capital,
            'final_value': self.portfolio_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'num_trades': len(self.trades),
            'num_buys': len(buys),
            'num_sells': len(sells),
            'win_rate': win_rate,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'total_pairs': total_trades
        }

        return metrics

    def print_trade_log(self):
        """
        Print all executed trades
        """
        print("="*60)
        print("TRADE LOG")
        print("="*60)

        if len(self.trades) == 0:
            print("No trades executed.")
            return

        print(f"\n{'Date':<12} {'Type':<6} {'BTC Amount':<15} {'Price':<12} {'USD Amount':<15} {'F&G':<5}")
        print("-"*80)

        for trade in self.trades:
            date_str = trade['date'].strftime('%Y-%m-%d')
            type_str = trade['type']
            btc_str = f"{trade['btc_amount']:.6f}"
            price_str = f"${trade['price']:,.2f}"
            usd_str = f"${trade['usd_amount']:,.2f}"
            fg_str = f"{trade['fear_greed']}"

            print(f"{date_str:<12} {type_str:<6} {btc_str:<15} {price_str:<12} {usd_str:<15} {fg_str:<5}")

    def print_summary(self):
        """
        Print backtest summary with metrics
        """
        metrics = self.calculate_metrics()

        print("\n" + "="*60)
        print("BACKTEST RESULTS SUMMARY")
        print("="*60)

        print(f"\n{'Starting Capital:':<30} ${metrics['starting_capital']:>12,.2f}")
        print(f"{'Final Portfolio Value:':<30} ${metrics['final_value']:>12,.2f}")
        print(f"{'Total Return:':<30} ${metrics['total_return']:>+12,.2f}")
        print(f"{'Return %:':<30} {metrics['total_return_pct']:>+12.2f}%")

        print(f"\n{'Total Trades Executed:':<30} {metrics['num_trades']:>12}")
        print(f"{'  - Buy Orders:':<30} {metrics['num_buys']:>12}")
        print(f"{'  - Sell Orders:':<30} {metrics['num_sells']:>12}")

        print(f"\n{'Complete Trade Pairs:':<30} {metrics['total_pairs']:>12}")
        print(f"{'  - Winning Trades:':<30} {metrics['winning_trades']:>12}")
        print(f"{'  - Losing Trades:':<30} {metrics['losing_trades']:>12}")
        print(f"{'Win Rate:':<30} {metrics['win_rate']:>12.1f}%")

        # Calculate buy-and-hold comparison
        if len(self.portfolio_history) > 0:
            first_price = self.portfolio_history[0]['btc_price']
            last_price = self.portfolio_history[-1]['btc_price']
            buy_hold_return = ((last_price - first_price) / first_price) * 100
            buy_hold_value = self.starting_capital * (1 + buy_hold_return/100)

            print(f"\n{'='*60}")
            print("COMPARISON: Buy-and-Hold")
            print("="*60)
            print(f"{'Buy & Hold Return:':<30} {buy_hold_return:>+12.2f}%")
            print(f"{'Buy & Hold Final Value:':<30} ${buy_hold_value:>12,.2f}")
            print(f"{'Strategy Outperformance:':<30} {metrics['total_return_pct'] - buy_hold_return:>+12.2f}pp")


def plot_backtest_results(backtester, save_path='backtest_results.png'):
    """
    Create visualization of backtest results

    Args:
        backtester: SimpleBacktester instance with results
        save_path: Where to save the plot
    """
    print("\n" + "="*60)
    print("CREATING BACKTEST VISUALIZATION")
    print("="*60)

    df = pd.DataFrame(backtester.portfolio_history)

    if len(df) == 0:
        print("No data to plot.")
        return

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Top plot: Bitcoin Price with Buy/Sell markers
    ax1.plot(df['date'], df['btc_price'], color='blue', linewidth=2, label='Bitcoin Price')

    # Mark buy trades
    buy_trades = [t for t in backtester.trades if t['type'] == 'BUY']
    if buy_trades:
        buy_dates = [t['date'] for t in buy_trades]
        buy_prices = [t['price'] for t in buy_trades]
        ax1.scatter(buy_dates, buy_prices, color='green', s=200, marker='^',
                   zorder=5, label='BUY', edgecolors='darkgreen', linewidths=2)

    # Mark sell trades
    sell_trades = [t for t in backtester.trades if t['type'] == 'SELL']
    if sell_trades:
        sell_dates = [t['date'] for t in sell_trades]
        sell_prices = [t['price'] for t in sell_trades]
        ax1.scatter(sell_dates, sell_prices, color='red', s=200, marker='v',
                   zorder=5, label='SELL', edgecolors='darkred', linewidths=2)

    ax1.set_ylabel('Bitcoin Price (USD)', fontsize=12, fontweight='bold')
    ax1.set_title('Backtest: Bitcoin Price with Trade Execution', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Bottom plot: Portfolio Value over time
    ax2.plot(df['date'], df['portfolio_value'], color='purple', linewidth=2.5, label='Portfolio Value')
    ax2.axhline(y=backtester.starting_capital, color='gray', linestyle='--',
                alpha=0.7, linewidth=1.5, label=f'Starting Capital (${backtester.starting_capital:,.0f})')

    # Fill area between portfolio value and starting capital
    ax2.fill_between(df['date'], backtester.starting_capital, df['portfolio_value'],
                     where=(df['portfolio_value'] >= backtester.starting_capital),
                     color='green', alpha=0.2, label='Profit')
    ax2.fill_between(df['date'], backtester.starting_capital, df['portfolio_value'],
                     where=(df['portfolio_value'] < backtester.starting_capital),
                     color='red', alpha=0.2, label='Loss')

    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Portfolio Value (USD)', fontsize=12, fontweight='bold')
    ax2.set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(True, alpha=0.3)

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {save_path}")

    plt.show()


def save_results_to_csv(backtester, filepath='backtest_results.csv'):
    """
    Save backtest results to CSV

    Args:
        backtester: SimpleBacktester instance
        filepath: Where to save the CSV
    """
    df = pd.DataFrame(backtester.portfolio_history)
    df.to_csv(filepath, index=False)
    print(f"Backtest results saved to {filepath}")


def main():
    """
    Main function to execute Day 4 backtest
    """
    print("="*60)
    print("DAY 4: SIMPLE BACKTEST")
    print("="*60)
    print()

    # Load signals from Day 3
    print("Loading signals from Day 3...")
    df = pd.read_csv('../day3/signals_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    print(f"Loaded {len(df)} days of signal data\n")

    # Initialize backtester
    backtester = SimpleBacktester(starting_capital=STARTING_CAPITAL)

    # Run backtest
    backtester.run_backtest(df)

    # Print trade log
    backtester.print_trade_log()

    # Print summary
    backtester.print_summary()

    # Save results
    save_results_to_csv(backtester)

    # Create visualization
    plot_backtest_results(backtester)

    print("\n" + "="*60)
    print("DAY 4 COMPLETE!")
    print("="*60)
    print("\nOutput files:")
    print("  - backtest_results.csv (portfolio history)")
    print("  - backtest_results.png (visualization)")
    print("\nNext steps:")
    print("  - Day 5: Analyze results and document findings")
    print("  - Test different strategies (position sizing, thresholds)")
    print("  - Add more sophisticated metrics (Sharpe ratio, drawdown)")


if __name__ == "__main__":
    main()