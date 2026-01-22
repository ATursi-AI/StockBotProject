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
        # 1. PROFILE & NAME (Finnhub)
        name_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        name_res = requests.get(name_url).json()
        full_name = name_res.get('name', symbol.upper())

        # 2. DATA ACQUISITION
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty: return None

        # 3. TECHNICAL CALCULATIONS
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df['MACD'] = macd['MACD_12_26_9']
        df['SIGNAL'] = macd['MACDs_12_26_9']
        df['ADX'] = ta.adx(df['High'], df['Low'], df['Close'])['ADX_14']
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)

        # 4. AI PATTERN ARCHITECT (20+ Patterns)
        patterns = []
        cdl = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name="all")
        if not cdl.empty:
            last_row = cdl.iloc[-1]
            found = last_row[last_row != 0]
            for name, val in found.items():
                sentiment = "Bullish" if val > 0 else "Bearish"
                patterns.append(f"{name.replace('CDL', '')} ({sentiment})")
        pattern_text = ", ".join(patterns) if patterns else "No clear patterns identified"

        # 5. DYNAMIC CROSS TRIGGERS (Live Check)
        cross_trigger = ""
        prev_50, curr_50 = df['SMA_50'].iloc[-2], df['SMA_50'].iloc[-1]
        prev_200, curr_200 = df['SMA_200'].iloc[-2], df['SMA_200'].iloc[-1]
        
        if prev_50 < prev_200 and curr_50 >= curr_200:
            cross_trigger = "\n🌟 **TRIGGER: GOLDEN CROSS**"
        elif prev_50 > prev_200 and curr_50 <= curr_200:
            cross_trigger = "\n💀 **TRIGGER: DEATH CROSS**"

        # 6. SENTIMENT & CATALYSTS
        news = ticker.news[:3]
        titles = " ".join([n.get('title', '') for n in news])
        sentiment = TextBlob(titles).sentiment.polarity if titles else 0
        
        # Earnings Data
        earn_url = f'https://finnhub.io/api/v1/stock/earnings?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        earn_data = requests.get(earn_url).json()
        earn_text = "N/A"
        if earn_data:
            surprise = earn_data[0].get('surprise', 0)
            earn_text = f"{'✅ BEAT' if surprise > 0 else '❌ MISS'} ({surprise:+})"

        # 7. VALUES & FORMATTING
        price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        adx = df['ADX'].iloc[-1]
        hi_52, lo_52 = df['High'].max(), df['Low'].min()
        
        rsi_bub = "🟢" if rsi < 40 else "🔴" if rsi > 70 else "🟡"
        macd_bub = "🟢" if df['MACD'].iloc[-1] > df['SIGNAL'].iloc[-1] else "🔴"
        adx_bub = "⚪️" if adx < 25 else "🔵" # Strength indicator

        # Synopsis Logic
        if price > df['SMA_50'].iloc[-1] and df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]:
            synopsis = "Bullish trend confirmed; institutional support is holding."
        else:
            synopsis = "Consolidating or showing weakness below major moving averages."

        # 8. THE COMPLETE ARCHITECT OUTPUT
        return (
            f"🔍 **SUPER-SCAN: {symbol.upper()}**\n"
            f"🏢 *{full_name}*\n"
            f"💰 Price: ${price:.2f} | 52W: ${lo_52:.2f}-${hi_52:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 **MARKET CATALYSTS (Finnhub)**\n"
            f"Earnings: {earn_text}\n"
            f"Mood: {'🔥 Bullish' if sentiment > 0.1 else '🧊 Bearish' if sentiment < -0.1 else 'Neutral'}\n\n"
            f"🤖 **AI PATTERN ARCHITECT**\n"
            f"Identified: `{pattern_text}`\n\n"
            f"📜 **TECHNICAL SYNOPSIS**\n"
            f"_{synopsis}_{cross_trigger}\n\n"
            f"📊 **TECHNICAL SCAN**\n"
            f"{rsi_bub} RSI: {rsi:.1f}\n"
            f"{macd_bub} MACD: {'Bullish' if macd_bub == '🟢' else 'Bearish'}\n"
            f"{adx_bub} ADX: {adx:.1f} (Strength)\n"
            f"• 50-Day SMA: ${df['SMA_50'].iloc[-1]:.2f}\n"
            f"• 200-Day SMA: ${df['SMA_200'].iloc[-1]:.2f}\n"
            f"• Trend: {'📈 Uptrend' if price > df['SMA_200'].iloc[-1] else '📉 Downtrend'}\n\n"
            f"🧱 **LEVELS & RISK**\n"
            f"Resist: ${df['High'].iloc[-5:].max():.2f} | Support: ${df['Low'].iloc[-5:].min():.2f}\n"
            f"Stop Loss: ${price - (df['ATR'].iloc[-1]*2):.2f}\n\n"
            f"🏆 **FINAL VERDICT:** {'🐂 BULLISH' if rsi < 60 and price > df['SMA_50'].iloc[-1] else '🐻 BEARISH'}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Analysis Error: {str(e)}"