import os
import math  # Added this to fix the isnan error
import requests
import yfinance as yf
import pandas_ta as ta
from textblob import TextBlob
from dotenv import load_dotenv

load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def get_stock_data(symbol):
    try:
        # 1. PROFILE & NAME
        name_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        name_res = requests.get(name_url).json()
        full_name = name_res.get('name', symbol.upper())

        # 2. DATA ACQUISITION
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty or len(df) < 10: return "❌ Analysis Error: Insufficient historical data."

        # 3. TECHNICAL CALCULATIONS
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df['MACD'] = macd['MACD_12_26_9']
        df['SIGNAL'] = macd['MACDs_12_26_9']
        df['ADX'] = ta.adx(df['High'], df['Low'], df['Close'])['ADX_14']
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)

        # 4. EARNINGS & SENTIMENT
        earn_url = f'https://finnhub.io/api/v1/stock/earnings?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        earn_data = requests.get(earn_url).json()
        earn_text = "N/A"
        if earn_data:
            surprise = earn_data[0].get('surprise', 0)
            earn_text = f"{'✅ BEAT' if surprise > 0 else '❌ MISS'} ({surprise:+})"

        news = ticker.news[:3]
        titles = " ".join([n.get('title', '') for n in news])
        sentiment = TextBlob(titles).sentiment.polarity if titles else 0

        # 5. INSTITUTIONAL INTEL
        pcr = "N/A"
        whale_alert = "No unusual spikes"
        try:
            expirations = ticker.options
            if expirations and len(expirations) > 0:
                opt = ticker.option_chain(expirations[0])
                calls_vol = opt.calls['volume'].sum()
                puts_vol = opt.puts['volume'].sum()
                if calls_vol > 0:
                    pcr_val = puts_vol / calls_vol
                    pcr = f"{pcr_val:.2f} ({'Bullish' if pcr_val < 0.7 else 'Bearish' if pcr_val > 1.0 else 'Neutral'})"
                
                high_oi_calls = opt.calls[opt.calls['volume'] > opt.calls['openInterest']]
                if not high_oi_calls.empty:
                    whale_alert = f"🚨 UNUSUAL OI SPIKE at ${high_oi_calls.iloc[0]['strike']} Call"
        except: pcr = "N/A (Limited Data)"

        # 6. AI PATTERN ARCHITECT
        patterns = []
        last, prev = df.iloc[-1], df.iloc[-2]
        if last['Close'] > prev['Open'] and last['Open'] < prev['Close'] and last['Close'] > last['Open'] and prev['Close'] < prev['Open']:
            patterns.append("Engulfing (Bullish)")
        body = abs(last['Close'] - last['Open'])
        lower_wick = min(last['Open'], last['Close']) - last['Low']
        if lower_wick > (body * 2):
            patterns.append("Hammer (Bullish)")
        pattern_text = ", ".join(patterns) if patterns else "No clear patterns identified"

        # 7. VALUES & TRIGGERS (CLEAN FORMATTING)
        price = df['Close'].iloc[-1]
        rsi_val = float(df['RSI'].iloc[-1]) if not df['RSI'].isnull().iloc[-1] else 0.0
        adx_val = float(df['ADX'].iloc[-1]) if not df['ADX'].isnull().iloc[-1] else 0.0
        atr_val = float(df['ATR'].iloc[-1]) if not df['ATR'].isnull().iloc[-1] else 0.0
        
        sma50_raw = df['SMA_50'].iloc[-1]
        sma200_raw = df['SMA_200'].iloc[-1]
        
        # FIXED: Using math.isnan instead of os.path.isnan
        sma50_display = f"{sma50_raw:.2f}" if sma50_raw and not math.isnan(sma50_raw) else "0.00"
        sma200_display = f"{sma200_raw:.2f}" if sma200_raw and not math.isnan(sma200_raw) else "0.00"
        rsi_display = f"{rsi_val:.1f}"
        adx_display = f"{adx_val:.1f}"

        hi_52, lo_52 = df['High'].max(), df['Low'].min()

        cross_trigger = ""
        if sma50_raw and sma200_raw and not df['SMA_50'].isnull().iloc[-2]:
            if df['SMA_50'].iloc[-2] < df['SMA_200'].iloc[-2] and sma50_raw >= sma200_raw:
                cross_trigger = "\n🌟 **TRIGGER: GOLDEN CROSS**"
            elif df['SMA_50'].iloc[-2] > df['SMA_200'].iloc[-2] and sma50_raw <= sma200_raw:
                cross_trigger = "\n💀 **TRIGGER: DEATH CROSS**"

        if sma50_raw and sma200_raw:
            if price > sma50_raw and sma50_raw > sma200_raw:
                synopsis = "Bullish trend confirmed; institutional support is holding above the 50-day SMA."
            elif price < sma50_raw and price > sma200_raw:
                synopsis = "Consolidating; price has lost the 50-day support but remains above the 200-day floor."
            else:
                synopsis = "Bearish pattern; price action is trending below major institutional moving averages."
        else:
            synopsis = "Technical trend is currently neutral due to insufficient SMA data."

        # 8. FINAL OUTPUT
        verdict = "⚠️ HOLD"
        if rsi_val > 0 and rsi_val < 55 and sma50_raw and price > sma50_raw:
            verdict = "🚀 STRONG BUY"

        return (
            f"🔍 **SUPER-SCAN: {symbol.upper()}**\n"
            f"🏢 *{full_name}*\n"
            f"💰 Price: ${price:.2f} | 52W: ${lo_52:.2f}-${hi_52:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 **MARKET CATALYSTS (Finnhub)**\n"
            f"Earnings: {earn_text}\n"
            f"Mood: {'🔥 Bullish' if sentiment > 0.1 else '🧊 Bearish' if sentiment < -0.1 else 'Neutral'}\n\n"
            f"🐋 **INSTITUTIONAL INTEL**\n"
            f"• Put/Call Ratio: {pcr}\n"
            f"• Whale Activity: {whale_alert}\n\n"
            f"🤖 **AI PATTERN ARCHITECT**\n"
            f"Identified: `{pattern_text}`\n\n"
            f"📊 **TECHNICAL SCAN**\n"
            f"{'🟢' if rsi_val < 45 else '🔴' if rsi_val > 65 else '🟡'} RSI: {rsi_display}\n"
            f"{'🟢' if df['MACD'].iloc[-1] > df['SIGNAL'].iloc[-1] else '🔴'} MACD: {'Bullish' if df['MACD'].iloc[-1] > df['SIGNAL'].iloc[-1] else 'Bearish'}\n"
            f"{'🔵' if adx_val > 25 else '⚪️'} ADX: {adx_display} (Strength)\n"
            f"• 50-Day SMA: ${sma50_display}\n"
            f"• 200-Day SMA: ${sma200_display}\n"
            f"• Trend: {'📈 Uptrend' if sma200_raw and price > sma200_raw else '📉 Downtrend'}\n\n"
            f"📜 **TECHNICAL SYNOPSIS**\n"
            f"_{synopsis}_{cross_trigger}\n\n"
            f"🧱 **LEVELS & RISK**\n"
            f"Resist: ${df['High'].iloc[-5:].max():.2f} | Support: ${df['Low'].iloc[-5:].min():.2f}\n"
            f"Stop Loss: ${price - (atr_val*2):.2f}\n\n"
            f"🎯 **TRADE PLAN (Moon Mission)**\n"
            f"• Entry: ${price:.2f}\n"
            f"• Target 1: ${price * 1.05:.2f} (+5%)\n"
            f"• Target 2: ${price * 1.12:.2f} (+12%)\n"
            f"• Moon: ${price * 1.25:.2f} (+25%)\n\n"
            f"🏆 **FINAL VERDICT: {verdict}**\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Analysis Error: {str(e)}"