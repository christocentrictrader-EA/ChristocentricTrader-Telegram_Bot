import os
import datetime
import logging
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
ALPHA_KEY = os.getenv("ALPHA_KEY")  # Add this in Railway Variables

SUBSCRIBERS_FILE = "subscribers.json"

# Load subscribers from file
def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

# Save subscribers to file
def save_subscribers():
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subscribers), f)

# Initialize subscribers
subscribers = load_subscribers()

# Shared function for sending the trading signal
async def send_trading_signal(bot, chat_id: int, source: str) -> None:
    logging.info(f"Trading signal sent via {source} to chat_id={chat_id}")
    await bot.send_message(
        chat_id=chat_id,
        text="📊 Trading signal: Stay Christocentric in your trades!"
    )

# Bible Verse of the Day
def get_bible_verse():
    url = "https://labs.bible.org/api/?passage=votd&type=json"
    response = requests.get(url)
    data = response.json()[0]
    return f"📖 {data['bookname']} {data['chapter']}:{data['verse']} - {data['text']}"

# Market News
def get_market_news():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": "ALL",
        "apikey": ALPHA_KEY
    }
    response = requests.get(url, params=params)
    feed = response.json().get("feed", [])
    if feed:
        item = feed[0]
        return f"📰 {item['title']}\n{item['summary']}\nRead more: {item['url']}"
    else:
        return "📰 No market news available right now."

# Daily scheduled job
async def daily_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    for chat_id in subscribers:
        await send_trading_signal(context.bot, chat_id, source="scheduled job")

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        await query.edit_message_text(
            text="Available commands:\n/start - Subscribe & launch bot\n/stop - Unsubscribe\n/daily - Daily trading alert"
        )
    elif query.data == "signal":
        await send_trading_signal(context.bot, query.message.chat_id, source="inline button")
    elif query.data == "verse":
        verse = get_bible_verse()
        await query.edit_message_text(text=verse)
    elif query.data == "news":
        news = get_market_news()
        await query.edit_message_text(text=news)

# /start command (subscribe)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    subscribers.add(chat_id)
    save_subscribers()  # persist change

    keyboard = [
        [
            InlineKeyboardButton("Open Trading WebApp", web_app={"url": WEBAPP_URL}),
            InlineKeyboardButton("Help", callback_data="help")
        ],
        [
            InlineKeyboardButton("Daily Signal", callback_data="signal")
        ],
        [
            InlineKeyboardButton("Bible Verse", callback_data="verse"),
            InlineKeyboardButton("Market News", callback_data="news")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Hello Digital! Your ChristocentricTrader bot is live and running.\n✅ You are now subscribed to daily alerts.",
        reply_markup=reply_markup
    )

# /stop command (unsubscribe)
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers()  # persist change
        await update.message.reply_text("❌ You have unsubscribed from daily alerts.")
    else:
        await update.message.reply_text("You are not currently subscribed.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Schedule daily job at 9 AM
    job_queue = application.job_queue
    job_queue.run_daily(daily_message, time=datetime.time(hour=9, minute=0))

    application.run_polling()

if __name__ == "__main__":
    main()
