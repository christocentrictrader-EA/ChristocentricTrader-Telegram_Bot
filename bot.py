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
APP_URL = os.getenv("APP_URL")
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
        "catchup_log": [],
        "catchup_done": "",
        "startup_done": ""
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

# --- Message builders with Markdown formatting ---
def good_morning_message():
    gm = rotate_and_log("good_morning", "gm_used")
    return "*🌺 Good Morning!*\n_"+gm["message"]+"_"

def verse_of_the_day_message():
    verse = rotate_and_log("verses", "verses_used")
    return (
        "*✨ Verse of the Day:*\n"
        "'text': _"+verse["text"]+"_ \n"
        "'reference': __"+verse["reference"]+"__\n"
        "'theme': _"+verse["theme"]+"_"
    )

def daily_scripture_message():
    s = rotate_and_log("daily_scriptures", "verses_used")
    return (
        "*📖 Daily Scripture:*\n"
        "'day': __"+s["day"]+"__\n"
        "'scripture': __"+s["scripture"]+"__\n"
        "'text': _"+s["text"]+"_ \n"
        "'reflection': _"+s["reflection"]+"_"
    )

def trading_message():
    t = rotate_and_log("trading", "trading_used")
    return (
        "*💹 Trading Idea:*\n"
        "'idea': _"+t["idea"]+"_ \n"
        "'scripture': __"+t["scripture"]+"__"
    )

def quote_message():
    q = rotate_and_log("quotes", "quotes_used")
    return (
        "*🌟 Motivation:*\n"
        "'quote': _"+q["quote"]+"_ \n"
        "'author': __"+q["author"]+"__"
    )

def prayer_message():
    p = rotate_and_log("prayers", "prayers_used")
    return "*🙏 "+p["title"]+"*\n_"+p["prayer"]+"_"

def reminder_message():
    r = rotate_and_log("reminders", "reminders_used")
    return "*⏰ Reminder:*\n_"+r["reminder"]+"_"

def seasonal_message():
    today = datetime.date.today().strftime("%m-%d")
    for event in content.get("seasonal", []):
        if event["date"] == today:
            return "*✨ Seasonal Message:*\n_"+event["message"]+"_"
    return None

# --- Catch-Up Logic ---
def log_catchup(job_name, timestamp):
    log_entry = {"job": job_name, "time": timestamp}
    log["catchup_log"].append(log_entry)
    with open("log.json", "w") as f:
        json.dump(log, f)

def catch_up_jobs(bot):
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    today = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%I:%M %p")

    if log.get("catchup_done") == today:
        return

    log["catchup_done"] = today
    with open("log.json", "w") as f:
        json.dump(log, f)

    if now.hour > 4 or (now.hour == 4 and now.minute >= 30):
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Good Morning\n\n{good_morning_message()}", parse_mode="Markdown")
        log_catchup("Good Morning", timestamp)
        seasonal = seasonal_message()
        if seasonal:
            bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Seasonal\n\n{seasonal}", parse_mode="Markdown")
            log_catchup("Seasonal", timestamp)

    if now.hour >= 6:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Verse of the Day\n\n{verse_of_the_day_message()}", parse_mode="Markdown")
        log_catchup("Verse of the Day", timestamp)

    if now.hour >= 7:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp}: Daily Scripture\n\n{daily_scripture_message()}", parse_mode="Markdown")
        log_catchup("Daily Scripture", timestamp)

# --- Midnight Reset ---
def reset_flags():
    log["catchup_done"] = ""
    log["startup_done"] = ""
    with open("log.json", "w") as f:
        json.dump(log, f)

# --- Main ---
def main():
    updater = Updater(BOT_TOKEN)
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Africa/Lagos"))

    # Startup message safeguard
    today = datetime.datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d")
    if log.get("startup_done") != today:
        updater.bot.send_message(chat_id=CHAT_ID, text="✅ ChristocentricTraderBot is live via webhook!", parse_mode="Markdown")
        log["startup_done"] = today
        with open("log.json", "w") as f:
            json.dump(log, f)

    # Catch up missed jobs
    catch_up_jobs(updater.bot)

    # Daily rhythm with Markdown formatting
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, good_morning_message(), parse_mode="Markdown"), 'cron', hour=4, minute=30)
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, verse_of_the_day_message(), parse_mode="Markdown"), 'cron', hour=6, minute=0)
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, daily_scripture_message(), parse_mode="Markdown"), 'cron', hour=7, minute=0)
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, trading_message(), parse_mode="Markdown"), 'cron', hour=9, minute=0)
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, quote_message(), parse_mode="Markdown"), 'cron', hour=12, minute=0)
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, prayer_message(), parse_mode="Markdown"), 'cron', hour=15, minute=0)
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, reminder_message(), parse_mode="Markdown"), 'cron', hour=18, minute=0)
    scheduler.add_job(lambda: updater.bot.send_message(CHAT_ID, seasonal_message(), parse_mode="Markdown"), 'cron', hour=4, minute=30)

    # Midnight reset of flags
    scheduler.add_job(reset_flags, 'cron', hour=0, minute=0)

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
