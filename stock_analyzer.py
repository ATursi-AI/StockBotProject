import yfinance as yf
import pandas_ta as ta

def get_stock_data(symbol):
    try:
        # Create the ticker object
        ticker = yf.Ticker(symbol)
        
        # 1. NEW: Get the Full Company Name
        # info can be slow, so we use a safe get() method
        info = ticker.info
        company_name = info.get('longName', 'Unknown Company')

        # 2. Get the historical data for analysis
        df = ticker.history(period="1y")

        if df.empty:
            return None

        # Calculate Technicals (RSI, EMA, etc.)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['EMA_50'] = ta.ema(df['Close'], length=50)

        current_price = df['Close'].iloc[-1]
        rsi_value = df['RSI'].iloc[-1]
        
        # Determine signals
        rsi_signal = "🟢 BULLISH" if rsi_value < 30 else "🔴 BEARISH" if rsi_value > 70 else "🟡 NEUTRAL"

        # 3. Format the Report with the Full Name
        report = (
            f"📊 *{company_name}* ({symbol.upper()})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Current Price:* ${current_price:.2f}\n"
            f"📈 *RSI (14):* {rsi_value:.2f} ({rsi_signal})\n"
            f"⚡ *Trend:* {'📈 Uptrend' if current_price > df['EMA_50'].iloc[-1] else '📉 Downtrend'}\n"
        )
        return report

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None