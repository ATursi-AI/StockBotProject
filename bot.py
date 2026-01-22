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

# 2. HEARTBEAT ROUTE
@app.route('/')
def home():
    return "📈 WallStreetBot Heartbeat: Active"

# 3. BACKGROUND WORKER
def run_bot():
    print("🚀 Background Bot process starting...")
    try:
        # Force a clean start by dropping old updates
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(2)
        print("📡 Bot is now POLLING...")
        bot.infinity_polling(none_stop=True, skip_pending=True)
    except Exception as e:
        print(f"❌ Polling Error: {e}")

# This starts the thread only once, even with Gunicorn workers
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    daemon = Thread(target=run_bot, daemon=True)
    daemon.start()

# 4. BOT HANDLERS
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)