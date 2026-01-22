import yfinance as yf
import pandas_ta as ta

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        # Pull the company info to get the full name
        # We use ticker.info.get to prevent the bot from crashing if name is missing
        info = ticker.info
        full_name = info.get('longName', '')

        # Get historical data
        df = ticker.history(period="1y")

        if df.empty:
            return None

        # Technical Calculations
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_50'] = ta.ema(df['Close'], length=50)

        current_price = df['Close'].iloc[-1]
        rsi_value = df['RSI'].iloc[-1]
        
        rsi_signal = "🟢 BULLISH" if rsi_value < 30 else "🔴 BEARISH" if rsi_value > 70 else "🟡 NEUTRAL"

        # The Header now displays: SYMBOL Full Name
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