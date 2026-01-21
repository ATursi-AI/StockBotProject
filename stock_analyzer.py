import yfinance as yf
import pandas_ta as ta
import pandas as pd
from textblob import TextBlob
import requests
import numpy as np
from scipy.signal import argrelextrema

# --- CONFIGURATION ---
FINNHUB_KEY = "d5o481pr01qma2b7favgd5o481pr01qma2b7fb00" 

# --- 1. INTELLIGENCE HELPERS ---

def get_sentiment(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news: return "⚖️ NEUTRAL", 0
        headlines = [n['title'] for n in news[:5]]
        pol = sum(TextBlob(h).sentiment.polarity for h in headlines) / len(headlines)
        return ("🔥 POSITIVE", 1) if pol > 0.1 else ("😨 NEGATIVE", -1) if pol < -0.1 else ("⚖️ NEUTRAL", 0)
    except: return "⚪ UNAVAILABLE", 0

def get_options_intel(ticker):
    try:
        stock = yf.Ticker(ticker)
        if not stock.options: return "⚪ NO DATA", 0
        expiry = stock.options[0]
        chain = stock.option_chain(expiry)
        pcr = chain.puts['volume'].sum() / chain.calls['volume'].sum()
        if pcr < 0.7: return f"🐂 BULLISH (PCR: {pcr:.2f})", 1
        if pcr > 1.2: return f"🐻 BEARISH (PCR: {pcr:.2f})", -1
        return f"⚖️ NEUTRAL ({pcr:.2f})", 0
    except: return "⚪ UNAVAILABLE", 0

def get_finnhub_catalyst(ticker):
    try:
        # Earnings
        url_e = f"https://finnhub.io/api/v1/stock/earnings?symbol={ticker}&token={FINNHUB_KEY}"
        data_e = requests.get(url_e).json()
        surp_msg, s_score = "⚪ No Data", 0
        if data_e and len(data_e) > 0:
            last = data_e[0]
            diff = (last.get('actual', 0) or 0) - (last.get('estimate', 0) or 0)
            surp_msg = f"✅ BEAT (+{diff:.2f})" if diff > 0 else f"❌ MISS ({diff:.2f})"
            s_score = 1 if diff > 0 else -1
        # Targets
        url_t = f"https://finnhub.io/api/v1/stock/price-target?symbol={ticker}&token={FINNHUB_KEY}"
        data_t = requests.get(url_t).json()
        target = f"${data_t['targetMean']:.2f}" if data_t and 'targetMean' in data_t else "⚪ N/A"
        return surp_msg, target, s_score
    except: return "⚪ Error", "⚪ N/A", 0

def detect_ai_patterns(df):
    if len(df) < 100: return "Scanning...", 0
    last, prev = df.iloc[-1], df.iloc[-2]
    close_prices = df['Close'].values
    patterns, p_score = [], 0
    peaks = argrelextrema(close_prices, np.greater, order=5)[0]
    valleys = argrelextrema(close_prices, np.less, order=5)[0]
    if len(peaks) >= 2 and len(valleys) >= 2:
        if abs(close_prices[peaks[-1]] - close_prices[peaks[-2]]) / close_prices[peaks[-1]] < 0.02:
            patterns.append("⛰️ DOUBLE TOP")
            p_score -= 1.5
        if abs(close_prices[valleys[-1]] - close_prices[valleys[-2]]) / close_prices[valleys[-1]] < 0.02:
            patterns.append("🏹 DOUBLE BOTTOM")
            p_score += 1.5
    body = abs(last['Close'] - last['Open'])
    total_range = last['High'] - last['Low']
    if (last['Low'] < min(last['Open'], last['Close'])) and (body < total_range * 0.3):
        patterns.append("🔨 HAMMER")
        p_score += 1
    if prev['Close'] < prev['Open'] and last['Close'] > last['Open']:
        patterns.append("✨ BULLISH ENGULFING")
        p_score += 1
    return " | ".join(patterns) if patterns else "No clear patterns", p_score

# --- 2. MASTER ANALYSIS ENGINE ---

def analyze_stock(ticker):
    try:
        stock_obj = yf.Ticker(ticker)
        df = stock_obj.history(period="1y")
        if df.empty: return None, f"❌ {ticker} not found."
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # Technical Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df['MACD'] = macd.iloc[:, 0]
        df['Signal'] = macd.iloc[:, 2]
        df['ADX'] = ta.adx(df['High'], df['Low'], df['Close'])['ADX_14']
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        latest, prev = df.dropna().iloc[-1], df.dropna().iloc[-2]
        price = latest['Close']

        # Intelligence Gathering (Finnhub + Options + Sentiment + Patterns)
        surp_msg, target_avg, c_score = get_finnhub_catalyst(ticker)
        opt_text, opt_score = get_options_intel(ticker)
        sent_label, sent_score = get_sentiment(ticker)
        pattern_text, p_score = detect_ai_patterns(df)

        # Levels
        pp = (prev['High'] + prev['Low'] + prev['Close']) / 3
        r1, s1 = (2 * pp) - prev['Low'], (2 * pp) - prev['High']

        # Total Scoring
        score = sum([1 if latest['RSI'] < 35 else -1 if latest['RSI'] > 65 else 0,
                     1 if latest['MACD'] > latest['Signal'] else -1,
                     opt_score, sent_score, p_score, c_score])
        
        verdict = "💎 STRONG BUY" if score >= 4 else "🐂 BULLISH" if score >= 1 else "🐻 BEARISH" if score <= -1 else "⚖️ NEUTRAL"

        # RE-INTEGRATED COMPLETE REPORT
        report = (
            f"🔍 **SUPER-SCAN: {ticker}**\n"
            f"💰 Price: **${price:.2f}** | Target: **{target_avg}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚀 **MARKET CATALYSTS (Finnhub)**\n"
            f"Earnings: {surp_msg}\n"
            f"Mood: **{sent_label}**\n"
            f"\n🤖 **AI PATTERN ARCHITECT**\n"
            f"Identified: `{pattern_text}`\n"
            f"\n📊 **TECHNICAL SCAN**\n"
            f"{'🟢' if latest['RSI']<35 else '🔴' if latest['RSI']>65 else '🟡'} **RSI:** {latest['RSI']:.1f}\n"
            f"{'🟢' if latest['MACD']>latest['Signal'] else '🔴'} **MACD:** {'Bullish' if latest['MACD']>latest['Signal'] else 'Bearish'}\n"
            f"{'🔥' if latest['ADX']>25 else '☁️'} **ADX:** {latest['ADX']:.1f} (Strength)\n"
            f"\n🧱 **LEVELS & RISK**\n"
            f"Resist: **${r1:.2f}** | Support: **${s1:.2f}**\n"
            f"Stop Loss (2x ATR): **${(price - 2*latest['ATR']):.2f}**\n"
            f"Options: {opt_text}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏁 **FINAL VERDICT: {verdict}**\n"
            f"AI Confidence: **{min(int(score * 12 + 50), 100)}%**"
        )
        return None, report
    except Exception as e:
        return None, f"⚠️ Analysis failed: {e}"