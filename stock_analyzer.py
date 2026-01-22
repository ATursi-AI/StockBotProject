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

        # 4. INSTITUTIONAL INTEL (Options Flow)
        # Calculate PCR based on current options chain
        pcr = "N/A"
        whale_alert = "No unusual spikes"
        try:
            expirations = ticker.options
            if expirations:
                opt = ticker.option_chain(expirations[0])
                calls_vol = opt.calls['volume'].sum()
                puts_vol = opt.puts['volume'].sum()
                pcr_val = puts_vol / calls_vol if calls_vol > 0 else 0
                pcr = f"{pcr_val:.2f} ({'Bullish' if pcr_val < 0.7 else 'Bearish' if pcr_val > 1.0 else 'Neutral'})"
                
                # Whale Alert: Check for Volume > Open Interest
                high_oi_calls = opt.calls[opt.calls['volume'] > opt.calls['openInterest']]
                if not high_oi_calls.empty:
                    whale_alert = f"🚨 UNUSUAL OI SPIKE at ${high_oi_calls.iloc[0]['strike']} Call"
        except:
            pass

        # 5. AI PATTERN ARCHITECT (20+ Patterns)
        patterns = []
        cdl = ta.cdl_pattern(df['Open'], df['High'], df['Low'], df['Close'], name="all")
        if not cdl.empty:
            last_row = cdl.iloc[-1]
            found = last_row[last_row != 0]
            for name, val in found.items():
                sentiment = "Bullish" if val > 0 else "Bearish"
                clean_name = name.replace('CDL_', '').replace('_', ' ').title()
                patterns.append(f"{clean_name} ({sentiment})")
        pattern_text = ", ".join(patterns) if patterns else "No clear patterns identified"

        # 6. VALUES & CROSS TRIGGERS
        price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        adx = df['ADX'].iloc[-1]
        hi_52, lo_52 = df['High'].max(), df['Low'].min()
        atr = df['ATR'].iloc[-1]
        
        # Golden/Death Cross Trigger Logic
        cross_trigger = ""
        prev_50, curr_50 = df['SMA_50'].iloc[-2], df['SMA_50'].iloc[-1]
        prev_200, curr_200 = df['SMA_200'].iloc[-2], df['SMA_200'].iloc[-1]
        if prev_50 < prev_200 and curr_50 >= curr_200:
            cross_trigger = "\n🌟 **TRIGGER: GOLDEN CROSS**"
        elif prev_50 > prev_200 and curr_50 <= curr_200:
            cross_trigger = "\n💀 **TRIGGER: DEATH CROSS**"

        # Synopsis Logic
        if price > df['SMA_50'].iloc[-1] and df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]:
            synopsis = "Bullish trend confirmed; institutional support is holding above the 50-day SMA."
        elif price < df['SMA_50'].iloc[-1] and price > df['SMA_200'].iloc[-1]:
            synopsis = "Consolidating; price has lost the 50-day support but remains above the 200-day floor."
        else:
            synopsis = "Bearish pattern; price action is trending below major institutional moving averages."

        # 7. SENTIMENT & EARNINGS
        news = ticker.news[:3]
        titles = " ".join([n.get('title', '') for n in news])
        sentiment = TextBlob(titles).sentiment.polarity if titles else 0
        
        # 8. OUTPUT GENERATION
        return (
            f"🔍 **SUPER-SCAN: {symbol.upper()}**\n"
            f"🏢 *{full_name}*\n"
            f"💰 Price: ${price:.2f} | 52W: ${lo_52:.2f}-${hi_52:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 **MARKET CATALYSTS (Finnhub)**\n"
            f"Mood: {'🔥 Bullish' if sentiment > 0.1 else '🧊 Bearish' if sentiment < -0.1 else 'Neutral'}\n\n"
            f"🐋 **INSTITUTIONAL INTEL**\n"
            f"• Put/Call Ratio: {pcr}\n"
            f"• Whale Activity: {whale_alert}\n\n"
            f"🤖 **AI PATTERN ARCHITECT**\n"
            f"Identified: `{pattern_text}`\n\n"
            f"📊 **TECHNICAL SCAN**\n"
            f"{'🟢' if rsi < 45 else '🔴' if rsi > 65 else '🟡'} RSI: {rsi:.1f}\n"
            f"{'🟢' if df['MACD'].iloc[-1] > df['SIGNAL'].iloc[-1] else '🔴'} MACD: {'Bullish' if df['MACD'].iloc[-1] > df['SIGNAL'].iloc[-1] else 'Bearish'}\n"
            f"{'🔵' if adx > 25 else '⚪️'} ADX: {adx:.1f} (Strength)\n"
            f"• 50-Day SMA: ${df['SMA_50'].iloc[-1]:.2f}\n"
            f"• 200-Day SMA: ${df['SMA_200'].iloc[-1]:.2f}\n"
            f"• Trend: {'📈 Uptrend' if price > df['SMA_200'].iloc[-1] else '📉 Downtrend'}\n\n"
            f"📜 **TECHNICAL SYNOPSIS**\n"
            f"_{synopsis}_{cross_trigger}\n\n"
            f"🧱 **LEVELS & RISK**\n"
            f"Resist: ${df['High'].iloc[-5:].max():.2f} | Support: ${df['Low'].iloc[-5:].min():.2f}\n"
            f"Stop Loss: ${price - (atr*2):.2f}\n\n"
            f"🎯 **TRADE PLAN (Moon Mission)**\n"
            f"• Entry: ${price:.2f}\n"
            f"• Target 1: ${price * 1.05:.2f} (+5%)\n"
            f"• Target 2: ${price * 1.12:.2f} (+12%)\n"
            f"• Moon: ${price * 1.25:.2f} (+25%)\n\n"
            f"🏆 **FINAL VERDICT: {'🚀 STRONG BUY' if rsi < 55 and price > df['SMA_50'].iloc[-1] else '⚠️ HOLD'}**\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Analysis Error: {str(e)}"