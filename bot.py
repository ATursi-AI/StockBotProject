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
def run_bot():
    start_bot()

if __name__ == "__main__":
    # This starts the bot thread
    threading_bot = Thread(target=run_bot)
    threading_bot.daemon = True
    threading_bot.start()
    
    # This starts the Flask web server that Render needs to see
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)