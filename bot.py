import os
import telebot
import time
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from stock_analyzer import get_stock_data

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_STOCK_TOKEN")

# 1. Initialize Bot & Flask
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "📈 WallStreetBot is running!"

# 2. This function handles the Telegram polling
def start_bot():
    print("🚀 Bot process starting...")
    try:
        # STEP 1: FORCE RESET - This kills any other instance's connection
        bot.delete_webhook(drop_pending_updates=True)
        print("🧹 Telegram connection reset. Waiting 5s for Render cleanup...")
        time.sleep(5) 
        
        print("📡 Initializing infinity_polling...")
        # skip_pending=True ensures we don't spam old messages on startup
        bot.infinity_polling(none_stop=True, skip_pending=True, timeout=60, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ Critical Bot Error: {e}")
        time.sleep(10) # Wait before Render restarts the process

# 3. Start the bot in a background thread
threading_bot = Thread(target=start_bot)
threading_bot.daemon = True
threading_bot.start()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me a ticker symbol (e.g., AAPL) for a Super-Scan.")

@bot.message_handler(func=lambda message: True)
def handle_stock(message):
    symbol = message.text.upper().strip()
    # Basic validation to ensure it looks like a ticker
    if len(symbol) > 6 or not symbol.isalpha():
        return

    bot.send_chat_action(message.chat.id, 'typing')
    try:
        report = get_stock_data(symbol)
        if report:
            bot.reply_to(message, report, parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Analysis Error: Could not generate report.")
    except Exception as e:
        bot.reply_to(message, f"❌ System Error: {str(e)}")

# Gunicorn uses 'app' directly