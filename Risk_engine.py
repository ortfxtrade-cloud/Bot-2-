import yfinance as yf
import requests
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

class MultiPairOracle:
    def __init__(token, chat_id):
        self.token="8211995565:AAE7b59PtbFY-h40XmDW7tPtyY9ld6rOnao"
        self.chat_id= "8701685996"
        self.watchlist= [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", 
            "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
            "AUDJPY", "CHFJPY", "CADJPY", "EURCHF", "GBPCHF"
        ]

    def fetch_data(chat_id, pair):
        ticker = yf.Ticker(f"{pair}=X")
        data = ticker.history(period="1d", interval="1m")
        if data.empty: return None, None
        return data['Volume'].iloc[-1], data['Close'].iloc[-1]

        
# RIGHT
def get_menu_keyboard(chat_id):
    """Generates a dynamic menu based on the watchlist."""
    keyboard = [...] # Everything inside is indented by 4 spaces
    """Generates a dynamic menu based on the watchlist."""
    keyboard = [
    [InlineKeyboardButton(f"Check {p}", callback_data=f"check_{p}")]
    for p in self.watchlist
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Triggered by /start command."""
        await update.message.reply_text("Select a pair to analyze:", reply_markup=self.get_menu_keyboard()    
        async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles inline button clicks."""
        query = update.callback_query
        await query.answer()  # Necessary to stop the "loading" animation
        
        data = query.data
        if data.startswith("check_"):
            pair = data.split("_")[1]
            vol, price = self.fetch_data(pair)
            
            if vol is None:
                await query.edit_message_text(f"⚠️ Could not fetch data for {pair}.")
            else:
                msg = f"📊 {pair} Analysis: Vol={vol}, Price={price:.5f}. [System: SAFE]"
                await query.edit_message_text(msg, reply_markup=self.get_menu_keyboard())

# --- Execution ---
if __name__ == "__main__":
    TOKEN = "8211995565:AAE7b59PtbFY-h40XmDW7tPtyY9ld6rOnao"
    CHAT_ID = "8701685996"
    
    oracle = MultiPairOracle(TOKEN, CHAT_ID)
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", oracle.start_menu))
    app.add_handler(CallbackQueryHandler(oracle.button_handler))
    
    print("Bot is running...")
    app.run_polling()
