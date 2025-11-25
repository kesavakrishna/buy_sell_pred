"""
Day 12: Multi-Indicator Signal Combination
Implement and test 4 different combination strategies
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_combined_data():
    """Load combined dataset with all 4 indicators from Day 11"""
    path = 'scratchpad/week2/day11/combined_with_rsi_trends.csv'
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    print(f"[OK] Loaded combined data from Day 11: {len(df)} days")
    print(f"[OK] Indicators available: Fear & Greed, Whale, RSI, Google Trends")
    return df

class SimpleVotingStrategy:
    """
    Strategy A: Simple Voting (need 3/4 votes)
    Each indicator votes BUY/SELL/NEUTRAL
    """

    def __init__(self):
        self.name = "Simple Voting (3/4)"

    def generate_signal(self, row):
        """
        Generate signal based on majority voting

        Args:
            row: DataFrame row with all indicators

        Returns:
            dict with signal and vote breakdown
        """
        votes = {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0}
        vote_details = {}

        # Fear & Greed vote
        fg = row.get('fear_greed_value', 50)
        if fg < 25:
            votes['BUY'] += 1
            vote_details['fg'] = 'BUY'
        elif fg > 75:
            votes['SELL'] += 1
            vote_details['fg'] = 'SELL'
        else:
            votes['NEUTRAL'] += 1
            vote_details['fg'] = 'NEUTRAL'

        # Whale vote
        whale_signal = row.get('signal', 'NEUTRAL')
        if whale_signal == 'ACCUMULATION':
            votes['BUY'] += 1
            vote_details['whale'] = 'BUY'
        elif whale_signal == 'DISTRIBUTION':
            votes['SELL'] += 1
            vote_details['whale'] = 'SELL'
        else:
            votes['NEUTRAL'] += 1
            vote_details['whale'] = 'NEUTRAL'

        # RSI vote
        rsi = row.get('rsi', 50)
        if pd.notna(rsi):
            if rsi < 30:
                votes['BUY'] += 1
                vote_details['rsi'] = 'BUY'
            elif rsi > 70:
                votes['SELL'] += 1
                vote_details['rsi'] = 'SELL'
            else:
                votes['NEUTRAL'] += 1
                vote_details['rsi'] = 'NEUTRAL'
        else:
            votes['NEUTRAL'] += 1
            vote_details['rsi'] = 'NEUTRAL'

        # Google Trends vote (contrarian)
        trends_ratio = row.get('trends_ratio', 1.0)
        if pd.notna(trends_ratio):
            if trends_ratio < 0.5:  # Low search = undervalued
                votes['BUY'] += 1
                vote_details['trends'] = 'BUY'
            elif trends_ratio > 1.5:  # High search = FOMO
                votes['SELL'] += 1
                vote_details['trends'] = 'SELL'
            else:
                votes['NEUTRAL'] += 1
                vote_details['trends'] = 'NEUTRAL'
        else:
            votes['NEUTRAL'] += 1
            vote_details['trends'] = 'NEUTRAL'

        # Need 3/4 votes for signal
        if votes['BUY'] >= 3:
            signal = 'BUY'
        elif votes['SELL'] >= 3:
            signal = 'SELL'
        else:
            signal = 'HOLD'

        return {
            'signal': signal,
            'votes': votes,
            'details': vote_details
        }

class UnanimousStrategy:
    """
    Strategy B: Unanimous (all 4 must agree)
    Very conservative - only acts when all indicators align
    """

    def __init__(self):
        self.name = "Unanimous (4/4)"

    def generate_signal(self, row):
        """Generate signal only when all 4 indicators agree"""
        votes = {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0}

        # Fear & Greed vote
        fg = row.get('fear_greed_value', 50)
        if fg < 25:
            votes['BUY'] += 1
        elif fg > 75:
            votes['SELL'] += 1
        else:
            votes['NEUTRAL'] += 1

        # Whale vote
        whale_signal = row.get('signal', 'NEUTRAL')
        if whale_signal == 'ACCUMULATION':
            votes['BUY'] += 1
        elif whale_signal == 'DISTRIBUTION':
            votes['SELL'] += 1
        else:
            votes['NEUTRAL'] += 1

        # RSI vote
        rsi = row.get('rsi', 50)
        if pd.notna(rsi):
            if rsi < 30:
                votes['BUY'] += 1
            elif rsi > 70:
                votes['SELL'] += 1
            else:
                votes['NEUTRAL'] += 1
        else:
            votes['NEUTRAL'] += 1

        # Google Trends vote
        trends_ratio = row.get('trends_ratio', 1.0)
        if pd.notna(trends_ratio):
            if trends_ratio < 0.5:
                votes['BUY'] += 1
            elif trends_ratio > 1.5:
                votes['SELL'] += 1
            else:
                votes['NEUTRAL'] += 1
        else:
            votes['NEUTRAL'] += 1

        # Need 4/4 votes for signal (unanimous)
        if votes['BUY'] == 4:
            signal = 'STRONG_BUY'
        elif votes['SELL'] == 4:
            signal = 'STRONG_SELL'
        else:
            signal = 'HOLD'

        return {
            'signal': signal,
            'votes': votes
        }

class WeightedVotingStrategy:
    """
    Strategy C: Weighted Voting
    RSI and Fear & Greed get 2 votes each (best performers)
    Whale and Trends get 1 vote each
    Total: 6 votes, need 4/6 for signal
    """

    def __init__(self):
        self.name = "Weighted Voting (4/6)"

    def generate_signal(self, row):
        """Generate signal with weighted votes"""
        buy_votes = 0
        sell_votes = 0

        # Fear & Greed: 2 votes (proven performer)
        fg = row.get('fear_greed_value', 50)
        if fg < 25:
            buy_votes += 2
        elif fg > 75:
            sell_votes += 2

        # RSI: 2 votes (best single indicator)
        rsi = row.get('rsi', 50)
        if pd.notna(rsi):
            if rsi < 30:
                buy_votes += 2
            elif rsi > 70:
                sell_votes += 2

        # Whale: 1 vote (predictive but noisy)
        whale_signal = row.get('signal', 'NEUTRAL')
        if whale_signal == 'ACCUMULATION':
            buy_votes += 1
        elif whale_signal == 'DISTRIBUTION':
            sell_votes += 1

        # Google Trends: 1 vote (sentiment filter)
        trends_ratio = row.get('trends_ratio', 1.0)
        if pd.notna(trends_ratio):
            if trends_ratio < 0.5:
                buy_votes += 1
            elif trends_ratio > 1.5:
                sell_votes += 1

        # Need 4/6 votes for signal
        if buy_votes >= 4:
            signal = 'BUY'
        elif sell_votes >= 4:
            signal = 'SELL'
        else:
            signal = 'HOLD'

        return {
            'signal': signal,
            'buy_votes': buy_votes,
            'sell_votes': sell_votes,
            'total_possible': 6
        }

class ConfidenceScoringStrategy:
    """
    Strategy D: Confidence Scoring
    Each indicator scores 0-2 based on signal strength
    Combines scores for overall confidence
    Uses confidence for position sizing
    """

    def __init__(self):
        self.name = "Confidence Scoring"

    def generate_signal(self, row):
        """Generate signal with confidence scoring"""
        scores = {'BUY': 0, 'SELL': 0}
        breakdown = {}

        # Fear & Greed (weighted by extremity)
        fg = row.get('fear_greed_value', 50)
        if fg <= 20:
            scores['BUY'] += 2  # Strong
            breakdown['fg'] = 'STRONG_BUY'
        elif fg <= 25:
            scores['BUY'] += 1  # Moderate
            breakdown['fg'] = 'BUY'
        elif fg >= 80:
            scores['SELL'] += 2
            breakdown['fg'] = 'STRONG_SELL'
        elif fg >= 75:
            scores['SELL'] += 1
            breakdown['fg'] = 'SELL'
        else:
            breakdown['fg'] = 'NEUTRAL'

        # RSI (weighted by extremity)
        rsi = row.get('rsi', 50)
        if pd.notna(rsi):
            if rsi < 25:
                scores['BUY'] += 2
                breakdown['rsi'] = 'STRONG_BUY'
            elif rsi < 30:
                scores['BUY'] += 1
                breakdown['rsi'] = 'BUY'
            elif rsi > 75:
                scores['SELL'] += 2
                breakdown['rsi'] = 'STRONG_SELL'
            elif rsi > 70:
                scores['SELL'] += 1
                breakdown['rsi'] = 'SELL'
            else:
                breakdown['rsi'] = 'NEUTRAL'
        else:
            breakdown['rsi'] = 'NEUTRAL'

        # Whale (weighted by volume)
        whale_flow = row.get('net_flow_millions', 0)
        if whale_flow > 20:
            scores['BUY'] += 2
            breakdown['whale'] = 'STRONG_ACCUMULATION'
        elif whale_flow > 10:
            scores['BUY'] += 1
            breakdown['whale'] = 'ACCUMULATION'
        elif whale_flow < -20:
            scores['SELL'] += 2
            breakdown['whale'] = 'STRONG_DISTRIBUTION'
        elif whale_flow < -10:
            scores['SELL'] += 1
            breakdown['whale'] = 'DISTRIBUTION'
        else:
            breakdown['whale'] = 'NEUTRAL'

        # Google Trends (contrarian with strength)
        trends_ratio = row.get('trends_ratio', 1.0)
        if pd.notna(trends_ratio):
            if trends_ratio > 2.0:
                scores['SELL'] += 2  # Extreme FOMO
                breakdown['trends'] = 'EXTREME_FOMO'
            elif trends_ratio > 1.5:
                scores['SELL'] += 1  # Moderate FOMO
                breakdown['trends'] = 'FOMO'
            elif trends_ratio < 0.3:
                scores['BUY'] += 2  # Extreme undervalued
                breakdown['trends'] = 'EXTREME_UNDERVALUED'
            elif trends_ratio < 0.5:
                scores['BUY'] += 1  # Moderate undervalued
                breakdown['trends'] = 'UNDERVALUED'
            else:
                breakdown['trends'] = 'NEUTRAL'
        else:
            breakdown['trends'] = 'NEUTRAL'

        # Determine signal with confidence (max score: 8)
        max_score = 8

        if scores['BUY'] >= 5:
            signal = 'STRONG_BUY'
            confidence = scores['BUY'] / max_score
        elif scores['BUY'] >= 3:
            signal = 'BUY'
            confidence = scores['BUY'] / max_score
        elif scores['SELL'] >= 5:
            signal = 'STRONG_SELL'
            confidence = scores['SELL'] / max_score
        elif scores['SELL'] >= 3:
            signal = 'SELL'
            confidence = scores['SELL'] / max_score
        else:
            signal = 'HOLD'
            confidence = 0

        return {
            'signal': signal,
            'confidence': confidence,
            'buy_score': scores['BUY'],
            'sell_score': scores['SELL'],
            'breakdown': breakdown
        }

def backtest_strategy(df, strategy, starting_capital=10000):
    """
    Backtest a combination strategy

    Args:
        df: DataFrame with all indicators
        strategy: Strategy instance
        starting_capital: Starting capital in USD

    Returns:
        Dictionary with backtest results
    """
    print(f"\n{'=' * 60}")
    print(f"BACKTESTING: {strategy.name}")
    print("=" * 60)

    capital = starting_capital
    btc_holdings = 0
    trades = []

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    for idx, row in df.iterrows():
        price = row[price_col]

        if pd.isna(price) or price == 0:
            continue

        # Generate signal from strategy
        signal_data = strategy.generate_signal(row)
        signal = signal_data['signal']

        # Determine position size
        if isinstance(strategy, ConfidenceScoringStrategy):
            # Use confidence for position sizing
            confidence = signal_data['confidence']
            if 'STRONG' in signal:
                position_size = 0.5  # 50%
            elif signal in ['BUY', 'SELL']:
                position_size = 0.25  # 25%
            else:
                position_size = 0
        else:
            # Standard position sizing
            if 'STRONG' in signal:
                position_size = 0.5
            elif signal in ['BUY', 'SELL']:
                position_size = 0.3
            else:
                position_size = 0

        # Execute BUY
        if 'BUY' in signal and capital > 0:
            amount_to_invest = capital * position_size
            btc_bought = amount_to_invest / price
            btc_holdings += btc_bought
            capital -= amount_to_invest

            trade_info = {
                'date': row['date'],
                'action': 'BUY',
                'price': price,
                'amount': btc_bought,
                'usd_amount': amount_to_invest,
                'signal': signal
            }

            # Add strategy-specific details
            if isinstance(strategy, SimpleVotingStrategy):
                trade_info['votes'] = signal_data['votes']['BUY']
            elif isinstance(strategy, WeightedVotingStrategy):
                trade_info['votes'] = f"{signal_data['buy_votes']}/6"
            elif isinstance(strategy, ConfidenceScoringStrategy):
                trade_info['confidence'] = f"{signal_data['confidence']:.2f}"
                trade_info['score'] = signal_data['buy_score']

            trades.append(trade_info)

        # Execute SELL
        elif 'SELL' in signal and btc_holdings > 0:
            btc_to_sell = btc_holdings * position_size
            usd_received = btc_to_sell * price
            btc_holdings -= btc_to_sell
            capital += usd_received

            trade_info = {
                'date': row['date'],
                'action': 'SELL',
                'price': price,
                'amount': btc_to_sell,
                'usd_amount': usd_received,
                'signal': signal
            }

            if isinstance(strategy, SimpleVotingStrategy):
                trade_info['votes'] = signal_data['votes']['SELL']
            elif isinstance(strategy, WeightedVotingStrategy):
                trade_info['votes'] = f"{signal_data['sell_votes']}/6"
            elif isinstance(strategy, ConfidenceScoringStrategy):
                trade_info['confidence'] = f"{signal_data['confidence']:.2f}"
                trade_info['score'] = signal_data['sell_score']

            trades.append(trade_info)

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
        'strategy': strategy.name,
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
        print(f"\nTRADE LOG (first 5):")
        for trade in trades[:5]:
            extra = ""
            if 'votes' in trade:
                extra = f" [{trade['votes']} votes]"
            elif 'confidence' in trade:
                extra = f" [conf={trade['confidence']}, score={trade['score']}]"

            print(f"  {trade['date']} {trade['action']:4s} {trade['amount']:.6f} BTC @ "
                  f"${trade['price']:,.0f} (${trade['usd_amount']:,.0f}){extra}")
        if len(trades) > 5:
            print(f"  ... and {len(trades) - 5} more trades")
    else:
        print("\nNo trades executed")

    return results

def compare_all_strategies(results_dict):
    """
    Compare all strategy results

    Args:
        results_dict: Dictionary of strategy_name -> results

    Returns:
        Comparison DataFrame
    """
    print("\n" + "=" * 60)
    print("ALL STRATEGIES COMPARISON")
    print("=" * 60)

    comparison = pd.DataFrame({
        'Strategy': list(results_dict.keys()),
        'Final Value': [f"${r['final_value']:,.2f}" for r in results_dict.values()],
        'Return (%)': [f"{r['total_return']:+.2f}%" for r in results_dict.values()],
        'vs B&H (pp)': [f"{r['vs_buy_hold']:+.2f}pp" for r in results_dict.values()],
        'Num Trades': [r['num_trades'] for r in results_dict.values()]
    })

    print("\n" + comparison.to_string(index=False))

    # Find best strategy
    best_strategy = max(results_dict.items(), key=lambda x: x[1]['total_return'])

    print("\n" + "=" * 60)
    print(f"BEST STRATEGY: {best_strategy[0]}")
    print(f"Return: {best_strategy[1]['total_return']:+.2f}%")
    print(f"Trades: {best_strategy[1]['num_trades']}")
    print("=" * 60)

    return comparison

def main():
    """Day 12 Main: Multi-Indicator Signal Combination"""
    print("=" * 60)
    print("DAY 12: MULTI-INDICATOR SIGNAL COMBINATION")
    print("=" * 60)

    # Create output directory
    output_dir = Path('scratchpad/week2/day12')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load combined data
    print("\n[1] Loading combined data with all indicators...")
    df = load_combined_data()

    # Initialize strategies
    print("\n[2] Initializing 4 combination strategies...")
    strategies = [
        SimpleVotingStrategy(),
        UnanimousStrategy(),
        WeightedVotingStrategy(),
        ConfidenceScoringStrategy()
    ]

    print(f"[OK] Initialized {len(strategies)} strategies:")
    for s in strategies:
        print(f"  - {s.name}")

    # Backtest all strategies
    print("\n[3] Backtesting all strategies...")
    all_results = {}

    for strategy in strategies:
        results = backtest_strategy(df, strategy, starting_capital=10000)
        all_results[strategy.name] = results

    # Compare all strategies
    print("\n[4] Comparing all strategies...")
    comparison = compare_all_strategies(all_results)

    # Save comparison
    comparison.to_csv(output_dir / 'combination_strategies_comparison.csv', index=False)
    print(f"\n[OK] Saved comparison: {output_dir / 'combination_strategies_comparison.csv'}")

    print("\n" + "=" * 60)
    print("DAY 12 COMPLETE")
    print("=" * 60)
    print()
    print(f"[RESULTS] Comparison: {output_dir / 'combination_strategies_comparison.csv'}")
    print()
    print("Next: Day 13 - Comprehensive Backtest with Risk Metrics")

if __name__ == "__main__":
    main()