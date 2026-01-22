import os
import telebot
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from stock_analyzer import get_stock_data

# 1. Load Environment Variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_STOCK_TOKEN")

if not TELEGRAM_TOKEN:
    exit("❌ Error: TELEGRAM_STOCK_TOKEN not found.")

# 2. Initialize the Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- WEB SERVER (HEARTBEAT) ---
app = Flask(__name__) # Use __name__ instead of '' for Gunicorn

@app.route('/')
def home():
    return "I am alive!"

def run():
    # This is still here for local testing, 
    # but Gunicorn will handle the port on Render.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
# ------------------------------

print("📈 WallStreetBot is online...")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me a ticker symbol (e.g., AAPL, NVDA) for a technical analysis.")

@bot.message_handler(func=lambda message: True)
def handle_stock(message):
    symbol = message.text.upper().strip()
    if " " in symbol or len(symbol) > 6:
        bot.reply_to(message, "Please send a valid ticker symbol.")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    report = get_stock_data(symbol)
    
    if report:
        bot.reply_to(message, report, parse_mode='Markdown')
    else:
        bot.reply_to(message, f"❌ Could not find data for '{symbol}'.")

if __name__ == "__main__":
    # If running locally (python bot.py), keep_alive starts the server.
    # On Render, Gunicorn will start 'app' directly.
    if not os.environ.get("GUNICORN_RUNNING"):
        keep_alive()
    
    bot.infinity_polling(none_stop=True)