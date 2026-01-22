import os
import telebot
import time
import threading
from flask import Flask
from dotenv import load_dotenv
from stock_analyzer import get_stock_data

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_STOCK_TOKEN")

# 1. Initialize Bot & Flask
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# 2. THE BACKGROUND POLLING FUNCTION
def run_bot_background():
    print("🚀 Background Bot process starting...")
    try:
        # Clear old sessions
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(5) 
        print("📡 Bot is now POLLING...")
        bot.infinity_polling(none_stop=True, skip_pending=True)
    except Exception as e:
        print(f"❌ Polling Error: {e}")

# 3. START THE THREAD IMMEDIATELY
# This ensures the thread starts regardless of how Gunicorn boots the app
bot_thread = threading.Thread(target=run_bot_background, daemon=True)
bot_thread.start()

@app.route('/')
def home():
    return "📈 WallStreetBot is active and polling!"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me a ticker symbol (e.g., AAPL) for a Super-Scan.")

@bot.message_handler(func=lambda message: True)
def handle_stock(message):
    symbol = message.text.upper().strip()
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        report = get_stock_data(symbol)
        if report:
            bot.reply_to(message, report, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ System Error: {str(e)}")

if __name__ == "__main__":
    # Local testing only; Render uses Gunicorn to call 'app'
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)