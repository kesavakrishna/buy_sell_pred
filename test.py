import ccxt
import os
import pandas as pd
import numpy as np
import ta  # Technical Analysis Library
from gnews import GNews
from newspaper import Article  # for extracting full news content
import logging
import time
from dotenv import load_dotenv

# LangChain imports
from langchain import PromptTemplate, LLMChain
from langchain.llms import HuggingFaceHub

load_dotenv()
# Get your Hugging Face API token from environment variables.
api_token = os.getenv('HUGGINGFACE_API_TOKEN')
if not api_token:
    raise ValueError("Please set the HUGGINGFACE_API_TOKEN environment variable.")
print("Token (last 5 chars):", api_token[-5:])

# -----------------------------
# 1. Data Aggregation: Historical Data
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

# Fetch historical data (e.g. last 120 days)
df = fetch_historical_data(symbol='BTC/USD', timeframe='1d', limit=120)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(df.head())

# -----------------------------
# 2. Technical Analysis: Compute Indicators
# -----------------------------
close = df['close']
high = df['high']
low = df['low']
volume = df['volume']

df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
df['ema'] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
macd = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
df['macd'] = macd.macd()
df['sma'] = ta.trend.SMAIndicator(close, window=20).sma_indicator()

bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=2)
df['bollinger_upper'] = bollinger.bollinger_hband()
df['bollinger_middle'] = bollinger.bollinger_mavg()
df['bollinger_lower'] = bollinger.bollinger_lband()

df['atr'] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()
df['adx'] = ta.trend.ADXIndicator(high, low, close, window=14).adx()

stoch = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
df['stoch_k'] = stoch.stoch()
df['stoch_d'] = stoch.stoch_signal()

df['obv'] = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()

recent_high = df['high'].max()
recent_low = df['low'].min()
fib_levels = {
    'fib_23.6': recent_high - 0.236 * (recent_high - recent_low),
    'fib_38.2': recent_high - 0.382 * (recent_high - recent_low),
    'fib_50.0': recent_high - 0.5   * (recent_high - recent_low),
    'fib_61.8': recent_high - 0.618 * (recent_high - recent_low)
}

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

logging.info("Technical Indicators:")
for key, value in indicators.items():
    logging.info(f"{key}: {value:.2f}")

# -----------------------------
# 3. Enhanced News Sentiment Analysis via Article Summarization + FinBERT (Local)
# -----------------------------
# Retrieve news articles using GNews
google_news = GNews(language='en', country='US', period='1d', max_results=5)
crypto_news = google_news.get_news('cryptocurrency')

logging.info("Retrieved News Articles:")
for article in crypto_news:
    logging.info(f"Title: {article.get('title', 'No title')} - URL: {article.get('url', 'No URL')}")

def extract_full_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        logging.info("Extracted article text.")
        return article.text
    except Exception as e:
        logging.error(f"Error extracting article: {e}")
        return ""

# ----- Summarization Chain via LangChain -----
from langchain import PromptTemplate, LLMChain
from langchain.llms import HuggingFaceHub

summary_prompt_template = """
You are an expert summarizer.
Please provide a concise summary (up to 3 sentences) of the following article:
{article_text}

Summary:
"""
summary_prompt = PromptTemplate(
    input_variables=["article_text"],
    template=summary_prompt_template
)

# Use a hosted LLM (Llama-2-7B-Chat) for summarization.
summarization_llm = HuggingFaceHub(
    repo_id="meta-llama/Llama-2-7B-Chat-hf",
    huggingfacehub_api_token=api_token,
    model_kwargs={"max_new_tokens": 100}
)
summary_chain = LLMChain(llm=summarization_llm, prompt=summary_prompt)

# ----- FinBERT for Sentiment Analysis (Local) -----
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline as hf_pipeline

# Download FinBERT locally
tokenizer_finbert = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
model_finbert = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
finbert_pipeline = hf_pipeline("sentiment-analysis", model=model_finbert, tokenizer=tokenizer_finbert)

sentiment_scores = []
for article in crypto_news:
    url = article.get('url', '')
    if url:
        full_text = extract_full_text(url)
        if full_text:
            # Summarize the full article text
            try:
                summary = summary_chain.run({"article_text": full_text})
                logging.info("Article summary: %s", summary)
            except Exception as e:
                logging.error("Error during summarization: %s", e)
                summary = full_text[:1000]  # Fallback: use first 1000 characters
            
            # Use FinBERT on the summary (limit to first 512 characters)
            try:
                result = finbert_pipeline(summary[:512])
                label = result[0]['label']
                if label.lower() == "positive":
                    score = 1
                elif label.lower() == "negative":
                    score = -1
                else:
                    score = 0
                sentiment_scores.append(score)
                logging.info("Article sentiment (%s): %s", label, score)
            except Exception as e:
                logging.error("Error during FinBERT sentiment analysis: %s", e)
            time.sleep(2)  # Throttle API calls

news_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
logging.info(f"Aggregated News Sentiment Score: {news_sentiment:.2f}")


# -----------------------------
# 4. LLM Agent for Decision-Making via LangChain
# -----------------------------
target_duration = 10

prompt_template = """
You are a professional crypto trader with extensive financial and technical analysis knowledge.
Current BTC price: ${current_price}.
Technical Indicators:
- RSI: {rsi}
- EMA (20-day): {ema}
- MACD: {macd}
- SMA (20-day): {sma}
- Bollinger Bands: Upper = {bollinger_upper}, Lower = {bollinger_lower}
- ATR (14-day): {atr}
- ADX (14-day): {adx}
- Stochastic: %K = {stoch_k}, %D = {stoch_d}
- OBV: {obv}
- Fibonacci Levels: 23.6% = {fib_23_6}, 38.2% = {fib_38_2}, 50% = {fib_50_0}, 61.8% = {fib_61_8}
News Sentiment Score (average, where positive=+1, negative=-1): {news_sentiment}.
Based on these factors, decide the ideal target price for BTC, the optimal stop loss, and estimate the probability (as a percentage) of reaching the target price within the next {target_duration} days.
Explain your reasoning in under 100 words.
"""

decision_prompt = PromptTemplate(
    input_variables=[
        "current_price", "rsi", "ema", "macd", "sma", "bollinger_upper", "bollinger_lower",
        "atr", "adx", "stoch_k", "stoch_d", "obv",
        "fib_23_6", "fib_38_2", "fib_50_0", "fib_61_8",
        "news_sentiment", "target_duration"
    ],
    template=prompt_template
)

# Instantiate the decision-making LLM (hosted inference via HuggingFaceHub in LangChain).
decision_llm = HuggingFaceHub(
    repo_id="meta-llama/Llama-2-7B-Chat-hf",
    huggingfacehub_api_token=api_token
)

chain = LLMChain(llm=decision_llm, prompt=decision_prompt)

chain_inputs = {
    "current_price": f"{indicators['Current Price']:.2f}",
    "rsi": f"{indicators['RSI']:.2f}",
    "ema": f"{indicators['EMA']:.2f}",
    "macd": f"{indicators['MACD']:.2f}",
    "sma": f"{indicators['SMA']:.2f}",
    "bollinger_upper": f"{indicators['Bollinger Upper']:.2f}",
    "bollinger_lower": f"{indicators['Bollinger Lower']:.2f}",
    "atr": f"{indicators['ATR']:.2f}",
    "adx": f"{indicators['ADX']:.2f}",
    "stoch_k": f"{indicators['Stochastic %K']:.2f}",
    "stoch_d": f"{indicators['Stochastic %D']:.2f}",
    "obv": f"{indicators['OBV']:.2f}",
    "fib_23_6": f"{fib_levels['fib_23.6']:.2f}",
    "fib_38_2": f"{fib_levels['fib_38.2']:.2f}",
    "fib_50_0": f"{fib_levels['fib_50.0']:.2f}",
    "fib_61_8": f"{fib_levels['fib_61.8']:.2f}",
    "news_sentiment": f"{news_sentiment:.2f}",
    "target_duration": target_duration
}

generated_text = chain.run(chain_inputs)
print("LLM Recommendation:\n", generated_text)

# -----------------------------
# 5. Combined Trading Advice Function
# -----------------------------
def generate_trading_advice(generated_text):
    advice = f"BTC is trading at ${indicators['Current Price']:.2f}. {generated_text}"
    return advice

print("\nFinal Trading Advice:")
print(generate_trading_advice(generated_text))
