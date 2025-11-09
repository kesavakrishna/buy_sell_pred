"""
Day 3: Generate Trading Signals
Create buy/sell signals based on Fear & Greed Index thresholds
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


# Trading Strategy Parameters
BUY_THRESHOLD = 25   # Buy when F&G < 25 (Extreme Fear)
SELL_THRESHOLD = 75  # Sell when F&G > 75 (Extreme Greed)


def load_data(filepath='../day2/combined_data.csv'):
    """
    Load the combined Bitcoin + Fear & Greed data from Day 2

    Args:
        filepath: Path to the combined CSV file

    Returns:
        DataFrame with combined data
    """
    print("Loading data from Day 2...")

    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])

    print(f"Loaded {len(df)} rows of data")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    return df


def generate_signals(df, buy_threshold=BUY_THRESHOLD, sell_threshold=SELL_THRESHOLD):
    """
    Generate trading signals based on Fear & Greed Index

    Trading Rules:
    - BUY when F&G < buy_threshold (default 25, Extreme Fear)
    - SELL when F&G > sell_threshold (default 75, Extreme Greed)
    - HOLD otherwise

    Args:
        df: DataFrame with bitcoin_price_usd and fear_greed_value columns
        buy_threshold: F&G value below which to generate buy signal
        sell_threshold: F&G value above which to generate sell signal

    Returns:
        DataFrame with added signal columns
    """
    print("\n" + "="*60)
    print("GENERATING TRADING SIGNALS")
    print("="*60)
    print(f"Buy Threshold:  F&G < {buy_threshold} (Extreme Fear)")
    print(f"Sell Threshold: F&G > {sell_threshold} (Extreme Greed)")
    print(f"Hold:           {buy_threshold} <= F&G <= {sell_threshold}")

    # Create a copy to avoid modifying original
    df = df.copy()

    # Generate signals
    df['signal'] = 'HOLD'
    df.loc[df['fear_greed_value'] <= buy_threshold, 'signal'] = 'BUY'
    df.loc[df['fear_greed_value'] >= sell_threshold, 'signal'] = 'SELL'

    # Add signal strength (how far from threshold)
    df['signal_strength'] = 0

    # For buy signals: how much below threshold (positive = stronger)
    buy_mask = df['signal'] == 'BUY'
    df.loc[buy_mask, 'signal_strength'] = buy_threshold - df.loc[buy_mask, 'fear_greed_value']

    # For sell signals: how much above threshold (positive = stronger)
    sell_mask = df['signal'] == 'SELL'
    df.loc[sell_mask, 'signal_strength'] = df.loc[sell_mask, 'fear_greed_value'] - sell_threshold

    return df


def analyze_signals(df):
    """
    Analyze and summarize the generated signals

    Args:
        df: DataFrame with signal column

    Returns:
        Dictionary with signal statistics
    """
    print("\n" + "="*60)
    print("SIGNAL ANALYSIS")
    print("="*60)

    # Count signals
    signal_counts = df['signal'].value_counts()

    print("\nSignal Distribution:")
    for signal, count in signal_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {signal:5s}: {count:3d} days ({percentage:5.1f}%)")

    # Analyze buy signals
    buy_signals = df[df['signal'] == 'BUY'].copy()
    if len(buy_signals) > 0:
        print("\n" + "-"*60)
        print("BUY SIGNALS DETAIL:")
        print("-"*60)
        print(f"Total Buy Signals: {len(buy_signals)}")
        print(f"Average F&G at Buy: {buy_signals['fear_greed_value'].mean():.1f}")
        print(f"Average Price at Buy: ${buy_signals['bitcoin_price_usd'].mean():,.2f}")
        print(f"Price Range at Buy: ${buy_signals['bitcoin_price_usd'].min():,.2f} - ${buy_signals['bitcoin_price_usd'].max():,.2f}")

        print("\nBuy Signal Dates:")
        for idx, row in buy_signals.iterrows():
            print(f"  {row['date'].strftime('%Y-%m-%d')}: "
                  f"BTC ${row['bitcoin_price_usd']:,.2f}, "
                  f"F&G {row['fear_greed_value']} ({row['fear_greed_classification']}), "
                  f"Strength: {row['signal_strength']:.1f}")
    else:
        print("\nNo BUY signals found in this period.")

    # Analyze sell signals
    sell_signals = df[df['signal'] == 'SELL'].copy()
    if len(sell_signals) > 0:
        print("\n" + "-"*60)
        print("SELL SIGNALS DETAIL:")
        print("-"*60)
        print(f"Total Sell Signals: {len(sell_signals)}")
        print(f"Average F&G at Sell: {sell_signals['fear_greed_value'].mean():.1f}")
        print(f"Average Price at Sell: ${sell_signals['bitcoin_price_usd'].mean():,.2f}")

        print("\nSell Signal Dates:")
        for idx, row in sell_signals.iterrows():
            print(f"  {row['date'].strftime('%Y-%m-%d')}: "
                  f"BTC ${row['bitcoin_price_usd']:,.2f}, "
                  f"F&G {row['fear_greed_value']} ({row['fear_greed_classification']}), "
                  f"Strength: {row['signal_strength']:.1f}")
    else:
        print("\nNo SELL signals found in this period.")

    # Calculate statistics
    stats = {
        'total_days': len(df),
        'buy_signals': len(buy_signals),
        'sell_signals': len(sell_signals),
        'hold_days': signal_counts.get('HOLD', 0),
        'buy_percentage': (len(buy_signals) / len(df)) * 100,
        'sell_percentage': (len(sell_signals) / len(df)) * 100
    }

    return stats


def plot_signals(df, save_path='signals_plot.png'):
    """
    Create visualization with trading signals marked on the chart

    Args:
        df: DataFrame with signal data
        save_path: Where to save the plot
    """
    print("\n" + "="*60)
    print("CREATING VISUALIZATION")
    print("="*60)

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot Bitcoin price on left y-axis
    color_price = 'tab:blue'
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Bitcoin Price (USD)', color=color_price, fontsize=12)
    ax1.plot(df['date'], df['bitcoin_price_usd'], color=color_price, linewidth=2,
             label='Bitcoin Price', alpha=0.7)
    ax1.tick_params(axis='y', labelcolor=color_price)
    ax1.grid(True, alpha=0.3)

    # Create second y-axis for Fear & Greed
    ax2 = ax1.twinx()
    color_fg = 'tab:gray'
    ax2.set_ylabel('Fear & Greed Index', color=color_fg, fontsize=12)
    ax2.plot(df['date'], df['fear_greed_value'], color=color_fg, linewidth=2,
             label='Fear & Greed Index', alpha=0.5)
    ax2.tick_params(axis='y', labelcolor=color_fg)
    ax2.set_ylim(0, 100)

    # Add threshold lines
    ax2.axhline(y=BUY_THRESHOLD, color='green', linestyle='--', alpha=0.6,
                linewidth=2, label=f'Buy Threshold ({BUY_THRESHOLD})')
    ax2.axhline(y=SELL_THRESHOLD, color='red', linestyle='--', alpha=0.6,
                linewidth=2, label=f'Sell Threshold ({SELL_THRESHOLD})')

    # Mark BUY signals on the price chart
    buy_signals = df[df['signal'] == 'BUY']
    if len(buy_signals) > 0:
        ax1.scatter(buy_signals['date'], buy_signals['bitcoin_price_usd'],
                   color='green', s=200, marker='^', zorder=5,
                   label='BUY Signal', edgecolors='darkgreen', linewidths=2)

    # Mark SELL signals on the price chart
    sell_signals = df[df['signal'] == 'SELL']
    if len(sell_signals) > 0:
        ax1.scatter(sell_signals['date'], sell_signals['bitcoin_price_usd'],
                   color='red', s=200, marker='v', zorder=5,
                   label='SELL Signal', edgecolors='darkred', linewidths=2)

    # Title
    plt.title('Bitcoin Price vs Fear & Greed Index with Trading Signals',
             fontsize=14, fontweight='bold', pad=20)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # Save plot
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {save_path}")

    plt.show()


def save_signals_to_csv(df, filepath='signals_data.csv'):
    """
    Save the data with signals to CSV

    Args:
        df: DataFrame with signals
        filepath: Where to save the CSV
    """
    # Select relevant columns and sort by date
    output_df = df[[
        'date',
        'bitcoin_price_usd',
        'fear_greed_value',
        'fear_greed_classification',
        'signal',
        'signal_strength'
    ]].copy()

    output_df = output_df.sort_values('date').reset_index(drop=True)

    # Save to CSV
    output_df.to_csv(filepath, index=False)
    print(f"\nSignals data saved to {filepath}")

    return output_df


def generate_trading_summary(df):
    """
    Generate a summary of potential trading outcomes

    Args:
        df: DataFrame with signals
    """
    print("\n" + "="*60)
    print("HYPOTHETICAL TRADING SUMMARY")
    print("="*60)

    buy_signals = df[df['signal'] == 'BUY'].copy()

    if len(buy_signals) == 0:
        print("No buy signals to analyze.")
        return

    # Get current price (last row)
    current_price = df.iloc[-1]['bitcoin_price_usd']
    current_date = df.iloc[-1]['date']

    print(f"Current Price (as of {current_date.strftime('%Y-%m-%d')}): ${current_price:,.2f}")
    print(f"\nIf we had bought on each BUY signal and held until now:\n")

    total_invested = 0
    total_value = 0
    position_size = 1000  # $1000 per signal

    print(f"{'Date':<12} {'Entry Price':>12} {'F&G':>5} {'Investment':>12} "
          f"{'Current Value':>15} {'Gain/Loss':>12} {'Return %':>10}")
    print("-" * 90)

    for idx, row in buy_signals.iterrows():
        entry_price = row['bitcoin_price_usd']
        entry_date = row['date'].strftime('%Y-%m-%d')
        fg_value = row['fear_greed_value']

        btc_bought = position_size / entry_price
        current_value = btc_bought * current_price
        gain_loss = current_value - position_size
        return_pct = (gain_loss / position_size) * 100

        total_invested += position_size
        total_value += current_value

        gain_loss_str = f"${gain_loss:+,.2f}"
        return_str = f"{return_pct:+.2f}%"

        print(f"{entry_date:<12} ${entry_price:>11,.2f} {fg_value:>5d} "
              f"${position_size:>11,.2f} ${current_value:>14,.2f} "
              f"{gain_loss_str:>12} {return_str:>10}")

    print("-" * 90)
    total_gain_loss = total_value - total_invested
    total_return_pct = (total_gain_loss / total_invested) * 100

    print(f"{'TOTAL':<12} {'':>12} {'':>5} ${total_invested:>11,.2f} "
          f"${total_value:>14,.2f} ${total_gain_loss:>+11,.2f} {total_return_pct:>+9.2f}%")

    print(f"\nStrategy Performance:")
    print(f"  Total Invested: ${total_invested:,.2f}")
    print(f"  Current Value:  ${total_value:,.2f}")
    print(f"  Total Return:   ${total_gain_loss:+,.2f} ({total_return_pct:+.2f}%)")
    print(f"  Avg Return:     {total_return_pct / len(buy_signals):+.2f}% per trade")


def main():
    """
    Main function to execute Day 3 tasks
    """
    print("="*60)
    print("DAY 3: TRADING SIGNAL GENERATION")
    print("="*60)

    # Load data from Day 2
    df = load_data()

    # Generate trading signals
    df_with_signals = generate_signals(df)

    # Analyze signals
    stats = analyze_signals(df_with_signals)

    # Generate trading summary
    generate_trading_summary(df_with_signals)

    # Save results
    save_signals_to_csv(df_with_signals)

    # Create visualization with signals marked
    plot_signals(df_with_signals)

    print("\n" + "="*60)
    print("DAY 3 COMPLETE!")
    print("="*60)
    print("\nOutput files:")
    print("  - signals_data.csv (data with signals)")
    print("  - signals_plot.png (visualization with signals)")
    print("\nNext steps:")
    print("  - Day 4: Backtest the strategy")
    print("  - Test different threshold values")
    print("  - Implement position sizing and risk management")


if __name__ == "__main__":
    main()