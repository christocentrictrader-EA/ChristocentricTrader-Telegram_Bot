import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load BOT_TOKEN from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Simple start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I am your ChristocentricTrader bot, ready to serve.")

# Example scheduled job
async def scheduled_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="This is a scheduled message from the bot."
    )

def main():
    # Build the application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))

    # Schedule a repeating job (every 10 seconds for demo)
    job_queue = application.job_queue
    job_queue.run_repeating(scheduled_job, interval=10, first=10, chat_id=123456789)

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
