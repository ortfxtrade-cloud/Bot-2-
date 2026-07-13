import os
import json
import threading
import yfinance as yf
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. Web Server (Render Port 8080) ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is alive!", 200

def run_flask_app():
    server.run(host="0.0.0.0", port=8080)

# --- 2. The Logic Class ---
class MultiPairOracle:
    def __init__(self):
        self.file_path = "watchlist.json"
        self.watchlist = self.load_watchlist()

    def load_watchlist(self):
        try:
            with open(self.file_path, "r") as f: return json.load(f)
        except: return ["BTC-USD", "EURUSD", "GBPUSD"]

    def save_watchlist(self):
        with open(self.file_path, "w") as f: json.dump(self.watchlist, f)

    def fetch_stats(self, pair):
        ticker = yf.Ticker(f"{pair}=X" if "USD" in pair and "-" not in pair else pair)
        # 5m interval, 1d period for real-time 5m binary option relevance
        data = ticker.history(period="1d", interval="5m")
        if data.empty: return None, None, None, None, None, None
        
        cv = data['Volume'].iloc[-1]
        nv = data['Volume'].mean()
        cvel = abs(data['Close'].iloc[-1] - data['Open'].iloc[-1])
        nvel = abs(data['Close'] - data['Open']).mean()
        c_spr = ((data['High'].iloc[-1] - data['Low'].iloc[-1]) / data['Close'].iloc[-1]) * 100
        n_spr = (((data['High'] - data['Low']) / data['Close']).mean()) * 100
        return cv, nv, cvel, nvel, c_spr, n_spr

    def generate_table(self):
        table = "```\n"
        table += f"{'PAIR':<9} | {'C.VOL':<6} | {'C.VEL':<6} | {'SPR%':<6} | {'ST'}\n"
        table += "----------|--------|--------|--------|-----\n"
        for p in self.watchlist:
            cv, nv, cvel, nvel, c_spr, n_spr = self.fetch_stats(p)
            if cv:
                is_unsafe = (cv > nv * 2.0) or (cvel > nvel * 2.0) or (c_spr > n_spr * 2.0)
                status = "⚠" if is_unsafe else "✔"
                table += f"{p:<9} | {cv/1000:<6.0f}k | {cvel:<6.4f} | {c_spr:<6.2f}% | {status}\n"
        return table + "```"

    async def show_table(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        table = self.generate_table()
        keyboard = [[InlineKeyboardButton("🔄 Refresh Data", callback_data='refresh')]]
        await update.message.reply_text(table, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='MarkdownV2')

    async def button_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=self.generate_table(), reply_markup=query.message.reply_markup, parse_mode='MarkdownV2')

# --- 3. Execution ---
if __name__ == "__main__":
    threading.Thread(target=run_flask_app, daemon=True).start()
    TOKEN = "8211995565:AAE7b59PtbFY-h40XmDW7tPtyY9ld6rOnao"
    oracle = MultiPairOracle()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("table", oracle.show_table))
    app.add_handler(CallbackQueryHandler(oracle.button_refresh, pattern='refresh'))
    app.run_polling()
