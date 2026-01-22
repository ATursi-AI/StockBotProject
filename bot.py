import os
import telebot
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from stock_analyzer import get_stock_data

# 1. Load Environment Variables
load_dotenv()

# 2. Grab the Token safely
TELEGRAM_TOKEN = os.getenv("TELEGRAM_STOCK_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ Error: TELEGRAM_STOCK_TOKEN not found.")
    exit()
else:
    print("✅ Token loaded successfully.")

# 3. Initialize the Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- RENDER HEARTBEAT SETUP ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    # Render provides a 'PORT' environment variable. We MUST use it.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Ensures the thread closes when the main program stops
    t.start()
# ------------------------------

print("📈 WallStreetBot is online. Waiting for tickers...")

# --- TELEGRAM HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me a ticker symbol (e.g., AAPL, NVDA) for a technical analysis.")

@bot.message_handler(func=lambda message: True)
def handle_stock(message):
    symbol = message.text.upper().strip()
    
    if " " in symbol or len(symbol) > 6:
        bot.reply_to(message, "Please send a valid ticker symbol (e.g., NVDA).")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    report = get_stock_data(symbol)
    
    if report:
        bot.reply_to(message, report, parse_mode='Markdown')
    else:
        bot.reply_to(message, f"❌ Could not find data for '{symbol}'.")

# 4. Run the Bot
if __name__ == "__main__":
    # Start the web server first
    keep_alive()
    
    # Start the Telegram polling
    # none_stop=True helps it reconnect if there's a network blip
    bot.infinity_polling(none_stop=True)