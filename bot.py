import pytz
import os
import json
import random
import datetime
import requests
from telegram.ext import Updater
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APP_URL = os.getenv("APP_URL")  # e.g. https://worker-production-25e7.up.railway.app
PORT = int(os.environ.get("PORT", 8443))

# Load content.json
with open("content.json", "r") as f:
    content = json.load(f)

# Load or create log.json
try:
    with open("log.json", "r") as f:
        log = json.load(f)
except FileNotFoundError:
    log = {
        "gm_used": [],
        "trading_used": [],
        "verses_used": [],
        "quotes_used": [],
        "prayers_used": [],
        "reminders_used": [],
        "catchup_log": []   # <-- new section for catch-up tracking
    }

# --- Utility: rotation with logging ---
def rotate_and_log(section, log_key):
    items = content.get(section, [])
    if not items:
        return {"message": "⚠️ No content available."}
    unused = [i for i in range(len(items)) if i not in log[log_key]]
    if not unused:
        log[log_key] = []
        unused = list(range(len(items)))
    choice = random.choice(unused)
    log[log_key].append(choice)
    with open("log.json", "w") as f:
        json.dump(log, f)
    return items[choice]

# --- Jobs ---
def good_morning_job(context):
    message = rotate_and_log("good_morning", "gm_used")["message"]
    context.bot.send_message(chat_id=CHAT_ID, text=message)

def verse_of_the_day_job(context):
    try:
        ref = rotate_and_log("verses", "verses_used")
        response = requests.get(f"https://bible-api.com/{ref.replace(' ', '+')}", timeout=5)
        response.raise_for_status()
        data = response.json()
        verse_text = data["text"]
        message = f"✨ Verse of the Day:\n{verse_text.strip()}\n📖 {ref}"
    except Exception:
        verse = rotate_and_log("verses", "verses_used")
        message = f"✨ Verse of the Day (Fallback):\n{verse}"
    context.bot.send_message(chat_id=CHAT_ID, text=message)

def daily_scripture_job(context):
    scripture = rotate_and_log("daily_scriptures", "verses_used")
    context.bot.send_message(chat_id=CHAT_ID, text=f"📖 Daily Scripture:\n{scripture}")

def trading_job(context):
    idea = rotate_and_log("trading", "trading_used")
    message = f"💹 Trading Idea:\n{idea['idea']}\n\n📖 {idea['scripture']}"
    context.bot.send_message(chat_id=CHAT_ID, text=message)

def quote_job(context):
    quote = rotate_and_log("quotes", "quotes_used")
    context.bot.send_message(chat_id=CHAT_ID, text=f"🌟 Motivation:\n{quote}")

def prayer_job(context):
    prayer = rotate_and_log("prayers", "prayers_used")
    context.bot.send_message(chat_id=CHAT_ID, text=prayer)

def reminder_job(context):
    reminder = rotate_and_log("reminders", "reminders_used")
    context.bot.send_message(chat_id=CHAT_ID, text=reminder)

# --- Seasonal Emojis ---
seasonal_emojis = {
    "Christmas": "🎄✨",
    "New Year": "🎉🥂",
    "Easter": "✝️🌅",
    "Ramadan": "🌙🕌",
    "Thanksgiving": "🦃🍂",
    "Valentine": "❤️🌹"
}

def seasonal_job(context):
    today = datetime.date.today().strftime("%m-%d")
    for event in content.get("seasonal", []):
        if event["date"] == today:
            emojis = "✨"
            for keyword, emoji in seasonal_emojis.items():
                if keyword.lower() in event["message"].lower():
                    emojis = emoji
                    break
            message = f"{emojis} {event['message']}"
            context.bot.send_message(chat_id=CHAT_ID, text=message)
            return

# --- Catch-Up Logic ---
def log_catchup(job_name, timestamp):
    log_entry = {"job": job_name, "time": timestamp}
    log["catchup_log"].append(log_entry)
    with open("log.json", "w") as f:
        json.dump(log, f)

def catch_up_jobs(bot):
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")  # e.g. "07:22 AM"
    hour = now.hour
    minute = now.minute

    if hour > 4 or (hour == 4 and minute >= 30):
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Good Morning")
        good_morning_job(bot)
        seasonal_job(bot)
        log_catchup("Good Morning", timestamp)

    if hour >= 6:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Verse of the Day")
        verse_of_the_day_job(bot)
        log_catchup("Verse of the Day", timestamp)

    if hour >= 7:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Daily Scripture")
        daily_scripture_job(bot)
        log_catchup("Daily Scripture", timestamp)

    if hour >= 9:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Trading Idea")
        trading_job(bot)
        log_catchup("Trading Idea", timestamp)

    if hour >= 12:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Motivation Quote")
        quote_job(bot)
        log_catchup("Motivation Quote", timestamp)

    if hour >= 15:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Prayer")
        prayer_job(bot)
        log_catchup("Prayer", timestamp)

    if hour >= 18:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Reminder")
        reminder_job(bot)
        log_catchup("Reminder", timestamp)

# --- Main ---
def main():
    updater = Updater(BOT_TOKEN)
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Africa/Lagos"))

    # Startup test message
    updater.bot.send_message(
        chat_id=CHAT_ID,
        text="✅ ChristocentricTraderBot is live via webhook!"
    )

    # --- Catch up missed jobs ---
    catch_up_jobs(updater.bot)

    # Daily rhythm
    scheduler.add_job(good_morning_job, 'cron', hour=4, minute=30, args=[updater.bot])
    scheduler.add_job(verse_of_the_day_job, 'cron', hour=6, minute=0, args=[updater.bot])
    scheduler.add_job(daily_scripture_job, 'cron', hour=7, minute=0, args=[updater.bot])
    scheduler.add_job(trading_job, 'cron', hour=9, minute=0, args=[updater.bot])
    scheduler.add_job(quote_job, 'cron', hour=12, minute=0, args=[updater.bot])
    scheduler.add_job(prayer_job, 'cron', hour=15, minute=0, args=[updater.bot])
    scheduler.add_job(reminder_job, 'cron', hour=18, minute=0, args=[updater.bot])
    scheduler.add_job(seasonal_job, 'cron', hour=4, minute=30, args=[updater.bot])

    scheduler.start()

    # Webhook setup
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{APP_URL}/{BOT_TOKEN}"
    )

    updater.idle()

if __name__ == "__main__":
    main()
