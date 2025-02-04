import ccxt
import os
import pandas as pd
import numpy as np
import ta  # Technical Analysis Library
from gnews import GNews
from newspaper import Article  # for extracting full news content
from huggingface_hub import InferenceApi
from huggingface_hub import InferenceClient

import time
from dotenv import load_dotenv
load_dotenv()
# Get your Hugging Face API token from environment variables
api_token = os.getenv('HUGGINGFACE_API_TOKEN')
print("Token:", api_token[-5:] if api_token else "No token found!")

# -----------------------------
# 1. Data Aggregation: Historical Data with Extended Timeframe
# -----------------------------
def fetch_historical_data(symbol='BTC/USD', timeframe='1d', limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# Initialize exchange connection (replace with your own keys/environment variables)
API_KEY = os.getenv('COINBASE_API_KEY')
API_SECRET = os.getenv('COINBASE_API_SECRET')
exchange = ccxt.coinbase({
    'apiKey': API_KEY,
    'secret': API_SECRET,
})

# Fetch historical data (using a daily timeframe for broader context)
df = fetch_historical_data(symbol='BTC/USD', timeframe='1d', limit=120)

# -----------------------------
# 2. Technical Analysis Module: Compute a Wide Range of Indicators
# -----------------------------
# Price series
close = df['close']
high = df['high']
low = df['low']
volume = df['volume']

# Basic indicators
df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
df['ema'] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
macd = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
df['macd'] = macd.macd()
df['macdsignal'] = macd.macd_signal()
df['sma'] = ta.trend.SMAIndicator(close, window=20).sma_indicator()

# Bollinger Bands
bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=2)
df['bollinger_upper'] = bollinger.bollinger_hband()
df['bollinger_middle'] = bollinger.bollinger_mavg()
df['bollinger_lower'] = bollinger.bollinger_lband()

# ATR (Average True Range)
df['atr'] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()

# ADX (Average Directional Index)
df['adx'] = ta.trend.ADXIndicator(high, low, close, window=14).adx()

# Stochastic Oscillator
stoch = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
df['stoch_k'] = stoch.stoch()
df['stoch_d'] = stoch.stoch_signal()

# On Balance Volume (OBV)
df['obv'] = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()

# Fibonacci Retracement Levels (based on recent period)
recent_high = df['high'].max()
recent_low = df['low'].min()
fib_levels = {
    'fib_23.6': recent_high - 0.236 * (recent_high - recent_low),
    'fib_38.2': recent_high - 0.382 * (recent_high - recent_low),
    'fib_50.0': recent_high - 0.5   * (recent_high - recent_low),
    'fib_61.8': recent_high - 0.618 * (recent_high - recent_low)
}

# For demonstration, take the latest available values
latest_data = df.iloc[-1]
indicators = {
    "Current Price": latest_data['close'],
    "RSI": latest_data['rsi'],
    "EMA": latest_data['ema'],
    "MACD": latest_data['macd'],
    "SMA": latest_data['sma'],
    "Bollinger Upper": latest_data['bollinger_upper'],
    "Bollinger Lower": latest_data['bollinger_lower'],
    "ATR": latest_data['atr'],
    "ADX": latest_data['adx'],
    "Stochastic %K": latest_data['stoch_k'],
    "Stochastic %D": latest_data['stoch_d'],
    "OBV": latest_data['obv'],
    **fib_levels
}

# -----------------------------
# 3. Enhanced News Sentiment Analysis using FinBERT and Full Article Text
# -----------------------------
# Retrieve news articles from GNews
google_news = GNews(language='en', country='US', period='1d', max_results=5)
crypto_news = google_news.get_news('cryptocurrency')

def extract_full_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error extracting article: {e}")
        return ""

# Create an inference API instance for FinBERT
finbert = InferenceApi(repo_id="yiyanghkust/finbert-tone", token=api_token)

# Aggregate sentiment scores from full articles with throttling
sentiment_scores = []
for article in crypto_news:
    url = article.get('url', '')
    if url:
        full_text = extract_full_text(url)
        if full_text:
            try:
                result = finbert(full_text[:512])  # Use first 512 tokens to stay within limits
                label = result[0]['label']
                score = 1 if label.upper() == "POSITIVE" else (-1 if label.upper() == "NEGATIVE" else 0)
                sentiment_scores.append(score)
            except Exception as e:
                print(f"Error during FinBERT API call: {e}")
            time.sleep(2)  # Throttle calls by sleeping 2 seconds between each request

news_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0

# -----------------------------
# 4. LLM Agent for Decision-Making via API Calls
# -----------------------------

# Initialize the InferenceClient
from transformers import pipeline
import os

# Load environment variables
load_dotenv()
api_token = os.getenv('HUGGINGFACE_API_TOKEN')

# Use a pipeline as a high-level helper
from transformers import pipeline

messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe = pipeline("text-generation", model="mistralai/Mistral-Small-24B-Instruct-2501")
pipe(messages)
target_duration = 10  # days

# Define the prompt for the LLM
prompt = f"""
You are a professional crypto trader with extensive financial and technical analysis knowledge.
Current BTC price: ${indicators['Current Price']:.2f}.
Technical Indicators:
- RSI: {indicators['RSI']:.2f}
- EMA (20-day): {indicators['EMA']:.2f}
- MACD: {indicators['MACD']:.2f}
- SMA (20-day): {indicators['SMA']:.2f}
- Bollinger Bands: Upper = {indicators['Bollinger Upper']:.2f}, Lower = {indicators['Bollinger Lower']:.2f}
- ATR (14-day): {indicators['ATR']:.2f}
- ADX (14-day): {indicators['ADX']:.2f}
- Stochastic: %K = {indicators['Stochastic %K']:.2f}, %D = {indicators['Stochastic %D']:.2f}
- OBV: {indicators['OBV']:.2f}
- Fibonacci Levels: 23.6% = {fib_levels['fib_23.6']:.2f}, 38.2% = {fib_levels['fib_38.2']:.2f}, 50% = {fib_levels['fib_50.0']:.2f}, 61.8% = {fib_levels['fib_61.8']:.2f}
News Sentiment Score (average, where positive=+1, negative=-1): {news_sentiment:.2f}.
Based on these factors, decide the ideal target price for BTC, the optimal stop loss, and estimate the probability (as a percentage) of reaching the target price within the next {target_duration} days.
Explain your reasoning in under 100 words.
"""

# Make the API call for LLM generation with error handling
try:
    llm_response = pipe(prompt)
    generated_text = llm_response[0]['generated_text'] if isinstance(llm_response, list) else llm_response.get("generated_text", "")
except Exception as e:
    print(f"Error during LLM API call: {e}")
    generated_text = ""

print("LLM Recommendation:\n", generated_text)

# -----------------------------
# 5. Combined Trading Advice Function
# -----------------------------
def generate_trading_advice():
    advice = f"BTC is trading at ${indicators['Current Price']:.2f}. {generated_text}"
    return advice

print("\nFinal Trading Advice:")
print(generate_trading_advice())
