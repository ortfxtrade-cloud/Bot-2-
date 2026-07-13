import os
import json
import threading
import yfinance as yf
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. Web Server (Render) ---
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
        self.available_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP", "BTC-USD", "ETH-USD"]

    def load_watchlist(self):
        try:
            with open(self.file_path, "r") as f: return json.load(f)
        except: return ["BTC-USD", "EURUSD"]

    def save_watchlist(self):
        with open(self.file_path, "w") as f: json.dump(self.watchlist, f)

    def fetch_stats(self, pair):
        ticker = yf.Ticker(f"{pair}=X" if "USD" in pair and "-" not in pair else pair)
        data = ticker.history(period="1d", interval="5m")
        if data.empty: return None, None, None, None, None, None
        return data['Volume'].iloc[-1], data['Volume'].mean(), abs(data['Close'].iloc[-1] - data['Open'].iloc[-1]), abs(data['Close'] - data['Open']).mean(), ((data['High'].iloc[-1] - data['Low'].iloc[-1]) / data['Close'].iloc[-1]) * 100, (((data['High'] - data['Low']) / data['Close']).mean()) * 100

    def get_main_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data='refresh')],
            [InlineKeyboardButton("➕ Add Pair", callback_data='add_menu'), 
             InlineKeyboardButton("➖ Remove Pair", callback_data='rem_menu')]
        ])

    def generate_table(self):
        table = "```\nPAIR      | C/N VOL  | C/N VEL  | C/N SPR% | ST\n----------|----------|----------|----------|-----\n"
        for p in self.watchlist:
            cv, nv, cvel, nvel, c_spr, n_spr = self.fetch_stats(p)
            if cv:
                # 2.0x Threshold logic for 5m binary options
                is_unsafe = (cv > nv * 2.0) or (cvel > nvel * 2.0) or (c_spr > n_spr * 2.0)
                status = "⚠" if is_unsafe else "✔"
                table += f"{p:<9} | {cv/1000:.0f}/{nv/1000:.0f} | {cvel:.3f}/{nvel:.3f} | {c_spr:.1f}/{n_spr:.1f} | {status}\n"
        return table + "```"

    async def show_table(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.generate_table(), reply_markup=self.get_main_keyboard(), parse_mode='MarkdownV2')

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == 'refresh':
            await query.edit_message_text(self.generate_table(), reply_markup=self.get_main_keyboard(), parse_mode='MarkdownV2')
        elif data == 'add_menu':
            keyboard = [[InlineKeyboardButton(p, callback_data=f'add_{p}')] for p in self.available_pairs if p not in self.watchlist]
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='refresh')])
            await query.edit_message_text("Select a pair to add:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif data.startswith('add_'):
            pair = data.split('_')[1]
            if pair not in self.watchlist: self.watchlist.append(pair); self.save_watchlist()
            await query.edit_message_text(f"✅ Added {pair}", reply_markup=self.get_main_keyboard())
        elif data == 'rem_menu':
            keyboard = [[InlineKeyboardButton(p, callback_data=f'rem_{p}')] for p in self.watchlist]
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='refresh')])
            await query.edit_message_text("Select to remove:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif data.startswith('rem_'):
            pair = data.split('_')[1]
            if pair in self.watchlist: self.watchlist.remove(pair); self.save_watchlist()
            await query.edit_message_text(f"🗑 Removed {pair}", reply_markup=self.get_main_keyboard())

# --- 3. Execution ---
if __name__ == "__main__":
    threading.Thread(target=run_flask_app, daemon=True).start()
    TOKEN = "8211995565:AAE7b59PtbFY-h40XmDW7tPtyY9ld6rOnao"
    oracle = MultiPairOracle()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("table", oracle.show_table))
    app.add_handler(CallbackQueryHandler(oracle.handle_callback))
    app.run_polling()
