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
        # 1. Company Name (Finnhub)
        name_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        name_response = requests.get(name_url).json()
        full_name = name_response.get('name', symbol.upper())

        # 2. Price Data & Technicals
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty: return None

        # Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df['MACD'] = macd['MACD_12_26_9']
        df['SIGNAL'] = macd['MACDs_12_26_9']
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        df['ADX'] = adx['ADX_14']
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

        # 3. Intelligence (Sentiment & Catalysts)
        news = ticker.news[:3]
        sentiment_score = 0
        if news:
            titles = " ".join([n['title'] for n in news])
            sentiment_score = TextBlob(titles).sentiment.polarity
        
        mood = "🔥 BULLISH" if sentiment_score > 0.1 else "🧊 BEARISH" if sentiment_score < -0.1 else "Neutral"

        fin_url = f'https://finnhub.io/api/v1/stock/recommendation?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        fin_data = requests.get(fin_url).json()
        analyst_target = "N/A"
        if fin_data:
            analyst_target = f"{fin_data[0]['buy'] + fin_data[0]['strongBuy']} Buy ratings"

        # 4. Score & Verdict Logic
        price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        adx_val = df['ADX'].iloc[-1]
        score = 0
        if rsi < 40: score += 1
        if rsi > 70: score -= 1
        if price > df['Close'].rolling(50).mean().iloc[-1]: score += 1
        if sentiment_score > 0: score += 1

        verdict = "🚀 STRONG BUY" if score >= 2 else "⚠️ HOLD" if score >= 0 else "📉 SELL"

        # 5. The Robust Output
        report = (
            f"🔍 **SUPER-SCAN: {symbol.upper()}**\n"
            f"🏢 *{full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **PRICE:** ${price:.2f}\n"
            f"🎭 **MOOD:** {mood}\n"
            f"📊 **ANALYSTS:** {analyst_target}\n\n"
            f"⚡ **SIGNALS**\n"
            f"{'🟢' if rsi < 45 else '🔴' if rsi > 65 else '🟡'} RSI: {rsi:.1f}\n"
            f"{'🟢' if df['MACD'].iloc[-1] > df['SIGNAL'].iloc[-1] else '🔴'} MACD: Crossing\n"
            f"{'🟢' if adx_val > 25 else '🟡'} Trend Strength: {adx_val:.1f}\n\n"
            f"🛡️ **RISK SETUP**\n"
            f"• Stop Loss (2x ATR): ${price - (df['ATR'].iloc[-1]*2):.2f}\n"
            f"• Volatility (ATR): ${df['ATR'].iloc[-1]:.2f}\n\n"
            f"🏆 **VERDICT: {verdict}**\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        return report

    except Exception as e:
        return f"❌ Analysis Error: {str(e)}"