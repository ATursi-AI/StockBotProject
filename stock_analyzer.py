import os
import requests
import yfinance as yf
import pandas_ta as ta
from dotenv import load_dotenv

load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def get_stock_data(symbol):
    try:
        # 1. Get the Full Company Name via Finnhub (Reliable)
        name_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_KEY}'
        name_response = requests.get(name_url).json()
        full_name = name_response.get('name', symbol.upper())

        # 2. Get the Technical Data via yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")

        if df.empty:
            return None

        # 3. Calculate Technicals
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_50'] = ta.ema(df['Close'], length=50)

        current_price = df['Close'].iloc[-1]
        rsi_value = df['RSI'].iloc[-1]
        rsi_signal = "🟢 BULLISH" if rsi_value < 30 else "🔴 BEARISH" if rsi_value > 70 else "🟡 NEUTRAL"

        # 4. Format the Output
        report = (
            f"📊 *{symbol.upper()} - {full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Current Price:* ${current_price:.2f}\n"
            f"📈 *RSI (14):* {rsi_value:.2f} ({rsi_signal})\n"
            f"⚡ *Trend:* {'📈 Uptrend' if current_price > df['EMA_50'].iloc[-1] else '📉 Downtrend'}\n"
        )
        return report

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None