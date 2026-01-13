"""
Day 2: Fetch Bitcoin Historical Prices and Combine with Fear & Greed Data
Quick proof-of-concept to test CoinGecko API
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def fetch_bitcoin_historical_prices(days=30):
    """
    Fetch Bitcoin historical prices from CoinGecko API (free, no key needed)

    Args:
        days: Number of days of historical data to fetch

    Returns:
        DataFrame with columns: date, price
    """
    print(f"Fetching {days} days of Bitcoin historical prices from CoinGecko...")

    # CoinGecko API endpoint for market chart data
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract prices (data contains: prices, market_caps, total_volumes)
        prices = data['prices']  # List of [timestamp_ms, price]

        # Convert to DataFrame
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])

        # Convert timestamp to datetime
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['date', 'price']]

        print(f"Successfully fetched {len(df)} days of Bitcoin prices")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Price range: ${df['price'].min():.2f} to ${df['price'].max():.2f}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Bitcoin prices: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def fetch_fear_greed_historical(days=30):
    """
    Fetch historical Fear & Greed Index data

    Args:
        days: Number of days of historical data

    Returns:
        DataFrame with columns: date, value, classification
    """
    print(f"Fetching {days} days of Fear & Greed Index data...")

    url = f"https://api.alternative.me/fng/?limit={days}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract data
        records = []
        for item in data['data']:
            records.append({
                'date': pd.to_datetime(int(item['timestamp']), unit='s'),
                'fear_greed_value': int(item['value']),
                'fear_greed_classification': item['value_classification']
            })

        df = pd.DataFrame(records)

        print(f"Successfully fetched {len(df)} days of Fear & Greed data")
        print(f"Value range: {df['fear_greed_value'].min()} to {df['fear_greed_value'].max()}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Fear & Greed data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def combine_data(bitcoin_df, fear_greed_df):
    """
    Combine Bitcoin prices and Fear & Greed data by date

    Args:
        bitcoin_df: DataFrame with Bitcoin prices
        fear_greed_df: DataFrame with Fear & Greed data

    Returns:
        Combined DataFrame
    """
    print("\nCombining Bitcoin and Fear & Greed data...")

    # Normalize dates to just the date (remove time)
    bitcoin_df['date_only'] = bitcoin_df['date'].dt.date
    fear_greed_df['date_only'] = fear_greed_df['date'].dt.date

    # Merge on date
    combined = pd.merge(
        bitcoin_df,
        fear_greed_df,
        on='date_only',
        how='inner',
        suffixes=('_bitcoin', '_fg')
    )

    # Clean up columns
    combined = combined[[
        'date_only',
        'price',
        'fear_greed_value',
        'fear_greed_classification'
    ]]

    combined.rename(columns={
        'date_only': 'date',
        'price': 'bitcoin_price_usd'
    }, inplace=True)

    # Sort by date
    combined = combined.sort_values('date').reset_index(drop=True)

    print(f"Combined data: {len(combined)} rows")

    return combined


def save_to_csv(df, filename='combined_data.csv'):
    """
    Save DataFrame to CSV
    """
    df.to_csv(filename, index=False)
    print(f"\nData saved to {filename}")


def plot_data(df):
    """
    Create visualization showing Bitcoin price vs Fear & Greed Index
    """
    print("\nCreating visualization...")

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot Bitcoin price on left y-axis
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Bitcoin Price (USD)', color=color)
    ax1.plot(df['date'], df['bitcoin_price_usd'], color=color, linewidth=2, label='Bitcoin Price')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Create second y-axis for Fear & Greed
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Fear & Greed Index', color=color)
    ax2.plot(df['date'], df['fear_greed_value'], color=color, linewidth=2, label='Fear & Greed Index')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 100)

    # Add horizontal lines for Fear & Greed thresholds
    ax2.axhline(y=25, color='green', linestyle='--', alpha=0.5, label='Extreme Fear (Buy Signal)')
    ax2.axhline(y=75, color='orange', linestyle='--', alpha=0.5, label='Extreme Greed (Sell Signal)')

    # Title and legend
    plt.title('Bitcoin Price vs Fear & Greed Index', fontsize=14, fontweight='bold')

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()

    # Save plot
    plt.savefig('bitcoin_fear_greed_plot.png', dpi=300, bbox_inches='tight')
    print("Plot saved to bitcoin_fear_greed_plot.png")

    plt.show()


def main():
    """
    Main function to orchestrate Day 2 tasks
    """
    print("="*60)
    print("DAY 2: Bitcoin Historical Prices + Fear & Greed Index")
    print("="*60 + "\n")

    # Fetch Bitcoin historical prices (30 days)
    bitcoin_df = fetch_bitcoin_historical_prices(days=30)

    if bitcoin_df is None:
        print("Failed to fetch Bitcoin data. Exiting.")
        return

    # Fetch Fear & Greed historical data (30 days)
    fear_greed_df = fetch_fear_greed_historical(days=30)

    if fear_greed_df is None:
        print("Failed to fetch Fear & Greed data. Exiting.")
        return

    # Combine the datasets
    combined_df = combine_data(bitcoin_df, fear_greed_df)

    print("\n" + "="*60)
    print("COMBINED DATA SAMPLE:")
    print("="*60)
    print(combined_df.head(10))

    # Save to CSV
    save_to_csv(combined_df, 'combined_data.csv')

    # Plot the data
    plot_data(combined_df)

    print("\n" + "="*60)
    print("DAY 2 COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review combined_data.csv")
    print("2. Check bitcoin_fear_greed_plot.png")
    print("3. Move on to Day 3: Create trading signals")


if __name__ == "__main__":
    main()