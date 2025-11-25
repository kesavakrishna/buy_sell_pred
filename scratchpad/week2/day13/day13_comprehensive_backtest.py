"""
Day 13: Comprehensive Backtest with Risk Metrics
Test all 9 strategies with transaction costs and advanced risk metrics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Import strategy classes from Day 12
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'day12')))

from day12_combination_strategies import (
    SimpleVotingStrategy,
    UnanimousStrategy,
    WeightedVotingStrategy,
    ConfidenceScoringStrategy
)

def load_combined_data():
    """Load combined dataset with all 4 indicators"""
    path = 'scratchpad/week2/day11/combined_with_rsi_trends.csv'
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    print(f"[OK] Loaded combined data: {len(df)} days")
    return df

class RealisticBacktester:
    """
    Enhanced backtester with transaction costs and risk metrics
    """

    def __init__(self, starting_capital=10000, fee_rate=0.001):
        """
        Args:
            starting_capital: Starting capital in USD
            fee_rate: Transaction fee rate (0.001 = 0.1%)
        """
        self.starting_capital = starting_capital
        self.fee_rate = fee_rate
        self.capital = starting_capital
        self.btc_holdings = 0
        self.trades = []
        self.portfolio_values = []

    def execute_buy(self, price, amount_usd, date, signal_info=None):
        """Execute BUY with fees"""
        fee = amount_usd * self.fee_rate
        net_amount = amount_usd - fee
        btc_bought = net_amount / price

        self.btc_holdings += btc_bought
        self.capital -= amount_usd

        self.trades.append({
            'date': date,
            'action': 'BUY',
            'price': price,
            'gross_amount': amount_usd,
            'fee': fee,
            'net_amount': net_amount,
            'btc': btc_bought,
            'signal_info': signal_info
        })

        return btc_bought

    def execute_sell(self, price, btc_amount, date, signal_info=None):
        """Execute SELL with fees"""
        gross_proceeds = btc_amount * price
        fee = gross_proceeds * self.fee_rate
        net_proceeds = gross_proceeds - fee

        self.btc_holdings -= btc_amount
        self.capital += net_proceeds

        self.trades.append({
            'date': date,
            'action': 'SELL',
            'price': price,
            'btc': btc_amount,
            'gross_amount': gross_proceeds,
            'fee': fee,
            'net_amount': net_proceeds,
            'signal_info': signal_info
        })

        return net_proceeds

    def record_portfolio_value(self, date, price):
        """Record portfolio value for tracking"""
        total_value = self.capital + (self.btc_holdings * price)
        self.portfolio_values.append({
            'date': date,
            'value': total_value,
            'price': price
        })

    def calculate_metrics(self, df):
        """Calculate comprehensive performance metrics"""
        if not self.portfolio_values:
            return self._empty_metrics()

        # Convert to DataFrame
        portfolio_df = pd.DataFrame(self.portfolio_values)

        # Calculate returns
        final_value = portfolio_df['value'].iloc[-1]
        total_return = ((final_value / self.starting_capital) - 1) * 100

        # Buy & hold comparison
        price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'
        initial_price = df[price_col].iloc[0]
        final_price = df[price_col].iloc[-1]
        buy_hold_return = ((final_price / initial_price) - 1) * 100

        # Calculate daily returns
        portfolio_df['daily_return'] = portfolio_df['value'].pct_change()
        daily_returns = portfolio_df['daily_return'].dropna()

        # Sharpe Ratio (annualized, assuming 0% risk-free rate)
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(365)
        else:
            sharpe = 0

        # Sortino Ratio (only penalizes downside volatility)
        downside_returns = daily_returns[daily_returns < 0]
        if len(downside_returns) > 1 and downside_returns.std() > 0:
            sortino = (daily_returns.mean() / downside_returns.std()) * np.sqrt(365)
        else:
            sortino = 0

        # Max Drawdown
        portfolio_df['cummax'] = portfolio_df['value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['cummax']) / portfolio_df['cummax'] * 100
        max_drawdown = portfolio_df['drawdown'].min()

        # Calmar Ratio (return / abs(max_drawdown))
        if max_drawdown != 0:
            calmar = total_return / abs(max_drawdown)
        else:
            calmar = 0

        # Win/Loss metrics
        if self.trades:
            # Calculate P&L for each trade
            buy_prices = {}
            wins = []
            losses = []

            for trade in self.trades:
                if trade['action'] == 'BUY':
                    buy_prices[trade['date']] = trade['price']
                elif trade['action'] == 'SELL' and buy_prices:
                    # Match with most recent buy
                    buy_price = list(buy_prices.values())[-1]
                    pnl_pct = ((trade['price'] - buy_price) / buy_price) * 100

                    if pnl_pct > 0:
                        wins.append(pnl_pct)
                    else:
                        losses.append(abs(pnl_pct))

            win_rate = len(wins) / (len(wins) + len(losses)) * 100 if (wins or losses) else 0
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            win_loss_ratio = 0

        # Total fees paid
        total_fees = sum(t['fee'] for t in self.trades)

        # Net return (after fees)
        net_return = total_return

        return {
            'final_value': final_value,
            'total_return': total_return,
            'net_return': net_return,
            'buy_hold_return': buy_hold_return,
            'vs_buy_hold': total_return - buy_hold_return,
            'num_trades': len(self.trades),
            'total_fees': total_fees,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'win_loss_ratio': win_loss_ratio,
            'final_btc': self.btc_holdings,
            'final_cash': self.capital
        }

    def _empty_metrics(self):
        """Return empty metrics for strategies with no trades"""
        return {
            'final_value': self.starting_capital,
            'total_return': 0,
            'net_return': 0,
            'buy_hold_return': 0,
            'vs_buy_hold': 0,
            'num_trades': 0,
            'total_fees': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'calmar_ratio': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'win_loss_ratio': 0,
            'final_btc': 0,
            'final_cash': self.starting_capital
        }

def backtest_single_indicator(df, indicator_name, starting_capital=10000, fee_rate=0.001):
    """
    Backtest a single indicator strategy with fees

    Indicator strategies from previous days:
    - Fear & Greed: Day 6 enhanced strategy
    - Whale: Day 9 strategy
    - RSI: Day 11 strategy
    - Google Trends: Day 11 strategy
    """
    print(f"\n{'=' * 60}")
    print(f"BACKTESTING: {indicator_name}")
    print("=" * 60)

    backtester = RealisticBacktester(starting_capital, fee_rate)
    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    for idx, row in df.iterrows():
        price = row[price_col]
        if pd.isna(price) or price == 0:
            continue

        # Record portfolio value
        backtester.record_portfolio_value(row['date'], price)

        # Generate signals based on indicator
        if indicator_name == "Fear & Greed":
            fg = row.get('fear_greed_value', 50)
            if fg <= 20:
                position_size = 0.5
                signal = 'STRONG_BUY'
            elif fg <= 25:
                position_size = 0.25
                signal = 'BUY'
            elif fg <= 30:
                position_size = 0.1
                signal = 'WEAK_BUY'
            elif fg >= 80:
                position_size = 0.5
                signal = 'STRONG_SELL'
            elif fg >= 75:
                position_size = 0.25
                signal = 'SELL'
            elif fg >= 70:
                position_size = 0.1
                signal = 'WEAK_SELL'
            else:
                position_size = 0
                signal = 'HOLD'

            if position_size > 0 and fg <= 30 and backtester.capital > 0:
                amount = backtester.capital * position_size
                backtester.execute_buy(price, amount, row['date'], f"F&G={fg:.0f}")
            elif position_size > 0 and fg >= 70 and backtester.btc_holdings > 0:
                btc_to_sell = backtester.btc_holdings * position_size
                backtester.execute_sell(price, btc_to_sell, row['date'], f"F&G={fg:.0f}")

        elif indicator_name == "Whale":
            whale_signal = row.get('signal', 'NEUTRAL')
            if whale_signal == 'ACCUMULATION' and backtester.capital > 0:
                amount = backtester.capital * 0.5
                backtester.execute_buy(price, amount, row['date'], whale_signal)
            elif whale_signal == 'DISTRIBUTION' and backtester.btc_holdings > 0:
                btc_to_sell = backtester.btc_holdings * 0.5
                backtester.execute_sell(price, btc_to_sell, row['date'], whale_signal)

        elif indicator_name == "RSI":
            rsi = row.get('rsi', 50)
            if pd.notna(rsi):
                if rsi < 25:
                    position_size = 0.5
                elif rsi < 30:
                    position_size = 0.25
                elif rsi > 75:
                    position_size = 0.5
                elif rsi > 70:
                    position_size = 0.25
                else:
                    position_size = 0

                if position_size > 0 and rsi < 30 and backtester.capital > 0:
                    amount = backtester.capital * position_size
                    backtester.execute_buy(price, amount, row['date'], f"RSI={rsi:.1f}")
                elif position_size > 0 and rsi > 70 and backtester.btc_holdings > 0:
                    btc_to_sell = backtester.btc_holdings * position_size
                    backtester.execute_sell(price, btc_to_sell, row['date'], f"RSI={rsi:.1f}")

        elif indicator_name == "Google Trends":
            trends_ratio = row.get('trends_ratio', 1.0)
            if pd.notna(trends_ratio):
                if trends_ratio > 2.0:
                    position_size = 0.5
                elif trends_ratio > 1.5:
                    position_size = 0.25
                elif trends_ratio < 0.3:
                    position_size = 0.5
                elif trends_ratio < 0.5:
                    position_size = 0.25
                else:
                    position_size = 0

                if position_size > 0 and trends_ratio < 0.5 and backtester.capital > 0:
                    amount = backtester.capital * position_size
                    backtester.execute_buy(price, amount, row['date'], f"Ratio={trends_ratio:.2f}")
                elif position_size > 0 and trends_ratio > 1.5 and backtester.btc_holdings > 0:
                    btc_to_sell = backtester.btc_holdings * position_size
                    backtester.execute_sell(price, btc_to_sell, row['date'], f"Ratio={trends_ratio:.2f}")

    # Calculate metrics
    metrics = backtester.calculate_metrics(df)
    metrics['strategy'] = indicator_name

    print(f"\nFinal Value: ${metrics['final_value']:,.2f}")
    print(f"Total Return: {metrics['total_return']:+.2f}%")
    print(f"Number of Trades: {metrics['num_trades']}")
    print(f"Total Fees: ${metrics['total_fees']:.2f}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.3f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Calmar Ratio: {metrics['calmar_ratio']:.3f}")

    return metrics

def backtest_combination_strategy(df, strategy, starting_capital=10000, fee_rate=0.001):
    """Backtest combination strategy with fees"""
    print(f"\n{'=' * 60}")
    print(f"BACKTESTING: {strategy.name}")
    print("=" * 60)

    backtester = RealisticBacktester(starting_capital, fee_rate)
    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    for idx, row in df.iterrows():
        price = row[price_col]
        if pd.isna(price) or price == 0:
            continue

        # Record portfolio value
        backtester.record_portfolio_value(row['date'], price)

        # Generate signal
        signal_data = strategy.generate_signal(row)
        signal = signal_data['signal']

        # Position sizing
        if isinstance(strategy, ConfidenceScoringStrategy):
            if 'STRONG' in signal:
                position_size = 0.5
            elif signal in ['BUY', 'SELL']:
                position_size = 0.25
            else:
                position_size = 0
        else:
            if 'STRONG' in signal:
                position_size = 0.5
            elif signal in ['BUY', 'SELL']:
                position_size = 0.3
            else:
                position_size = 0

        # Execute trades
        if 'BUY' in signal and backtester.capital > 0:
            amount = backtester.capital * position_size
            backtester.execute_buy(price, amount, row['date'], signal)
        elif 'SELL' in signal and backtester.btc_holdings > 0:
            btc_to_sell = backtester.btc_holdings * position_size
            backtester.execute_sell(price, btc_to_sell, row['date'], signal)

    # Calculate metrics
    metrics = backtester.calculate_metrics(df)
    metrics['strategy'] = strategy.name

    print(f"\nFinal Value: ${metrics['final_value']:,.2f}")
    print(f"Total Return: {metrics['total_return']:+.2f}%")
    print(f"Number of Trades: {metrics['num_trades']}")
    print(f"Total Fees: ${metrics['total_fees']:.2f}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.3f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Calmar Ratio: {metrics['calmar_ratio']:.3f}")

    return metrics

def backtest_buy_hold(df, starting_capital=10000):
    """Backtest buy and hold baseline"""
    print(f"\n{'=' * 60}")
    print("BACKTESTING: Buy & Hold")
    print("=" * 60)

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'
    initial_price = df[price_col].iloc[0]
    final_price = df[price_col].iloc[-1]

    btc_bought = starting_capital / initial_price
    final_value = btc_bought * final_price
    total_return = ((final_value / starting_capital) - 1) * 100

    # Calculate daily returns for risk metrics
    price_returns = df[price_col].pct_change().dropna()

    sharpe = (price_returns.mean() / price_returns.std()) * np.sqrt(365) if price_returns.std() > 0 else 0
    downside = price_returns[price_returns < 0]
    sortino = (price_returns.mean() / downside.std()) * np.sqrt(365) if len(downside) > 0 and downside.std() > 0 else 0

    # Max drawdown
    cummax = df[price_col].cummax()
    drawdown = (df[price_col] - cummax) / cummax * 100
    max_drawdown = drawdown.min()

    calmar = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

    metrics = {
        'strategy': 'Buy & Hold',
        'final_value': final_value,
        'total_return': total_return,
        'net_return': total_return,
        'buy_hold_return': total_return,
        'vs_buy_hold': 0,
        'num_trades': 1,
        'total_fees': 0,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar,
        'win_rate': 0,
        'avg_win': 0,
        'avg_loss': 0,
        'win_loss_ratio': 0,
        'final_btc': btc_bought,
        'final_cash': 0
    }

    print(f"\nFinal Value: ${metrics['final_value']:,.2f}")
    print(f"Total Return: {metrics['total_return']:+.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")

    return metrics

def create_comprehensive_comparison(all_metrics):
    """Create comprehensive comparison table"""
    comparison = pd.DataFrame(all_metrics)

    # Sort by total return
    comparison = comparison.sort_values('total_return', ascending=False)

    # Format for display
    display_df = pd.DataFrame({
        'Strategy': comparison['strategy'],
        'Return (%)': comparison['total_return'].apply(lambda x: f"{x:+.2f}%"),
        'vs B&H (pp)': comparison['vs_buy_hold'].apply(lambda x: f"{x:+.2f}pp"),
        'Trades': comparison['num_trades'],
        'Fees ($)': comparison['total_fees'].apply(lambda x: f"${x:.2f}"),
        'Sharpe': comparison['sharpe_ratio'].apply(lambda x: f"{x:.3f}"),
        'Sortino': comparison['sortino_ratio'].apply(lambda x: f"{x:.3f}"),
        'Calmar': comparison['calmar_ratio'].apply(lambda x: f"{x:.3f}"),
        'Max DD (%)': comparison['max_drawdown'].apply(lambda x: f"{x:.2f}%"),
        'Win Rate': comparison['win_rate'].apply(lambda x: f"{x:.1f}%" if x > 0 else "N/A")
    })

    return comparison, display_df

def main():
    """Day 13 Main: Comprehensive Backtest"""
    print("=" * 60)
    print("DAY 13: COMPREHENSIVE BACKTEST WITH RISK METRICS")
    print("=" * 60)

    # Create output directory
    output_dir = Path('scratchpad/week2/day13')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("\n[1] Loading combined data...")
    df = load_combined_data()

    # Test all strategies
    print("\n[2] Backtesting all strategies with 0.1% transaction fees...")

    all_metrics = []

    # Single indicators
    print("\n--- SINGLE INDICATORS ---")
    for indicator in ["Fear & Greed", "Whale", "RSI", "Google Trends"]:
        metrics = backtest_single_indicator(df, indicator)
        all_metrics.append(metrics)

    # Combination strategies
    print("\n--- COMBINATION STRATEGIES ---")
    strategies = [
        SimpleVotingStrategy(),
        UnanimousStrategy(),
        WeightedVotingStrategy(),
        ConfidenceScoringStrategy()
    ]

    for strategy in strategies:
        metrics = backtest_combination_strategy(df, strategy)
        all_metrics.append(metrics)

    # Buy & Hold baseline
    print("\n--- BASELINE ---")
    bh_metrics = backtest_buy_hold(df)
    all_metrics.append(bh_metrics)

    # Create comparison
    print("\n[3] Creating comprehensive comparison...")
    comparison, display_df = create_comprehensive_comparison(all_metrics)

    print("\n" + "=" * 60)
    print("COMPREHENSIVE COMPARISON (Sorted by Return)")
    print("=" * 60)
    print("\n" + display_df.to_string(index=False))

    # Find best strategies
    best_return = comparison.iloc[0]
    best_sharpe = comparison.loc[comparison['sharpe_ratio'].idxmax()]
    best_calmar = comparison.loc[comparison['calmar_ratio'].idxmax()]

    print("\n" + "=" * 60)
    print("BEST STRATEGIES")
    print("=" * 60)
    print(f"\nBest Return: {best_return['strategy']} ({best_return['total_return']:+.2f}%)")
    print(f"Best Sharpe: {best_sharpe['strategy']} ({best_sharpe['sharpe_ratio']:.3f})")
    print(f"Best Calmar: {best_calmar['strategy']} ({best_calmar['calmar_ratio']:.3f})")

    # Save results
    comparison.to_csv(output_dir / 'comprehensive_results.csv', index=False)
    print(f"\n[OK] Saved results: {output_dir / 'comprehensive_results.csv'}")

    print("\n" + "=" * 60)
    print("DAY 13 COMPLETE")
    print("=" * 60)
    print()
    print(f"[RESULTS] {output_dir / 'comprehensive_results.csv'}")
    print()
    print("Next: Day 14 - Documentation & ML Prep")

if __name__ == "__main__":
    main()