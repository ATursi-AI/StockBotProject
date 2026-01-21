from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import stock_analyzer  # Ensure this file is in the same folder
import os

# --- CONFIGURATION ---
TOKEN = "8526258831:AAFZs9Fqs0NsjRAqkhaW-5cveouUpuFIoJo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initial Welcome Message"""
    await update.message.reply_text(
        "🤖 **StockBot Pro V18 Online**\n\n"
        "Send me any ticker symbol (e.g., NVDA) for a Deep Scan report."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main Logic: Responds to Tickers"""
    # 1. Clean up user input
    user_input = update.message.text.upper().strip()
    
    # 2. Professional UX Update: "Analyzing..." instead of "Drawing..."
    status_msg = await update.message.reply_text(f"🚀 Analyzing {user_input}...")

    try:
        # 3. Call the Brain
        # This is where the 'AttributeError' happens if analyze_stock isn't defined
        chart_file, report = stock_analyzer.analyze_stock(user_input)
        
        # 4. Send the Professional Text Report
        await update.message.reply_text(report, parse_mode="Markdown")
        
        # 5. Optional: Cleanup chart file if one was created
        if chart_file and os.path.exists(chart_file):
            os.remove(chart_file)

    except AttributeError:
        await update.message.reply_text("⚠️ Error: The analyzer engine is missing the 'analyze_stock' function.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Analysis Error: {str(e)}")
    finally:
        # Delete the "Analyzing..." status to keep the chat clean
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Listeners
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("💎 StockBot Pro is live and listening...")
    app.run_polling()