import os
import json
import asyncio
import requests
import zendriver as uc
import tempfile
from datetime import datetime
from colorama import  Fore, Style
from enum import Enum
import psutil
import shutil
import multiprocessing
from datetime import datetime, timezone ,timedelta
from pystyle import Center
from notifypy import Notify
import sys
import re
import time
import hashlib

try:
    with open('config.json', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    print("config.json file not found.")
    sys.exit(1)
    
API_KEY = config.get("api_key")
API_URL = config.get("api_url")
COUNTRY = config.get("country")
OPERATOR = config.get("operator")
PRODUCT = config.get("product")
CODE = config.get("country_code")
if not all([API_KEY, API_URL, COUNTRY, OPERATOR, PRODUCT, CODE]):
    print("Missing configuration values in config.json.")
    sys.exit(1)

RESET = "\033[0m"
ANSI_PATTERN = re.compile(r'\033\[[0-9;]*m')
def write_print(text, interval=0.01, hide_cursor=True, end=RESET):
    if hide_cursor:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
    i = 0
    while i < len(text):
        if text[i] == '\033':  
            match = ANSI_PATTERN.match(text, i)
            if match:
                sys.stdout.write(match.group())  
                sys.stdout.flush()
                i = match.end()
                continue
        sys.stdout.write(text[i])
        sys.stdout.flush()
        time.sleep(interval)
        i += 1
    sys.stdout.write(end)
    sys.stdout.flush()
    if hide_cursor:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    SUCCESS = 4
    ERROR = 5
    CRITICAL = 6
class Logger:
    def __init__(self, level: LogLevel = LogLevel.DEBUG):
        self.level = level
        self.prefix = "\033[38;5;176m[\033[38;5;97mtermwave\033[38;5;176m] "
        self.WHITE = "\u001b[37m"
        self.MAGENTA = "\033[38;5;97m"
        self.BRIGHT_MAGENTA = "\033[38;2;157;38;255m"
        self.LIGHT_CORAL = "\033[38;5;210m"
        self.RED = "\033[38;5;196m"
        self.GREEN = "\033[38;5;40m"
        self.YELLOW = "\033[38;5;220m"
        self.BLUE = "\033[38;5;21m"
        self.PINK = "\033[38;5;176m"
        self.CYAN = "\033[96m"
    def get_time(self):
        return datetime.now().strftime("%H:%M:%S")
    def _should_log(self, message_level: LogLevel) -> bool:
        return message_level.value >= self.level.value
    def _write(self, level_color, level_tag, message):
        write_print(f"{self.prefix}[{self.BRIGHT_MAGENTA}{self.get_time()}{self.PINK}] {self.PINK}[{level_color}{level_tag}{self.PINK}] -> {level_color}{message}{Style.RESET_ALL}", interval=0.01)
        print()
    def info(self, message: str):
        if self._should_log(LogLevel.INFO):
            self._write(self.CYAN, "!", message)
    def success(self, message: str):
        if self._should_log(LogLevel.SUCCESS):
            self._write(self.GREEN, "Success", message)
    def warning(self, message: str):
        if self._should_log(LogLevel.WARNING):
            self._write(self.YELLOW, "Warning", message)
    def error(self, message: str):
        if self._should_log(LogLevel.ERROR):
            self._write(self.RED, "Error", message)
    def debug(self, message: str):
        if self._should_log(LogLevel.DEBUG):
            self._write(self.BLUE, "DEBUG", message)
    def failure(self, message: str):
        if self._should_log(LogLevel.ERROR):
            self._write(self.RED, "Failure", message)
log = Logger()

def buy_activation_number(country, operator, product):
    """Buy activation number from SMS service"""
    try:
        response = requests.get(
            f"{API_URL}/user/buy/activation/{country}/{operator}/{product}",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Accept": "application/json"
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to buy number: {e}")
        return None

def get_activation_status(activation_id):
    """Get activation status and SMS code"""
    try:
        response = requests.get(
            f"{API_URL}/user/check/{activation_id}",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Accept": "application/json"
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to get status: {e}")
        return None

async def wait_for_element_with_retry(tab, selector, timeout=5000, max_retries=5):
    """Wait for element with retry logic"""
    for attempt in range(max_retries):
        try:
            element = await tab.select(selector, timeout=timeout)
            if element:
                return element
        except Exception as e:
            log.error(f"Error finding element {selector} : {e}")
        if attempt < max_retries - 1:
            await asyncio.sleep(1)
    
    return None

async def wait_for_page_load(tab, max_wait=15):
    """Wait for page to fully load with improved checks"""
    try:
        await tab.wait_for_ready_state('complete', timeout=max_wait * 1000)
        for _ in range(3):
            is_ready = await tab.evaluate("""
                () => {
                    try {
                        return document.readyState === 'complete' && 
                               document.body && 
                               document.body.children.length > 0 &&
                               !document.querySelector('[aria-busy="true"]');
                    } catch (e) {
                        return false;
                    }
                }
            """)
            if is_ready:
                return
            await asyncio.sleep(1)
    except Exception as e:
        log.error(f"Error waiting for page load: {e}")

async def find_and_click_verify_button(tab, max_attempts=10):
    js_click_script = """
        (() => {
            try {
                const buttons = Array.from(document.querySelectorAll("button"));
                for (const btn of buttons) {
                    const text = btn.innerText.toLowerCase();
                    if (text.includes("verify by phone") || text.includes("verify")) {
                        btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        btn.click();
                        return;
                    }
                }
            } catch (e) {
                console.error("Eval error:", e);
            }
        })()
    """
    for attempt in range(1, max_attempts + 1):
        try:
            await wait_for_page_load(tab)
            await asyncio.sleep(1.5)
            await tab.evaluate(js_click_script) 
            await asyncio.sleep(1)
            current_url = await tab.evaluate("window.location.href")
            if "phone" in current_url.lower() or "verify" not in current_url.lower():
                return True
        except Exception as e:
            log.error(f"❌ Attempt {attempt} error: {e}")
            await asyncio.sleep(1)
    log.error("❌ All attempts failed to click 'Verify by Phone'.")
    return False

async def find_and_click_confirm_button(tab, max_attempts=10):
    js_click_script = """
        (() => {
            try {
                const buttons = document.querySelectorAll("button");
                for (const btn of buttons) {
                    const text = btn.innerText.trim().toLowerCase();
                    if (text.includes("confirm")) {
                        btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        btn.click();
                        return;
                    }
                }
            } catch (e) {
                console.error("Confirm button click error:", e);
            }
        })()
    """
    for attempt in range(1, max_attempts + 1):
        try:
            await wait_for_page_load(tab)
            await asyncio.sleep(1.5)
            await tab.evaluate(js_click_script) 
            await asyncio.sleep(1)
            return True  
        except Exception as e:
            log.error(f"❌ Attempt {attempt} error: {e}")
            await asyncio.sleep(1)
    log.error("❌ Could not click Confirm button.")
    return False

async def click_dropdown_option(tab, expected_text):
    js = f"""
        (() => {{
            const options = document.querySelectorAll('div[class*="option"]');
            for (const opt of options) {{
                if (opt.innerText.trim().toLowerCase() === "{expected_text.lower()}") {{
                    opt.click();
                    return true;
                }}
            }}
            return false;
        }})()
    """
    await tab.evaluate(js)

def close_chrome(profile_dir):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'chrome' in proc.info['name'].lower():
                cmd = ' '.join(proc.info['cmdline']).lower()
                if profile_dir.lower() in cmd:
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    shutil.rmtree(profile_dir, ignore_errors=True)

def load_tokens():
    with open("tokens.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [line.strip().split(":") for line in lines if line.strip() and ":" in line]

def send_notification(title, message):
    if not config.get("notify", False):
        return
    try:
        notification = Notify()
        notification.application_name = "Ultimate Verifier"
        notification.title = title
        notification.message = message
        icon_path = config.get("notification_icon")
        if icon_path and os.path.isfile(icon_path):
            notification.icon = icon_path  
        notification.send()
    except Exception as e:
        log.error(f"❌ Notification error: {e}")

async def login_discord_with_token(token, password, mail):
    """Main login function with verification"""
    temp_profile_dir = tempfile.mkdtemp(prefix="chrome-profile-")
    browser = await uc.start(options={"user_data_dir": temp_profile_dir})
    tab = await browser.get("https://discord.com/login")
    await tab.wait_for_ready_state('complete')
    log.info(f"🕒 Loaded Discord")
    await tab.evaluate(f"""
        function login(token) {{
            setInterval(() => {{
                document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"${{token}}"`;
            }}, 50);
            setTimeout(() => {{ location.reload(); }}, 2500);
        }}
        login("{token}");
        """)
    for _ in range(120):
            try:
                current_url = await tab.evaluate("window.location.href")
                if "discord.com/channels/@me" in current_url:
                    log.success(f"🎉 Successfully logged in with {token}!")
                    break
            except Exception as e:
                log.error(f"Logging in with {token} : {e}")
            await asyncio.sleep(1)
    else:
            log.error(f"Logging in with {token}")
            return False
    await wait_for_page_load(tab)
    if not await find_and_click_verify_button(tab):
        log.failure("finding verify button")
        return False
    dropdown_button = await tab.select("button[class*='countryButton']", timeout=120_000)
    if dropdown_button:
            await dropdown_button.mouse_click()
    else:
            log.failure("❌ Country dropdown not found.")
            return
    country_search_input = await tab.select('input[placeholder="Search a country"]', timeout=120_000)
    if country_search_input:
            await country_search_input.send_keys(COUNTRY)
    else:
            log.failure("❌ Could not find the country search input.")
            return
    for attempt in range(120):
                try:
                        clicked = await tab.evaluate(f'''
                        (() => {{
                                const items = document.querySelectorAll("div.selectableItem_eb626b");
                                for (const item of items) {{
                                        const countryText = item.innerText.toLowerCase();
                                        if (countryText.includes("{COUNTRY.lower()}")) {{
                                                item.click();
                                                return true;
                                        }}
                                }}
                                return false;
                        }})()
                        ''')
                        if clicked:
                                break
                except Exception as e:
                        log.failure(f"while waiting for country option: {e}")
    activation_data = buy_activation_number(COUNTRY, OPERATOR, PRODUCT)
    if not activation_data:
            log.error("Failed to buy activation number")
            return
    number = activation_data["phone"].replace("+", "")
    activation_id = activation_data["id"]
    log.info(f"✅ Phone number bought: +{number}")
    if number.startswith(CODE):
            number = number[len(CODE):]
    no = await tab.select("input[class*='inputField']", timeout=120_000)
    await no.send_keys(number)
    send_btn = await tab.select("button.sendButton_a0c54f", timeout=10000)
    await send_btn.click()
    log.warning("⚠️ Please solve the CAPTCHA!")
    send_notification("ULTIMATE - Termwave", "⚠️ Please solve the CAPTCHA!")
    for attempt in range(120):  
                otp_inputs = await tab.query_selector_all("input.input__5ecaa")
                if len(otp_inputs) == 6:
                        log.success("🎉 Captcha sucessfully solved by the user!")
                        break
                await asyncio.sleep(1)
    else:
                log.error("❌ OTP inputs not found in time.")
                return
    log.info("🔐 Waiting for OTP!")
    otp = None
    for _ in range(30):
            status_data = get_activation_status(activation_id)
            if status_data and "sms" in status_data and len(status_data["sms"]) > 0:
                otp = status_data["sms"][0]["code"]
                log.info(f"🔐 Received OTP: {otp}")
                break
            await asyncio.sleep(1)
    if not otp:
            log.error("Failed to receive OTP in time")
            return
    for i, digit in enumerate(otp):
                await otp_inputs[i].send_keys(digit)
    log.info("🎉 OTP verification complete!")
    for attempt in range(120):  
                try:
                        password_field = await tab.select('input[type="password"]', timeout=120_000)
                        if password_field:
                                await password_field.send_keys(password)
                                log.info("🔐 Entered password.")
                                break
                except:
                        pass
                await asyncio.sleep(1)
    else:
                log.error("❌ Password input did not appear after OTP.")
                return
    clicked = await find_and_click_confirm_button(tab)
    if not clicked:
            return
    await tab.wait_for_ready_state('complete')
    with open("verified.txt", "a", encoding="utf-8") as vf:
        vf.write(f"{mail}:{password}:{token}\n")
    log.success(f"✅ Saved verified token: {mail}:{password}:{token}")
    with open("tokens.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open("tokens.txt", "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip() !=f"{mail}:{password}:{token}":
                  f.write(line)
    close_chrome(temp_profile_dir)
    try:
        await browser.stop()
    except Exception as e:
        log.error(f"❌ Failed to stop browser: {e}")

def main():
    multiprocessing.freeze_support()
    try:
        thread_limit = int(input(Fore.CYAN + f"[{Fore.MAGENTA}?{Fore.CYAN}] Number of parallel threads to run (max 15): "))
        if thread_limit <= 0 or thread_limit > 5:
            log.warning("⚠️ Invalid number, using 5 threads.")
            thread_limit = 15
    except ValueError:
        log.warning("⚠️ Invalid input. Using 1 threads.")
        thread_limit = 1
    accounts = load_tokens()
    if not accounts:
        log.error("No accounts found in tokens.txt.")
        return
    active_processes = []
    for mail, password, token in accounts:
        while len(active_processes) >= thread_limit:
            active_processes = [p for p in active_processes if p.is_alive()]
        p = multiprocessing.Process(target=run_register_and_get_promo, args=(mail, password, token))
        p.start()
        active_processes.append(p)
        log.info(f"🚀 Started process for {mail}")
    for p in active_processes:
        p.join()
    log.success("🎉 All tokens processed!")


banner = '''
 █    ██  ██▓  ▄▄▄█████▓ ██▓ ███▄ ▄███▓ ▄▄▄     ▄▄▄█████▓▓█████ 
 ██  ▓██▒▓██▒  ▓  ██▒ ▓▒▓██▒▓██▒▀█▀ ██▒▒████▄   ▓  ██▒ ▓▒▓█   ▀ 
▓██  ▒██░▒██░  ▒ ▓██░ ▒░▒██▒▓██    ▓██░▒██  ▀█▄ ▒ ▓██░ ▒░▒███   
▓▓█  ░██░▒██░  ░ ▓██▓ ░ ░██░▒██    ▒██ ░██▄▄▄▄██░ ▓██▓ ░ ▒▓█  ▄ 
▒▒█████▓ ░██████▒▒██▒ ░ ░██░▒██▒   ░██▒ ▓█   ▓██▒ ▒██▒ ░ ░▒████▒
░▒▓▒ ▒ ▒ ░ ▒░▓  ░▒ ░░   ░▓  ░ ▒░   ░  ░ ▒▒   ▓▒█░ ▒ ░░   ░░ ▒░ ░
░░▒░ ░ ░ ░ ░ ▒  ░  ░     ▒ ░░  ░      ░  ▒   ▒▒ ░   ░     ░ ░  ░
 ░░░ ░ ░   ░ ░   ░       ▒ ░░      ░     ░   ▒    ░         ░   
   ░         ░  ░        ░         ░         ░  ░           ░  ░
                                                                
'''
def print_gradient_text(text, start_color=(137, 207, 240), end_color=(25, 25, 112)):
    lines = text.split('\n')
    total_lines = len(lines)
    for i, line in enumerate(lines):
        if not line.strip():
            print(line)
            continue
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / total_lines)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / total_lines)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / total_lines)
        color_code = f"\033[38;2;{r};{g};{b}m"
        print(f"{color_code}{line}{Style.RESET_ALL}")            
cret = f'''[+] Creator - Termwave'''
contri = f'''[+] Contributor - Wizard X Predzen'''
def run_register_and_get_promo(mail, password, token):
    asyncio.run(login_discord_with_token(token, password, mail))

async def register_and_get_promo():
    accounts = load_tokens()
    for mail, password, token in accounts:
        try:
            asyncio.run(login_discord_with_token(token, password, mail))
        except Exception as e:
            log.error(f"Unhandled error for {mail}: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    print("\n")
    print_gradient_text(Center.XCenter(banner))
    print_gradient_text(Center.XCenter(cret))
    print_gradient_text(Center.XCenter(contri))
    print("\n")
    if not config.get("notify", True):
        log.warning("⚠️ Notification Alert is disabled at config.json.")
    main()