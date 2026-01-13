"""
Day 11: Add Google Trends + RSI
Set up Google Trends tracking with daily resolution and calculate RSI technical indicator
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
import time

def calculate_rsi(prices, period=14):
    """
    Calculate RSI (Relative Strength Index) - Classic technical indicator
    No API needed - pure math on price data

    Args:
        prices: Pandas Series of prices
        period: RSI period (default 14 days)

    Returns:
        Pandas Series with RSI values (0-100)
    """
    # Calculate price changes
    delta = prices.diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi

def rsi_signal(rsi_value):
    """
    Generate trading signal from RSI value

    Args:
        rsi_value: RSI value (0-100)

    Returns:
        Signal string: OVERSOLD, OVERBOUGHT, or NEUTRAL
    """
    if pd.isna(rsi_value):
        return 'NEUTRAL'
    elif rsi_value < 30:
        return 'OVERSOLD'  # BUY signal
    elif rsi_value > 70:
        return 'OVERBOUGHT'  # SELL signal
    else:
        return 'NEUTRAL'

def get_daily_trends(keyword='bitcoin', days=90):
    """
    Get daily Google Trends data
    Google Trends gives daily data for requests < 7 days, so we need to chunk it

    Args:
        keyword: Search keyword (default 'bitcoin')
        days: Number of days to fetch (default 90)

    Returns:
        Pandas DataFrame with daily trends data
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[WARNING] pytrends not installed. Install with: pip install pytrends")
        print("[INFO] Using simulated Google Trends data for demo")
        return simulate_trends_data(days)

    print(f"\n[TRENDS] Fetching {days} days of Google Trends data for '{keyword}'...")
    print("[INFO] This may take a few minutes due to rate limiting...")

    pytrends = TrendReq(hl='en-US', tz=360)
    all_data = []

    # Fetch in 6-day chunks to get daily resolution
    for i in range(0, days, 6):
        end_date = datetime.now() - timedelta(days=i)
        start_date = end_date - timedelta(days=6)

        timeframe = f'{start_date.strftime("%Y-%m-%d")} {end_date.strftime("%Y-%m-%d")}'

        try:
            pytrends.build_payload([keyword], timeframe=timeframe)
            data = pytrends.interest_over_time()

            if not data.empty:
                # Keep only the keyword column
                data = data[[keyword]]
                data.columns = ['trends_value']
                all_data.append(data)

            # Rate limiting
            time.sleep(2)

            print(f"[TRENDS] Fetched {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        except Exception as e:
            print(f"[WARNING] Failed to fetch trends for {timeframe}: {e}")
            continue

    if not all_data:
        print("[WARNING] No trends data fetched. Using simulated data.")
        return simulate_trends_data(days)

    # Combine all chunks
    combined = pd.concat(all_data)

    # Remove duplicates (overlapping dates)
    combined = combined[~combined.index.duplicated(keep='first')]

    # Sort by date
    combined = combined.sort_index()

    print(f"[OK] Fetched {len(combined)} days of Google Trends data")

    return combined

def simulate_trends_data(days=90):
    """
    Simulate Google Trends data for demo purposes
    Based on typical search interest patterns

    Args:
        days: Number of days to simulate

    Returns:
        Pandas DataFrame with simulated trends data
    """
    print(f"\n[DEMO] Simulating {days} days of Google Trends data...")

    # Create date range
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # Simulate search interest (0-100)
    # Base level around 50, with some variation and spikes
    np.random.seed(42)
    base_interest = 50
    variation = np.random.normal(0, 10, days)

    # Add some spikes (FOMO moments)
    spikes = np.zeros(days)
    spike_indices = np.random.choice(days, size=days//15, replace=False)
    spikes[spike_indices] = np.random.uniform(20, 40, len(spike_indices))

    trends_value = base_interest + variation + spikes
    trends_value = np.clip(trends_value, 0, 100)  # Keep in 0-100 range

    df = pd.DataFrame({
        'trends_value': trends_value
    }, index=dates)

    print(f"[OK] Simulated {len(df)} days of trends data")

    return df

def trends_signal(current_interest, historical_avg):
    """
    Generate trading signal from Google Trends data
    High search = Retail FOMO = Potential top (contrarian)
    Low search = Lack of attention = Potential bottom

    Args:
        current_interest: Current search interest (0-100)
        historical_avg: Historical average search interest

    Returns:
        Signal string: FOMO_WARNING, UNDERVALUED, or NEUTRAL
    """
    if pd.isna(current_interest) or pd.isna(historical_avg):
        return 'NEUTRAL'

    ratio = current_interest / historical_avg

    if ratio > 1.5:
        return 'FOMO_WARNING'  # Too much hype - SELL
    elif ratio < 0.5:
        return 'UNDERVALUED'  # Nobody cares - BUY
    else:
        return 'NEUTRAL'

def load_combined_data():
    """Load combined dataset from Day 10"""
    path = 'scratchpad/week2/day10/combined_data.csv'
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    print(f"[OK] Loaded combined data from Day 10: {len(df)} days")
    return df

def add_rsi_to_data(df, period=14):
    """
    Add RSI indicator to DataFrame

    Args:
        df: DataFrame with price data
        period: RSI period (default 14)

    Returns:
        DataFrame with RSI columns added
    """
    print(f"\n[RSI] Calculating {period}-day RSI...")

    # Get price column
    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    # Calculate RSI
    df['rsi'] = calculate_rsi(df[price_col], period=period)

    # Generate RSI signals
    df['rsi_signal'] = df['rsi'].apply(rsi_signal)

    # Calculate signal strength (distance from neutral zone)
    df['rsi_strength'] = df['rsi'].apply(lambda x:
        'STRONG' if (x < 25 or x > 75) else
        'MODERATE' if (x < 30 or x > 70) else
        'WEAK'
    )

    print(f"[OK] RSI calculated. Valid values: {df['rsi'].notna().sum()}/{len(df)}")

    return df

def add_trends_to_data(df, trends_df):
    """
    Add Google Trends data to combined DataFrame

    Args:
        df: Combined DataFrame
        trends_df: Google Trends DataFrame

    Returns:
        DataFrame with trends columns added
    """
    print(f"\n[TRENDS] Merging trends data...")

    # Ensure both have date as index
    if 'date' in df.columns:
        df = df.set_index('date')

    # Merge on date
    df = df.join(trends_df, how='left')

    # Fill missing trends values with forward fill
    df['trends_value'] = df['trends_value'].fillna(method='ffill')

    # Calculate 30-day moving average
    df['trends_ma30'] = df['trends_value'].rolling(window=30, min_periods=1).mean()

    # Generate trends signals
    df['trends_signal'] = df.apply(
        lambda row: trends_signal(row['trends_value'], row['trends_ma30']),
        axis=1
    )

    # Calculate trends ratio
    df['trends_ratio'] = df['trends_value'] / df['trends_ma30']

    # Reset index
    df = df.reset_index()

    print(f"[OK] Trends data merged. Valid values: {df['trends_value'].notna().sum()}/{len(df)}")

    return df

def backtest_rsi_only(df, starting_capital=10000):
    """
    Backtest using ONLY RSI signals

    Args:
        df: DataFrame with RSI data
        starting_capital: Starting capital in USD

    Returns:
        Dictionary with backtest results
    """
    print("\n" + "=" * 60)
    print("RSI-ONLY BACKTEST")
    print("=" * 60)

    capital = starting_capital
    btc_holdings = 0
    trades = []

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    for idx, row in df.iterrows():
        rsi = row.get('rsi', np.nan)
        signal = row.get('rsi_signal', 'NEUTRAL')
        price = row[price_col]

        if pd.isna(price) or pd.isna(rsi) or price == 0:
            continue

        # Determine position size based on RSI strength
        if rsi < 25:
            position_size = 0.5  # STRONG oversold
        elif rsi < 30:
            position_size = 0.25  # MODERATE oversold
        elif rsi > 75:
            position_size = 0.5  # STRONG overbought
        elif rsi > 70:
            position_size = 0.25  # MODERATE overbought
        else:
            position_size = 0  # NEUTRAL

        # BUY on oversold
        if signal == 'OVERSOLD' and capital > 0:
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
                'rsi': rsi
            })

        # SELL on overbought
        elif signal == 'OVERBOUGHT' and btc_holdings > 0:
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
                'rsi': rsi
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
        print(f"\nTRADE LOG (first 10):")
        for trade in trades[:10]:
            print(f"  {trade['date']} {trade['action']:4s} {trade['amount']:.6f} BTC @ "
                  f"${trade['price']:,.0f} (${trade['usd_amount']:,.0f}) [RSI={trade['rsi']:.1f}]")
        if len(trades) > 10:
            print(f"  ... and {len(trades) - 10} more trades")

    return results

def backtest_trends_only(df, starting_capital=10000):
    """
    Backtest using ONLY Google Trends signals (contrarian)

    Args:
        df: DataFrame with trends data
        starting_capital: Starting capital in USD

    Returns:
        Dictionary with backtest results
    """
    print("\n" + "=" * 60)
    print("GOOGLE TRENDS-ONLY BACKTEST (Contrarian)")
    print("=" * 60)

    capital = starting_capital
    btc_holdings = 0
    trades = []

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    for idx, row in df.iterrows():
        signal = row.get('trends_signal', 'NEUTRAL')
        trends_ratio = row.get('trends_ratio', 1.0)
        price = row[price_col]

        if pd.isna(price) or price == 0 or pd.isna(trends_ratio):
            continue

        # Determine position size based on deviation
        if trends_ratio > 2.0:
            position_size = 0.5  # STRONG FOMO - sell heavily
        elif trends_ratio > 1.5:
            position_size = 0.25  # MODERATE FOMO - sell some
        elif trends_ratio < 0.3:
            position_size = 0.5  # STRONG undervalued - buy heavily
        elif trends_ratio < 0.5:
            position_size = 0.25  # MODERATE undervalued - buy some
        else:
            position_size = 0  # NEUTRAL

        # BUY when undervalued (low search interest)
        if signal == 'UNDERVALUED' and capital > 0:
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
                'trends_ratio': trends_ratio
            })

        # SELL when FOMO (high search interest)
        elif signal == 'FOMO_WARNING' and btc_holdings > 0:
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
                'trends_ratio': trends_ratio
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
        print(f"\nTRADE LOG (first 10):")
        for trade in trades[:10]:
            print(f"  {trade['date']} {trade['action']:4s} {trade['amount']:.6f} BTC @ "
                  f"${trade['price']:,.0f} (${trade['usd_amount']:,.0f}) [Ratio={trade['trends_ratio']:.2f}]")
        if len(trades) > 10:
            print(f"  ... and {len(trades) - 10} more trades")

    return results

def analyze_lag_correlation(df, indicator_col, indicator_name, max_lag=7):
    """
    Analyze correlation at different time lags
    (Reused from Day 10)
    """
    print(f"\n{'=' * 60}")
    print(f"LAG CORRELATION: {indicator_name}")
    print("=" * 60)

    price_col = 'bitcoin_price_usd' if 'bitcoin_price_usd' in df.columns else 'price'

    lags = range(-max_lag, max_lag + 1)
    correlations = {}

    for lag in lags:
        correlations[lag] = df[price_col].corr(df[indicator_col].shift(lag))

    best_lag = max(correlations.items(), key=lambda x: abs(x[1]))

    print(f"\nBest correlation: {best_lag[1]:.3f} at lag {best_lag[0]} days")

    if best_lag[0] > 0:
        print(f"-> {indicator_name} PREDICTS price {best_lag[0]} days ahead")
    elif best_lag[0] < 0:
        print(f"-> {indicator_name} LAGS behind price by {abs(best_lag[0])} days")
    else:
        print(f"-> {indicator_name} moves WITH price (same day)")

    # Plot
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

    plt.annotate(f'Best: {best_lag[0]}d ({best_lag[1]:.3f})',
                xy=(best_lag[0], best_lag[1]),
                xytext=(best_lag[0] + 1, best_lag[1] + 0.05),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10, color='red', fontweight='bold')

    plt.tight_layout()

    return correlations

def main():
    """Day 11 Main: Add Google Trends + RSI"""
    print("=" * 60)
    print("DAY 11: ADD GOOGLE TRENDS + RSI")
    print("=" * 60)

    # Create output directory
    output_dir = Path('scratchpad/week2/day11')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load combined data from Day 10
    print("\n[1] Loading combined data from Day 10...")
    df = load_combined_data()

    # 2. Add RSI
    print("\n[2] Adding RSI indicator...")
    df = add_rsi_to_data(df, period=14)

    # 3. Fetch Google Trends
    print("\n[3] Fetching Google Trends data...")
    trends_df = get_daily_trends(keyword='bitcoin', days=90)

    # Save trends data
    trends_path = output_dir / 'trends_data_90days.csv'
    trends_df.to_csv(trends_path)
    print(f"[OK] Saved trends data: {trends_path}")

    # 4. Add trends to combined data
    print("\n[4] Adding Google Trends to dataset...")
    df = add_trends_to_data(df, trends_df)

    # Save combined dataset with all indicators
    combined_path = output_dir / 'combined_with_rsi_trends.csv'
    df.to_csv(combined_path, index=False)
    print(f"[OK] Saved combined dataset: {combined_path}")

    # 5. Test RSI independently
    print("\n[5] Testing RSI strategy...")
    rsi_results = backtest_rsi_only(df, starting_capital=10000)

    # 6. Test Trends independently
    print("\n[6] Testing Google Trends strategy...")
    trends_results = backtest_trends_only(df, starting_capital=10000)

    # 7. Lag correlation analysis
    print("\n[7] Analyzing lag correlations...")

    # RSI lag analysis
    rsi_lag_corr = analyze_lag_correlation(df, 'rsi', 'RSI', max_lag=7)
    plt.savefig(output_dir / 'rsi_lag_correlation.png', dpi=300, bbox_inches='tight')

    # Trends lag analysis
    trends_lag_corr = analyze_lag_correlation(df, 'trends_value', 'Google Trends', max_lag=7)
    plt.savefig(output_dir / 'trends_lag_correlation.png', dpi=300, bbox_inches='tight')

    print(f"[OK] Saved lag correlation charts")

    # 8. Summary comparison
    print("\n" + "=" * 60)
    print("ALL INDICATORS COMPARISON")
    print("=" * 60)

    summary = pd.DataFrame({
        'Indicator': ['RSI', 'Google Trends'],
        'Final Value': [
            f"${rsi_results['final_value']:,.2f}",
            f"${trends_results['final_value']:,.2f}"
        ],
        'Return (%)': [
            f"{rsi_results['total_return']:+.2f}%",
            f"{trends_results['total_return']:+.2f}%"
        ],
        'vs B&H (pp)': [
            f"{rsi_results['vs_buy_hold']:+.2f}pp",
            f"{trends_results['vs_buy_hold']:+.2f}pp"
        ],
        'Num Trades': [
            rsi_results['num_trades'],
            trends_results['num_trades']
        ]
    })

    print("\n" + summary.to_string(index=False))

    # Save summary
    summary.to_csv(output_dir / 'indicators_comparison.csv', index=False)

    print("\n" + "=" * 60)
    print("DAY 11 COMPLETE")
    print("=" * 60)
    print()
    print(f"[DATA] Trends data: {trends_path}")
    print(f"[DATA] Combined dataset: {combined_path}")
    print(f"[CHARTS] RSI lag correlation: {output_dir / 'rsi_lag_correlation.png'}")
    print(f"[CHARTS] Trends lag correlation: {output_dir / 'trends_lag_correlation.png'}")
    print(f"[RESULTS] Indicators comparison: {output_dir / 'indicators_comparison.csv'}")
    print()
    print("Next: Day 12 - Multi-Indicator Signal Combination")

if __name__ == "__main__":
    main()