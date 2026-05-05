import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load BOT_TOKEN from Railway environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello Digital! Your ChristocentricTrader bot is live and running.")

def main():
    # Build the application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
