import os
import threading
import yfinance as yf
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# 1. Flask Web Server (For Render Port Binding)
server = Flask(__name__)

@server.route('/')
def live_health_status_endpoint():
    return "Bot is alive!", 200

def run_flask_app():
    # Forced to 8080 as requested
    server.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

# 2. Correct Class Structure using 'self'
class MultiPairOracle:
    def __init__(self, token, chat_id):
        self.token = "8211995565:AAE7b59PtbFY-h40XmDW7tPtyY9ld6rOnao"
        self.chat_id = "8701685996"
        self.watchlist = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", 
            "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
            "AUDJPY", "CHFJPY", "CADJPY", "EURCHF", "GBPCHF"
        ]

    def fetch_data(self, pair):
        ticker = yf.Ticker(f"{pair}=X")
        data = ticker.history(period="1d", interval="1m")
        if data.empty: return None, None
        return data['Volume'].iloc[-1], data['Close'].iloc[-1]

    def get_menu_keyboard(self):
        keyboard = [[InlineKeyboardButton(f"Check {p}", callback_data=f"check_{p}")] for p in self.watchlist]
        return InlineKeyboardMarkup(keyboard)

    async def start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Select a pair to analyze:", reply_markup=self.get_menu_keyboard())
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):  
        query = update.callback_query
        await query.answer()
        
        if query.data and query.data.startswith("check_"):
            pair = query.data.split("_")[1]
            vol, price = self.fetch_data(pair)
            if vol is None:
                await query.edit_message_text(f"⚠️ Could not fetch data for {pair}.")
            else:
                msg = f"📊 {pair} Analysis: Vol={vol:.0f}, Price={price:.5f}."
                await query.edit_message_text(msg, reply_markup=self.get_menu_keyboard())

# 3. Execution Block
if __name__ == "__main__":
    # Start Web Server in background thread
    threading.Thread(target=run_flask_app, daemon=True).start()
    
    # Securely get credentials from environment variables
    TOKEN = "8211995565:AAE7b59PtbFY-h40XmDW7tPtyY9ld6rOnao"
    CHAT_ID = "8701685996"
    # Initialize Oracle with 'self' handled automatically
    oracle = MultiPairOracle(TOKEN, CHAT_ID)
    
    # Telegram Application Setup
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", oracle.start_menu))
    app.add_handler(CallbackQueryHandler(oracle.button_handler))
    
    print("Bot is running on port 8080...")
    app.run_polling()
