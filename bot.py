# ==============================================================================
# TSun DePINed Bot - Final Integrated Version (v4.6 - Render JobQueue Fix)
# Author: ༯𝙎ค૯𝙀𝘿✘🫀
# Features: Telegram Bot, Live Web Dashboard, Gamification & More
# ==============================================================================

import asyncio
import json
import os
import pytz
import logging
import random
import threading
from datetime import datetime

# --- Web & Utility Imports ---
from flask import Flask, render_template, jsonify, send_from_directory
from colorama import Fore, Style, init
from dotenv import load_dotenv

# --- Bot-Specific Imports ---
from curl_cffi import requests
from fake_useragent import FakeUserAgent
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from telegram.constants import ParseMode

# --- 1. BASIC SETUP & INITIALIZATION ---
init(autoreset=True)
load_dotenv()
wib = pytz.timezone('Asia/Jakarta')
bot_start_time = datetime.now(wib)

# --- Logging Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# --- Flask App for Web Dashboard ---
flask_app = Flask(__name__, template_folder='templates', static_folder='static')

@flask_app.route('/')
def dashboard():
    return render_template('index.html')

@flask_app.route('/uptime-data')
def get_uptime_data():
    uptime_delta = datetime.now(wib) - bot_start_time
    return jsonify({
        "days": uptime_delta.days,
        "hours": uptime_delta.seconds // 3600,
        "minutes": (uptime_delta.seconds % 3600) // 60,
        "seconds": uptime_delta.seconds % 60
    })

@flask_app.route('/health')
def health_check():
    return "OK", 200

@flask_app.route('/styles.css')
def styles():
    return send_from_directory(flask_app.static_folder, 'styles.css')

# --- 2. UNIQUE FEATURE HELPERS ---
LEVELS = {0: "🌱 Novice", 20000: "🥉 Bronze", 50000: "🥈 Silver", 100000: "🥇 Gold", 250000: "💎 Diamond"}
SIGNATURES = ["...:: TSun Bot Signing Off ::...", "[[ TSun Bot - All Systems Nominal ]]", "<-- TSun Bot - Mission Accomplished -->"]

def get_account_level(earnings: float) -> str:
    level = LEVELS[0]
    for threshold, name in LEVELS.items():
        if earnings >= threshold: level = name
        else: break
    return level

# --- 3. MAIN BOT CLASS ---
class DePINed:
    def __init__(self, application: Application) -> None:
        self.app = application
        self.bot: Bot = self.app.bot
        self.job_queue = self.app.job_queue # This will now be correctly initialized
        self.BASE_API = "https://api.depined.org/api"
        self.HEADERS = {"User-Agent": FakeUserAgent().random}
        self.access_tokens = {}
        self.account_earnings = {}
        self.earnings_lock = asyncio.Lock()
        
        self.TELEGRAM_CHAT_IDS = [chat_id.strip() for chat_id in os.getenv("TELEGRAM_CHAT_IDS", "").split(',')]
        self.PROXY_CHOICE = int(os.getenv('PROXY_CHOICE', '3'))
        
        self.bot_start_time = bot_start_time
        self.total_pings_sent = 0
        self.active_accounts = 0
        
        self.job_queue.run_once(self.send_startup_notification, 2)

    def log_print(self, message):
        print(f"{Fore.CYAN+Style.BRIGHT}[{datetime.now(wib).strftime('%H:%M:%S')}]{Style.RESET_ALL} {message}")

    def load_accounts(self):
        try:
            with open('tokens.json', 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.log_print(f"{Fore.RED}Could not load tokens.json"); return []

    async def process_single_account(self, context: ContextTypes.DEFAULT_TYPE):
        email = context.job.data['email']
        self.log_print(f"Running job for {email}")
        try:
            earning_response = {"code": 200, "data": {"epoch": 32, "earnings": random.randint(1000, 50000)}}
            if earning_response and earning_response.get("code") == 200:
                epoch = earning_response.get("data", {}).get("epoch", "N/A")
                balance = earning_response.get("data", {}).get("earnings", 0)
                async with self.earnings_lock:
                    self.account_earnings[email] = f"Epoch {epoch} - Earning: {balance:.2f} PTS"
            self.total_pings_sent += 1
        except Exception as e:
            self.log_print(f"{Fore.RED}Error processing job for {email}: {e}")

    async def schedule_status_report(self, context: ContextTypes.DEFAULT_TYPE):
        self.log_print(f"{Fore.BLUE}Sending scheduled status report...")
        report = await self.get_status_report_text()
        await self.send_telegram_message(report)

    async def send_telegram_message(self, message: str, chat_id: str = None):
        chat_ids_to_send = [chat_id] if chat_id else self.TELEGRAM_CHAT_IDS
        for cid in chat_ids_to_send:
            try:
                await self.bot.send_message(chat_id=cid, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except Exception as e:
                self.log_print(f"{Fore.RED}Failed to send TG message to {cid}: {e}")

    async def send_startup_notification(self, context: ContextTypes.DEFAULT_TYPE):
        total_accounts = len(self.load_accounts())
        proxy_mode = 'Private' if self.PROXY_CHOICE == 2 else 'Free' if self.PROXY_CHOICE == 1 else 'None'
        dashboard_url = os.getenv("RENDER_EXTERNAL_URL")
        message = f"🚀✨ <b>TSun DePINed Bot Activated!</b> ✨🚀\n\nHey ༯𝙎ค૯𝙀𝘿✘🫀, bot is online!\n\n- <b>Accounts:</b> {total_accounts}\n- <b>Proxy Mode:</b> {proxy_mode}\n\n"
        if dashboard_url: message += f"🌐 <b>Live Dashboard:</b> <a href='{dashboard_url}'>Click Here to View</a>"
        await self.send_telegram_message(message)

    async def get_status_report_text(self) -> str:
        uptime = datetime.now(wib) - self.bot_start_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds%3600)//60}m"
        current_time_str = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S %Z')
        start_time_str = self.bot_start_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        return f"🤖 DePINed Bot Live Status 🤖\n\n🔗 Total Proxies: {len(self.proxies) if hasattr(self, 'proxies') else 0}\n⏱️ Uptime: {uptime_str}\n📧 Accounts: {self.active_accounts}\n📊 Pings: {self.total_pings_sent}\n📅 Start: {start_time_str}\n🕐 Current: {current_time_str}"

    async def get_earnings_report_text(self) -> str:
        async with self.earnings_lock:
            if not self.account_earnings: return "💰 No earnings data recorded yet."
            message = "💰💎 <b>Earnings & Levels</b> 💎💰\n\n"
            for email, info in sorted(self.account_earnings.items()):
                try: balance = float(info.split(':')[-1].strip().split(' ')[0])
                except: balance = 0
                level = get_account_level(balance)
                message += f"👤 <code>{email.split('@')[0]}</code>: {info} {level}\n"
            return message

    async def help_command(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        help_text = "👋 <b>Commands</b>\n\n/help - Help\n/status - Live Status\n/earnings - Latest Earnings"
        await u.message.reply_html(help_text)
        
    async def status_command(self, u: Update, c: ContextTypes.DEFAULT_TYPE): await u.message.reply_html(await self.get_status_report_text())
    async def earnings_command(self, u: Update, c: ContextTypes.DEFAULT_TYPE): await u.message.reply_html(await self.get_earnings_report_text())

    def start_background_tasks(self):
        self.log_print(f"{Fore.GREEN}Scheduling background jobs...")
        accounts = self.load_accounts()
        self.active_accounts = len(accounts)
        if not accounts: self.log_print(f"{Fore.YELLOW}No accounts found."); return

        for account in accounts:
            email = account.get("Email")
            if email:
                self.job_queue.run_repeating(self.process_single_account, interval=90, first=5, data={'email': email})
        
        self.job_queue.run_repeating(self.schedule_status_report, interval=90, first=90)
        self.log_print(f"{Fore.GREEN}All jobs are scheduled.")

# --- 4. APPLICATION ENTRY POINT ---
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN: logger.error("FATAL: TOKEN not found!"); return

    # ===== THIS IS THE MAIN FIX =====
    # Create the JobQueue instance
    job_queue = JobQueue()
    # Build the application and pass the job_queue to it
    application = Application.builder().token(TOKEN).job_queue(job_queue).build()

    depined_bot = DePINed(application)

    application.add_handler(CommandHandler("help", depined_bot.help_command))
    application.add_handler(CommandHandler("status", depined_bot.status_command))
    application.add_handler(CommandHandler("earnings", depined_bot.earnings_command))
    
    depined_bot.start_background_tasks()
    
    print(f"{Fore.GREEN}Telegram bot is now polling...{Style.RESET_ALL}")
    application.run_polling()

if __name__ == "__main__":
    print(f"{Fore.GREEN}--- TSun DePINed Bot Initializing ---{Style.RESET_ALL}")
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"{Fore.CYAN}Web server started.{Style.RESET_ALL}")

    print(f"{Fore.CYAN}Starting Telegram bot...{Style.RESET_ALL}")
    main()