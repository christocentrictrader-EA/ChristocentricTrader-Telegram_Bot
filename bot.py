from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
from logging.handlers import RotatingFileHandler

# Logging setup with rotation
file_handler = RotatingFileHandler("bot.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), file_handler]
)
logging.getLogger("telegram").setLevel(logging.DEBUG)
logging.getLogger("telegram.ext").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Open WebApp", url="https://christocentrictrader.d9thprofithub.com.ng")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Tap below to open the WebApp:", reply_markup=reply_markup)

if __name__ == "__main__":
    app = (
        Application.builder()
        .token("8496752004:AAEEEWE08jO9Wv9WqT_ygs8KyG_y9_Vctmk")
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
