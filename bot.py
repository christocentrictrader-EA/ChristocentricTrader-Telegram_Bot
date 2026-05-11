import pytz
import os
import json
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

# --- Deterministic selection for Good Morning ---
def good_morning_message():
    gms = content.get("good_morning", [])
    if not gms:
        return "*🌺 Good Morning!*\n_No content available._"
    today_index = datetime.datetime.now(pytz.timezone("Africa/Lagos")).weekday()
    gm = gms[today_index % len(gms)]
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")
    return "*🌺 Good Morning!*\n_"+gm["message"]+"_ \n_Posted at "+timestamp+"_"

# --- Verse of the Day (still rotates) ---
def verse_of_the_day_message():
    verses = content.get("verses", [])
    if not verses:
        return "*✨ Verse of the Day:*\n_No content available._"
    today_index = datetime.datetime.now(pytz.timezone("Africa/Lagos")).weekday()
    verse = verses[today_index % len(verses)]
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")
    return (
        "*✨ Verse of the Day:*\n"
        "'text': _"+verse["text"]+"_ \n"
        "'reference': __"+verse["reference"]+"__\n"
        "'theme': _"+verse["theme"]+"_ \n"
        "_Posted at "+timestamp+"_"
    )

# --- Daily Scripture (match actual weekday) ---
def daily_scripture_message():
    today = datetime.datetime.now(pytz.timezone("Africa/Lagos")).strftime("%A")
    scriptures = content.get("daily_scriptures", [])
    for s in scriptures:
        if s["day"].lower() == today.lower():
            now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
            timestamp = now.strftime("%I:%M %p")
            return (
                "*📖 Daily Scripture:*\n"
                "'day': __"+s["day"]+"__\n"
                "'scripture': __"+s["scripture"]+"__\n"
                "'text': _"+s["text"]+"_ \n"
                "'reflection': _"+s["reflection"]+"_ \n"
                "_Posted at "+timestamp+"_"
            )
    return "*📖 Daily Scripture:*\n_No scripture found for today._"

# --- Trading Idea ---
def trading_message():
    t = content.get("trading", [])
    if not t:
        return "*💹 Trading Idea:*\n_No content available._"
    today_index = datetime.datetime.now(pytz.timezone("Africa/Lagos")).weekday()
    idea = t[today_index % len(t)]
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")
    return (
        "*💹 Trading Idea:*\n"
        "'idea': _"+idea["idea"]+"_ \n"
        "'scripture': __"+idea["scripture"]+"__\n"
        "_Posted at "+timestamp+"_"
    )

# --- Quote ---
def quote_message():
    q = content.get("quotes", [])
    if not q:
        return "*🌟 Motivation:*\n_No content available._"
    today_index = datetime.datetime.now(pytz.timezone("Africa/Lagos")).weekday()
    quote = q[today_index % len(q)]
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")
    return (
        "*🌟 Motivation:*\n"
        "'quote': _"+quote["quote"]+"_ \n"
        "'author': __"+quote["author"]+"__\n"
        "_Posted at "+timestamp+"_"
    )

# --- Prayer ---
def prayer_message():
    p = content.get("prayers", [])
    if not p:
        return "*🙏 Prayer:*\n_No content available._"
    today_index = datetime.datetime.now(pytz.timezone("Africa/Lagos")).weekday()
    prayer = p[today_index % len(p)]
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")
    return "*🙏 "+prayer["title"]+"*\n_"+prayer["prayer"]+"_ \n_Posted at "+timestamp+"_"

# --- Reminder ---
def reminder_message():
    r = content.get("reminders", [])
    if not r:
        return "*⏰ Reminder:*\n_No content available._"
    today_index = datetime.datetime.now(pytz.timezone("Africa/Lagos")).weekday()
    reminder = r[today_index % len(r)]
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")
    return "*⏰ Reminder:*\n_"+reminder["reminder"]+"_ \n_Posted at "+timestamp+"_"

# --- Seasonal ---
def seasonal_message():
    today = datetime.date.today().strftime("%m-%d")
    now = datetime.datetime.now(pytz.timezone("Africa/Lagos"))
    timestamp = now.strftime("%I:%M %p")
    for event in content.get("seasonal", []):
        if event["date"] == today:
            return "*✨ Seasonal Message:*\n_"+event["message"]+"_ \n_Posted at "+timestamp+"_"
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
        intended = "04:30 AM"
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp} (intended {intended}): Good Morning\n\n{good_morning_message()}", parse_mode="Markdown")
        log_catchup("Good Morning", timestamp)
        seasonal = seasonal_message()
        if seasonal:
            bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp} (intended {intended}): Seasonal\n\n{seasonal}", parse_mode="Markdown")
            log_catchup("Seasonal", timestamp)

    if now.hour >= 6:
        intended = "06:00 AM"
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp} (intended {intended}): Verse of the Day\n\n{verse_of_the_day_message()}", parse_mode="Markdown")
        log_catchup("Verse of the Day", timestamp)

    if now.hour >= 7:
        intended = "07:00 AM"
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Catch‑Up at {timestamp} (intended {intended}): Daily Scripture\n\n{daily_scripture_message()}", parse_mode="Markdown")
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

    today = datetime.datetime.now
# Startup message safeguard
    today = datetime.datetime.now(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d")
    if log.get("startup_done") != today:
        updater.bot.send_message(
            chat_id=CHAT_ID,
            text="✅ ChristocentricTraderBot is live via webhook!",
            parse_mode="Markdown"
        )
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
