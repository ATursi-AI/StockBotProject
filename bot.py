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
        # Kicks out any old 'ghost' connections from the previous deploy
        bot.delete_webhook()
        print("🧹 Old sessions cleared. Waiting 5 seconds for cleanup...")
        time.sleep(5) 
    except Exception as e:
        print(f"Non-critical setup warning: {e}")

    print("📡 Initializing infinity_polling...")
    bot.infinity_polling(none_stop=True, skip_pending=True)

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
    bot.send_chat_action(message.chat.id, 'typing')
    report = get_stock_data(symbol)
    if report:
        bot.reply_to(message, report, parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Analysis Error.")

# We don't need the __main__ block because Gunicorn handles the 'app' directly.