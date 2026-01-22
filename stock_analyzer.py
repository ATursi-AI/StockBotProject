import yfinance as yf
import pandas_ta as ta

def get_stock_data(symbol):
    try:
        # 1. Create the ticker object
        ticker = yf.Ticker(symbol)
        
        # 2. Get historical data first (this is the most reliable part of the library)
        df = ticker.history(period="1y")

        if df.empty:
            return None

        # 3. FIX: Get Company Name from Metadata instead of .info
        # This works much better on Cloud Servers (Render)
        metadata = ticker.history_metadata
        full_name = metadata.get('longName', metadata.get('symbol', symbol.upper()))

        # 4. Calculate Technicals
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_50'] = ta.ema(df['Close'], length=50)

        current_price = df['Close'].iloc[-1]
        rsi_value = df['RSI'].iloc[-1]
        
        rsi_signal = "🟢 BULLISH" if rsi_value < 30 else "🔴 BEARISH" if rsi_value > 70 else "🟡 NEUTRAL"

        # 5. Format the Header: "AAPL Apple Inc."
        report = (
            f"📊 *{symbol.upper()} {full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Current Price:* ${current_price:.2f}\n"
            f"📈 *RSI (14):* {rsi_value:.2f} ({rsi_signal})\n"
            f"⚡ *Trend:* {'📈 Uptrend' if current_price > df['EMA_50'].iloc[-1] else '📉 Downtrend'}\n"
        )
        return report

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None