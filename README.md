# ChristocentricTraderEA Telegram Bot

A Telegram bot built with [python-telegram-bot](https://python-telegram-bot.org) and deployed on [Railway](https://railway.app) for 24/7 uptime.

## Features
- Responds to `/start` with a welcome message
- Provides inline keyboard buttons linking to the ChristocentricTrader WebApp
- Runs continuously on Railway

## Project Structure

bot.py              # Main bot script requirements.txt    # Python dependencies Procfile            # Railway process definition .gitignore          # Excluded files and folders

## Running Locally
```bash
pip install -r requirements.txt
python bot.py

DeploymentPush this repo to GitHubConnect the repo to RailwayAdd your bot token as an environment variable:Key: BOT_TOKENValue: <your-telegram-bot-token>Railway will install dependencies and run bot.py automatically

---

### 🛠 How to Create It in Termux
1. Open the file with nano:
   ```bash
   nano README.md
Paste the text above into the editor.Save and exit nano:Press CTRL + O → Enter (to save).Press CTRL + X (to exit).
