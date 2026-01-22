import yfinance as yf
import pandas_ta as ta

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        # 1. Get historical data (most reliable)
        df = ticker.history(period="1y")
        if df.empty:
            return None

        # 2. TRIPLE-CHECK for Company Name
        # Method A: Check the metadata from the history download
        full_name = ticker.history_metadata.get('longName')
        
        # Method B: If A fails, try a fast_info check
        if not full_name:
            try:
                full_name = ticker.fast_info.get('longName')
            except:
                full_name = None
        
        # Method C: If all else fails, use the Ticker Symbol
        if not full_name:
            full_name = symbol.upper()

        # 3. Technicals
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_50'] = ta.ema(df['Close'], length=50)

        current_price = df['Close'].iloc[-1]
        rsi_value = df['RSI'].iloc[-1]
        rsi_signal = "🟢 BULLISH" if rsi_value < 30 else "🔴 BEARISH" if rsi_value > 70 else "🟡 NEUTRAL"

        # 4. Format the Output Header
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