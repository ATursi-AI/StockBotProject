import os
import requests
import yfinance as yf
import pandas_ta as ta
from dotenv import load_dotenv

# Load keys for the Cloud
load_dotenv()
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def get_stock_data(symbol):
    try:
        # 1. GET FULL NAME (The Cloud-Safe Way)
        name_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol.upper()}&token={FINNHUB_KEY}'
        name_response = requests.get(name_url).json()
        full_name = name_response.get('name', symbol.upper())

        # 2. GET HISTORICAL DATA
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty:
            return None

        # 3. ADVANCED TECHNICAL CALCULATIONS (The "Hedge Fund" Logic)
        # Moving Averages
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        # Volatility & Risk (ATR)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        # RSI
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # 4. DATA POINTS FOR REPORT
        current_price = df['Close'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]
        rsi_val = df['RSI'].iloc[-1]
        atr_val = df['ATR'].iloc[-1]
        
        # Price Targets (Fibonacci 61.8% Retracement)
        year_high = df['High'].max()
        year_low = df['Low'].min()
        fib_618 = year_high - (0.618 * (year_high - year_low))
        
        # Stop Loss (2x ATR)
        stop_loss = current_price - (atr_val * 2)

        # 5. SIGNALS & VERDICT
        trend = "📈 BULLISH" if current_price > sma_50 else "📉 BEARISH"
        golden_cross = "✅ GOLDEN CROSS" if sma_50 > sma_200 else "❌ BELOW 200-DAY"
        
        rsi_signal = "🟢 OVERSOLD" if rsi_val < 30 else "🔴 OVERBOUGHT" if rsi_val > 70 else "🟡 NEUTRAL"

        # 6. THE COMPLETE REPORT
        report = (
            f"🏦 *{symbol.upper()} - {full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Current Price:* ${current_price:.2f}\n"
            f"📊 *Market Trend:* {trend}\n"
            f"🧬 *Institutional:* {golden_cross}\n\n"
            f"🔍 **TECHNICAL SPECS**\n"
            f"• RSI (14): {rsi_val:.2f} ({rsi_signal})\n"
            f"• 50-Day SMA: ${sma_50:.2f}\n"
            f"• 200-Day SMA: ${sma_200:.2f}\n\n"
            f"🛡️ **RISK MANAGEMENT**\n"
            f"• Suggested Stop-Loss: ${stop_loss:.2f}\n"
            f"• Major Support (Fib 61.8%): ${fib_618:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        return report

    except Exception as e:
        print(f"Error in analysis: {e}")
        return f"❌ Error analyzing {symbol}. Check logs."