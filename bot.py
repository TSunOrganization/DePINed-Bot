
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DePINed Bot - Enhanced Version 2.0
Deployment-ready with comprehensive monitoring and analytics
"""

from curl_cffi import requests
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, json, os, pytz
from flask import Flask, render_template_string, jsonify
import threading
import time
import statistics
from collections import defaultdict, deque

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
        
        # Enhanced Analytics
        self.error_stats = defaultdict(int)
        self.account_stats = defaultdict(lambda: {
            'pings_sent': 0,
            'pings_failed': 0,
            'earnings': 0.0,
            'last_success': None,
            'success_rate': 0.0
        })
        self.proxy_stats = defaultdict(lambda: {
            'success': 0,
            'failures': 0,
            'speed': deque(maxlen=10),
            'blacklisted': False
        })
        self.performance_metrics = {
            'response_times': deque(maxlen=100),
            'success_rate': 0.0,
            'last_24h_errors': deque(maxlen=1440)  # 24h * 60min
        }
        self.notification_throttle = defaultdict(lambda: {'count': 0, 'last_sent': 0})
        self.daily_earnings = defaultdict(float)
        self.hourly_stats = defaultdict(lambda: {'pings': 0, 'errors': 0})
        
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
            return self.get_best_proxy_for_account(account)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        # Remove current proxy assignment and get a new one
        if account in self.account_proxies:
            old_proxy = self.account_proxies[account]
            # Mark old proxy as problematic
            self.proxy_stats[old_proxy]['failures'] += 1
        
        return self.get_best_proxy_for_account(account)
    
    def mask_account(self, account):
        if "@" in account:
            local, domain = account.split('@', 1)
            hide_local = local[:3] + '*' * 3 + local[-3:]
            return f"{hide_local}@{domain}"
    
    async def send_telegram_message(self, chat_id, message, level="INFO"):
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # Notification throttling
        throttle_key = f"{chat_id}_{level}"
        current_time = time.time()
        throttle_info = self.notification_throttle[throttle_key]
        
        # Throttle rules: max 3 per 5 minutes for ERROR, 1 per hour for INFO
        throttle_limits = {"CRITICAL": 60, "ERROR": 300, "WARNING": 600, "INFO": 3600}
        max_count = {"CRITICAL": 10, "ERROR": 3, "WARNING": 2, "INFO": 1}
        
        if current_time - throttle_info['last_sent'] < throttle_limits.get(level, 3600):
            if throttle_info['count'] >= max_count.get(level, 1):
                return False
        else:
            throttle_info['count'] = 0
        
        # Add level emoji
        level_emojis = {"CRITICAL": "🔴", "ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}
        message = f"{level_emojis.get(level, '')} {message}"
        
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = await asyncio.to_thread(requests.post, url=url, json=data, timeout=30)
            response.raise_for_status()
            throttle_info['count'] += 1
            throttle_info['last_sent'] = current_time
            return True
        except Exception as e:
            self.log(f"{Fore.RED}Failed to send Telegram message: {e}{Style.RESET_ALL}")
            return False
    
    async def send_failure_notification(self, error_type, error_message, account_email=None, level="ERROR"):
        """Send failure notifications with enhanced categorization and analytics"""
        current_time = datetime.now().astimezone(wib)
        
        # Update error statistics
        self.error_stats[error_type] += 1
        self.performance_metrics['last_24h_errors'].append(current_time.timestamp())
        
        # Determine severity level
        critical_errors = ["System Failure", "All Accounts Failed", "Network Down"]
        if error_type in critical_errors:
            level = "CRITICAL"
        elif "Connection" in error_type or "Proxy" in error_type:
            level = "WARNING"
        
        if account_email:
            self.account_stats[account_email]['pings_failed'] += 1
            success_rate = self.calculate_account_success_rate(account_email)
            
            message = f"""
🚨 <b>Account Failure Alert</b>

❌ <b>Error Type:</b> {error_type}
📧 <b>Account:</b> {self.mask_account(account_email)}
📊 <b>Success Rate:</b> {success_rate:.1f}%
🔍 <b>Details:</b> {error_message}
📈 <b>Total Errors Today:</b> {self.error_stats[error_type]}
🕐 <b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

{'🔧 <b>Action Required:</b> Check account credentials or proxy' if success_rate < 50 else ''}
            """
        else:
            message = f"""
🚨 <b>System Failure Alert</b>

❌ <b>Error Type:</b> {error_type}
🔍 <b>Details:</b> {error_message}
📊 <b>Error Frequency:</b> {self.error_stats[error_type]} times today
🕐 <b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

{'🚨 <b>CRITICAL:</b> Immediate attention required!' if level == 'CRITICAL' else ''}
            """
        
        # Send to all recipients with appropriate level
        await self.send_telegram_message(self.ADMIN_CHAT_ID, message, level)
        await self.send_telegram_message(self.USER_CHAT_ID, message, level)
        await self.send_telegram_message(self.GROUP_ID, message, level)
    
    def calculate_account_success_rate(self, email):
        stats = self.account_stats[email]
        total = stats['pings_sent'] + stats['pings_failed']
        return (stats['pings_sent'] / total * 100) if total > 0 else 100.0
    
    def get_proxy_health_score(self, proxy):
        stats = self.proxy_stats[proxy]
        total = stats['success'] + stats['failures']
        if total == 0:
            return 100.0
        health = (stats['success'] / total) * 100
        # Factor in speed if available
        if stats['speed']:
            avg_speed = statistics.mean(stats['speed'])
            speed_factor = min(avg_speed / 1000, 1.0)  # Normalize to 1 second
            health *= (1 + speed_factor) / 2
        return health
    
    def blacklist_proxy(self, proxy, reason="Poor performance"):
        self.proxy_stats[proxy]['blacklisted'] = True
        self.log(f"{Fore.YELLOW}Proxy blacklisted: {proxy} - {reason}{Style.RESET_ALL}")
    
    def get_best_proxy_for_account(self, account):
        if not self.proxies:
            return None
        
        # Filter out blacklisted proxies
        available_proxies = [p for p in self.proxies if not self.proxy_stats[p]['blacklisted']]
        if not available_proxies:
            # Reset blacklist if all proxies are blacklisted
            for proxy in self.proxies:
                self.proxy_stats[proxy]['blacklisted'] = False
            available_proxies = self.proxies
        
        # Sort by health score
        proxy_scores = [(p, self.get_proxy_health_score(p)) for p in available_proxies]
        proxy_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Use top 10% of proxies for rotation
        top_proxies = proxy_scores[:max(1, len(proxy_scores) // 10)]
        selected_proxy = top_proxies[self.proxy_index % len(top_proxies)][0]
        
        self.account_proxies[account] = self.check_proxy_schemes(selected_proxy)
        self.proxy_index = (self.proxy_index + 1) % len(top_proxies)
        
        return self.account_proxies[account]
    
    async def send_daily_summary(self):
        """Send comprehensive daily summary report"""
        current_time = datetime.now().astimezone(wib)
        
        # Calculate daily statistics
        total_errors = sum(self.error_stats.values())
        top_errors = sorted(self.error_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        
        avg_success_rate = statistics.mean([
            self.calculate_account_success_rate(email) 
            for email in self.account_stats.keys()
        ]) if self.account_stats else 100.0
        
        total_earnings = sum(stats['earnings'] for stats in self.account_stats.values())
        
        message = f"""
📊 <b>Daily Summary Report</b>
📅 <b>Date:</b> {current_time.strftime('%Y-%m-%d')}

📈 <b>Performance Metrics:</b>
• Success Rate: {avg_success_rate:.1f}%
• Total Pings: {self.total_pings_sent}
• Total Errors: {total_errors}
• Active Accounts: {self.active_accounts}

💰 <b>Earnings:</b>
• Total: {total_earnings:.4f} PTS
• Per Account: {total_earnings/max(1, self.active_accounts):.4f} PTS

🔴 <b>Top Error Types:</b>
{chr(10).join([f'• {error}: {count}x' for error, count in top_errors[:3]])}

🌐 <b>Proxy Health:</b>
• Active Proxies: {len([p for p in self.proxies if not self.proxy_stats[p]['blacklisted']])}
• Blacklisted: {len([p for p in self.proxies if self.proxy_stats[p]['blacklisted']])}

⏱️ <b>Uptime:</b> {str(current_time - self.start_time).split('.')[0]}
        """
        
        await self.send_telegram_message(self.ADMIN_CHAT_ID, message, "INFO")
        await self.send_telegram_message(self.USER_CHAT_ID, message, "INFO")
    
    async def send_uptime_report(self):
        report_count = 0
        while True:
            try:
                current_time = datetime.now().astimezone(wib)
                uptime_delta = current_time - self.start_time
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                # Calculate recent success rate
                recent_errors = len([ts for ts in self.performance_metrics['last_24h_errors'] 
                                   if current_time.timestamp() - ts < 300])  # Last 5 minutes
                
                # Calculate average response time
                avg_response_time = statistics.mean(self.performance_metrics['response_times']) \
                    if self.performance_metrics['response_times'] else 0
                
                # Get top performing account
                best_account = max(self.account_stats.items(), 
                                 key=lambda x: self.calculate_account_success_rate(x[0]),
                                 default=("No accounts", {"earnings": 0}))
                
                status_emoji = "✅" if recent_errors < 5 else "⚠️" if recent_errors < 15 else "🚨"
                
                message = f"""
🤖 <b>DePINed Bot Status Report #{report_count + 1}</b>

⏱️ <b>Uptime:</b> {days}d {hours}h {minutes}m
📧 <b>Active accounts:</b> {self.active_accounts}
📊 <b>Total pings sent:</b> {self.total_pings_sent}
📈 <b>Success rate:</b> {100 - (recent_errors * 2):.1f}% (5min)
⚡ <b>Avg response:</b> {avg_response_time:.2f}s

🏆 <b>Top performer:</b> {self.mask_account(best_account[0])}
💰 <b>Earnings:</b> {sum(s['earnings'] for s in self.account_stats.values()):.4f} PTS

🌐 <b>Network status:</b>
• Healthy proxies: {len([p for p in self.proxies if not self.proxy_stats[p]['blacklisted']])}
• Recent errors: {recent_errors}

📅 <b>Started:</b> {self.start_time.strftime('%m/%d %H:%M')}
🕐 <b>Now:</b> {current_time.strftime('%m/%d %H:%M:%S %Z')}

{status_emoji} System status: {'Excellent' if recent_errors < 5 else 'Good' if recent_errors < 15 else 'Needs Attention'}
                """
                
                await self.send_telegram_message(self.ADMIN_CHAT_ID, message, "INFO")
                await self.send_telegram_message(self.USER_CHAT_ID, message, "INFO")
                await self.send_telegram_message(self.GROUP_ID, message, "INFO")
                
                self.log(f"{Fore.GREEN}Enhanced uptime report #{report_count + 1} sent{Style.RESET_ALL}")
                report_count += 1
                
                # Send daily summary at midnight
                if current_time.hour == 0 and current_time.minute < 5:
                    await self.send_daily_summary()
                
            except Exception as e:

    
    async def startup_health_check(self):
        """Perform comprehensive startup health check"""
        issues = []
        
        try:
            # Check tokens file
            if not os.path.exists('tokens.json'):
                issues.append("tokens.json missing")
            
            # Check proxy file if needed
            if not os.path.exists('proxy.txt') and len(self.proxies) == 0:
                issues.append("No proxies available")
            
            # Test telegram connectivity
            test_result = await self.send_telegram_message(self.ADMIN_CHAT_ID, "🔍 Bot startup test", "INFO")
            if not test_result:
                issues.append("Telegram connectivity failed")
            
            # Check internet connectivity
            try:
                response = await asyncio.to_thread(requests.get, "https://httpbin.org/ip", timeout=10)
                if response.status_code != 200:
                    issues.append("Internet connectivity issues")
            except Exception:
                issues.append("Internet connectivity failed")
            
            if issues:
                status = f"⚠️ Issues detected: {', '.join(issues)}"
                await self.send_failure_notification("Startup Issues", f"Bot started with issues: {', '.join(issues)}", level="WARNING")
            else:
                status = "✅ All systems operational"
                
            return status
            
        except Exception as e:
            error_status = f"❌ Health check failed: {str(e)}"
            await self.send_failure_notification("Health Check Failed", str(e), level="ERROR")
            return error_status

                error_msg = f"Error sending uptime report: {e}"
                self.log(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
                await self.send_failure_notification("Report System Error", error_msg, level="WARNING")
            
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
            
            return jsonify({
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
                "active_accounts": self.active_accounts,
                "total_pings": self.total_pings_sent,
                "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            })
        
        @self.app.route('/analytics')
        def analytics():
            current_time = datetime.now().astimezone(wib)
            
            # Calculate success rates
            account_rates = {
                self.mask_account(email): self.calculate_account_success_rate(email)
                for email in self.account_stats.keys()
            }
            
            # Proxy health
            proxy_health = {
                proxy: self.get_proxy_health_score(proxy)
                for proxy in self.proxies[:10]  # Top 10 for display
            }
            
            # Error breakdown
            error_breakdown = dict(self.error_stats)
            
            return jsonify({
                "account_success_rates": account_rates,
                "proxy_health": proxy_health,
                "error_breakdown": error_breakdown,
                "total_earnings": sum(s['earnings'] for s in self.account_stats.values()),
                "avg_response_time": statistics.mean(self.performance_metrics['response_times']) 
                    if self.performance_metrics['response_times'] else 0,
                "recent_errors": len([ts for ts in self.performance_metrics['last_24h_errors'] 
                                    if current_time.timestamp() - ts < 3600]),
                "blacklisted_proxies": len([p for p in self.proxies if self.proxy_stats[p]['blacklisted']]),
                "healthy_proxies": len([p for p in self.proxies if not self.proxy_stats[p]['blacklisted']])
            })
        
        @self.app.route('/logs')
        def logs():
            # Return recent error logs (last 50)
            recent_errors = []
            current_time = datetime.now().astimezone(wib)
            
            for error_type, count in self.error_stats.items():
                recent_errors.append({
                    "type": error_type,
                    "count": count,
                    "timestamp": current_time.isoformat()
                })
            
            return jsonify({
                "recent_errors": recent_errors[-50:],
                "total_errors": sum(self.error_stats.values()),
                "error_types": len(self.error_stats)
            })
        
        @self.app.route('/accounts')
        def accounts_info():
            account_details = []
            for email, stats in self.account_stats.items():
                account_details.append({
                    "email": self.mask_account(email),
                    "pings_sent": stats['pings_sent'],
                    "pings_failed": stats['pings_failed'],
                    "success_rate": self.calculate_account_success_rate(email),
                    "earnings": stats['earnings'],
                    "last_success": stats['last_success'].isoformat() if stats['last_success'] else None
                })
            
            return jsonify({
                "accounts": account_details,
                "total_active": len(account_details),
                "avg_success_rate": statistics.mean([acc['success_rate'] for acc in account_details]) 
                    if account_details else 0
            })
        
        @self.app.route('/health')
        def health():
            current_time = datetime.now().astimezone(wib)
            recent_errors = len([ts for ts in self.performance_metrics['last_24h_errors'] 
                               if current_time.timestamp() - ts < 300])
            
            status = "healthy"
            if recent_errors > 15:
                status = "critical"
            elif recent_errors > 5:
                status = "warning"
            
            return jsonify({
                "status": status,
                "uptime": str(current_time - self.start_time),
                "recent_errors": recent_errors,
                "total_accounts": self.active_accounts,
                "healthy_proxies": len([p for p in self.proxies if not self.proxy_stats[p]['blacklisted']])
            })
        
        @self.app.route('/ping')
        def ping():
            return jsonify({
                "message": "pong", 
                "timestamp": datetime.now().astimezone(wib).isoformat(),
                "version": "2.0.0-enhanced"
            })
        
        @self.app.route('/status')
        def status():
            current_time = datetime.now().astimezone(wib)
            uptime_delta = current_time - self.start_time
            
            return jsonify({
                "status": "running",
                "uptime": str(uptime_delta),
                "active_accounts": self.active_accounts,
                "total_pings_sent": self.total_pings_sent,
                "total_earnings": sum(s['earnings'] for s in self.account_stats.values()),
                "error_count": sum(self.error_stats.values()),
                "proxy_health": f"{len([p for p in self.proxies if not self.proxy_stats[p]['blacklisted']])}/{len(self.proxies)}",
                "start_time": self.start_time.isoformat(),
                "current_time": current_time.isoformat()
            })
    
    def start_web_server(self):
        self.setup_web_interface()
        self.app.run(host='0.0.0.0', port=5000, debug=False)

    def load_config(self):
        """Load configuration from config.json and environment variables"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            # Get proxy settings from config or environment
            proxy_choice = int(os.environ.get('PROXY_CHOICE', config.get('bot_settings', {}).get('proxy_choice', 1)))
            rotate_proxy = os.environ.get('ROTATE_PROXY', str(config.get('bot_settings', {}).get('proxy_rotation', True))).lower() == 'true'
            
            return proxy_choice, rotate_proxy
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.log(f"{Fore.YELLOW}Config error: {e}. Using defaults.{Style.RESET_ALL}")
            # Default to free proxyscrape with rotation
            return 1, True
    
    def print_question(self):
        """Non-interactive configuration loading for deployment environments"""
        try:
            choose, rotate = self.load_config()
            
            if choose not in [1, 2, 3]:
                choose = 1  # Default to free proxy
                
            proxy_type = (
                "With Free Proxyscrape" if choose == 1 else 
                "With Private" if choose == 2 else 
                "Without"
            )
            
            self.log(f"{Fore.GREEN + Style.BRIGHT}Auto-configured: Run {proxy_type} Proxy, Rotation: {rotate}{Style.RESET_ALL}")
            return choose, rotate
            
        except Exception as e:
            error_msg = f"Configuration loading failed: {str(e)}"
            self.log(f"{Fore.RED + Style.BRIGHT}{error_msg}{Style.RESET_ALL}")
            # Return safe defaults
            return 1, True
    
    async def check_connection(self, email: str, proxy=None):
        url = "https://api.ipify.org?format=json"
        proxies = {"http":proxy, "https":proxy} if proxy else None
        start_time = time.time()
        
        await asyncio.sleep(3)
        try:
            response = await asyncio.to_thread(requests.get, url=url, proxies=proxies, timeout=30, impersonate="chrome110", verify=False)
            response.raise_for_status()
            
            # Track performance metrics
            response_time = time.time() - start_time
            self.performance_metrics['response_times'].append(response_time)
            
            if proxy:
                self.proxy_stats[proxy]['success'] += 1
                self.proxy_stats[proxy]['speed'].append(response_time)
            
            return True
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Connection Failed: {str(e)}"
            
            if proxy:
                self.proxy_stats[proxy]['failures'] += 1
                # Blacklist proxy if it fails too much
                if self.proxy_stats[proxy]['failures'] > 5:
                    self.blacklist_proxy(proxy, "Too many connection failures")
            
            self.print_message(email, proxy, Fore.RED, error_msg)
            await self.send_failure_notification("Connection Failed", error_msg, email, "WARNING")
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
        
        start_time = time.time()
        
        for attempt in range(retries):
            proxies = {"http":proxy, "https":proxy} if proxy else None
            await asyncio.sleep(5)
            try:
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, data=data, proxies=proxies, timeout=60, impersonate="chrome110", verify=False)
                response.raise_for_status()
                
                # Track successful ping
                response_time = time.time() - start_time
                self.account_stats[email]['pings_sent'] += 1
                self.account_stats[email]['last_success'] = datetime.now().astimezone(wib)
                self.performance_metrics['response_times'].append(response_time)
                
                if proxy:
                    self.proxy_stats[proxy]['success'] += 1
                    self.proxy_stats[proxy]['speed'].append(response_time)
                
                return response.json()
                
            except Exception as e:
                if proxy:
                    self.proxy_stats[proxy]['failures'] += 1
                
                if attempt < retries - 1:
                    # Try different proxy on retry if available
                    if proxy and len(self.proxies) > 1:
                        proxy = self.get_best_proxy_for_account(email)
                        proxies = {"http":proxy, "https":proxy} if proxy else None
                    continue
                    
                error_msg = f"PING Failed after {retries} attempts: {str(e)}"
                self.account_stats[email]['pings_failed'] += 1
                self.print_message(email, proxy, Fore.RED, error_msg)
                
                # Determine error severity
                level = "CRITICAL" if "401" in str(e) or "403" in str(e) else "ERROR"
                await self.send_failure_notification("Ping Failed", error_msg, email, level)
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
            # Check if running in deployment environment
            is_deployment = os.environ.get('RENDER') or os.environ.get('HEROKU') or not os.isatty(0)
            if is_deployment:
                self.log(f"{Fore.CYAN}Running in deployment mode{Style.RESET_ALL}")
            
            tokens = self.load_accounts()
            if not tokens:
                error_msg = "No Accounts Loaded - Check tokens.json file"
                self.log(f"{Fore.RED+Style.BRIGHT}{error_msg}{Style.RESET_ALL}")
                await self.send_failure_notification("Configuration Error", error_msg, level="CRITICAL")
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
            
            # Perform startup health check
            health_status = await self.startup_health_check()
            
            # Send initial startup notification
            startup_message = f"""
🚀 <b>DePINed Bot Started!</b>

📅 <b>Start time:</b> {self.start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
📧 <b>Active accounts:</b> {self.active_accounts}
🌐 <b>Web dashboard:</b> http://0.0.0.0:5000
📡 <b>Telegram notifications:</b> Enabled
🔧 <b>Proxy mode:</b> {"Free Proxyscrape" if use_proxy_choice == 1 else "Private" if use_proxy_choice == 2 else "None"}
📊 <b>Health status:</b> {health_status}

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