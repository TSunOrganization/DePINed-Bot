from curl_cffi import requests
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, json, os, pytz
from flask import Flask, render_template_string
import threading
import time

wib = pytz.timezone('Asia/Jakarta')

class DePINed:
    def __init__(self) -> None:
        self.BASE_API = "https://api.depined.org/api"
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN = "6381595536:AAHhbkjoGWhYLZ7OMglW5Q9lW7LjEF8yePc"
        self.ADMIN_CHAT_ID = "6218146252"
        self.USER_CHAT_ID = "5734967213"
        self.GROUP_ID = "-1002193530778"
        
        # Bot Statistics
        self.start_time = datetime.now().astimezone(wib)
        self.active_accounts = 0
        self.total_pings_sent = 0
        
        # Flask app for web interface
        self.app = Flask(__name__)

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}DePINed {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "tokens.json"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
                return

            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                response = await asyncio.to_thread(requests.get, "https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/all.txt")
                response.raise_for_status()
                content = response.text
                with open(filename, 'w') as f:
                    f.write(content)
                self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            error_msg = f"Failed To Load Proxies: {str(e)}"
            self.log(f"{Fore.RED + Style.BRIGHT}{error_msg}{Style.RESET_ALL}")
            await self.send_failure_notification("Proxy Loading Failed", error_msg)
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def mask_account(self, account):
        if "@" in account:
            local, domain = account.split('@', 1)
            hide_local = local[:3] + '*' * 3 + local[-3:]
            return f"{hide_local}@{domain}"
    
    async def send_telegram_message(self, chat_id, message):
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = await asyncio.to_thread(requests.post, url=url, json=data, timeout=30)
            response.raise_for_status()
            return True
        except Exception as e:
            self.log(f"{Fore.RED}Failed to send Telegram message: {e}{Style.RESET_ALL}")
            return False
    
    async def send_failure_notification(self, error_type, error_message, account_email=None):
        """Send failure notifications to all configured recipients"""
        current_time = datetime.now().astimezone(wib)
        
        if account_email:
            message = f"""
🚨 <b>Bot Failure Alert</b>

❌ <b>Error Type:</b> {error_type}
📧 <b>Account:</b> {self.mask_account(account_email)}
🔍 <b>Details:</b> {error_message}
🕐 <b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

Please check the bot status and take necessary action.
            """
        else:
            message = f"""
🚨 <b>Bot System Failure Alert</b>

❌ <b>Error Type:</b> {error_type}
🔍 <b>Details:</b> {error_message}
🕐 <b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

The bot system encountered an error. Please check immediately.
            """
        
        # Send to all recipients
        await self.send_telegram_message(self.ADMIN_CHAT_ID, message)
        await self.send_telegram_message(self.USER_CHAT_ID, message)
        await self.send_telegram_message(self.GROUP_ID, message)
    
    async def send_uptime_report(self):
        while True:
            try:
                current_time = datetime.now().astimezone(wib)
                uptime_delta = current_time - self.start_time
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                message = f"""
🤖 <b>DePINed Bot Status Report</b>

⏱️ <b>Current uptime:</b> {days} days, {hours} hours, {minutes} minutes
📧 <b>Active accounts:</b> {self.active_accounts}
📊 <b>Total pings sent:</b> {self.total_pings_sent}
📅 <b>Bot start time:</b> {self.start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
🕐 <b>Current timestamp:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

✅ Bot is running smoothly!
                """
                
                # Send to admin
                await self.send_telegram_message(self.ADMIN_CHAT_ID, message)
                # Send to user
                await self.send_telegram_message(self.USER_CHAT_ID, message)
                # Send to group
                await self.send_telegram_message(self.GROUP_ID, message)
                
                self.log(f"{Fore.GREEN}Uptime report sent to Telegram{Style.RESET_ALL}")
                
            except Exception as e:
                self.log(f"{Fore.RED}Error sending uptime report: {e}{Style.RESET_ALL}")
            
            # Wait 5 minutes
            await asyncio.sleep(5 * 60)

    def print_message(self, email, proxy, color, message):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}[ Account:{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(email)} {Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT} Proxy: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{proxy}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
            f"{color + Style.BRIGHT} {message} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
        )

    def setup_web_interface(self):
        @self.app.route('/')
        def dashboard():
            with open('index.html', 'r') as f:
                html_content = f.read()
            return html_content
        
        @self.app.route('/uptime-data')
        def uptime_data():
            current_time = datetime.now().astimezone(wib)
            uptime_delta = current_time - self.start_time
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
                "active_accounts": self.active_accounts,
                "total_pings": self.total_pings_sent,
                "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            }
        
        @self.app.route('/health')
        def health():
            return {"status": "healthy", "uptime": str(datetime.now().astimezone(wib) - self.start_time)}
        
        @self.app.route('/ping')
        def ping():
            return {"message": "pong", "timestamp": datetime.now().astimezone(wib).isoformat()}
        
        @self.app.route('/status')
        def status():
            current_time = datetime.now().astimezone(wib)
            uptime_delta = current_time - self.start_time
            return {
                "status": "running",
                "uptime": str(uptime_delta),
                "active_accounts": self.active_accounts,
                "total_pings_sent": self.total_pings_sent,
                "start_time": self.start_time.isoformat(),
                "current_time": current_time.isoformat()
            }
    
    def start_web_server(self):
        self.setup_web_interface()
        self.app.run(host='0.0.0.0', port=5000, debug=False)

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Free Proxyscrape Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "With Free Proxyscrape" if choose == 1 else 
                        "With Private" if choose == 2 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        rotate = False
        if choose in [1, 2]:
            while True:
                rotate = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()
                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return choose, rotate
    
    async def check_connection(self, email: str, proxy=None):
        url = "https://api.ipify.org?format=json"
        proxies = {"http":proxy, "https":proxy} if proxy else None
        await asyncio.sleep(3)
        try:
            response = await asyncio.to_thread(requests.get, url=url, proxies=proxies, timeout=30, impersonate="chrome110", verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            error_msg = f"Connection Not 200 OK: {str(e)}"
            self.print_message(email, proxy, Fore.RED, f"{error_msg}")
            await self.send_failure_notification("Connection Failed", error_msg, email)
            return None

    async def user_epoch_earning(self, email: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/stats/epoch-earnings"
        headers = self.HEADERS[email].copy()
        headers["Authorization"] = f"Bearer {self.access_tokens[email]}"
        for attempt in range(retries):
            proxies = {"http":proxy, "https":proxy} if proxy else None
            await asyncio.sleep(5)
            try:
                response = await asyncio.to_thread(requests.get, url=url, headers=headers, proxies=proxies, timeout=60, impersonate="chrome110", verify=False)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    continue
                error_msg = f"GET Earning Failed: {str(e)}"
                self.print_message(email, proxy, Fore.RED, error_msg)
                await self.send_failure_notification("Earning Fetch Failed", error_msg, email)
                return None
            
    async def user_send_ping(self, email: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/user/widget-connect"
        data = json.dumps({"connected":True})
        headers = self.HEADERS[email].copy()
        headers["Authorization"] = f"Bearer {self.access_tokens[email]}"
        headers["Content-Length"] = str(len(data))
        headers["Content-Type"] = "application/json"
        for attempt in range(retries):
            proxies = {"http":proxy, "https":proxy} if proxy else None
            await asyncio.sleep(5)
            try:
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, data=data, proxies=proxies, timeout=60, impersonate="chrome110", verify=False)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    continue
                error_msg = f"PING Failed: {str(e)}"
                self.print_message(email, proxy, Fore.RED, error_msg)
                await self.send_failure_notification("Ping Failed", error_msg, email)
                return None
            
    async def process_check_connection(self, email: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None

            is_valid = await self.check_connection(email, proxy)
            if is_valid:
                return True
            
            if rotate_proxy:
                proxy = self.rotate_proxy_for_account(email)
            
    async def process_user_earning(self, email: str, use_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None

            earning = await self.user_epoch_earning(email, proxy)
            if earning and earning.get("code") == 200:
                epoch = earning.get("data", {}).get("epoch", "N/A")
                balance = earning.get("data", {}).get("earnings", 0)

                self.print_message(email, proxy, Fore.WHITE, f"Epoch {epoch} "
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.CYAN + Style.BRIGHT} Earning: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{balance:.2f} PTS{Style.RESET_ALL}"
                )

            await asyncio.sleep(15 * 60)
            
    async def process_send_ping(self, email: str, use_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None

            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Try to Sent Ping...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )

            ping = await self.user_send_ping(email, proxy)
            if ping and ping.get("message") == "Widget connection status updated":
                self.total_pings_sent += 1
                self.print_message(email, proxy, Fore.GREEN, "PING Success")

            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For 90 Seconds For Next Ping...{Style.RESET_ALL}",
                end="\r"
            )
            await asyncio.sleep(1.5 * 60)
        
    async def process_accounts(self, email: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(email, use_proxy, rotate_proxy)
        if is_valid:
            tasks = [
                asyncio.create_task(self.process_user_earning(email, use_proxy)),
                asyncio.create_task(self.process_send_ping(email, use_proxy))
            ]
            await asyncio.gather(*tasks)

    async def main(self):
        try:
            tokens = self.load_accounts()
            if not tokens:
                self.log(f"{Fore.RED+Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}")
                return
            
            use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            self.clear_terminal()
            self.welcome()
            self.active_accounts = len([t for t in tokens if t and "@" in t.get("Email", "") and t.get("accessToken", "")])
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(tokens)}{Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Active Accounts: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{self.active_accounts}{Style.RESET_ALL}"
            )

            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*75)

            # Start web server in a separate thread
            web_thread = threading.Thread(target=self.start_web_server, daemon=True)
            web_thread.start()
            self.log(f"{Fore.GREEN}Web dashboard started at http://0.0.0.0:5000{Style.RESET_ALL}")
            
            # Send initial startup notification
            startup_message = f"""
🚀 <b>DePINed Bot Started!</b>

📅 <b>Start time:</b> {self.start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
📧 <b>Active accounts:</b> {self.active_accounts}
🌐 <b>Web dashboard:</b> Available
📡 <b>Telegram notifications:</b> Enabled

Bot is now running and will send reports every 5 minutes.
            """
            await self.send_telegram_message(self.ADMIN_CHAT_ID, startup_message)
            await self.send_telegram_message(self.USER_CHAT_ID, startup_message)
            await self.send_telegram_message(self.GROUP_ID, startup_message)
            
            tasks = [
                asyncio.create_task(self.send_uptime_report())
            ]
            
            for idx, account in enumerate(tokens, start=1):
                if account:
                    email = account["Email"]
                    token = account["accessToken"]

                    if not "@" in email or not token:
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}[ Account: {Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT}{idx}{Style.RESET_ALL}"
                            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
                            f"{Fore.RED + Style.BRIGHT} Invalid Account Data {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
                        )
                        continue

                    self.HEADERS[email] = {
                        "Accept": "*/*",
                        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Origin": "chrome-extension://pjlappmodaidbdjhmhifbnnmmkkicjoc",
                        "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Site": "none",
                        "User-Agent": FakeUserAgent().random,
                        "X-Requested-With": "XMLHttpRequest"
                    }

                    self.access_tokens[email] = token

                    tasks.append(asyncio.create_task(self.process_accounts(email, use_proxy, rotate_proxy)))

            await asyncio.gather(*tasks)

        except Exception as e:
            error_msg = f"System Error: {str(e)}"
            self.log(f"{Fore.RED+Style.BRIGHT}{error_msg}{Style.RESET_ALL}")
            await self.send_failure_notification("System Failure", error_msg)
            raise e

if __name__ == "__main__":
    try:
        bot = DePINed()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] DePINed - BOT{Style.RESET_ALL}                                       "                              
        )