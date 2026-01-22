import os
import requests
import yfinance as yf
import pandas_ta as ta
from textblob import TextBlob
from dotenv import load_dotenv

load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def get_stock_data(symbol):
    try:
        # 1. CLOUD-SAFE NAME RETRIEVAL
        name_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        name_response = requests.get(name_url).json()
        full_name = name_response.get('name', symbol.upper())

        # 2. CORE DATA FETCH
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty: return None

        # 3. ROBUST INDICATORS
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        # MACD for Momentum
        macd = ta.macd(df['Close'])
        df['MACD'] = macd['MACD_12_26_9']
        df['SIGNAL'] = macd['MACDs_12_26_9']

        # 4. CURRENT VALUES
        price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        sma200 = df['SMA_200'].iloc[-1]
        atr = df['ATR'].iloc[-1]
        macd_val = df['MACD'].iloc[-1]
        sig_val = df['SIGNAL'].iloc[-1]

        # 5. FIXED GOLDEN CROSS LOGIC
        # Only Green if 50 is ABOVE 200. Red if BELOW.
        if sma50 > sma200:
            gc_status = "✅ GOLDEN CROSS (Bullish)"
            gc_emoji = "🟢"
        else:
            gc_status = "❌ DEATH CROSS (Bearish)"
            gc_emoji = "🔴"

        # 6. TECHNICAL CHART SYNOPSIS
        # This builds a narrative based on the data points
        synopsis = ""
        if price > sma50 and sma50 > sma200:
            synopsis = "Stock is in a strong institutional uptrend, holding above key moving averages."
        elif price < sma50 and price > sma200:
            synopsis = "Stock is consolidating; it has lost the 50-day support but remains above the long-term 200-day floor."
        else:
            synopsis = "Chart pattern shows significant weakness; selling pressure is dominating the short and long term."

        # 7. SENTIMENT & VERDICT
        news = ticker.news[:3]
        sentiment = 0
        if news:
            sentiment = TextBlob(" ".join([n['title'] for n in news])).sentiment.polarity
        
        score = 0
        if rsi < 40: score += 1
        if price > sma50: score += 1
        if macd_val > sig_val: score += 1
        verdict = "🚀 STRONG BUY" if score >= 2 else "⚠️ HOLD" if score >= 1 else "📉 SELL"

        # 8. THE FINAL ROBUST OUTPUT
        report = (
            f"🔍 **SUPER-SCAN: {symbol.upper()}**\n"
            f"🏢 *{full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **PRICE:** ${price:.2f}\n"
            f"🎭 **MOOD:** {'🔥 Bullish' if sentiment > 0 else '🧊 Bearish' if sentiment < 0 else 'Neutral'}\n\n"
            f"📜 **TECHNICAL SYNOPSIS**\n"
            f"_{synopsis}_\n\n"
            f"⚡ **SIGNALS**\n"
            f"{'🟢' if rsi < 45 else '🔴' if rsi > 65 else '🟡'} RSI: {rsi:.1f}\n"
            f"{gc_emoji} {gc_status}\n"
            f"{'🟢' if macd_val > sig_val else '🔴'} Momentum: {'Bullish' if macd_val > sig_val else 'Bearish'}\n\n"
            f"🛡️ **RISK SETUP**\n"
            f"• Stop Loss: ${price - (atr*2):.2f}\n"
            f"• 200-Day Floor: ${sma200:.2f}\n\n"
            f"🏆 **VERDICT: {verdict}**\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        return report

    except Exception as e:
        return f"❌ Analysis Error: Check your FINNHUB_KEY and Ticker."