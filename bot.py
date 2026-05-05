import os
import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Shared function for sending the trading signal
async def send_trading_signal(bot, chat_id: int, source: str) -> None:
    logging.info(f"Trading signal sent via {source} to chat_id={chat_id}")
    await bot.send_message(
        chat_id=chat_id,
        text="📊 Trading signal: Stay Christocentric in your trades!"
    )

# Daily scheduled job
async def daily_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_trading_signal(context.bot, CHAT_ID, source="scheduled job")

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        await query.edit_message_text(
            text="Available commands:\n/start - Launch bot\n/help - Show help\n/daily - Daily trading alert"
        )
    elif query.data == "signal":
        await send_trading_signal(context.bot, query.message.chat_id, source="inline button")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Open Trading WebApp", web_app={"url": WEBAPP_URL}),
            InlineKeyboardButton("Help", callback_data="help")
        ],
        [
            InlineKeyboardButton("Daily Signal", callback_data="signal")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Hello Digital! Your ChristocentricTrader bot is live and running.",
        reply_markup=reply_markup
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Schedule daily job at 9 AM
    job_queue = application.job_queue
    job_queue.run_daily(daily_message, time=datetime.time(hour=9, minute=0))

    application.run_polling()

if __name__ == "__main__":
    main()
