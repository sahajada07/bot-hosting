"""
╔══════════════════════════════════════════════════════╗
║  🚀 EXU HOSTING PRO X — Bangladesh Premium Edition  ║
║  v2.2 FIXED — Smart Entry Detection + Stable Run    ║
╚══════════════════════════════════════════════════════╝
"""

import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import random
import hashlib
import string
import traceback

# ═══════════════════════════════════════════════════
#  FLASK KEEP ALIVE
# ═══════════════════════════════════════════════════
from flask import Flask, jsonify
from threading import Thread

flask_app = Flask('')


@flask_app.route('/')
def home():
    return "🚀 EXU HOSTING PRO X is Running!"


@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy", "uptime": get_uptime(), "version": "2.2"})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)


def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ Flask Keep-Alive started")


# ═══════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════
TOKEN = os.environ.get('BOT_TOKEN', '8511307590:AAHUT-ZrtcoqEZgU5m1-g2kFVh70xa8SC_g')
OWNER_ID = int(os.environ.get('OWNER_ID', '6678577936'))
ADMIN_ID = int(os.environ.get('ADMIN_ID', '6678577936'))
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'apon_vps_bot')
YOUR_USERNAME = os.environ.get('SUPPORT_USERNAME', '@developer_apon')
UPDATE_CHANNEL = os.environ.get('UPDATE_CHANNEL', 'https://t.me/developer_apon_07')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
DATA_DIR = os.path.join(BASE_DIR, 'exu_data')
DATABASE_PATH = os.path.join(DATA_DIR, 'exu_hosting.db')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')

PLAN_LIMITS = {
    'free': {'name': '🆓 Free Plan', 'max_bots': 1, 'storage_mb': 50,
             'ram_mb': 128, 'restarts_per_day': 2, 'auto_restart': False,
             'priority_support': False, 'price_bdt': 0},
    'basic': {'name': '⭐ Basic Plan', 'max_bots': 3, 'storage_mb': 256,
              'ram_mb': 512, 'restarts_per_day': -1, 'auto_restart': True,
              'priority_support': False, 'price_bdt': 199},
    'pro': {'name': '💎 Pro Plan', 'max_bots': 10, 'storage_mb': 1024,
            'ram_mb': 2048, 'restarts_per_day': -1, 'auto_restart': True,
            'priority_support': True, 'price_bdt': 499},
    'lifetime': {'name': '👑 Lifetime Plan', 'max_bots': -1, 'storage_mb': 5120,
                 'ram_mb': 4096, 'restarts_per_day': -1, 'auto_restart': True,
                 'priority_support': True, 'price_bdt': 1999},
}

PAYMENT_METHODS = {
    'bkash': {'name': 'bKash', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟪'},
    'nagad': {'name': 'Nagad', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟧'},
    'rocket': {'name': 'Rocket', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟦'},
    'upay': {'name': 'Upay', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟩'},
    'bank': {'name': 'Bank Transfer', 'number': 'AC: XXXXXXXXXX', 'type': 'Transfer', 'icon': '🏦'},
}

REFERRAL_BONUS_DAYS = 3
REFERRAL_COMMISSION_BDT = 20

for d in [UPLOAD_BOTS_DIR, DATA_DIR, LOGS_DIR, BACKUPS_DIR]:
    os.makedirs(d, exist_ok=True)

# ═══════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-15s | %(levelname)-7s | %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'exu_hosting.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EXU')

# ═══════════════════════════════════════════════════
#  INITIALIZE BOT
# ═══════════════════════════════════════════════════
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ═══════════════════════════════════════════════════
#  IN-MEMORY DATA
# ═══════════════════════════════════════════════════
bot_scripts = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False
bot_start_time = datetime.now()
user_states = {}
payment_states = {}
deploy_states = {}

TELEGRAM_MODULES = {
    'telebot': 'pytelegrambotapi', 'telegram': 'python-telegram-bot',
    'pyrogram': 'pyrogram', 'telethon': 'telethon', 'aiogram': 'aiogram',
    'PIL': 'Pillow', 'cv2': 'opencv-python', 'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4', 'dotenv': 'python-dotenv', 'yaml': 'pyyaml',
    'aiohttp': 'aiohttp', 'numpy': 'numpy', 'pandas': 'pandas',
    'requests': 'requests', 'flask': 'flask', 'fastapi': 'fastapi',
}


# ═══════════════════════════════════════════════════
#  🔥 SMART ENTRY FILE DETECTOR (নতুন!)
# ═══════════════════════════════════════════════════
class EntryFileDetector:
    """
    Smart detection system — কোন ফাইল দিয়ে বট রান করতে হবে
    সেটা automatically খুঁজে বের করে
    """

    # Priority order — এই ক্রমে খুঁজবে
    PYTHON_ENTRY_PRIORITY = [
        'main.py',
        'app.py',
        'bot.py',
        'run.py',
        'start.py',
        'server.py',
        'index.py',
        'manage.py',
        '__main__.py',
    ]

    JS_ENTRY_PRIORITY = [
        'index.js',
        'app.js',
        'bot.js',
        'main.js',
        'server.js',
        'start.js',
        'run.js',
    ]

    @staticmethod
    def detect_entry_file(directory):
        """
        একটি ডিরেক্টরিতে entry file খুঁজে বের করে
        Returns: (entry_file_path, file_type, confidence)
        """
        if not os.path.isdir(directory):
            # Single file
            if os.path.isfile(directory):
                ext = directory.rsplit('.', 1)[-1].lower()
                return os.path.basename(directory), ext, 'exact'
            return None, None, None

        # ── Step 1: Top-level priority files খুঁজি ──
        top_files = os.listdir(directory)

        # Python files check
        for entry in EntryFileDetector.PYTHON_ENTRY_PRIORITY:
            if entry in top_files:
                full_path = os.path.join(directory, entry)
                if os.path.isfile(full_path):
                    logger.info(f"✅ Entry detected (top-level): {entry}")
                    return entry, 'py', 'high'

        # JS files check
        for entry in EntryFileDetector.JS_ENTRY_PRIORITY:
            if entry in top_files:
                full_path = os.path.join(directory, entry)
                if os.path.isfile(full_path):
                    logger.info(f"✅ Entry detected (top-level JS): {entry}")
                    return entry, 'js', 'high'

        # ── Step 2: package.json চেক করি (Node.js project) ──
        package_json = os.path.join(directory, 'package.json')
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    pkg = json.load(f)
                # "main" field check
                if 'main' in pkg:
                    main_file = pkg['main']
                    if os.path.exists(os.path.join(directory, main_file)):
                        logger.info(f"✅ Entry from package.json: {main_file}")
                        ext = main_file.rsplit('.', 1)[-1].lower()
                        return main_file, ext, 'high'
                # "scripts.start" check
                if 'scripts' in pkg and 'start' in pkg['scripts']:
                    start_cmd = pkg['scripts']['start']
                    # "node index.js" বা "node app.js" থেকে file name বের করি
                    match = re.search(r'node\s+(\S+\.js)', start_cmd)
                    if match:
                        js_file = match.group(1)
                        if os.path.exists(os.path.join(directory, js_file)):
                            logger.info(f"✅ Entry from package.json scripts: {js_file}")
                            return js_file, 'js', 'high'
                    # "python app.py" বা "python3 main.py"
                    match = re.search(r'python[3]?\s+(\S+\.py)', start_cmd)
                    if match:
                        py_file = match.group(1)
                        if os.path.exists(os.path.join(directory, py_file)):
                            logger.info(f"✅ Entry from package.json scripts: {py_file}")
                            return py_file, 'py', 'high'
            except Exception as e:
                logger.warning(f"package.json parse error: {e}")

        # ── Step 3: Procfile চেক করি (Railway/Heroku) ──
        procfile = os.path.join(directory, 'Procfile')
        if os.path.exists(procfile):
            try:
                with open(procfile, 'r') as f:
                    content = f.read()
                # "worker: python main.py" বা "web: python app.py"
                match = re.search(r'(?:worker|web):\s*python[3]?\s+(\S+\.py)', content)
                if match:
                    py_file = match.group(1)
                    if os.path.exists(os.path.join(directory, py_file)):
                        logger.info(f"✅ Entry from Procfile: {py_file}")
                        return py_file, 'py', 'high'
                match = re.search(r'(?:worker|web):\s*node\s+(\S+\.js)', content)
                if match:
                    js_file = match.group(1)
                    if os.path.exists(os.path.join(directory, js_file)):
                        logger.info(f"✅ Entry from Procfile: {js_file}")
                        return js_file, 'js', 'high'
            except Exception as e:
                logger.warning(f"Procfile parse error: {e}")

        # ── Step 4: requirements.txt / setup.py আছে কিনা (Python project) ──
        has_requirements = os.path.exists(os.path.join(directory, 'requirements.txt'))
        has_setup = os.path.exists(os.path.join(directory, 'setup.py'))

        # ── Step 5: Subdirectory তে খুঁজি ──
        for root, dirs, files in os.walk(directory):
            # শুধু ১ লেভেল ডিপ
            rel_root = os.path.relpath(root, directory)
            depth = rel_root.count(os.sep)
            if depth > 1:
                continue

            for entry in EntryFileDetector.PYTHON_ENTRY_PRIORITY:
                if entry in files:
                    rel_path = os.path.relpath(os.path.join(root, entry), directory)
                    logger.info(f"✅ Entry detected (subdirectory): {rel_path}")
                    return rel_path, 'py', 'medium'

            for entry in EntryFileDetector.JS_ENTRY_PRIORITY:
                if entry in files:
                    rel_path = os.path.relpath(os.path.join(root, entry), directory)
                    logger.info(f"✅ Entry detected (subdirectory JS): {rel_path}")
                    return rel_path, 'js', 'medium'

        # ── Step 6: Content analysis — ফাইলের ভিতরে দেখি ──
        py_files = []
        js_files = []
        for root, dirs, files in os.walk(directory):
            rel_root = os.path.relpath(root, directory)
            if rel_root.count(os.sep) > 1:
                continue
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, directory)
                if f.endswith('.py'):
                    py_files.append((rel, full))
                elif f.endswith('.js'):
                    js_files.append((rel, full))

        # Python ফাইলের ভিতরে bot/telebot/polling খুঁজি
        for rel, full in py_files:
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000)  # প্রথম 5KB পড়ি

                # Bot indicators
                bot_indicators = [
                    'infinity_polling', 'polling()', 'bot.polling',
                    'bot.run()', 'app.run(', 'if __name__',
                    'telebot.TeleBot', 'Bot(token', 'Client(',
                    'Updater(', 'Application.builder',
                    '.start_polling', '.run_polling',
                ]
                score = sum(1 for ind in bot_indicators if ind in content)
                if score >= 2:
                    logger.info(f"✅ Entry detected (content analysis): {rel} (score: {score})")
                    return rel, 'py', 'medium'
            except:
                pass

        # JS ফাইলের ভিতরে bot indicators খুঁজি
        for rel, full in js_files:
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000)
                indicators = [
                    'require(', 'module.exports', 'app.listen',
                    'bot.launch', 'client.login', 'bot.start',
                    'createServer', 'express()',
                ]
                score = sum(1 for ind in indicators if ind in content)
                if score >= 2:
                    logger.info(f"✅ Entry detected (content analysis JS): {rel} (score: {score})")
                    return rel, 'js', 'medium'
            except:
                pass

        # ── Step 7: Fallback — প্রথম .py বা .js ফাইল নিই ──
        if py_files:
            logger.info(f"⚠️ Entry fallback (first .py): {py_files[0][0]}")
            return py_files[0][0], 'py', 'low'

        if js_files:
            logger.info(f"⚠️ Entry fallback (first .js): {js_files[0][0]}")
            return js_files[0][0], 'js', 'low'

        return None, None, None

    @staticmethod
    def install_requirements(directory, chat_id=None):
        """requirements.txt থাকলে auto install করে"""
        req_file = os.path.join(directory, 'requirements.txt')
        if os.path.exists(req_file):
            logger.info(f"📦 Installing requirements from {req_file}")
            if chat_id:
                try:
                    bot.send_message(chat_id,
                                     "📦 <b>Installing requirements.txt...</b>",
                                     parse_mode='HTML')
                except:
                    pass
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', req_file,
                     '--quiet', '--no-warn-script-location'],
                    capture_output=True, text=True, timeout=300,
                    cwd=directory
                )
                if result.returncode == 0:
                    logger.info("✅ Requirements installed successfully")
                    return True
                else:
                    logger.warning(f"⚠️ Some requirements failed: {result.stderr[:200]}")
                    return True  # Continue anyway
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Requirements install timeout")
                return True
            except Exception as e:
                logger.error(f"Requirements install error: {e}")
                return True
        return True

    @staticmethod
    def install_npm_packages(directory, chat_id=None):
        """package.json থাকলে npm install করে"""
        pkg_file = os.path.join(directory, 'package.json')
        if os.path.exists(pkg_file):
            node_modules = os.path.join(directory, 'node_modules')
            if os.path.exists(node_modules):
                return True  # Already installed

            logger.info(f"📦 Running npm install in {directory}")
            if chat_id:
                try:
                    bot.send_message(chat_id,
                                     "📦 <b>Running npm install...</b>",
                                     parse_mode='HTML')
                except:
                    pass
            try:
                result = subprocess.run(
                    ['npm', 'install', '--production'],
                    capture_output=True, text=True, timeout=300,
                    cwd=directory
                )
                if result.returncode == 0:
                    logger.info("✅ npm install success")
                    return True
                else:
                    logger.warning(f"npm install issues: {result.stderr[:200]}")
                    return True
            except FileNotFoundError:
                logger.warning("npm not found")
                return False
            except Exception as e:
                logger.error(f"npm install error: {e}")
                return True
        return True

    @staticmethod
    def get_detection_report(directory):
        """Detection report তৈরি করে — user কে দেখানোর জন্য"""
        entry, ftype, confidence = EntryFileDetector.detect_entry_file(directory)

        if not entry:
            return None, None, "❌ No runnable file found!"

        confidence_icons = {
            'exact': '🎯 Exact Match',
            'high': '✅ High Confidence',
            'medium': '🟡 Medium Confidence',
            'low': '⚠️ Low Confidence (Fallback)'
        }

        type_icons = {
            'py': '🐍 Python',
            'js': '🟨 Node.js'
        }

        report = (
            f"📄 <b>Entry File:</b> <code>{entry}</code>\n"
            f"🔤 <b>Type:</b> {type_icons.get(ftype, ftype)}\n"
            f"🎯 <b>Detection:</b> {confidence_icons.get(confidence, confidence)}"
        )

        return entry, ftype, report


# Create detector instance
detector = EntryFileDetector()


# ═══════════════════════════════════════════════════
#  ANIMATION SYSTEM
# ═══════════════════════════════════════════════════
def send_animated_message(chat_id, final_text, animation_type="loading",
                          duration=2, steps=4):
    """Animated loading message"""
    try:
        action_map = {
            "loading": "Authenticating session",
            "upload": "Uploading file",
            "deploy": "Deploying bot",
            "run": "Starting script",
            "stop": "Stopping script",
            "install": "Installing dependencies",
            "detect": "Detecting entry file",
            "payment": "Processing payment",
        }
        action_text = action_map.get(animation_type, "Processing")

        msg = None
        for i in range(steps + 1):
            percent = int((i / steps) * 100)
            bar = "🟩" * i + "⬜" * (steps - i)
            display = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({percent}%)\n[{bar}] {action_text}..."
            if i == 0:
                msg = bot.send_message(chat_id, display)
            else:
                try:
                    bot.edit_message_text(display, chat_id, msg.message_id)
                except:
                    pass
            time.sleep(duration / steps)

        try:
            bot.edit_message_text(final_text, chat_id, msg.message_id,
                                  parse_mode='HTML')
        except:
            msg = bot.send_message(chat_id, final_text, parse_mode='HTML')
        return msg
    except Exception as e:
        logger.error(f"Animation error: {e}")
        return bot.send_message(chat_id, final_text, parse_mode='HTML')


def send_progress_animation(chat_id, action_text, total_steps=4):
    """Progress animation"""
    try:
        msg = None
        for step in range(total_steps + 1):
            percent = int((step / total_steps) * 100)
            bar = "🟩" * step + "⬜" * (total_steps - step)
            display = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({percent}%)\n[{bar}] {action_text}..."
            if step == 0:
                msg = bot.send_message(chat_id, display)
            else:
                try:
                    bot.edit_message_text(display, chat_id, msg.message_id)
                except:
                    pass
            time.sleep(0.4)
        return msg
    except Exception as e:
        logger.error(f"Progress error: {e}")
        return None


# ═══════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════
def get_uptime():
    uptime = datetime.now() - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"


def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def create_mini_bar(percentage, length=20):
    filled = int((percentage / 100) * length)
    return f"[{'█' * filled}{'░' * (length - filled)}]"


def generate_referral_code(user_id):
    hash_str = hashlib.md5(str(user_id).encode()).hexdigest()[:6]
    return f"EXU{hash_str.upper()}"


def time_remaining(end_date_str):
    if not end_date_str:
        return "♾️ Lifetime"
    try:
        end = datetime.fromisoformat(end_date_str)
        if end <= datetime.now():
            return "❌ Expired"
        diff = end - datetime.now()
        return f"{diff.days}d {diff.seconds // 3600}h remaining"
    except:
        return "Unknown"


def get_user_folder(user_id):
    folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder


def is_bot_running_check(script_key):
    info = bot_scripts.get(script_key)
    if info and info.get('process'):
        try:
            proc = psutil.Process(info['process'].pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except:
            return False
    return False


def is_bot_running(user_id, bot_name):
    return is_bot_running_check(f"{user_id}_{bot_name}")


def cleanup_script(script_key):
    if script_key in bot_scripts:
        info = bot_scripts[script_key]
        if 'log_file' in info:
            try:
                if hasattr(info['log_file'], 'close') and not info['log_file'].closed:
                    info['log_file'].close()
            except:
                pass
        del bot_scripts[script_key]
        logger.info(f"Cleaned: {script_key}")


def kill_process_tree(process_info):
    try:
        if 'log_file' in process_info:
            try:
                if hasattr(process_info['log_file'], 'close'):
                    if not process_info['log_file'].closed:
                        process_info['log_file'].close()
            except:
                pass
        proc = process_info.get('process')
        if proc and hasattr(proc, 'pid'):
            try:
                parent = psutil.Process(proc.pid)
                children = parent.children(recursive=True)
                for c in children:
                    try:
                        c.terminate()
                    except:
                        pass
                psutil.wait_procs(children, timeout=3)
                for c in children:
                    try:
                        c.kill()
                    except:
                        pass
                try:
                    parent.terminate()
                    parent.wait(timeout=3)
                except psutil.TimeoutExpired:
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass
            except psutil.NoSuchProcess:
                pass
    except Exception as e:
        logger.error(f"Kill error: {e}")


def get_system_stats():
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            'cpu': cpu, 'memory_used': mem.percent,
            'memory_total': format_size(mem.total),
            'disk_percent': round(disk.used / disk.total * 100, 1),
            'disk_total': round(disk.total / (1024 ** 3), 1),
            'uptime': get_uptime()
        }
    except:
        return {'cpu': 0, 'memory_used': 0, 'memory_total': '0',
                'disk_percent': 0, 'disk_total': 0, 'uptime': get_uptime()}


# ═══════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════
class Database:
    _lock = threading.Lock()

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._create_tables()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def execute(self, query, params=(), fetch=False, fetchone=False):
        with self._lock:
            conn = self._connect()
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                if fetch:
                    r = [dict(row) for row in cursor.fetchall()]
                    conn.close()
                    return r
                if fetchone:
                    row = cursor.fetchone()
                    conn.close()
                    return dict(row) if row else None
                conn.commit()
                lid = cursor.lastrowid
                conn.close()
                return lid
            except Exception as e:
                conn.close()
                logger.error(f"DB: {e}")
                return None

    def _create_tables(self):
        self.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '',
            full_name TEXT DEFAULT '', language TEXT DEFAULT 'en',
            plan TEXT DEFAULT 'free', subscription_end TEXT DEFAULT NULL,
            is_lifetime INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0,
            ban_reason TEXT DEFAULT '', is_admin INTEGER DEFAULT 0,
            wallet_balance REAL DEFAULT 0.0, referral_code TEXT UNIQUE,
            referred_by INTEGER DEFAULT NULL, referral_count INTEGER DEFAULT 0,
            referral_level TEXT DEFAULT 'bronze', referral_earnings REAL DEFAULT 0.0,
            total_spent REAL DEFAULT 0.0, created_at TEXT DEFAULT (datetime('now')),
            last_active TEXT DEFAULT (datetime('now'))
        )""")

        self.execute("""CREATE TABLE IF NOT EXISTS bots (
            bot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, bot_name TEXT NOT NULL,
            bot_token TEXT DEFAULT '', file_path TEXT NOT NULL,
            entry_file TEXT DEFAULT 'main.py', file_type TEXT DEFAULT 'py',
            status TEXT DEFAULT 'stopped', pid INTEGER DEFAULT NULL,
            ram_usage_mb REAL DEFAULT 0, cpu_usage_pct REAL DEFAULT 0,
            restarts_today INTEGER DEFAULT 0, total_restarts INTEGER DEFAULT 0,
            auto_restart INTEGER DEFAULT 1, last_started TEXT DEFAULT NULL,
            last_stopped TEXT DEFAULT NULL, last_crash TEXT DEFAULT NULL,
            error_log TEXT DEFAULT '', file_size INTEGER DEFAULT 0,
            detection_confidence TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )""")

        self.execute("""CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, amount REAL NOT NULL,
            method TEXT NOT NULL, transaction_id TEXT NOT NULL,
            plan TEXT NOT NULL, duration_days INTEGER DEFAULT 30,
            status TEXT DEFAULT 'pending', approved_by INTEGER DEFAULT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            processed_at TEXT DEFAULT NULL
        )""")

        self.execute("""CREATE TABLE IF NOT EXISTS referrals (
            ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL, referred_id INTEGER NOT NULL,
            bonus_days INTEGER DEFAULT 0, commission REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )""")

        self.execute("""CREATE TABLE IF NOT EXISTS wallet_transactions (
            tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, amount REAL NOT NULL,
            tx_type TEXT NOT NULL, description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )""")

        self.execute("""CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY, discount_pct INTEGER DEFAULT 0,
            bonus_days INTEGER DEFAULT 0, max_uses INTEGER DEFAULT -1,
            current_uses INTEGER DEFAULT 0, created_by INTEGER DEFAULT NULL,
            is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT (datetime('now'))
        )""")

        self.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL, action TEXT NOT NULL,
            target_user INTEGER DEFAULT NULL, details TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )""")

        logger.info("✅ Database initialized")

    # ── User Methods ──
    def get_user(self, uid):
        return self.execute("SELECT * FROM users WHERE user_id=?", (uid,), fetchone=True)

    def create_user(self, uid, username='', full_name='', ref_code='', referred_by=None):
        self.execute("INSERT OR IGNORE INTO users (user_id,username,full_name,referral_code,referred_by) VALUES(?,?,?,?,?)",
                     (uid, username, full_name, ref_code, referred_by))

    def update_user(self, uid, **kw):
        if not kw: return
        f = ', '.join(f"{k}=?" for k in kw)
        self.execute(f"UPDATE users SET {f} WHERE user_id=?", list(kw.values()) + [uid])

    def get_all_users(self):
        return self.execute("SELECT * FROM users", fetch=True) or []

    def ban_user(self, uid, reason=''):
        self.update_user(uid, is_banned=1, ban_reason=reason)

    def unban_user(self, uid):
        self.update_user(uid, is_banned=0, ban_reason='')

    def set_subscription(self, uid, plan, days=30):
        if plan == 'lifetime':
            self.update_user(uid, plan=plan, is_lifetime=1, subscription_end=None)
        else:
            end = (datetime.now() + timedelta(days=days)).isoformat()
            self.update_user(uid, plan=plan, is_lifetime=0, subscription_end=end)

    def remove_subscription(self, uid):
        self.update_user(uid, plan='free', is_lifetime=0, subscription_end=None)

    def is_subscription_active(self, uid):
        u = self.get_user(uid)
        if not u: return False
        if u['is_lifetime']: return True
        if u['plan'] == 'free': return True
        if u['subscription_end']:
            try: return datetime.fromisoformat(u['subscription_end']) > datetime.now()
            except: return False
        return False

    def get_user_plan(self, uid):
        u = self.get_user(uid)
        if not u: return PLAN_LIMITS['free']
        if uid == OWNER_ID or uid in admin_ids: return PLAN_LIMITS['lifetime']
        return PLAN_LIMITS.get(u['plan'], PLAN_LIMITS['free'])

    # ── Bot Methods ──
    def add_bot(self, uid, name, path, entry='main.py', ftype='py',
                token='', size=0, confidence=''):
        return self.execute(
            "INSERT INTO bots (user_id,bot_name,file_path,entry_file,file_type,bot_token,file_size,detection_confidence) VALUES(?,?,?,?,?,?,?,?)",
            (uid, name, path, entry, ftype, token, size, confidence))

    def get_user_bots(self, uid):
        return self.execute("SELECT * FROM bots WHERE user_id=?", (uid,), fetch=True) or []

    def get_bot(self, bid):
        return self.execute("SELECT * FROM bots WHERE bot_id=?", (bid,), fetchone=True)

    def update_bot(self, bid, **kw):
        if not kw: return
        f = ', '.join(f"{k}=?" for k in kw)
        self.execute(f"UPDATE bots SET {f} WHERE bot_id=?", list(kw.values()) + [bid])

    def delete_bot(self, bid):
        self.execute("DELETE FROM bots WHERE bot_id=?", (bid,))

    def get_user_bot_count(self, uid):
        r = self.execute("SELECT COUNT(*) as c FROM bots WHERE user_id=?", (uid,), fetchone=True)
        return r['c'] if r else 0

    # ── Payment Methods ──
    def create_payment(self, uid, amount, method, trx_id, plan, days=30):
        return self.execute(
            "INSERT INTO payments (user_id,amount,method,transaction_id,plan,duration_days) VALUES(?,?,?,?,?,?)",
            (uid, amount, method, trx_id, plan, days))

    def get_pending_payments(self):
        return self.execute("SELECT * FROM payments WHERE status='pending' ORDER BY created_at DESC", fetch=True) or []

    def get_payment(self, pid):
        return self.execute("SELECT * FROM payments WHERE payment_id=?", (pid,), fetchone=True)

    def approve_payment(self, pid, admin_id):
        p = self.get_payment(pid)
        if not p: return None
        self.execute("UPDATE payments SET status='approved',approved_by=?,processed_at=datetime('now') WHERE payment_id=?",
                     (admin_id, pid))
        self.set_subscription(p['user_id'], p['plan'], p['duration_days'])
        return p

    def reject_payment(self, pid, admin_id):
        self.execute("UPDATE payments SET status='rejected',approved_by=?,processed_at=datetime('now') WHERE payment_id=?",
                     (admin_id, pid))

    # ── Referral ──
    def add_referral(self, referrer, referred, days=3, commission=20):
        self.execute("INSERT INTO referrals (referrer_id,referred_id,bonus_days,commission) VALUES(?,?,?,?)",
                     (referrer, referred, days, commission))
        u = self.get_user(referrer)
        if u:
            self.update_user(referrer,
                             referral_count=u['referral_count'] + 1,
                             referral_earnings=u['referral_earnings'] + commission,
                             wallet_balance=u['wallet_balance'] + commission,
                             referral_level='gold' if u['referral_count'] + 1 >= 50 else 'silver' if u['referral_count'] + 1 >= 10 else 'bronze')

    def get_referral_leaderboard(self, limit=10):
        return self.execute("SELECT * FROM users ORDER BY referral_count DESC LIMIT ?", (limit,), fetch=True) or []

    def get_user_referrals(self, uid):
        return self.execute("SELECT * FROM referrals WHERE referrer_id=?", (uid,), fetch=True) or []

    # ── Wallet ──
    def add_wallet_tx(self, uid, amount, tx_type, desc=''):
        self.execute("INSERT INTO wallet_transactions (user_id,amount,tx_type,description) VALUES(?,?,?,?)",
                     (uid, amount, tx_type, desc))
        if tx_type in ('credit', 'referral', 'refund'):
            self.execute("UPDATE users SET wallet_balance=wallet_balance+? WHERE user_id=?", (amount, uid))
        elif tx_type in ('debit', 'withdraw', 'purchase'):
            self.execute("UPDATE users SET wallet_balance=wallet_balance-? WHERE user_id=?", (amount, uid))

    def get_wallet_history(self, uid, limit=20):
        return self.execute("SELECT * FROM wallet_transactions WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                            (uid, limit), fetch=True) or []

    # ── Promo ──
    def create_promo(self, code, disc=0, days=0, max_uses=-1, by=None):
        self.execute("INSERT OR IGNORE INTO promo_codes (code,discount_pct,bonus_days,max_uses,created_by) VALUES(?,?,?,?,?)",
                     (code.upper(), disc, days, max_uses, by))

    # ── Admin Log ──
    def add_admin_log(self, aid, action, target=None, details=''):
        self.execute("INSERT INTO admin_logs (admin_id,action,target_user,details) VALUES(?,?,?,?)",
                     (aid, action, target, details))

    def get_admin_logs(self, limit=50):
        return self.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?", (limit,), fetch=True) or []

    # ── Stats ──
    def get_stats(self):
        tu = (self.execute("SELECT COUNT(*) as c FROM users", fetchone=True) or {}).get('c', 0)
        tb = (self.execute("SELECT COUNT(*) as c FROM bots", fetchone=True) or {}).get('c', 0)
        pp = (self.execute("SELECT COUNT(*) as c FROM payments WHERE status='pending'", fetchone=True) or {}).get('c', 0)
        rev = (self.execute("SELECT COALESCE(SUM(amount),0) as s FROM payments WHERE status='approved'", fetchone=True) or {}).get('s', 0)
        return {'total_users': tu, 'total_bots': tb, 'pending_payments': pp, 'total_revenue': rev}


db = Database()


# ═══════════════════════════════════════════════════
#  🔥 FIXED SCRIPT RUNNER ENGINE
# ═══════════════════════════════════════════════════
def attempt_install_pip(module_name, chat_id):
    """Auto install missing Python package"""
    package = TELEGRAM_MODULES.get(module_name.split('.')[0].lower(), module_name)
    try:
        msg = send_progress_animation(chat_id, f"Installing {package}", 4)
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package, '--quiet'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            try:
                bot.edit_message_text(f"✅ Installed <code>{package}</code>",
                                      chat_id, msg.message_id, parse_mode='HTML')
            except:
                pass
            return True
        return False
    except:
        return False


def run_bot_script(bot_id, chat_id, attempt=1):
    """
    🔥 FIXED: Universal bot runner
    - Auto-detects entry file (app.py, main.py, bot.py, etc.)
    - Installs requirements automatically
    - Waits longer before checking (5 seconds instead of 2)
    - Better error handling
    """
    MAX_ATTEMPTS = 3
    if attempt > MAX_ATTEMPTS:
        bot.send_message(chat_id,
                         f"❌ Failed after {MAX_ATTEMPTS} attempts.\n"
                         f"Check your code for errors!")
        return

    bot_data = db.get_bot(bot_id)
    if not bot_data:
        bot.send_message(chat_id, "❌ Bot not found!")
        return

    user_id = bot_data['user_id']
    bot_name = bot_data['bot_name']
    file_path = bot_data['file_path']
    entry_file = bot_data['entry_file']
    file_type = bot_data['file_type']
    script_key = f"{user_id}_{bot_name}"

    logger.info(f"▶️ Starting bot #{bot_id}: {bot_name} (attempt {attempt})")

    # ── Step 1: Determine working directory ──
    if os.path.isdir(file_path):
        work_dir = file_path
    else:
        work_dir = get_user_folder(user_id)

    # ── Step 2: Re-detect entry file if needed ──
    if attempt == 1:
        # Fresh detection every time
        detected_entry, detected_type, report = detector.get_detection_report(work_dir)

        if detected_entry:
            entry_file = detected_entry
            file_type = detected_type or 'py'
            # Update database with detected entry
            db.update_bot(bot_id, entry_file=entry_file, file_type=file_type)
            logger.info(f"🔍 Detection result: {entry_file} ({file_type})")
        elif not os.path.exists(os.path.join(work_dir, entry_file)):
            # Entry file doesn't exist, try detection
            detected_entry, detected_type, report = detector.get_detection_report(work_dir)
            if detected_entry:
                entry_file = detected_entry
                file_type = detected_type or 'py'
                db.update_bot(bot_id, entry_file=entry_file, file_type=file_type)

    # ── Step 3: Verify entry file exists ──
    full_script_path = os.path.join(work_dir, entry_file)

    if not os.path.exists(full_script_path):
        # Try alternate locations
        found = False
        for root, dirs, files in os.walk(work_dir):
            basename = os.path.basename(entry_file)
            if basename in files:
                full_script_path = os.path.join(root, basename)
                entry_file = os.path.relpath(full_script_path, work_dir)
                db.update_bot(bot_id, entry_file=entry_file)
                found = True
                break

        if not found:
            error_text = f"""
╔══════════════════════════════════════╗
║  ❌ <b>ENTRY FILE NOT FOUND!</b>             ║
╠══════════════════════════════════════╣
║
║  📄 Expected: <code>{entry_file}</code>
║  📂 Directory: <code>{work_dir[-30:]}</code>
║
║  <b>Files found in directory:</b>
"""
            # List files in directory
            try:
                all_files = []
                for root, dirs, files in os.walk(work_dir):
                    for f in files:
                        if f.endswith(('.py', '.js')):
                            rel = os.path.relpath(os.path.join(root, f), work_dir)
                            all_files.append(rel)

                for f in all_files[:10]:
                    error_text += f"║  • <code>{f}</code>\n"

                if not all_files:
                    error_text += "║  (No .py or .js files found)\n"
            except:
                pass

            error_text += "╚══════════════════════════════════════╝"
            bot.send_message(chat_id, error_text, parse_mode='HTML')
            return

    # ── Step 4: Install dependencies ──
    if attempt == 1:
        if file_type == 'py':
            detector.install_requirements(work_dir, chat_id)
        elif file_type == 'js':
            detector.install_npm_packages(work_dir, chat_id)

    # ── Step 5: Show starting animation ──
    start_text = f"""
╔══════════════════════════════════════╗
║  🚀 <b>STARTING BOT</b>                      ║
╠══════════════════════════════════════╣
║  📄 File: <code>{entry_file[:25]}</code>
║  🔤 Type: {'🐍 Python' if file_type == 'py' else '🟨 Node.js'}
║  🔄 Attempt: {attempt}/{MAX_ATTEMPTS}
║  📂 Dir: <code>{os.path.basename(work_dir)[:20]}</code>
╚══════════════════════════════════════╝
"""
    msg = send_animated_message(chat_id, start_text, "run", duration=2)

    # ── Step 6: Start process ──
    try:
        log_file_path = os.path.join(LOGS_DIR, f"{script_key}.log")
        log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')

        if file_type == 'js':
            cmd = ['node', full_script_path]
        else:
            cmd = [sys.executable, '-u', full_script_path]
            # -u flag = unbuffered output (logs show immediately)

        env = os.environ.copy()
        if bot_data.get('bot_token'):
            env['BOT_TOKEN'] = bot_data['bot_token']
        env['EXU_BOT_ID'] = str(bot_id)
        env['PYTHONUNBUFFERED'] = '1'

        process = subprocess.Popen(
            cmd,
            cwd=work_dir,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='ignore',
            env=env,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )

        bot_scripts[script_key] = {
            'process': process,
            'file_name': bot_name,
            'bot_id': bot_id,
            'user_id': user_id,
            'start_time': datetime.now(),
            'log_file': log_file,
            'log_path': log_file_path,
            'script_key': script_key,
            'script_path': full_script_path,
            'work_dir': work_dir,
            'entry_file': entry_file,
            'type': file_type,
            'attempt': attempt,
        }

        # ── Step 7: Wait and check (5 seconds!) ──
        # 🔥 FIX: Wait 5 seconds instead of 2
        time.sleep(5)

        if process.poll() is None:
            # ✅ STILL RUNNING! Success!
            # Double check after 3 more seconds
            time.sleep(3)

            if process.poll() is None:
                # ✅ Confirmed running!
                success_text = f"""
╔══════════════════════════════════════╗
║  ✅ <b>BOT IS RUNNING!</b>                   ║
╠══════════════════════════════════════╣
║
║  📄 <b>File:</b> <code>{entry_file[:25]}</code>
║  🆔 <b>PID:</b> {process.pid}
║  🔤 <b>Type:</b> {'🐍 Python' if file_type == 'py' else '🟨 Node.js'}
║  ⏱️ <b>Started:</b> {datetime.now().strftime('%H:%M:%S')}
║  📊 <b>Status:</b> 🟢 Running
║
║  📋 Use /logs to view output
║  🛑 Use Stop button to stop
║
╚══════════════════════════════════════╝
"""
                db.update_bot(bot_id, status='running', pid=process.pid,
                              last_started=datetime.now().isoformat(),
                              entry_file=entry_file, file_type=file_type)

                try:
                    bot.edit_message_text(success_text, chat_id,
                                          msg.message_id, parse_mode='HTML')
                except:
                    bot.send_message(chat_id, success_text, parse_mode='HTML')

                logger.info(f"✅ Bot #{bot_id} running (PID: {process.pid})")
                return
            else:
                # Died in the extra 3 seconds
                pass

        # ── Script exited/crashed ──
        log_file.close()
        exit_code = process.returncode

        # Read error output
        error_output = ""
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                error_output = f.read()[-2000:]
        except:
            pass

        logger.warning(f"Bot #{bot_id} exited (code: {exit_code})")
        logger.warning(f"Output: {error_output[:500]}")

        # ── Try auto-install missing module ──
        # Python: ModuleNotFoundError
        match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", error_output)
        if match:
            module_name = match.group(1).split('.')[0]
            logger.info(f"📦 Missing module: {module_name}")
            cleanup_script(script_key)
            if attempt_install_pip(module_name, chat_id):
                time.sleep(1)
                run_bot_script(bot_id, chat_id, attempt + 1)
                return

        # Node.js: Cannot find module
        match = re.search(r"Cannot find module '([^']+)'", error_output)
        if match:
            module_name = match.group(1)
            if not module_name.startswith('.'):
                logger.info(f"📦 Missing npm module: {module_name}")
                cleanup_script(script_key)
                try:
                    subprocess.run(['npm', 'install', module_name],
                                   cwd=work_dir, capture_output=True,
                                   timeout=60)
                    time.sleep(1)
                    run_bot_script(bot_id, chat_id, attempt + 1)
                    return
                except:
                    pass

        # ── Check if wrong entry file ──
        if attempt == 1 and exit_code != 0:
            # Try detecting a different entry file
            alt_entries = ['app.py', 'main.py', 'bot.py', 'run.py',
                           'index.js', 'app.js', 'bot.js']
            for alt in alt_entries:
                alt_path = os.path.join(work_dir, alt)
                if os.path.exists(alt_path) and alt != entry_file:
                    logger.info(f"🔄 Trying alternate entry: {alt}")
                    cleanup_script(script_key)
                    db.update_bot(bot_id, entry_file=alt,
                                  file_type='js' if alt.endswith('.js') else 'py')
                    run_bot_script(bot_id, chat_id, attempt + 1)
                    return

        # ── Show error ──
        error_text = f"""
╔══════════════════════════════════════╗
║  ❌ <b>BOT CRASHED!</b>                      ║
╠══════════════════════════════════════╣
║  📄 <b>File:</b> <code>{entry_file[:25]}</code>
║  ❗ <b>Exit Code:</b> {exit_code}
║  🔄 <b>Attempt:</b> {attempt}/{MAX_ATTEMPTS}
╠══════════════════════════════════════╣
║  <b>Error Output:</b>
╠══════════════════════════════════════╣
<code>{error_output[-800:] if error_output.strip() else 'No output (script exited silently)'}</code>
╚══════════════════════════════════════╝
"""
        db.update_bot(bot_id, status='crashed',
                      last_crash=datetime.now().isoformat(),
                      error_log=error_output[-500:])

        try:
            bot.edit_message_text(error_text, chat_id,
                                  msg.message_id, parse_mode='HTML')
        except:
            bot.send_message(chat_id, error_text, parse_mode='HTML')

        cleanup_script(script_key)

    except Exception as e:
        logger.error(f"Run error: {e}", exc_info=True)
        bot.send_message(chat_id, f"❌ Error: {str(e)[:200]}")
        cleanup_script(script_key)


# ═══════════════════════════════════════════════════
#  PROCESS MONITOR (Auto-Restart)
# ═══════════════════════════════════════════════════
def process_monitor():
    """Monitor crashed bots and auto-restart if enabled"""
    while True:
        try:
            for skey in list(bot_scripts.keys()):
                info = bot_scripts.get(skey)
                if not info:
                    continue

                proc = info.get('process')
                if proc and proc.poll() is not None:
                    # Bot died
                    uid = info.get('user_id')
                    bid = info.get('bot_id')
                    fname = info.get('file_name')

                    logger.warning(f"💥 Bot crashed: {skey}")

                    if bid:
                        db.update_bot(bid, status='crashed',
                                      last_crash=datetime.now().isoformat())

                    # Check auto-restart eligibility
                    if uid and bid:
                        user = db.get_user(uid)
                        if user and db.is_subscription_active(uid):
                            plan = PLAN_LIMITS.get(user['plan'], PLAN_LIMITS['free'])
                            attempt = info.get('attempt', 1)

                            if plan.get('auto_restart') and attempt < 3:
                                logger.info(f"🔄 Auto-restart: {skey}")
                                cleanup_script(skey)
                                time.sleep(5)

                                # Run in background
                                threading.Thread(
                                    target=run_bot_script,
                                    args=(bid, uid, attempt + 1),
                                    daemon=True
                                ).start()
                                continue

                    cleanup_script(skey)

        except Exception as e:
            logger.error(f"Monitor error: {e}")

        time.sleep(30)


# ═══════════════════════════════════════════════════
#  BACKUP & EXPIRY
# ═══════════════════════════════════════════════════
def auto_backup():
    while True:
        try:
            time.sleep(86400)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            bp = os.path.join(BACKUPS_DIR, f"backup_{ts}.db")
            shutil.copy2(DATABASE_PATH, bp)
            logger.info(f"💾 Backup: {bp}")
            backups = sorted([f for f in os.listdir(BACKUPS_DIR) if f.startswith('backup_')], reverse=True)
            for old in backups[10:]:
                os.remove(os.path.join(BACKUPS_DIR, old))
        except Exception as e:
            logger.error(f"Backup error: {e}")


def expiry_checker():
    while True:
        try:
            time.sleep(3600)
            now = datetime.now().isoformat()
            expired = db.execute(
                "SELECT * FROM users WHERE subscription_end<=? AND is_lifetime=0 AND plan!='free'",
                (now,), fetch=True) or []
            for u in expired:
                uid = u['user_id']
                db.remove_subscription(uid)
                for b in db.get_user_bots(uid):
                    skey = f"{uid}_{b['bot_name']}"
                    if skey in bot_scripts:
                        kill_process_tree(bot_scripts[skey])
                        cleanup_script(skey)
                    db.update_bot(b['bot_id'], status='stopped')
                try:
                    bot.send_message(uid, "⚠️ Subscription expired! Bots stopped.\nRenew to continue.")
                except:
                    pass
        except Exception as e:
            logger.error(f"Expiry error: {e}")


# ═══════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════
def get_main_keyboard(uid):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    is_admin = uid == OWNER_ID or uid in admin_ids
    m.row("🤖 My Bots", "📤 Deploy Bot")
    m.row("💎 Subscription", "💰 Wallet")
    m.row("🎁 Referral", "📊 Statistics")
    m.row("🟢 Running Bots", "⚡ Bot Speed")
    if is_admin:
        m.row("👑 Admin Panel", "📢 Broadcast")
        m.row("🔒 Lock Bot", "💳 Payments")
    m.row("⚙️ Settings", "📞 Contact")
    return m


def get_bot_actions_keyboard(bot_id, status, fname):
    m = types.InlineKeyboardMarkup(row_width=2)
    if status == 'running':
        m.add(types.InlineKeyboardButton("🛑 Stop", callback_data=f"bot_stop:{bot_id}"),
              types.InlineKeyboardButton("🔄 Restart", callback_data=f"bot_restart:{bot_id}"))
        m.add(types.InlineKeyboardButton("📋 Logs", callback_data=f"bot_logs:{bot_id}"),
              types.InlineKeyboardButton("📊 Resources", callback_data=f"bot_resources:{bot_id}"))
    else:
        m.add(types.InlineKeyboardButton("▶️ Start", callback_data=f"bot_start:{bot_id}"),
              types.InlineKeyboardButton("🗑️ Delete", callback_data=f"bot_delete:{bot_id}"))
        m.add(types.InlineKeyboardButton("📥 Download", callback_data=f"bot_download:{bot_id}"),
              types.InlineKeyboardButton("📋 Logs", callback_data=f"bot_logs:{bot_id}"))
        m.add(types.InlineKeyboardButton("🔍 Re-detect Entry",
                                          callback_data=f"bot_redetect:{bot_id}"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="my_bots"))
    return m


def get_plan_keyboard():
    m = types.InlineKeyboardMarkup(row_width=1)
    for k, p in PLAN_LIMITS.items():
        if k == 'free': continue
        m.add(types.InlineKeyboardButton(f"{p['name']} — {p['price_bdt']} BDT/mo",
                                          callback_data=f"select_plan:{k}"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="main_menu_cb"))
    return m


def get_payment_method_keyboard(plan_key):
    m = types.InlineKeyboardMarkup(row_width=2)
    for k, method in PAYMENT_METHODS.items():
        m.add(types.InlineKeyboardButton(f"{method['icon']} {method['name']}",
                                          callback_data=f"pay_method:{plan_key}:{k}"))
    m.add(types.InlineKeyboardButton("💰 Pay from Wallet", callback_data=f"pay_wallet:{plan_key}"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="subscription_cb"))
    return m


def get_admin_keyboard():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👥 Users", callback_data="admin_users"),
          types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
    m.add(types.InlineKeyboardButton("💳 Payments", callback_data="admin_payments"),
          types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
    m.add(types.InlineKeyboardButton("➕ Add Sub", callback_data="admin_add_sub"),
          types.InlineKeyboardButton("➖ Remove Sub", callback_data="admin_remove_sub"))
    m.add(types.InlineKeyboardButton("🚫 Ban", callback_data="admin_ban"),
          types.InlineKeyboardButton("✅ Unban", callback_data="admin_unban"))
    m.add(types.InlineKeyboardButton("🎟 Promo", callback_data="admin_promo"),
          types.InlineKeyboardButton("🖥 System", callback_data="admin_system"))
    m.add(types.InlineKeyboardButton("🛑 Stop All", callback_data="admin_stopall"),
          types.InlineKeyboardButton("💾 Backup", callback_data="admin_backup"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="main_menu_cb"))
    return m


def payment_approval_kb(pid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_pay:{pid}"),
          types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_pay:{pid}"))
    return m


# ═══════════════════════════════════════════════════
#  /START COMMAND
# ═══════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.from_user.id
    uname = message.from_user.username or ''
    fname = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    active_users.add(uid)

    existing = db.get_user(uid)
    if existing and existing['is_banned']:
        bot.reply_to(message, f"🚫 Banned. Reason: {existing.get('ban_reason', 'N/A')}")
        return
    if bot_locked and uid not in admin_ids and uid != OWNER_ID:
        bot.reply_to(message, "🔒 Bot is locked.")
        return

    is_new = existing is None
    referred_by = None
    args = message.text.split()
    if len(args) > 1 and is_new:
        ref = db.execute("SELECT user_id FROM users WHERE referral_code=?",
                          (args[1],), fetchone=True)
        if ref and ref['user_id'] != uid:
            referred_by = ref['user_id']

    ref_code = generate_referral_code(uid)
    if is_new:
        db.create_user(uid, uname, fname, ref_code, referred_by)
        if referred_by:
            db.add_referral(referred_by, uid, REFERRAL_BONUS_DAYS, REFERRAL_COMMISSION_BDT)
            try:
                bot.send_message(referred_by,
                                  f"🎉 <b>New referral!</b> {fname} joined!\n"
                                  f"💰 +{REFERRAL_COMMISSION_BDT} BDT added!", parse_mode='HTML')
            except:
                pass
    else:
        db.update_user(uid, username=uname, full_name=fname,
                       last_active=datetime.now().isoformat())

    user = db.get_user(uid)
    plan = PLAN_LIMITS.get(user['plan'], PLAN_LIMITS['free']) if user else PLAN_LIMITS['free']
    bcount = db.get_user_bot_count(uid)
    maxb = '♾️' if plan['max_bots'] == -1 else str(plan['max_bots'])
    status = '👑 Owner' if uid == OWNER_ID else '⭐ Admin' if uid in admin_ids else plan['name']

    welcome = f"""
╔══════════════════════════════════════╗
║  🚀 <b>EXU HOSTING PRO X</b>                 ║
║  <i>Bangladesh Premium Edition v2.2</i>      ║
╠══════════════════════════════════════╣
║
║  👋 Welcome, <b>{fname}</b>!
║
║  📤 Deploy & Host your bots
║  🚀 Run Python & Node.js
║  🔍 <b>Smart Entry Detection</b> (NEW!)
║  📊 Monitor running bots
║  💳 BD Payment (bKash/Nagad)
║  🎁 Earn with Referrals
║
╠══════════════════════════════════════╣
║  🆔 <code>{uid}</code> | 📦 {status}
║  🤖 Bots: {bcount}/{maxb} | 💰 {user['wallet_balance'] if user else 0} BDT
╚══════════════════════════════════════╝
"""
    send_animated_message(message.chat.id, welcome, "loading", 2)
    bot.send_message(message.chat.id, "⬇️ Choose:", reply_markup=get_main_keyboard(uid))


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, """
╔══════════════════════════════════════╗
║      📚 <b>EXU HOSTING HELP</b>               ║
╠══════════════════════════════════════╣
║ <b>📤 Deploy:</b> Upload ZIP/PY/JS file
║ <b>🔍 Detection:</b> Auto-finds entry file:
║   app.py, main.py, bot.py, run.py,
║   index.js, app.js + package.json,
║   Procfile, requirements.txt
║
║ <b>🤖 Bot Control:</b>
║ Start/Stop/Restart/Logs/Resources
║
║ <b>💎 Plans:</b> Free/Basic/Pro/Lifetime
║ <b>💳 Pay:</b> bKash/Nagad/Rocket/Upay
║ <b>🎁 Refer:</b> Earn BDT + bonus days
║
║ <b>👑 Admin:</b> /admin
║ <b>📞 Support:</b> """ + YOUR_USERNAME + """
╚══════════════════════════════════════╝
""", parse_mode='HTML')


# ═══════════════════════════════════════════════════
#  TEXT HANDLER
# ═══════════════════════════════════════════════════
@bot.message_handler(content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    text = message.text
    active_users.add(uid)

    user = db.get_user(uid)
    if user and user['is_banned']:
        return
    if bot_locked and uid not in admin_ids and uid != OWNER_ID:
        bot.reply_to(message, "🔒 Locked")
        return

    if uid in payment_states:
        handle_payment_text(message)
        return
    if uid in user_states:
        handle_state_text(message)
        return

    # Button routing
    handlers = {
        "🤖 My Bots": show_my_bots,
        "📤 Deploy Bot": handle_deploy_request,
        "💎 Subscription": show_subscription,
        "💰 Wallet": show_wallet,
        "🎁 Referral": show_referral,
        "📊 Statistics": show_stats,
        "🟢 Running Bots": show_running_bots,
        "⚡ Bot Speed": show_speed,
        "👑 Admin Panel": show_admin_panel,
        "📢 Broadcast": handle_broadcast,
        "🔒 Lock Bot": handle_lock,
        "💳 Payments": show_pending_payments,
        "⚙️ Settings": show_settings,
    }

    if text in handlers:
        handlers[text](message)
    elif text == "📞 Contact":
        bot.send_message(uid, f"📞 {YOUR_USERNAME}\n📢 {UPDATE_CHANNEL}")
    else:
        bot.send_message(uid, "❓ Use buttons below ⬇️",
                         reply_markup=get_main_keyboard(uid))


# ═══════════════════════════════════════════════════
#  MY BOTS (FIXED INDENTATION)
# ═══════════════════════════════════════════════════
def show_my_bots(message):
    uid = message.from_user.id
    msg = send_progress_animation(message.chat.id, "Loading bots", 4)
    bots = db.get_user_bots(uid)
    plan = db.get_user_plan(uid)
    maxb = '♾️' if plan['max_bots'] == -1 else str(plan['max_bots'])

    if not bots:
        t = f"📭 No bots yet! Deploy one with 📤\n📦 Slots: 0/{maxb}"
        try:
            bot.edit_message_text(t, message.chat.id, msg.message_id, parse_mode='HTML')
        except:
            bot.send_message(message.chat.id, t, parse_mode='HTML')
        return

    running = sum(1 for b in bots if is_bot_running(uid, b['bot_name']))
    stopped = len(bots) - running
    t = f"🤖 <b>My Bots</b> ({len(bots)}) | 🟢 {running} | 🔴 {stopped}\n📦 Limit: {maxb}\n\n"

    m = types.InlineKeyboardMarkup(row_width=1)
    for b in bots:
        run = is_bot_running(uid, b['bot_name'])
        s = "🟢" if run else "🔴"
        icon = "🐍" if b['file_type'] == 'py' else "🟨"
        t += f"{s} {icon} <code>{b['bot_name'][:20]}</code> (#{b['bot_id']}) — {b['entry_file']}\n"
        m.add(types.InlineKeyboardButton(
            f"{s} {b['bot_name'][:15]} (#{b['bot_id']})",
            callback_data=f"bot_detail:{b['bot_id']}"))

    m.add(types.InlineKeyboardButton("📤 Deploy New", callback_data="deploy_cb"))

    try:
        bot.edit_message_text(t, message.chat.id, msg.message_id, parse_mode='HTML', reply_markup=m)
    except:
        bot.send_message(message.chat.id, t, parse_mode='HTML', reply_markup=m)


# ═══════════════════════════════════════════════════
#  🔥 FIXED DEPLOY (Smart Detection)
# ═══════════════════════════════════════════════════
def handle_deploy_request(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user:
        bot.reply_to(message, "/start first!")
        return

    plan = db.get_user_plan(uid)
    current = db.get_user_bot_count(uid)
    maxb = plan['max_bots']
    if maxb != -1 and current >= maxb:
        bot.reply_to(message, f"⚠️ Limit reached ({current}/{maxb})!\nUpgrade plan.")
        return

    remaining = '♾️' if maxb == -1 else str(maxb - current)
    t = f"""
╔══════════════════════════════════════╗
║      📤 <b>DEPLOY YOUR BOT</b>               ║
╠══════════════════════════════════════╣
║
║  Send your file now!
║
║  <b>Supported:</b>
║  🐍 Python (.py) — app.py, main.py, bot.py
║  🟨 Node.js (.js) — index.js, app.js
║  📦 ZIP (auto-detects entry file!)
║
║  <b>🔍 Smart Detection checks:</b>
║  ✅ app.py / main.py / bot.py / run.py
║  ✅ index.js / app.js / bot.js
║  ✅ package.json (main / scripts.start)
║  ✅ Procfile (worker/web command)
║  ✅ requirements.txt (auto-install)
║  ✅ Content analysis (bot patterns)
║
║  📦 Slots: {remaining} | Max: 100MB
║
╚══════════════════════════════════════╝
"""
    deploy_states[uid] = {'step': 'waiting'}
    bot.send_message(message.chat.id, t, parse_mode='HTML')


@bot.message_handler(content_types=['document'])
def handle_document(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user:
        bot.reply_to(message, "/start first!")
        return

    plan = db.get_user_plan(uid)
    current = db.get_user_bot_count(uid)
    maxb = plan['max_bots']
    if maxb != -1 and current >= maxb:
        bot.reply_to(message, f"❌ Limit! ({current}/{maxb})")
        return

    fname = message.document.file_name
    fsize = message.document.file_size
    ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''

    allowed = ['py', 'js', 'zip', 'json', 'txt', 'env', 'yml', 'yaml', 'cfg', 'ini']
    if ext not in allowed:
        bot.reply_to(message, f"❌ Unsupported: .{ext}")
        return

    upload_header = f"📤 <b>Uploading</b> <code>{fname[:25]}</code> ({format_size(fsize)})\n"
    progress_msg = bot.reply_to(message, upload_header + "⏳ Downloading...", parse_mode='HTML')

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)

        try:
            bot.edit_message_text(upload_header + "📥 Processing...",
                                  message.chat.id, progress_msg.message_id, parse_mode='HTML')
        except:
            pass

        user_folder = get_user_folder(uid)

        if ext == 'zip':
            # ── ZIP UPLOAD WITH SMART DETECTION ──
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                tmp.write(downloaded)
                tmp_path = tmp.name

            try:
                with zipfile.ZipFile(tmp_path, 'r') as z:
                    # Security
                    for n in z.namelist():
                        if n.startswith('/') or '..' in n:
                            bot.edit_message_text(upload_header + "❌ Suspicious paths!",
                                                  message.chat.id, progress_msg.message_id, parse_mode='HTML')
                            os.unlink(tmp_path)
                            return

                    bot_name = fname.replace('.zip', '')
                    extract_dir = os.path.join(user_folder, bot_name)

                    # Clean old if exists
                    if os.path.exists(extract_dir):
                        shutil.rmtree(extract_dir, ignore_errors=True)

                    os.makedirs(extract_dir, exist_ok=True)
                    z.extractall(extract_dir)

                    # Check if ZIP has a single root folder
                    items = os.listdir(extract_dir)
                    if len(items) == 1 and os.path.isdir(os.path.join(extract_dir, items[0])):
                        # Move contents up one level
                        inner = os.path.join(extract_dir, items[0])
                        for item in os.listdir(inner):
                            src = os.path.join(inner, item)
                            dst = os.path.join(extract_dir, item)
                            if os.path.exists(dst):
                                if os.path.isdir(dst):
                                    shutil.rmtree(dst)
                                else:
                                    os.remove(dst)
                            shutil.move(src, dst)
                        os.rmdir(inner)

                os.unlink(tmp_path)

                # ── SMART DETECTION ──
                try:
                    bot.edit_message_text(upload_header + "🔍 Detecting entry file...",
                                          message.chat.id, progress_msg.message_id, parse_mode='HTML')
                except:
                    pass

                entry_file, file_type, report = detector.get_detection_report(extract_dir)

                if not entry_file:
                    # List all files for user
                    all_files = []
                    for root, dirs, files in os.walk(extract_dir):
                        for f in files:
                            if f.endswith(('.py', '.js')):
                                all_files.append(os.path.relpath(os.path.join(root, f), extract_dir))

                    error_text = upload_header + f"""❌ <b>No entry file detected!</b>

<b>Files in ZIP:</b>
"""
                    for f in all_files[:15]:
                        error_text += f"• <code>{f}</code>\n"

                    if not all_files:
                        error_text += "(No .py or .js files found)\n"

                    error_text += "\n<i>Make sure your ZIP contains app.py, main.py, or bot.py</i>"

                    bot.edit_message_text(error_text, message.chat.id,
                                          progress_msg.message_id, parse_mode='HTML')
                    return

                # Add to DB
                bot_id = db.add_bot(uid, bot_name, extract_dir, entry_file,
                                     file_type, '', fsize,
                                     confidence=report.split('\n')[-1] if report else '')

                success_text = f"""
╔══════════════════════════════════════╗
║  ✅ <b>ZIP DEPLOYED!</b>                     ║
╠══════════════════════════════════════╣
║
║  📦 <b>Name:</b> <code>{bot_name[:20]}</code>
║  🆔 <b>Bot ID:</b> #{bot_id}
║
║  <b>🔍 Smart Detection Result:</b>
║  {report}
║
╚══════════════════════════════════════╝
"""
                m = types.InlineKeyboardMarkup(row_width=2)
                m.add(types.InlineKeyboardButton("▶️ Start Now", callback_data=f"bot_start:{bot_id}"),
                      types.InlineKeyboardButton("🤖 My Bots", callback_data="my_bots"))
                m.add(types.InlineKeyboardButton("🔍 Re-detect Entry", callback_data=f"bot_redetect:{bot_id}"))

                try:
                    bot.edit_message_text(success_text, message.chat.id,
                                          progress_msg.message_id, parse_mode='HTML', reply_markup=m)
                except:
                    bot.send_message(message.chat.id, success_text, parse_mode='HTML', reply_markup=m)

            except zipfile.BadZipFile:
                bot.edit_message_text(upload_header + "❌ Invalid ZIP!",
                                      message.chat.id, progress_msg.message_id, parse_mode='HTML')
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        elif ext in ['py', 'js']:
            # ── SINGLE FILE UPLOAD ──
            file_path = os.path.join(user_folder, fname)
            with open(file_path, 'wb') as f:
                f.write(downloaded)

            ftype = ext
            bot_id = db.add_bot(uid, fname, user_folder, fname, ftype, '', fsize, 'exact')

            success = upload_header + f"✅ Uploaded! Bot ID: #{bot_id}"
            m = types.InlineKeyboardMarkup(row_width=2)
            m.add(types.InlineKeyboardButton("▶️ Run Now", callback_data=f"bot_start:{bot_id}"),
                  types.InlineKeyboardButton("🤖 My Bots", callback_data="my_bots"))

            try:
                bot.edit_message_text(success, message.chat.id,
                                      progress_msg.message_id, parse_mode='HTML', reply_markup=m)
            except:
                bot.send_message(message.chat.id, success, parse_mode='HTML', reply_markup=m)

        else:
            # Config files (json, env, etc)
            file_path = os.path.join(user_folder, fname)
            with open(file_path, 'wb') as f:
                f.write(downloaded)
            bot.edit_message_text(upload_header + f"✅ Config file saved!",
                                  message.chat.id, progress_msg.message_id, parse_mode='HTML')

        deploy_states.pop(uid, None)

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        try:
            bot.edit_message_text(upload_header + f"❌ Error: {str(e)[:50]}",
                                  message.chat.id, progress_msg.message_id, parse_mode='HTML')
        except:
            bot.reply_to(message, f"❌ Failed: {str(e)[:100]}")


# ═══════════════════════════════════════════════════
#  SHOW FUNCTIONS
# ═══════════════════════════════════════════════════
def show_subscription(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user: return bot.reply_to(message, "/start first!")
    plan = PLAN_LIMITS.get(user['plan'], PLAN_LIMITS['free'])
    exp = time_remaining(user['subscription_end'])
    maxb = '♾️' if plan['max_bots'] == -1 else str(plan['max_bots'])
    t = f"""💎 <b>Subscription</b>
📦 Plan: {plan['name']}
📅 Expires: {exp}
🤖 Slots: {maxb}
💾 RAM: {plan['ram_mb']}MB
🔄 Auto Restart: {'✅' if plan['auto_restart'] else '❌'}"""
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📋 Upgrade", callback_data="view_plans"))
    bot.send_message(uid, t, parse_mode='HTML', reply_markup=m)


def show_wallet(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user: return
    hist = db.get_wallet_history(uid, 5)
    t = f"💰 <b>Wallet</b>\n💵 Balance: <b>{user['wallet_balance']} BDT</b>\n💰 Earned: {user['referral_earnings']} BDT\n"
    for h in hist:
        icon = "➕" if h['tx_type'] in ('credit', 'referral') else "➖"
        t += f"\n{icon} {h['amount']} BDT — {h['description'][:20]}"
    bot.send_message(uid, t, parse_mode='HTML')


def show_referral(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user: return
    link = f"https://t.me/{BOT_USERNAME}?start={user['referral_code']}"
    icons = {'bronze': '🥉', 'silver': '🥈', 'gold': '🥇'}
    t = f"""🎁 <b>Referral</b>
🔗 <code>{link}</code>
👥 Referrals: {user['referral_count']}
{icons.get(user['referral_level'], '🥉')} Level: {user['referral_level'].title()}
💰 Earned: {user['referral_earnings']} BDT
Rewards: 💰 {REFERRAL_COMMISSION_BDT} BDT + 📅 {REFERRAL_BONUS_DAYS} days per ref"""
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🏆 Leaderboard", callback_data="ref_leaderboard"))
    m.add(types.InlineKeyboardButton("📤 Share", switch_inline_query=f"Join EXU Hosting! {link}"))
    bot.send_message(uid, t, parse_mode='HTML', reply_markup=m)


def show_stats(message):
    msg = send_progress_animation(message.chat.id, "Gathering stats", 4)
    stats = db.get_stats()
    s = get_system_stats()
    running = len([k for k in bot_scripts if is_bot_running_check(k)])
    t = f"""📊 <b>EXU HOSTING STATS</b>
🖥️ CPU: {s['cpu']}% {create_mini_bar(s['cpu'])}
🧠 RAM: {s['memory_used']}% {create_mini_bar(s['memory_used'])}
💾 Disk: {s['disk_percent']}% {create_mini_bar(s['disk_percent'])}
⏱️ Uptime: {s['uptime']}
🤖 Running: {running} | 👥 Users: {stats['total_users']}
💰 Revenue: {stats['total_revenue']} BDT"""
    try: bot.edit_message_text(t, message.chat.id, msg.message_id, parse_mode='HTML')
    except: bot.send_message(message.chat.id, t, parse_mode='HTML')


def show_running_bots(message):
    uid = message.from_user.id
    msg = send_progress_animation(message.chat.id, "Fetching bots", 4)
    running = []
    for sk, info in bot_scripts.items():
        if is_bot_running_check(sk):
            if uid == OWNER_ID or uid in admin_ids or info.get('user_id') == uid:
                up = str(datetime.now() - info.get('start_time', datetime.now())).split('.')[0]
                running.append(f"📄 <code>{info.get('file_name', '?')[:20]}</code> | PID: {info['process'].pid} | ⏱️ {up}")

    t = f"🟢 <b>Running Bots ({len(running)})</b>\n\n" + "\n".join(running) if running else "🔴 No bots running."
    try: bot.edit_message_text(t, message.chat.id, msg.message_id, parse_mode='HTML')
    except: bot.send_message(message.chat.id, t, parse_mode='HTML')


def show_speed(message):
    msg = send_progress_animation(message.chat.id, "Testing", 4)
    start = time.time()
    lat = (time.time() - start) * 1000
    t = f"⚡ Latency: {lat:.2f}ms\n🖥️ CPU: {psutil.cpu_percent()}%\n🧠 RAM: {psutil.virtual_memory().percent}%\n⏱️ {get_uptime()}"
    try: bot.edit_message_text(t, message.chat.id, msg.message_id, parse_mode='HTML')
    except: pass


def show_settings(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user: return
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="set_lang:en"),
          types.InlineKeyboardButton("🇧🇩 বাংলা", callback_data="set_lang:bn"))
    bot.send_message(uid, f"⚙️ <b>Settings</b>\n👤 {user['full_name']}\n🆔 <code>{uid}</code>",
                     parse_mode='HTML', reply_markup=m)


def show_admin_panel(message):
    uid = message.from_user.id
    if uid != OWNER_ID and uid not in admin_ids:
        return bot.reply_to(message, "❌ Admin only!")
    stats = db.get_stats()
    running = len([k for k in bot_scripts if is_bot_running_check(k)])
    t = f"👑 <b>Admin Panel</b>\n👥 {stats['total_users']} users | 🤖 {running} running | 💳 {stats['pending_payments']} pending | 💰 {stats['total_revenue']} BDT"
    bot.send_message(uid, t, parse_mode='HTML', reply_markup=get_admin_keyboard())


def handle_broadcast(message):
    uid = message.from_user.id
    if uid != OWNER_ID and uid not in admin_ids:
        return
    user_states[uid] = {'action': 'broadcast'}
    bot.reply_to(message, "📢 Send broadcast message:")


def handle_lock(message):
    global bot_locked
    uid = message.from_user.id
    if uid != OWNER_ID and uid not in admin_ids:
        return
    bot_locked = not bot_locked
    bot.reply_to(message, f"{'🔒 LOCKED' if bot_locked else '🔓 UNLOCKED'}")


def show_pending_payments(message):
    uid = message.from_user.id
    if uid != OWNER_ID and uid not in admin_ids:
        return
    payments = db.get_pending_payments()
    if not payments:
        return bot.send_message(uid, "💳 No pending payments!")
    t = f"💳 <b>Pending ({len(payments)})</b>\n\n"
    m = types.InlineKeyboardMarkup(row_width=2)
    for p in payments[:10]:
        u = db.get_user(p['user_id'])
        name = u['full_name'] if u else str(p['user_id'])
        t += f"#{p['payment_id']} — {name}\n💰 {p['amount']} BDT | {p['method']} | {p['plan']}\nTRX: {p['transaction_id']}\n\n"
        m.add(types.InlineKeyboardButton(f"✅ #{p['payment_id']}", callback_data=f"approve_pay:{p['payment_id']}"),
              types.InlineKeyboardButton(f"❌ #{p['payment_id']}", callback_data=f"reject_pay:{p['payment_id']}"))
    bot.send_message(uid, t, parse_mode='HTML', reply_markup=m)


# ═══════════════════════════════════════════════════
#  STATE TEXT HANDLERS
# ═══════════════════════════════════════════════════
def handle_state_text(message):
    uid = message.from_user.id
    state = user_states.get(uid)
    if not state: return
    action = state.get('action')

    if action == 'broadcast':
        text = message.text
        users = db.get_all_users()
        sent = failed = 0
        for u in users:
            try:
                bot.send_message(u['user_id'], f"📢 <b>Broadcast</b>\n\n{text}", parse_mode='HTML')
                sent += 1
            except:
                failed += 1
        bot.reply_to(message, f"📢 Sent: {sent} | Failed: {failed}")
        user_states.pop(uid, None)

    elif action == 'admin_add_sub':
        if state.get('step', 1) == 1:
            try:
                target = int(message.text.strip())
                user_states[uid] = {'action': 'admin_add_sub', 'step': 2, 'target': target}
                m = types.InlineKeyboardMarkup(row_width=2)
                for k, p in PLAN_LIMITS.items():
                    if k == 'free': continue
                    m.add(types.InlineKeyboardButton(p['name'], callback_data=f"asub_plan:{k}:{target}"))
                bot.reply_to(message, f"User: <code>{target}</code>\nSelect plan:", parse_mode='HTML', reply_markup=m)
            except:
                bot.reply_to(message, "❌ Invalid ID!")
                user_states.pop(uid, None)

    elif action == 'admin_add_sub_days':
        try:
            days = int(message.text.strip())
            target = state['target']
            plan = state['plan']
            db.set_subscription(target, plan if days > 0 else 'lifetime', days)
            db.add_admin_log(uid, 'add_sub', target, f"{plan}/{days}d")
            bot.reply_to(message, f"✅ {plan} → {target} for {'Lifetime' if days == 0 else f'{days}d'}")
            try: bot.send_message(target, f"🎉 Plan upgraded: {PLAN_LIMITS.get(plan, {}).get('name', plan)}!")
            except: pass
        except:
            bot.reply_to(message, "❌ Invalid!")
        user_states.pop(uid, None)

    elif action == 'admin_remove_sub':
        try:
            target = int(message.text.strip())
            db.remove_subscription(target)
            bot.reply_to(message, f"✅ Sub removed: {target}")
        except:
            bot.reply_to(message, "❌ Invalid!")
        user_states.pop(uid, None)

    elif action == 'admin_ban':
        parts = message.text.strip().split(maxsplit=1)
        try:
            target = int(parts[0])
            reason = parts[1] if len(parts) > 1 else "Banned"
            db.ban_user(target, reason)
            for b in db.get_user_bots(target):
                sk = f"{target}_{b['bot_name']}"
                if sk in bot_scripts:
                    kill_process_tree(bot_scripts[sk])
                    cleanup_script(sk)
            bot.reply_to(message, f"🚫 Banned {target}")
            try: bot.send_message(target, f"🚫 Banned: {reason}")
            except: pass
        except:
            bot.reply_to(message, "❌ Format: ID REASON")
        user_states.pop(uid, None)

    elif action == 'admin_unban':
        try:
            target = int(message.text.strip())
            db.unban_user(target)
            bot.reply_to(message, f"✅ Unbanned {target}")
        except:
            bot.reply_to(message, "❌ Invalid!")
        user_states.pop(uid, None)

    elif action == 'admin_promo':
        parts = message.text.strip().split()
        if len(parts) >= 3:
            try:
                db.create_promo(parts[0].upper(), int(parts[1]), 0, int(parts[2]), uid)
                bot.reply_to(message, f"✅ Promo <code>{parts[0].upper()}</code> created!", parse_mode='HTML')
            except:
                bot.reply_to(message, "❌ Format: CODE DISC MAX")
        else:
            bot.reply_to(message, "❌ Format: CODE DISC MAX")
        user_states.pop(uid, None)


def handle_payment_text(message):
    uid = message.from_user.id
    state = payment_states.get(uid)
    if not state or state.get('step') != 'waiting_trx': return

    trx = message.text.strip() if message.text else 'SCREENSHOT'
    if not trx:
        return bot.reply_to(message, "❌ Send TRX ID!")

    pid = db.create_payment(uid, state['amount'], state['method'], trx, state['plan'], 30)
    payment_states.pop(uid, None)

    bot.send_message(uid, f"✅ Payment #{pid} submitted!\n⏳ Waiting approval...")

    user = db.get_user(uid)
    for aid in admin_ids:
        try:
            bot.send_message(aid,
                              f"💳 <b>New Payment!</b>\n👤 {user['full_name']} (<code>{uid}</code>)\n"
                              f"📦 {state['plan']} | 💰 {state['amount']} BDT\n"
                              f"💳 {state['method']} | TRX: <code>{trx}</code>\n#{pid}",
                              parse_mode='HTML', reply_markup=payment_approval_kb(pid))
        except:
            pass


# ═══════════════════════════════════════════════════
#  CALLBACK HANDLER
# ═══════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    data = call.data

    try:
        # ── Main Menu ──
        if data == "main_menu_cb":
            bot.answer_callback_query(call.id)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(uid, "🏠 Main Menu", reply_markup=get_main_keyboard(uid))

        # ── My Bots ──
        elif data == "my_bots":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s, c): s.chat = c.message.chat; s.from_user = c.from_user
            show_my_bots(M(call))

        # ── Bot Detail ──
        elif data.startswith("bot_detail:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd:
                return bot.answer_callback_query(call.id, "Not found!")

            sk = f"{bd['user_id']}_{bd['bot_name']}"
            run = is_bot_running_check(sk)
            ram = cpu = 0
            if run and sk in bot_scripts:
                try:
                    p = psutil.Process(bot_scripts[sk]['process'].pid)
                    ram = round(p.memory_info().rss / (1024 ** 2), 1)
                    cpu = round(p.cpu_percent(interval=0.1), 1)
                except: pass

            icon = "🐍" if bd['file_type'] == 'py' else "🟨"
            t = f"""{icon} <b>{bd['bot_name'][:20]}</b> (#{bid})
📄 Entry: <code>{bd['entry_file']}</code>
🔤 Type: {bd['file_type'].upper()}
📊 {'🟢 Running' if run else '🔴 Stopped'}
💾 RAM: {ram}MB | ⚡ CPU: {cpu}%
🔄 Restarts: {bd['total_restarts']}
{'📍 Confidence: ' + bd.get('detection_confidence', '') if bd.get('detection_confidence') else ''}"""

            m = get_bot_actions_keyboard(bid, 'running' if run else 'stopped', bd['bot_name'])
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: bot.send_message(uid, t, parse_mode='HTML', reply_markup=m)
            bot.answer_callback_query(call.id)

        # ── 🔥 BOT START (FIXED!) ──
        elif data.startswith("bot_start:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd:
                return bot.answer_callback_query(call.id, "Not found!")

            if not db.is_subscription_active(bd['user_id']):
                return bot.answer_callback_query(call.id, "⚠️ Subscription expired!", show_alert=True)

            # Check if already running
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if is_bot_running_check(sk):
                return bot.answer_callback_query(call.id, "⚠️ Already running!")

            bot.answer_callback_query(call.id, "🚀 Starting...")

            # Run in separate thread
            threading.Thread(
                target=run_bot_script,
                args=(bid, call.message.chat.id),
                daemon=True
            ).start()

        # ── Bot Stop ──
        elif data.startswith("bot_stop:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd:
                return bot.answer_callback_query(call.id, "Not found!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if sk in bot_scripts:
                kill_process_tree(bot_scripts[sk])
                cleanup_script(sk)
                db.update_bot(bid, status='stopped', last_stopped=datetime.now().isoformat())
                bot.answer_callback_query(call.id, "✅ Stopped!")
            else:
                db.update_bot(bid, status='stopped')
                bot.answer_callback_query(call.id, "Already stopped!")
            call.data = f"bot_detail:{bid}"
            handle_callback(call)

        # ── Bot Restart ──
        elif data.startswith("bot_restart:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd:
                return bot.answer_callback_query(call.id, "Not found!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if sk in bot_scripts:
                kill_process_tree(bot_scripts[sk])
                cleanup_script(sk)
            time.sleep(2)
            bot.answer_callback_query(call.id, "🔄 Restarting...")
            threading.Thread(target=run_bot_script, args=(bid, call.message.chat.id), daemon=True).start()

        # ── Bot Logs ──
        elif data.startswith("bot_logs:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd:
                return bot.answer_callback_query(call.id, "Not found!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            lp = os.path.join(LOGS_DIR, f"{sk}.log")
            logs = "No logs yet."
            if os.path.exists(lp):
                with open(lp, 'r', encoding='utf-8', errors='ignore') as f:
                    logs = f.read()[-2000:] or "Empty log."

            t = f"📋 <b>Logs — #{bid}</b>\n<code>{logs[-1500:]}</code>"
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔄 Refresh", callback_data=f"bot_logs:{bid}"),
                  types.InlineKeyboardButton("🔙 Back", callback_data=f"bot_detail:{bid}"))
            try: bot.edit_message_text(t[:4000], call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)

        # ── Bot Resources ──
        elif data.startswith("bot_resources:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd: return
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            ram = cpu = 0
            if sk in bot_scripts:
                try:
                    p = psutil.Process(bot_scripts[sk]['process'].pid)
                    ram = round(p.memory_info().rss / (1024**2), 1)
                    cpu = round(p.cpu_percent(interval=0.5), 1)
                except: pass
            t = f"📊 <b>Resources #{bid}</b>\n💾 RAM: {ram}MB\n⚡ CPU: {cpu}%"
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"bot_detail:{bid}"))
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)

        # ── 🔥 RE-DETECT ENTRY FILE (নতুন!) ──
        elif data.startswith("bot_redetect:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd:
                return bot.answer_callback_query(call.id, "Not found!")

            work_dir = bd['file_path'] if os.path.isdir(bd['file_path']) else get_user_folder(bd['user_id'])

            entry, ftype, report = detector.get_detection_report(work_dir)

            if entry:
                db.update_bot(bid, entry_file=entry, file_type=ftype)
                t = f"""🔍 <b>Re-Detection Result</b>

{report}

✅ Entry file updated!
Press ▶️ Start to run with new entry."""
            else:
                # Show all files so user can see what's inside
                all_files = []
                for root, dirs, files in os.walk(work_dir):
                    for f in files:
                        if f.endswith(('.py', '.js')):
                            all_files.append(os.path.relpath(os.path.join(root, f), work_dir))

                t = "🔍 <b>Re-Detection</b>\n\n❌ No entry file found!\n\n<b>Files in directory:</b>\n"
                for f in all_files[:15]:
                    t += f"• <code>{f}</code>\n"
                if not all_files:
                    t += "(No .py or .js files)\n"

                # Let user manually select
                if all_files:
                    t += "\n<b>Select entry file:</b>"
                    m = types.InlineKeyboardMarkup(row_width=1)
                    for f in all_files[:10]:
                        ftype_btn = 'js' if f.endswith('.js') else 'py'
                        m.add(types.InlineKeyboardButton(
                            f"📄 {f}",
                            callback_data=f"set_entry:{bid}:{f}:{ftype_btn}"
                        ))
                    m.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"bot_detail:{bid}"))

                    try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
                    except: pass
                    bot.answer_callback_query(call.id)
                    return

            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("▶️ Start", callback_data=f"bot_start:{bid}"),
                  types.InlineKeyboardButton("🔙 Back", callback_data=f"bot_detail:{bid}"))
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)

        # ── Manual Entry File Selection ──
        elif data.startswith("set_entry:"):
            parts = data.split(":")
            bid = int(parts[1])
            entry = parts[2]
            ftype = parts[3]
            db.update_bot(bid, entry_file=entry, file_type=ftype)
            bot.answer_callback_query(call.id, f"✅ Entry set to: {entry}")
            call.data = f"bot_detail:{bid}"
            handle_callback(call)

        # ── Bot Delete ──
        elif data.startswith("bot_delete:"):
            bid = int(data.split(":")[1])
            m = types.InlineKeyboardMarkup(row_width=2)
            m.add(types.InlineKeyboardButton("✅ Yes", callback_data=f"confirm_del:{bid}"),
                  types.InlineKeyboardButton("❌ No", callback_data=f"bot_detail:{bid}"))
            try: bot.edit_message_text(f"🗑 Delete #{bid}?\n⚠️ Cannot undo!", call.message.chat.id, call.message.message_id, reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)

        elif data.startswith("confirm_del:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if bd:
                sk = f"{bd['user_id']}_{bd['bot_name']}"
                if sk in bot_scripts:
                    kill_process_tree(bot_scripts[sk])
                    cleanup_script(sk)
                if os.path.exists(bd['file_path']) and os.path.isdir(bd['file_path']):
                    shutil.rmtree(bd['file_path'], ignore_errors=True)
                else:
                    try: os.remove(os.path.join(get_user_folder(bd['user_id']), bd['bot_name']))
                    except: pass
                db.delete_bot(bid)
            bot.answer_callback_query(call.id, "✅ Deleted!")
            call.data = "my_bots"
            handle_callback(call)

        # ── Bot Download ──
        elif data.startswith("bot_download:"):
            bid = int(data.split(":")[1])
            bd = db.get_bot(bid)
            if not bd: return
            fp = os.path.join(bd['file_path'], bd['entry_file']) if os.path.isdir(bd['file_path']) else os.path.join(get_user_folder(bd['user_id']), bd['bot_name'])
            if os.path.exists(fp):
                with open(fp, 'rb') as f:
                    bot.send_document(uid, f, caption=f"📄 {bd['bot_name']}")
            bot.answer_callback_query(call.id, "📥 Sent!")

        # ── Deploy ──
        elif data == "deploy_cb":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s, c): s.chat = c.message.chat; s.from_user = c.from_user
            handle_deploy_request(M(call))

        # ── Plans ──
        elif data in ("view_plans", "subscription_cb"):
            t = "📋 <b>Plans:</b>\n\n"
            for k, p in PLAN_LIMITS.items():
                if k == 'free': continue
                t += f"{p['name']}\n🤖 {p['max_bots']} bots | 💾 {p['ram_mb']}MB | 💰 {p['price_bdt']} BDT\n\n"
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_plan_keyboard())
            except: bot.send_message(uid, t, parse_mode='HTML', reply_markup=get_plan_keyboard())
            bot.answer_callback_query(call.id)

        elif data.startswith("select_plan:"):
            pk = data.split(":")[1]
            p = PLAN_LIMITS.get(pk)
            if not p: return
            t = f"{p['name']}\n🤖 {'♾️' if p['max_bots']==-1 else p['max_bots']} | 💾 {p['ram_mb']}MB | 🔄 {'✅' if p['auto_restart'] else '❌'}\n💰 {p['price_bdt']} BDT/mo\n\nSelect payment:"
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_payment_method_keyboard(pk))
            except: pass
            bot.answer_callback_query(call.id)

        elif data.startswith("pay_method:"):
            parts = data.split(":")
            pk, mk = parts[1], parts[2]
            p = PLAN_LIMITS.get(pk)
            m = PAYMENT_METHODS.get(mk)
            if not p or not m: return
            t = f"💳 <b>{m['name']}</b>\n📱 <code>{m['number']}</code>\n💰 <b>{p['price_bdt']} BDT</b>\n📦 {p['name']}\n\nSend Transaction ID:"
            payment_states[uid] = {'step': 'waiting_trx', 'plan': pk, 'method': mk, 'amount': p['price_bdt']}
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except: bot.send_message(uid, t, parse_mode='HTML')
            bot.answer_callback_query(call.id)

        elif data.startswith("pay_wallet:"):
            pk = data.split(":")[1]
            user = db.get_user(uid)
            p = PLAN_LIMITS.get(pk)
            if not user or not p: return
            if user['wallet_balance'] < p['price_bdt']:
                return bot.answer_callback_query(call.id, "❌ Low balance!", show_alert=True)
            db.add_wallet_tx(uid, p['price_bdt'], 'purchase', f"Plan: {pk}")
            db.set_subscription(uid, pk if pk != 'lifetime' else 'lifetime', 30)
            bot.answer_callback_query(call.id, "✅ Paid!")
            try: bot.edit_message_text(f"✅ <b>Upgraded to {p['name']}!</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except: pass

        # ── Payment Approve/Reject ──
        elif data.startswith("approve_pay:"):
            if uid not in admin_ids and uid != OWNER_ID: return
            pid = int(data.split(":")[1])
            p = db.approve_payment(pid, uid)
            if p:
                bot.answer_callback_query(call.id, "✅ Approved!")
                try: bot.edit_message_text(call.message.text + "\n\n✅ APPROVED", call.message.chat.id, call.message.message_id, parse_mode='HTML')
                except: pass
                try: bot.send_message(p['user_id'], f"🎉 Payment approved! Plan activated!")
                except: pass

        elif data.startswith("reject_pay:"):
            if uid not in admin_ids and uid != OWNER_ID: return
            pid = int(data.split(":")[1])
            db.reject_payment(pid, uid)
            bot.answer_callback_query(call.id, "❌ Rejected!")
            try: bot.edit_message_text(call.message.text + "\n\n❌ REJECTED", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except: pass

        # ── Referral ──
        elif data == "ref_leaderboard":
            leaders = db.get_referral_leaderboard(10)
            t = "🏆 <b>Leaderboard</b>\n\n"
            medals = ['🥇', '🥈', '🥉']
            for i, l in enumerate(leaders):
                m_ = medals[i] if i < 3 else f"#{i+1}"
                t += f"{m_} {l['full_name'] or l['username'] or '?'} — {l['referral_count']} refs\n"
            if not leaders: t += "No referrals yet!"
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Back", callback_data="main_menu_cb"))
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)

        # ── Language ──
        elif data.startswith("set_lang:"):
            lang = data.split(":")[1]
            db.update_user(uid, language=lang)
            bot.answer_callback_query(call.id, "✅ Changed!" if lang == 'en' else "✅ পরিবর্তন হয়েছে!")

        # ═══ ADMIN CALLBACKS ═══
        elif data == "admin_users":
            if uid not in admin_ids and uid != OWNER_ID: return
            users = db.get_all_users()
            t = f"👥 <b>Users ({len(users)})</b>\n\n"
            for u in users[:20]:
                t += f"{'🚫' if u['is_banned'] else '✅'} <code>{u['user_id']}</code> — {u['full_name'] or 'N/A'} [{u['plan']}]\n"
            bot.send_message(uid, t[:4000], parse_mode='HTML')
            bot.answer_callback_query(call.id)

        elif data == "admin_stats":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s, c): s.chat = c.message.chat; s.from_user = c.from_user
            show_stats(M(call))

        elif data == "admin_payments":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s, c): s.chat = c.message.chat; s.from_user = c.from_user
            show_pending_payments(M(call))

        elif data == "admin_broadcast":
            user_states[uid] = {'action': 'broadcast'}
            bot.answer_callback_query(call.id)
            bot.send_message(uid, "📢 Send broadcast:")

        elif data == "admin_add_sub":
            user_states[uid] = {'action': 'admin_add_sub', 'step': 1}
            bot.answer_callback_query(call.id)
            bot.send_message(uid, "➕ Send user ID:")

        elif data.startswith("asub_plan:"):
            parts = data.split(":")
            user_states[uid] = {'action': 'admin_add_sub_days', 'target': int(parts[2]), 'plan': parts[1]}
            bot.answer_callback_query(call.id)
            bot.send_message(uid, f"Plan: {PLAN_LIMITS[parts[1]]['name']}\nSend days (0=lifetime):")

        elif data == "admin_remove_sub":
            user_states[uid] = {'action': 'admin_remove_sub'}
            bot.answer_callback_query(call.id)
            bot.send_message(uid, "➖ Send user ID:")

        elif data == "admin_ban":
            user_states[uid] = {'action': 'admin_ban'}
            bot.answer_callback_query(call.id)
            bot.send_message(uid, "🚫 Send: USER_ID REASON")

        elif data == "admin_unban":
            user_states[uid] = {'action': 'admin_unban'}
            bot.answer_callback_query(call.id)
            bot.send_message(uid, "✅ Send user ID:")

        elif data == "admin_promo":
            user_states[uid] = {'action': 'admin_promo'}
            bot.answer_callback_query(call.id)
            bot.send_message(uid, "🎟 Send: CODE DISCOUNT MAX_USES")

        elif data == "admin_system":
            s = get_system_stats()
            t = f"🖥 CPU: {s['cpu']}% | 💾 RAM: {s['memory_used']}% | 💿 Disk: {s['disk_percent']}% | ⏱️ {s['uptime']}"
            bot.answer_callback_query(call.id)
            bot.send_message(uid, t)

        elif data == "admin_stopall":
            if uid not in admin_ids and uid != OWNER_ID: return
            stopped = 0
            for sk in list(bot_scripts.keys()):
                try:
                    kill_process_tree(bot_scripts[sk])
                    cleanup_script(sk)
                    stopped += 1
                except: pass
            bot.answer_callback_query(call.id, f"🛑 Stopped {stopped}")

        elif data == "admin_backup":
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy2(DATABASE_PATH, os.path.join(BACKUPS_DIR, f"backup_{ts}.db"))
            bot.answer_callback_query(call.id, "💾 Backup created!")

    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        bot.answer_callback_query(call.id, f"❌ {str(e)[:50]}")


# ═══════════════════════════════════════════════════
#  ADMIN COMMANDS
# ═══════════════════════════════════════════════════
@bot.message_handler(commands=['admin', 'adminpanel'])
def cmd_admin(m): show_admin_panel(m)

@bot.message_handler(commands=['subscribe', 'sub'])
def cmd_sub(m):
    uid = m.from_user.id
    if uid != OWNER_ID and uid not in admin_ids: return
    p = m.text.split()
    if len(p) < 3: return bot.reply_to(m, "/subscribe UID DAYS")
    try:
        db.set_subscription(int(p[1]), 'pro' if int(p[2]) > 0 else 'lifetime', int(p[2]))
        bot.reply_to(m, f"✅ Done")
    except: bot.reply_to(m, "❌ Error")

@bot.message_handler(commands=['ban'])
def cmd_ban(m):
    uid = m.from_user.id
    if uid != OWNER_ID and uid not in admin_ids: return
    p = m.text.split(maxsplit=2)
    if len(p) < 2: return
    try: db.ban_user(int(p[1]), p[2] if len(p) > 2 else "Banned"); bot.reply_to(m, "🚫 Done")
    except: pass

@bot.message_handler(commands=['unban'])
def cmd_unban(m):
    uid = m.from_user.id
    if uid != OWNER_ID and uid not in admin_ids: return
    p = m.text.split()
    if len(p) < 2: return
    try: db.unban_user(int(p[1])); bot.reply_to(m, "✅ Done")
    except: pass


# ═══════════════════════════════════════════════════
#  CLEANUP
# ═══════════════════════════════════════════════════
def cleanup_on_exit():
    logger.info("🛑 Shutting down...")
    for sk in list(bot_scripts.keys()):
        try: kill_process_tree(bot_scripts[sk])
        except: pass
    logger.info("✅ Done")

atexit.register(cleanup_on_exit)


# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════
def main():
    logger.info("═" * 50)
    logger.info("🚀 EXU HOSTING PRO X v2.2 — Starting...")
    logger.info(f"👑 Owner: {OWNER_ID} | Admins: {admin_ids}")
    logger.info(f"📁 Base: {BASE_DIR}")
    logger.info(f"🔍 Smart Entry Detection: ENABLED")
    logger.info("═" * 50)

    # Background threads
    threading.Thread(target=process_monitor, daemon=True).start()
    logger.info("⚙️ Process monitor started")
    threading.Thread(target=auto_backup, daemon=True).start()
    logger.info("💾 Auto-backup started")
    threading.Thread(target=expiry_checker, daemon=True).start()
    logger.info("⏰ Expiry checker started")

    keep_alive()

    for aid in admin_ids:
        try:
            bot.send_message(aid,
                              "🚀 <b>EXU HOSTING PRO X v2.2 Started!</b>\n"
                              "✅ All systems operational\n"
                              "🔍 Smart Entry Detection: ON\n"
                              "📊 /admin to manage", parse_mode='HTML')
        except: pass

    while True:
        try:
            logger.info("🟢 Polling started...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error! Retry 10s...")
            time.sleep(10)
        except requests.exceptions.ReadTimeout:
            logger.error("Timeout! Retry 5s...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            time.sleep(5)


if __name__ == "__main__":
    main()