"""
Day 9: Add Whale Movements Indicator
Track large Bitcoin transactions to/from exchanges using WhaleAlert API

Whale Logic:
- Transfers TO exchanges = Bearish (whales might sell)
- Transfers FROM exchanges = Bullish (accumulation off exchanges)
- Net flow = from_exchange - to_exchange
- Positive net flow = ACCUMULATION (bullish)
- Negative net flow = DISTRIBUTION (bearish)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os

class WhaleTracker:
    """
    Track whale movements using WhaleAlert API

    Free tier: 10 calls/minute
    """

    def __init__(self, api_key=None):
        """
        Initialize whale tracker

        Args:
            api_key: WhaleAlert API key (if None, will try to load from .env)
        """
        self.api_key = api_key or self._load_api_key()
        self.base_url = "https://api.whale-alert.io/v1"

    def _load_api_key(self):
        """Load API key from .env file"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            key = os.getenv('WHALE_ALERT_API_KEY')
            if not key:
                print("[WARNING] No WHALE_ALERT_API_KEY found in .env")
                print("Sign up at: https://whale-alert.io/")
                print("For now, using demo mode with simulated data")
                return None
            return key
        except ImportError:
            print("[WARNING] python-dotenv not installed")
            return None

    def get_transactions(self, start_time, end_time, min_value=500000):
        """
        Get large BTC transactions from WhaleAlert

        Args:
            start_time: datetime object for start
            end_time: datetime object for end
            min_value: minimum USD value (default $500k)

        Returns:
            list of transaction dicts
        """
        if not self.api_key:
            # Demo mode - simulate whale transactions
            return self._simulate_transactions(start_time, end_time, min_value)

        url = f"{self.base_url}/transactions"
        params = {
            'api_key': self.api_key,
            'start': int(start_time.timestamp()),
            'end': int(end_time.timestamp()),
            'min_value': min_value,
            'currency': 'btc'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('result') == 'success':
                return data.get('transactions', [])
            else:
                print(f"[ERROR] API returned: {data.get('message', 'Unknown error')}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
            return []

    def _simulate_transactions(self, start_time, end_time, min_value):
        """
        Simulate whale transactions for demo purposes
        Based on typical exchange flow patterns
        """
        np.random.seed(int(start_time.timestamp()) % 10000)

        # Simulate 3-8 large transactions per day
        num_txs = np.random.randint(3, 9)
        transactions = []

        for _ in range(num_txs):
            # Random timestamp within the day
            random_seconds = np.random.randint(0, 86400)
            tx_time = start_time + timedelta(seconds=random_seconds)

            # Random transaction amount ($500k - $50M)
            amount_usd = np.random.uniform(min_value, 50_000_000)

            # 60% chance to exchange, 40% chance from exchange
            to_exchange = np.random.random() < 0.6

            # Simulate exchange names
            exchanges = ['binance', 'coinbase', 'kraken', 'bitfinex', 'okex']
            exchange_name = np.random.choice(exchanges)

            tx = {
                'timestamp': int(tx_time.timestamp()),
                'amount_usd': amount_usd,
                'from': {
                    'owner_type': 'exchange' if not to_exchange else 'unknown',
                    'owner': exchange_name if not to_exchange else None
                },
                'to': {
                    'owner_type': 'exchange' if to_exchange else 'unknown',
                    'owner': exchange_name if to_exchange else None
                }
            }
            transactions.append(tx)

        return transactions

    def calculate_whale_signal(self, transactions):
        """
        Analyze whale movements and generate signal

        Args:
            transactions: list of transaction dicts

        Returns:
            dict with analysis results
        """
        to_exchange = 0
        from_exchange = 0
        total_volume = 0
        num_to_exchange = 0
        num_from_exchange = 0

        for tx in transactions:
            amount = tx.get('amount_usd', 0)
            total_volume += amount

            # Check if destination is an exchange (bearish)
            if tx.get('to', {}).get('owner_type') == 'exchange':
                to_exchange += amount
                num_to_exchange += 1

            # Check if source is an exchange (bullish)
            if tx.get('from', {}).get('owner_type') == 'exchange':
                from_exchange += amount
                num_from_exchange += 1

        # Net flow: positive = accumulation (bullish), negative = distribution (bearish)
        net_flow = from_exchange - to_exchange

        # Determine signal based on net flow
        # Thresholds: $10M+ = strong signal
        if net_flow > 10_000_000:
            signal = 'ACCUMULATION'
            strength = 'STRONG'
        elif net_flow > 5_000_000:
            signal = 'ACCUMULATION'
            strength = 'MODERATE'
        elif net_flow < -10_000_000:
            signal = 'DISTRIBUTION'
            strength = 'STRONG'
        elif net_flow < -5_000_000:
            signal = 'DISTRIBUTION'
            strength = 'MODERATE'
        else:
            signal = 'NEUTRAL'
            strength = 'WEAK'

        return {
            'to_exchange': to_exchange,
            'from_exchange': from_exchange,
            'net_flow': net_flow,
            'total_volume': total_volume,
            'num_transactions': len(transactions),
            'num_to_exchange': num_to_exchange,
            'num_from_exchange': num_from_exchange,
            'signal': signal,
            'strength': strength,
            'net_flow_millions': net_flow / 1_000_000
        }

    def fetch_historical_whale_data(self, days=30, min_value=500000):
        """
        Fetch historical whale data with rate limiting

        Args:
            days: number of days to fetch
            min_value: minimum transaction value

        Returns:
            pandas DataFrame with daily aggregated whale data
        """
        print(f"\n[WHALE] Fetching {days} days of whale transaction data...")
        print(f"[WHALE] Min transaction value: ${min_value:,}")

        all_data = []

        for i in range(days):
            # Calculate date range for this day
            end_date = datetime.now() - timedelta(days=i)
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)

            # Fetch transactions for this day
            print(f"[WHALE] Fetching {start_date.strftime('%Y-%m-%d')}...", end='')
            transactions = self.get_transactions(start_date, end_date, min_value)

            # Analyze whale movements
            analysis = self.calculate_whale_signal(transactions)

            # Add date to analysis
            analysis['date'] = start_date.date()
            all_data.append(analysis)

            print(f" {len(transactions)} txs, {analysis['signal']} ({analysis['net_flow_millions']:+.1f}M)")

            # Rate limiting: 10 calls/min = 6 seconds between calls
            # Only sleep if not the last iteration
            if i < days - 1:
                if not self.api_key:
                    time.sleep(0.1)  # Fast for demo mode
                else:
                    time.sleep(6)  # Real rate limiting

        # Convert to DataFrame
        df = pd.DataFrame(all_data)

        # Sort by date (oldest first)
        df = df.sort_values('date').reset_index(drop=True)

        print(f"\n[OK] Fetched {len(df)} days of whale data")

        return df

    def backtest_whale_only(self, df, starting_capital=10000):
        """
        Backtest using ONLY whale signals

        Args:
            df: DataFrame with whale data and Bitcoin prices
            starting_capital: starting capital in USD

        Returns:
            dict with backtest results
        """
        capital = starting_capital
        btc_holdings = 0
        trades = []

        for idx, row in df.iterrows():
            signal = row['signal']
            price = row.get('bitcoin_price_usd', row.get('price', 0))

            if price == 0:
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
                    'signal_strength': row['strength']
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
                    'signal_strength': row['strength']
                })

        # Calculate final value
        final_price = df['bitcoin_price_usd'].iloc[-1] if 'bitcoin_price_usd' in df.columns else df['price'].iloc[-1]
        final_value = capital + (btc_holdings * final_price)
        total_return = ((final_value / starting_capital) - 1) * 100

        return {
            'final_value': final_value,
            'total_return': total_return,
            'num_trades': len(trades),
            'trades': trades,
            'final_btc': btc_holdings,
            'final_cash': capital
        }

def merge_with_bitcoin_data(whale_df, btc_csv_path='scratchpad/day2/combined_data.csv'):
    """
    Merge whale data with Bitcoin price data

    Args:
        whale_df: DataFrame with whale data
        btc_csv_path: path to combined Bitcoin + F&G data

    Returns:
        merged DataFrame
    """
    # Load Bitcoin data
    btc_df = pd.read_csv(btc_csv_path)
    btc_df['date'] = pd.to_datetime(btc_df['date']).dt.date

    # Ensure whale_df date is date type
    whale_df['date'] = pd.to_datetime(whale_df['date']).dt.date

    # Merge on date
    merged = btc_df.merge(whale_df, on='date', how='left')

    # Fill missing whale data with neutral
    merged['signal'] = merged['signal'].fillna('NEUTRAL')
    merged['net_flow'] = merged['net_flow'].fillna(0)
    merged['net_flow_millions'] = merged['net_flow_millions'].fillna(0)

    return merged

def save_whale_data(df, filename='scratchpad/week2/day9/whale_data_30days.csv'):
    """Save whale data to CSV"""
    df.to_csv(filename, index=False)
    print(f"[OK] Saved whale data to: {filename}")

def print_whale_summary(df):
    """Print summary statistics of whale data"""
    print("\n" + "=" * 60)
    print("WHALE DATA SUMMARY")
    print("=" * 60)
    print()
    print(f"Period: {df['date'].min()} to {df['date'].max()}")
    print(f"Total Days: {len(df)}")
    print()

    # Signal distribution
    signal_counts = df['signal'].value_counts()
    print("SIGNAL DISTRIBUTION:")
    for signal, count in signal_counts.items():
        pct = count / len(df) * 100
        print(f"  {signal}: {count} days ({pct:.1f}%)")
    print()

    # Net flow statistics
    print("NET FLOW STATISTICS:")
    print(f"  Average: ${df['net_flow'].mean():,.0f} ({df['net_flow_millions'].mean():+.1f}M)")
    print(f"  Max Inflow: ${df['net_flow'].max():,.0f} ({df['net_flow_millions'].max():+.1f}M)")
    print(f"  Max Outflow: ${df['net_flow'].min():,.0f} ({df['net_flow_millions'].min():+.1f}M)")
    print(f"  Std Dev: ${df['net_flow'].std():,.0f}")
    print()

    # Volume statistics
    print("VOLUME STATISTICS:")
    print(f"  Avg Daily Volume: ${df['total_volume'].mean():,.0f}")
    print(f"  Total Volume: ${df['total_volume'].sum():,.0f}")
    print(f"  Avg Transactions/Day: {df['num_transactions'].mean():.1f}")
    print()

    # Strongest signals
    strongest_accumulation = df[df['signal'] == 'ACCUMULATION'].nlargest(3, 'net_flow_millions')
    strongest_distribution = df[df['signal'] == 'DISTRIBUTION'].nsmallest(3, 'net_flow_millions')

    if len(strongest_accumulation) > 0:
        print("STRONGEST ACCUMULATION DAYS:")
        for _, row in strongest_accumulation.iterrows():
            print(f"  {row['date']}: {row['net_flow_millions']:+.1f}M ({row['strength']})")
        print()

    if len(strongest_distribution) > 0:
        print("STRONGEST DISTRIBUTION DAYS:")
        for _, row in strongest_distribution.iterrows():
            print(f"  {row['date']}: {row['net_flow_millions']:+.1f}M ({row['strength']})")
        print()

def main():
    """
    Day 9 Main: Fetch whale data and test whale-only strategy
    """
    print("=" * 60)
    print("DAY 9: ADD WHALE MOVEMENTS INDICATOR")
    print("=" * 60)

    # Initialize whale tracker
    print("\n[1] Initializing WhaleAlert tracker...")
    whale = WhaleTracker()

    # Fetch 30 days of historical data
    print("\n[2] Fetching 30 days of whale transaction data...")
    whale_df = whale.fetch_historical_whale_data(days=30, min_value=500000)

    # Print summary
    print_whale_summary(whale_df)

    # Save whale data
    print("\n[3] Saving whale data...")
    save_whale_data(whale_df)

    # Merge with Bitcoin data
    print("\n[4] Merging with Bitcoin price data...")
    try:
        combined_df = merge_with_bitcoin_data(whale_df)
        print(f"[OK] Merged data: {len(combined_df)} days")

        # Save combined data
        combined_df.to_csv('scratchpad/week2/day9/combined_with_whale.csv', index=False)
        print("[OK] Saved combined data to: scratchpad/week2/day9/combined_with_whale.csv")

        # Test whale-only strategy
        print("\n[5] Backtesting whale-only strategy...")
        results = whale.backtest_whale_only(combined_df, starting_capital=10000)

        print("\n" + "=" * 60)
        print("WHALE-ONLY BACKTEST RESULTS")
        print("=" * 60)
        print()
        print(f"Starting Capital: $10,000")
        print(f"Final Value: ${results['final_value']:,.2f}")
        print(f"Total Return: {results['total_return']:+.2f}%")
        print(f"Number of Trades: {results['num_trades']}")
        print(f"Final BTC Holdings: {results['final_btc']:.6f}")
        print(f"Final Cash: ${results['final_cash']:,.2f}")
        print()

        if results['num_trades'] > 0:
            print("TRADE LOG:")
            for trade in results['trades']:
                print(f"  {trade['date']} {trade['action']:4s} {trade['amount']:.6f} BTC @ ${trade['price']:,.0f} "
                      f"(${trade['usd_amount']:,.0f}) [{trade['signal_strength']}]")
        else:
            print("No trades executed (no signals generated)")

    except FileNotFoundError:
        print("[WARNING] Bitcoin data not found. Skipping backtest.")
        print("Run scratchpad/day2/day2_bitcoin_prices.py first to generate Bitcoin data.")

    print("\n" + "=" * 60)
    print("DAY 9 COMPLETE")
    print("=" * 60)
    print()
    print("[DATA] Whale data saved: scratchpad/week2/day9/whale_data_30days.csv")
    print("[DATA] Combined data saved: scratchpad/week2/day9/combined_with_whale.csv")
    print()
    print("Next: Day 10 - Integration & Correlation Analysis")

if __name__ == "__main__":
    main()