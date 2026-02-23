"""
╔══════════════════════════════════════════════════════════════╗
║  🌟 APON HOSTING PANEL v6.0 — Ultimate Edition 🌟           ║
║  Developer: @developer_apon                                  ║
║  Complete rewrite — Zero bugs, Maximum features              ║
║  Advanced animations, Unlimited admin, Auto-restart          ║
╚══════════════════════════════════════════════════════════════╝
"""

import telebot, subprocess, os, zipfile, tempfile, shutil, time, psutil
import sqlite3, json, logging, signal, threading, re, sys, atexit
import requests, random, hashlib, string, traceback
from telebot import types
from datetime import datetime, timedelta
from flask import Flask, jsonify
from threading import Thread
from collections import defaultdict
from functools import wraps

# ═══════════════════════════════════════════════════
#  FLASK KEEP-ALIVE
# ═══════════════════════════════════════════════════
flask_app = Flask('AponHosting')

@flask_app.route('/')
def flask_home():
    rn = len([k for k in bot_scripts if is_running(k)])
    return f"""<html><head><title>APON HOSTING PANEL v6.0</title>
    <style>body{{background:#0a0a1a;color:#0f0;font-family:monospace;text-align:center;padding:50px}}
    h1{{color:#0ff;font-size:2em}}p{{font-size:1.2em}}.box{{background:#111;border:1px solid #0f0;
    padding:20px;margin:10px auto;max-width:400px;border-radius:10px}}</style></head>
    <body><h1>🌟 APON HOSTING PANEL v6.0</h1>
    <div class="box"><p>✅ Status: Online</p><p>⏱ Uptime: {get_uptime()}</p>
    <p>🤖 Running: {rn} bots</p><p>📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}</p></div>
    </body></html>"""

@flask_app.route('/health')
def flask_health():
    return jsonify({"status":"ok","uptime":get_uptime(),"v":"6.0",
                    "bots":len([k for k in bot_scripts if is_running(k)])})

def keep_alive():
    Thread(target=lambda: flask_app.run(host='0.0.0.0',
           port=int(os.environ.get("PORT",8080)), use_reloader=False), daemon=True).start()

# ═══════════════════════════════════════════════════
#  BRANDING & CONFIG
# ═══════════════════════════════════════════════════
BRAND = "🌟 APON HOSTING PANEL"
VER = "v6.0"
TAG = f"{BRAND} {VER}"

TOKEN = os.environ.get('BOT_TOKEN', '8258702948:AAHCT3iI934w6MnLle72GPUxQTR2O3z6aWA')
OWNER_ID = int(os.environ.get('OWNER_ID', 6678577936))
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'apon_vps_bot')
DEV_USERNAME = '@developer_apon'
UPDATE_CHANNEL = 'https://t.me/developer_apon_07'
DEFAULT_CHANNELS = {'developer_apon_07': 'Developer Apon Updates'}

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'upload_bots')
DATA_DIR = os.path.join(BASE_DIR, 'apon_data')
DB_PATH = os.path.join(DATA_DIR, 'apon.db')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

PLANS = {
    'free':      {'name':'🆓 Free',      'bots':1,  'ram':128,  'restart':False,'price':0},
    'starter':   {'name':'🟢 Starter',   'bots':2,  'ram':256,  'restart':True, 'price':99},
    'basic':     {'name':'⭐ Basic',      'bots':5,  'ram':512,  'restart':True, 'price':199},
    'pro':       {'name':'💎 Pro',        'bots':15, 'ram':2048, 'restart':True, 'price':499},
    'enterprise':{'name':'🏢 Enterprise', 'bots':50, 'ram':4096, 'restart':True, 'price':999},
    'lifetime':  {'name':'👑 Lifetime',   'bots':-1, 'ram':8192, 'restart':True, 'price':1999},
}

PAYMENTS = {
    'bkash':  {'name':'bKash',      'num':'01306633616',          'type':'Send Money',     'icon':'🟪'},
    'nagad':  {'name':'Nagad',      'num':'01306633616',          'type':'Send Money',     'icon':'🟧'},
    'rocket': {'name':'Rocket',     'num':'01306633616',          'type':'Send Money',     'icon':'🟦'},
    'upay':   {'name':'Upay',       'num':'01306633616',          'type':'Send Money',     'icon':'🟩'},
    'binance':{'name':'Binance Pay','num':'Binance ID: 758637628','type':'Binance/USDT',  'icon':'🟡'},
    'bank':   {'name':'Bank',       'num':'Contact Admin',        'type':'Transfer',       'icon':'🏦'},
}

MODULES_MAP = {
    'telebot':'pytelegrambotapi','telegram':'python-telegram-bot','pyrogram':'pyrogram',
    'telethon':'telethon','aiogram':'aiogram','PIL':'Pillow','cv2':'opencv-python',
    'sklearn':'scikit-learn','bs4':'beautifulsoup4','dotenv':'python-dotenv',
    'yaml':'pyyaml','aiohttp':'aiohttp','numpy':'numpy','pandas':'pandas',
    'requests':'requests','flask':'flask','fastapi':'fastapi','motor':'motor',
    'pymongo':'pymongo','httpx':'httpx','cryptography':'cryptography',
}

REF_BONUS_DAYS = 3
REF_COMMISSION = 20

for d in [UPLOAD_DIR, DATA_DIR, LOGS_DIR, BACKUP_DIR]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
    handlers=[logging.FileHandler(os.path.join(LOGS_DIR,'apon.log'),encoding='utf-8'),
              logging.StreamHandler()])
logger = logging.getLogger('APON')

bot = telebot.TeleBot(TOKEN, parse_mode='HTML', threaded=True, num_threads=4)

# Global variables
bot_scripts = {}
active_users = set()
admin_ids = {OWNER_ID}
bot_locked = False
bot_start_time = datetime.now()
user_msg_times = defaultdict(list)

# ═══════════════════════════════════════════════════
#  STATE MANAGER (Bug-free)
# ═══════════════════════════════════════════════════
class StateManager:
    def __init__(self):
        self._states = {}
        self._payments = {}
        self._lock = threading.Lock()

    def set(self, uid, action, **kw):
        with self._lock:
            self._states[uid] = {'action':action, 'ts':time.time(), **kw}

    def get(self, uid):
        with self._lock:
            s = self._states.get(uid)
            if s and time.time() - s.get('ts',0) > 300:
                del self._states[uid]
                return None
            return s

    def clear(self, uid):
        with self._lock:
            self._states.pop(uid, None)

    def has(self, uid):
        return self.get(uid) is not None

    def set_pay(self, uid, **kw):
        with self._lock:
            self._payments[uid] = {'ts':time.time(), **kw}

    def get_pay(self, uid):
        with self._lock:
            s = self._payments.get(uid)
            if s and time.time() - s.get('ts',0) > 600:
                del self._payments[uid]
                return None
            return s

    def clear_pay(self, uid):
        with self._lock:
            self._payments.pop(uid, None)

    def has_pay(self, uid):
        return self.get_pay(uid) is not None

    def clear_all(self, uid):
        with self._lock:
            self._states.pop(uid, None)
            self._payments.pop(uid, None)

    def cleanup(self):
        with self._lock:
            now = time.time()
            for uid in [u for u,s in self._states.items() if now-s.get('ts',0)>300]:
                del self._states[uid]
            for uid in [u for u,s in self._payments.items() if now-s.get('ts',0)>600]:
                del self._payments[uid]

SM = StateManager()

# ═══════════════════════════════════════════════════
#  SAFE MESSAGING
# ═══════════════════════════════════════════════════
def safe_send(cid, text, **kw):
    try:
        if not text: return None
        if len(str(text)) > 4000: text = str(text)[:4000] + "\n..."
        kw.setdefault('parse_mode','HTML')
        return bot.send_message(cid, text, **kw)
    except telebot.apihelper.ApiTelegramException as e:
        if 'can\'t parse' in str(e).lower():
            try:
                kw.pop('parse_mode',None)
                return bot.send_message(cid, text, **kw)
            except: pass
    except: pass
    return None

def safe_edit(text, cid, mid, **kw):
    try:
        if not text: return None
        if len(str(text)) > 4000: text = str(text)[:4000] + "\n..."
        kw.setdefault('parse_mode','HTML')
        return bot.edit_message_text(text, cid, mid, **kw)
    except telebot.apihelper.ApiTelegramException as e:
        if 'not modified' in str(e).lower(): return None
        if 'can\'t parse' in str(e).lower():
            try:
                kw.pop('parse_mode',None)
                return bot.edit_message_text(text, cid, mid, **kw)
            except: pass
    except: pass
    return None

def safe_answer(cid, text="", **kw):
    try: bot.answer_callback_query(cid, text, **kw)
    except: pass

def safe_delete(cid, mid):
    try: bot.delete_message(cid, mid); return True
    except: return False

# ═══════════════════════════════════════════════════
#  ANIMATIONS (Advanced loading effects)
# ═══════════════════════════════════════════════════
def animate(cid, final_text, style="load", **kw):
    """Advanced animations with progress bar"""
    try:
        frames = {
            "load": ["⏳ Loading.", "⏳ Loading..", "⏳ Loading...", "✅ Done!"],
            "run":  ["🚀 Starting.", "🚀 Starting..", "🚀 Starting...", "🚀 Launching!", "✅ Running!"],
            "stop": ["🛑 Stopping.", "🛑 Stopping..", "🛑 Stopping...", "✅ Stopped!"],
            "scan": ["🔍 Scanning.", "🔍 Scanning..", "🔍 Scanning...", "✅ Found!"],
            "install": ["📦 Installing.", "📦 Installing..", "📦 Installing...", "✅ Installed!"],
            "upload": ["📤 Uploading.", "📤 Uploading..", "📤 Uploading...", "✅ Uploaded!"],
            "progress": [
                "▓░░░░░░░░░ 10%", "▓▓▓░░░░░░░ 30%",
                "▓▓▓▓▓░░░░░ 50%", "▓▓▓▓▓▓▓░░░ 70%",
                "▓▓▓▓▓▓▓▓▓░ 90%", "▓▓▓▓▓▓▓▓▓▓ 100% ✅"
            ],
        }
        f = frames.get(style, frames["load"])
        msg = bot.send_message(cid, f[0])
        for frame in f[1:]:
            time.sleep(0.4)
            try: safe_edit(frame, cid, msg.message_id)
            except: pass
        time.sleep(0.3)
        safe_edit(final_text, cid, msg.message_id, **kw)
        return msg
    except:
        return safe_send(cid, final_text, **kw)

# ═══════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════
def get_uptime():
    d = datetime.now() - bot_start_time
    h, r = divmod(d.seconds, 3600); m, s = divmod(r, 60)
    p = []
    if d.days: p.append(f"{d.days}d")
    if h: p.append(f"{h}h")
    p.append(f"{m}m {s}s")
    return " ".join(p)

def fmt_size(b):
    for u in ['B','KB','MB','GB','TB']:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} PB"

def gen_ref(uid):
    uid = int(uid); chars = string.digits + string.ascii_uppercase
    enc = ''
    t = uid if uid > 0 else 0
    if t == 0: enc = '0'
    while t > 0: enc = chars[t%36] + enc; t //= 36
    salt = hashlib.md5(f"{uid}_apon".encode()).hexdigest()[:2].upper()
    return f"AHP{enc}{salt}"

def time_left(e):
    if not e: return "♾️ Lifetime"
    try:
        end = datetime.fromisoformat(e)
        if end <= datetime.now(): return "❌ Expired"
        d = end - datetime.now()
        return f"{d.days}d {d.seconds//3600}h" if d.days > 0 else f"{d.seconds//3600}h {(d.seconds%3600)//60}m"
    except: return "?"

def user_dir(uid):
    f = os.path.join(UPLOAD_DIR, str(uid)); os.makedirs(f, exist_ok=True); return f

def is_running(sk):
    i = bot_scripts.get(sk)
    if i and i.get('process'):
        try:
            p = psutil.Process(i['process'].pid)
            return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except: pass
    return False

def bot_running(uid, name): return is_running(f"{uid}_{name}")

def cleanup_bot(sk):
    if sk in bot_scripts:
        i = bot_scripts[sk]
        try:
            lf = i.get('log_file')
            if lf and hasattr(lf,'close') and not lf.closed: lf.close()
        except: pass
        del bot_scripts[sk]

def kill_tree(pi):
    try:
        try:
            lf = pi.get('log_file')
            if lf and hasattr(lf,'close') and not lf.closed: lf.close()
        except: pass
        p = pi.get('process')
        if p and hasattr(p,'pid'):
            try:
                par = psutil.Process(p.pid)
                ch = par.children(recursive=True)
                for c in ch:
                    try: c.terminate()
                    except: pass
                psutil.wait_procs(ch, timeout=3)
                for c in ch:
                    try: c.kill()
                    except: pass
                try: par.terminate(); par.wait(3)
                except psutil.TimeoutExpired: par.kill()
                except psutil.NoSuchProcess: pass
            except psutil.NoSuchProcess: pass
    except: pass

def sys_stats():
    try:
        c = psutil.cpu_percent(interval=0.5); m = psutil.virtual_memory(); d = psutil.disk_usage('/')
        return {'cpu':c,'mem':m.percent,'disk':round(d.used/d.total*100,1),'up':get_uptime(),
                'mem_total':fmt_size(m.total),'mem_used':fmt_size(m.used),
                'disk_total':fmt_size(d.total),'disk_used':fmt_size(d.used)}
    except:
        return {'cpu':0,'mem':0,'disk':0,'up':get_uptime(),'mem_total':'?','mem_used':'?','disk_total':'?','disk_used':'?'}

def bot_res(sk):
    i = bot_scripts.get(sk)
    if not i or not i.get('process'): return 0, 0
    try:
        p = psutil.Process(i['process'].pid)
        return round(p.memory_info().rss/(1024**2),1), round(p.cpu_percent(0.3),1)
    except: return 0, 0

def rate_check(uid):
    now = time.time()
    user_msg_times[uid] = [t for t in user_msg_times[uid] if now-t < 60]
    if len(user_msg_times[uid]) >= 40: return False
    if user_msg_times[uid] and now - user_msg_times[uid][-1] < 0.3: return False
    user_msg_times[uid].append(now)
    return True

# ═══════════════════════════════════════════════════
#  FORCE SUBSCRIBE
# ═══════════════════════════════════════════════════
def check_joined(uid):
    if uid == OWNER_ID or uid in admin_ids: return True, []
    try:
        if not settings.get_bool('force_sub', True): return True, []
    except: pass
    channels = db.get_channels()
    if not channels: channels = [{'channel_username':u,'channel_name':n} for u,n in DEFAULT_CHANNELS.items()]
    nj = []
    for ch in channels:
        try:
            mem = bot.get_chat_member(f"@{ch['channel_username']}", uid)
            if mem.status in ['left','kicked']: nj.append((ch['channel_username'], ch['channel_name']))
        except telebot.apihelper.ApiTelegramException: continue
        except: continue
    return len(nj)==0, nj

def force_sub_msg(cid, nj):
    ch = "".join(f"  {i}. {cn} — @{cu}\n" for i,(cu,cn) in enumerate(nj,1))
    m = types.InlineKeyboardMarkup(row_width=1)
    for cu, cn in nj:
        m.add(types.InlineKeyboardButton(f"📢 Join {cn}", url=f"https://t.me/{cu}"))
    m.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify_join"))
    safe_send(cid, f"🔒 <b>JOIN REQUIRED</b>\n━━━━━━━━━━━━━━━━━━━━\n{ch}\n👇 Join & Verify", reply_markup=m)

# ═══════════════════════════════════════════════════
#  SMART DETECTOR
# ═══════════════════════════════════════════════════
class Detector:
    PY = ['main.py','app.py','bot.py','run.py','start.py','server.py','index.py','__main__.py']
    JS = ['index.js','app.js','bot.js','main.js','server.js','start.js','run.js']

    @staticmethod
    def detect(d):
        if not os.path.isdir(d):
            if os.path.isfile(d): return os.path.basename(d), d.rsplit('.',1)[-1].lower(), 'exact'
            return None, None, None
        top = os.listdir(d)
        for e in Detector.PY:
            if e in top and os.path.isfile(os.path.join(d,e)): return e,'py','high'
        for e in Detector.JS:
            if e in top and os.path.isfile(os.path.join(d,e)): return e,'js','high'
        pj = os.path.join(d,'package.json')
        if os.path.exists(pj):
            try:
                with open(pj) as f: pkg = json.load(f)
                if 'main' in pkg and os.path.exists(os.path.join(d,pkg['main'])):
                    return pkg['main'], pkg['main'].rsplit('.',1)[-1].lower(), 'high'
                if 'scripts' in pkg and 'start' in pkg['scripts']:
                    cmd = pkg['scripts']['start']
                    m = re.search(r'node\s+(\S+\.js)', cmd)
                    if m and os.path.exists(os.path.join(d,m.group(1))): return m.group(1),'js','high'
                    m = re.search(r'python[3]?\s+(\S+\.py)', cmd)
                    if m and os.path.exists(os.path.join(d,m.group(1))): return m.group(1),'py','high'
            except: pass
        pf = os.path.join(d,'Procfile')
        if os.path.exists(pf):
            try:
                with open(pf) as f: c = f.read()
                m = re.search(r'(?:worker|web):\s*python[3]?\s+(\S+\.py)', c)
                if m and os.path.exists(os.path.join(d,m.group(1))): return m.group(1),'py','high'
                m = re.search(r'(?:worker|web):\s*node\s+(\S+\.js)', c)
                if m and os.path.exists(os.path.join(d,m.group(1))): return m.group(1),'js','high'
            except: pass
        for root, dirs, files in os.walk(d):
            if os.path.relpath(root,d).count(os.sep)>1: continue
            for e in Detector.PY:
                if e in files: return os.path.relpath(os.path.join(root,e),d),'py','medium'
            for e in Detector.JS:
                if e in files: return os.path.relpath(os.path.join(root,e),d),'js','medium'
        pyf = [(os.path.relpath(os.path.join(r,f),d),os.path.join(r,f)) for r,_,fs in os.walk(d) for f in fs if f.endswith('.py') and os.path.relpath(r,d).count(os.sep)<=1]
        jsf = [(os.path.relpath(os.path.join(r,f),d),os.path.join(r,f)) for r,_,fs in os.walk(d) for f in fs if f.endswith('.js') and os.path.relpath(r,d).count(os.sep)<=1]
        kw_py = ['infinity_polling','polling()','bot.polling','app.run(','if __name__','TeleBot','Bot(token']
        for rp,fp in pyf:
            try:
                with open(fp,'r',encoding='utf-8',errors='ignore') as f: c=f.read(5000)
                if sum(1 for x in kw_py if x in c)>=2: return rp,'py','medium'
            except: pass
        kw_js = ['require(','app.listen','bot.launch','client.login','express()']
        for rp,fp in jsf:
            try:
                with open(fp,'r',encoding='utf-8',errors='ignore') as f: c=f.read(5000)
                if sum(1 for x in kw_js if x in c)>=2: return rp,'js','medium'
            except: pass
        if pyf: return pyf[0][0],'py','low'
        if jsf: return jsf[0][0],'js','low'
        return None, None, None

    @staticmethod
    def install_deps(d, ft, cid=None):
        if ft == 'py':
            r = os.path.join(d,'requirements.txt')
            if os.path.exists(r):
                if cid: safe_send(cid, "📦 Installing requirements...")
                try: subprocess.run([sys.executable,'-m','pip','install','-r',r,'--quiet'], capture_output=True,text=True,timeout=300,cwd=d)
                except: pass
        elif ft == 'js':
            if os.path.exists(os.path.join(d,'package.json')) and not os.path.exists(os.path.join(d,'node_modules')):
                if cid: safe_send(cid, "📦 npm install...")
                try: subprocess.run(['npm','install','--production'], capture_output=True,text=True,timeout=300,cwd=d)
                except: pass

    @staticmethod
    def report(d):
        e, ft, cf = Detector.detect(d)
        if not e: return None, None, "❌ No runnable file!"
        ci = {'exact':'🎯','high':'✅','medium':'🟡','low':'⚠️'}
        ti = {'py':'🐍 Python','js':'🟨 Node.js'}
        return e, ft, f"📄 Entry: {e}\n🔤 Type: {ti.get(ft,ft)}\n🎯 Confidence: {ci.get(cf,cf)} {cf}"

det = Detector()

# ═══════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════
class DB:
    _lock = threading.Lock()

    def __init__(self):
        self.path = DB_PATH
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=10000")
        return c

    def exe(self, q, p=(), fetch=False, one=False):
        with self._lock:
            c = self._conn()
            try:
                cur = c.cursor(); cur.execute(q, p)
                if fetch: r=[dict(x) for x in cur.fetchall()]; c.close(); return r
                if one: x=cur.fetchone(); c.close(); return dict(x) if x else None
                c.commit(); lid=cur.lastrowid; c.close(); return lid
            except Exception as e:
                c.close(); logger.error(f"DB: {e}"); return None

    def _init(self):
        self.exe("""CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '', full_name TEXT DEFAULT '',
            language TEXT DEFAULT 'en', plan TEXT DEFAULT 'free', subscription_end TEXT,
            is_lifetime INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0, ban_reason TEXT DEFAULT '',
            wallet_balance REAL DEFAULT 0.0, referral_code TEXT UNIQUE, referred_by INTEGER,
            referral_count INTEGER DEFAULT 0, referral_level TEXT DEFAULT 'bronze',
            referral_earnings REAL DEFAULT 0.0, total_spent REAL DEFAULT 0.0,
            created_at TEXT DEFAULT(datetime('now')), last_active TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS bots(
            bot_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            bot_name TEXT NOT NULL, bot_token TEXT DEFAULT '', file_path TEXT NOT NULL,
            entry_file TEXT DEFAULT 'main.py', file_type TEXT DEFAULT 'py',
            status TEXT DEFAULT 'stopped', pid INTEGER, restarts_today INTEGER DEFAULT 0,
            total_restarts INTEGER DEFAULT 0, auto_restart INTEGER DEFAULT 1,
            last_started TEXT, last_stopped TEXT, last_crash TEXT,
            error_log TEXT DEFAULT '', file_size INTEGER DEFAULT 0,
            should_run INTEGER DEFAULT 0, created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS payments(
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            amount REAL NOT NULL, method TEXT NOT NULL, transaction_id TEXT NOT NULL,
            plan TEXT NOT NULL, duration_days INTEGER DEFAULT 30, status TEXT DEFAULT 'pending',
            approved_by INTEGER, created_at TEXT DEFAULT(datetime('now')), processed_at TEXT)""")

        self.exe("""CREATE TABLE IF NOT EXISTS referrals(
            ref_id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL, bonus_days INTEGER DEFAULT 0,
            commission REAL DEFAULT 0, created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS wallet_tx(
            tx_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            amount REAL NOT NULL, tx_type TEXT NOT NULL, description TEXT DEFAULT '',
            created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS admin_logs(
            log_id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER NOT NULL,
            action TEXT NOT NULL, target_user INTEGER, details TEXT DEFAULT '',
            created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS force_channels(
            channel_id INTEGER PRIMARY KEY AUTOINCREMENT, channel_username TEXT UNIQUE NOT NULL,
            channel_name TEXT DEFAULT '', added_by INTEGER, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS tickets(
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            subject TEXT NOT NULL, message TEXT NOT NULL, status TEXT DEFAULT 'open',
            admin_reply TEXT DEFAULT '', created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS notifications(
            notif_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            title TEXT DEFAULT 'Notification', message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0, created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS promo_codes(
            promo_id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
            discount_pct INTEGER DEFAULT 10, max_uses INTEGER DEFAULT 100,
            used_count INTEGER DEFAULT 0, created_by INTEGER, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT(datetime('now')))""")

        self.exe("""CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY, value TEXT NOT NULL,
            updated_at TEXT DEFAULT(datetime('now')))""")

        logger.info("✅ DB ready")

    # ── Users ──
    def get_user(self, uid): return self.exe("SELECT * FROM users WHERE user_id=?", (uid,), one=True)
    def create_user(self, uid, un='', fn='', rc='', rb=None):
        self.exe("INSERT OR IGNORE INTO users(user_id,username,full_name,referral_code,referred_by) VALUES(?,?,?,?,?)", (uid,un,fn,rc,rb))
    def update_user(self, uid, **kw):
        if kw: self.exe(f"UPDATE users SET {','.join(f'{k}=?' for k in kw)} WHERE user_id=?", list(kw.values())+[uid])
    def get_all_users(self): return self.exe("SELECT * FROM users", fetch=True) or []
    def ban(self, uid, r=''): self.update_user(uid, is_banned=1, ban_reason=r)
    def unban(self, uid): self.update_user(uid, is_banned=0, ban_reason='')

    def set_sub(self, uid, plan, days=30):
        if plan == 'lifetime': self.update_user(uid, plan=plan, is_lifetime=1, subscription_end=None)
        else: self.update_user(uid, plan=plan, is_lifetime=0, subscription_end=(datetime.now()+timedelta(days=days)).isoformat())

    def rem_sub(self, uid): self.update_user(uid, plan='free', is_lifetime=0, subscription_end=None)

    def is_active(self, uid):
        u = self.get_user(uid)
        if not u: return False
        if u['is_lifetime'] or u['plan']=='free': return True
        if u['subscription_end']:
            try: return datetime.fromisoformat(u['subscription_end']) > datetime.now()
            except: return False
        return False

    def get_plan(self, uid):
        u = self.get_user(uid)
        if not u: return PLANS['free']
        if uid == OWNER_ID or uid in admin_ids: return PLANS['lifetime']
        return PLANS.get(u['plan'], PLANS['free'])

    # ── Bots ──
    def add_bot(self, uid, name, path, entry='main.py', ft='py', tok='', sz=0):
        return self.exe("INSERT INTO bots(user_id,bot_name,file_path,entry_file,file_type,bot_token,file_size) VALUES(?,?,?,?,?,?,?)", (uid,name,path,entry,ft,tok,sz))
    def get_bots(self, uid): return self.exe("SELECT * FROM bots WHERE user_id=?", (uid,), fetch=True) or []
    def get_bot(self, bid): return self.exe("SELECT * FROM bots WHERE bot_id=?", (bid,), one=True)
    def update_bot(self, bid, **kw):
        if kw: self.exe(f"UPDATE bots SET {','.join(f'{k}=?' for k in kw)} WHERE bot_id=?", list(kw.values())+[bid])
    def del_bot(self, bid): self.exe("DELETE FROM bots WHERE bot_id=?", (bid,))
    def bot_count(self, uid): return (self.exe("SELECT COUNT(*) as c FROM bots WHERE user_id=?", (uid,), one=True) or {}).get('c',0)
    def should_run_bots(self): return self.exe("SELECT * FROM bots WHERE should_run=1", fetch=True) or []

    # ── Payments ──
    def add_pay(self, uid, amt, method, trx, plan, days=30):
        return self.exe("INSERT INTO payments(user_id,amount,method,transaction_id,plan,duration_days) VALUES(?,?,?,?,?,?)", (uid,amt,method,trx,plan,days))
    def pending_pay(self): return self.exe("SELECT * FROM payments WHERE status='pending' ORDER BY created_at DESC", fetch=True) or []
    def get_pay(self, pid): return self.exe("SELECT * FROM payments WHERE payment_id=?", (pid,), one=True)
    def approve_pay(self, pid, aid):
        p = self.get_pay(pid)
        if not p: return None
        self.exe("UPDATE payments SET status='approved',approved_by=?,processed_at=datetime('now') WHERE payment_id=?", (aid,pid))
        self.set_sub(p['user_id'], p['plan'], p['duration_days'])
        return p
    def reject_pay(self, pid, aid):
        self.exe("UPDATE payments SET status='rejected',approved_by=?,processed_at=datetime('now') WHERE payment_id=?", (aid,pid))

    # ── Referrals ──
    def add_ref(self, rr, rd, days=3, comm=20):
        self.exe("INSERT INTO referrals(referrer_id,referred_id,bonus_days,commission) VALUES(?,?,?,?)", (rr,rd,days,comm))
        u = self.get_user(rr)
        if u:
            nc = u['referral_count']+1
            lv = 'diamond' if nc>=100 else 'platinum' if nc>=50 else 'gold' if nc>=25 else 'silver' if nc>=10 else 'bronze'
            self.update_user(rr, referral_count=nc, referral_earnings=u['referral_earnings']+comm, wallet_balance=u['wallet_balance']+comm, referral_level=lv)
    def ref_board(self, lim=10): return self.exe("SELECT * FROM users ORDER BY referral_count DESC LIMIT ?", (lim,), fetch=True) or []
    def user_refs(self, uid): return self.exe("SELECT * FROM referrals WHERE referrer_id=?", (uid,), fetch=True) or []

    # ── Wallet ──
    def wallet_tx(self, uid, amt, tt, desc=''):
        self.exe("INSERT INTO wallet_tx(user_id,amount,tx_type,description) VALUES(?,?,?,?)", (uid,amt,tt,desc))
        if tt in ('credit','referral','refund','bonus'): self.exe("UPDATE users SET wallet_balance=wallet_balance+? WHERE user_id=?", (amt,uid))
        elif tt in ('debit','withdraw','purchase'): self.exe("UPDATE users SET wallet_balance=wallet_balance-? WHERE user_id=?", (amt,uid))
    def wallet_hist(self, uid, lim=20): return self.exe("SELECT * FROM wallet_tx WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid,lim), fetch=True) or []

    # ── Channels ──
    def add_channel(self, username, name='', added_by=None):
        username = username.strip().lstrip('@').lower()
        if not re.match(r'^[a-z][a-z0-9_]{3,}$', username): return None
        ex = self.exe("SELECT * FROM force_channels WHERE channel_username=?", (username,), one=True)
        if ex: self.exe("UPDATE force_channels SET is_active=1,channel_name=? WHERE channel_username=?", (name or username,username)); return ex['channel_id']
        return self.exe("INSERT INTO force_channels(channel_username,channel_name,added_by) VALUES(?,?,?)", (username,name or username,added_by))
    def remove_channel(self, username): self.exe("UPDATE force_channels SET is_active=0 WHERE channel_username=?", (username.strip().lstrip('@').lower(),))
    def get_channels(self): return self.exe("SELECT * FROM force_channels WHERE is_active=1", fetch=True) or []
    def get_all_channels(self): return self.exe("SELECT * FROM force_channels ORDER BY is_active DESC", fetch=True) or []
    def toggle_channel(self, cid):
        ch = self.exe("SELECT * FROM force_channels WHERE channel_id=?", (cid,), one=True)
        if ch: ns = 0 if ch['is_active'] else 1; self.exe("UPDATE force_channels SET is_active=? WHERE channel_id=?", (ns,cid)); return ns
        return None
    def delete_channel(self, cid): self.exe("DELETE FROM force_channels WHERE channel_id=?", (cid,))

    # ── Tickets ──
    def add_ticket(self, uid, subj, msg): return self.exe("INSERT INTO tickets(user_id,subject,message) VALUES(?,?,?)", (uid,subj,msg))
    def open_tickets(self): return self.exe("SELECT * FROM tickets WHERE status='open' ORDER BY created_at DESC", fetch=True) or []
    def reply_ticket(self, tid, reply): self.exe("UPDATE tickets SET admin_reply=?,status='replied' WHERE ticket_id=?", (reply,tid))

    # ── Notifications ──
    def add_notif(self, uid, title, msg): return self.exe("INSERT INTO notifications(user_id,title,message) VALUES(?,?,?)", (uid,title,msg))
    def get_notifs(self, uid, lim=10): return self.exe("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid,lim), fetch=True) or []
    def unread_count(self, uid): r=self.exe("SELECT COUNT(*) as c FROM notifications WHERE user_id=? AND is_read=0", (uid,), one=True); return r['c'] if r else 0
    def mark_read(self, uid): self.exe("UPDATE notifications SET is_read=1 WHERE user_id=?", (uid,))

    # ── Admin ──
    def admin_log(self, aid, act, tgt=None, det=''): self.exe("INSERT INTO admin_logs(admin_id,action,target_user,details) VALUES(?,?,?,?)", (aid,act,tgt,det))

    # ── Stats ──
    def stats(self):
        return {
            'users': (self.exe("SELECT COUNT(*) as c FROM users", one=True) or {}).get('c',0),
            'bots': (self.exe("SELECT COUNT(*) as c FROM bots", one=True) or {}).get('c',0),
            'pending': (self.exe("SELECT COUNT(*) as c FROM payments WHERE status='pending'", one=True) or {}).get('c',0),
            'revenue': (self.exe("SELECT COALESCE(SUM(amount),0) as s FROM payments WHERE status='approved'", one=True) or {}).get('s',0),
            'today': (self.exe("SELECT COUNT(*) as c FROM users WHERE date(created_at)=date('now')", one=True) or {}).get('c',0),
            'active_subs': (self.exe("SELECT COUNT(*) as c FROM users WHERE plan!='free' AND(is_lifetime=1 OR subscription_end>datetime('now'))", one=True) or {}).get('c',0),
            'banned': (self.exe("SELECT COUNT(*) as c FROM users WHERE is_banned=1", one=True) or {}).get('c',0),
        }

db = DB()

# ═══════════════════════════════════════════════════
#  SETTINGS (Persistent)
# ═══════════════════════════════════════════════════
class Settings:
    def __init__(self, db_inst): self.db = db_inst; self._cache = {}
    def get(self, key, default=None):
        if key in self._cache: return self._cache[key]
        row = self.db.exe("SELECT value FROM settings WHERE key=?", (key,), one=True)
        if row: self._cache[key] = row['value']; return row['value']
        return default
    def set(self, key, value):
        self._cache[key] = str(value)
        self.db.exe("INSERT OR REPLACE INTO settings(key,value,updated_at) VALUES(?,?,datetime('now'))", (key,str(value)))
    def get_bool(self, key, default=True):
        val = self.get(key)
        if val is None: return default
        return val.lower() in ('true','1','yes','on')
    def set_bool(self, key, value): self.set(key, 'true' if value else 'false')

settings = Settings(db)
if settings.get('force_sub') is None: settings.set_bool('force_sub', True)
# ═══════════════════════════════════════════════════
#  BOT RUNNER ENGINE
# ═══════════════════════════════════════════════════
def pip_install(mod, cid):
    pkg = MODULES_MAP.get(mod.split('.')[0].lower(), mod)
    try:
        safe_send(cid, f"📦 Installing {pkg}...")
        r = subprocess.run([sys.executable,'-m','pip','install',pkg,'--quiet'], capture_output=True,text=True,timeout=120)
        if r.returncode == 0: safe_send(cid, f"✅ {pkg} installed"); return True
    except: pass
    return False

def run_bot(bid, cid, att=1):
    if att > 3:
        safe_send(cid, "❌ <b>Failed 3 attempts!</b> Check your code.")
        db.update_bot(bid, should_run=0, status='crashed')
        return
    bd = db.get_bot(bid)
    if not bd: safe_send(cid, "❌ Bot not found!"); return
    uid, bn, fp, ef, ft = bd['user_id'], bd['bot_name'], bd['file_path'], bd['entry_file'], bd['file_type']
    sk = f"{uid}_{bn}"
    wd = fp if os.path.isdir(fp) else user_dir(uid)

    if att == 1:
        de, dt, _ = det.report(wd)
        if de: ef, ft = de, dt or 'py'; db.update_bot(bid, entry_file=ef, file_type=ft)

    fsp = os.path.join(wd, ef)
    if not os.path.exists(fsp):
        found = False
        for root, dirs, files in os.walk(wd):
            if os.path.basename(ef) in files:
                fsp = os.path.join(root, os.path.basename(ef))
                ef = os.path.relpath(fsp, wd)
                db.update_bot(bid, entry_file=ef); found = True; break
        if not found:
            af = [os.path.relpath(os.path.join(r,f),wd) for r,_,fs in os.walk(wd) for f in fs if f.endswith(('.py','.js'))]
            safe_send(cid, f"❌ {ef} not found!\n\nFiles:\n" + "\n".join(f"• {f}" for f in af[:10]))
            db.update_bot(bid, should_run=0); return

    if att == 1: det.install_deps(wd, ft, cid)

    ti = '🐍 Python' if ft == 'py' else '🟨 Node.js'
    safe_send(cid, f"🚀 <b>Starting...</b>\n📄 {ef}\n🔤 {ti}\n🔄 Attempt {att}/3")

    try:
        lp = os.path.join(LOGS_DIR, f"{sk}.log")
        lf = open(lp, 'w', encoding='utf-8', errors='ignore')
        cmd = ['node', fsp] if ft == 'js' else [sys.executable, '-u', fsp]
        env = os.environ.copy()
        if bd.get('bot_token'): env['BOT_TOKEN'] = bd['bot_token']
        env['PYTHONUNBUFFERED'] = '1'

        proc = subprocess.Popen(cmd, cwd=wd, stdout=lf, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='ignore', env=env,
            preexec_fn=os.setsid if os.name != 'nt' else None)

        bot_scripts[sk] = {'process':proc,'file_name':bn,'bot_id':bid,'user_id':uid,
            'start_time':datetime.now(),'log_file':lf,'log_path':lp,'entry_file':ef,
            'work_dir':wd,'type':ft,'attempt':att}

        time.sleep(5)
        if proc.poll() is None:
            time.sleep(3)
            if proc.poll() is None:
                db.update_bot(bid, status='running', pid=proc.pid,
                    last_started=datetime.now().isoformat(), entry_file=ef, file_type=ft, should_run=1)
                safe_send(cid,
                    f"✅ <b>BOT RUNNING!</b>\n\n"
                    f"📄 {ef}\n🆔 PID: {proc.pid}\n🔤 {ti}\n"
                    f"⏱ {datetime.now().strftime('%H:%M:%S')}\n📊 🟢 Online")
                return

        lf.close()
        err = ""
        try:
            with open(lp,'r',encoding='utf-8',errors='ignore') as f: err = f.read()[-2000:]
        except: pass

        match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", err)
        if match:
            cleanup_bot(sk)
            if pip_install(match.group(1).split('.')[0], cid):
                time.sleep(1); run_bot(bid, cid, att+1); return

        match = re.search(r"Cannot find module '([^']+)'", err)
        if match and not match.group(1).startswith('.'):
            cleanup_bot(sk)
            try:
                subprocess.run(['npm','install',match.group(1)], cwd=wd, capture_output=True, timeout=60)
                time.sleep(1); run_bot(bid, cid, att+1); return
            except: pass

        if att == 1:
            for alt in ['app.py','main.py','bot.py','run.py','index.js','app.js']:
                if os.path.exists(os.path.join(wd,alt)) and alt != ef:
                    cleanup_bot(sk)
                    db.update_bot(bid, entry_file=alt, file_type='js' if alt.endswith('.js') else 'py')
                    run_bot(bid, cid, att+1); return

        ed = err[-500:] if err.strip() else 'No output'
        safe_send(cid, f"❌ <b>CRASHED!</b>\n📄 {ef}\nExit: {proc.returncode}\n\n<code>{ed}</code>")
        db.update_bot(bid, status='crashed', should_run=0, last_crash=datetime.now().isoformat(), error_log=err[-500:])
        cleanup_bot(sk)
    except Exception as e:
        logger.error(f"Run: {e}", exc_info=True)
        safe_send(cid, f"❌ {str(e)[:200]}")
        cleanup_bot(sk)

# ═══════════════════════════════════════════════════
#  AUTO-RESTART AFTER PANEL RESTART
# ═══════════════════════════════════════════════════
def auto_restart_bots():
    time.sleep(10)
    bots_list = db.should_run_bots()
    if not bots_list: logger.info("✅ No bots to auto-restart"); return
    logger.info(f"🔄 Auto-restarting {len(bots_list)} bots...")
    ok = fail = 0
    for bd in bots_list:
        try:
            if not db.is_active(bd['user_id']): db.update_bot(bd['bot_id'], should_run=0); continue
            wd = bd['file_path'] if os.path.isdir(bd['file_path']) else user_dir(bd['user_id'])
            if not os.path.exists(wd): db.update_bot(bd['bot_id'], should_run=0); continue
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if is_running(sk): continue
            threading.Thread(target=run_bot, args=(bd['bot_id'],bd['user_id'],1), daemon=True).start()
            ok += 1; time.sleep(3)
        except: fail += 1
    logger.info(f"🔄 Done: {ok} restarted, {fail} failed")
    for aid in admin_ids:
        safe_send(aid, f"🔄 <b>Auto-Restart</b>\n✅ {ok} restarted\n❌ {fail} failed")

# ═══════════════════════════════════════════════════
#  BACKGROUND THREADS
# ═══════════════════════════════════════════════════
def thread_monitor():
    while True:
        try:
            for sk in list(bot_scripts.keys()):
                i = bot_scripts.get(sk)
                if not i: continue
                if i.get('process') and i['process'].poll() is not None:
                    bid, uid = i.get('bot_id'), i.get('user_id')
                    if bid: db.update_bot(bid, status='crashed', last_crash=datetime.now().isoformat(),
                        total_restarts=(db.get_bot(bid) or {}).get('total_restarts',0)+1)
                    if uid and bid:
                        u = db.get_user(uid)
                        if u and db.is_active(uid):
                            pl = PLANS.get(u['plan'], PLANS['free'])
                            att = i.get('attempt',1)
                            if pl.get('restart') and att < 3:
                                cleanup_bot(sk); time.sleep(5)
                                threading.Thread(target=run_bot, args=(bid,uid,att+1), daemon=True).start()
                                continue
                            else:
                                db.update_bot(bid, should_run=0)
                                safe_send(uid, f"❌ Bot #{bid} stopped — max retries reached.")
                    cleanup_bot(sk)
            SM.cleanup()
        except Exception as e: logger.error(f"Monitor: {e}")
        time.sleep(30)

def thread_backup():
    while True:
        try:
            time.sleep(86400)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy2(DB_PATH, os.path.join(BACKUP_DIR, f"bk_{ts}.db"))
            bks = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('bk_')], reverse=True)
            for old in bks[10:]: os.remove(os.path.join(BACKUP_DIR, old))
        except: pass

def thread_expiry():
    while True:
        try:
            time.sleep(3600)
            expired = db.exe("SELECT * FROM users WHERE subscription_end<=? AND is_lifetime=0 AND plan!='free'",
                (datetime.now().isoformat(),), fetch=True) or []
            for u in expired:
                uid = u['user_id']; db.rem_sub(uid)
                for b in db.get_bots(uid):
                    sk = f"{uid}_{b['bot_name']}"
                    if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup_bot(sk)
                    db.update_bot(b['bot_id'], status='stopped', should_run=0)
                safe_send(uid, f"⚠️ <b>Subscription Expired!</b>\nBots stopped. Renew to continue.\n\n{TAG}")
        except: pass

def thread_ping():
    while True:
        try:
            time.sleep(300)
            try: requests.get(f"http://localhost:{os.environ.get('PORT',8080)}/health", timeout=5)
            except: pass
        except: pass

# ═══════════════════════════════════════════════════
#  KEYBOARDS (Advanced with more buttons)
# ═══════════════════════════════════════════════════
def main_kb(uid):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.row("🤖 My Bots", "📤 Deploy Bot")
    m.row("💎 Subscription", "💰 Wallet")
    m.row("🎁 Referral", "📊 Statistics")
    m.row("🟢 Running Bots", "⚡ Speed Test")
    m.row("🔔 Notifications", "🎫 Support")
    m.row("📋 My Profile", "🏆 Leaderboard")
    if uid == OWNER_ID or uid in admin_ids:
        m.row("👑 Admin Panel", "📢 Broadcast")
        m.row("🔒 Lock Bot", "💳 Payments")
        m.row("📢 Channels", "🎟 Promo Codes")
    m.row("⚙️ Settings", "📞 Contact")
    return m

def bot_kb(bid, running):
    m = types.InlineKeyboardMarkup(row_width=2)
    if running:
        m.add(types.InlineKeyboardButton("🛑 Stop", callback_data=f"stop:{bid}"),
              types.InlineKeyboardButton("🔄 Restart", callback_data=f"restart:{bid}"))
        m.add(types.InlineKeyboardButton("📋 Logs", callback_data=f"logs:{bid}"),
              types.InlineKeyboardButton("📊 Resources", callback_data=f"res:{bid}"))
        m.add(types.InlineKeyboardButton("📥 Download", callback_data=f"dl:{bid}"))
    else:
        m.add(types.InlineKeyboardButton("▶️ Start", callback_data=f"start:{bid}"),
              types.InlineKeyboardButton("🗑 Delete", callback_data=f"del:{bid}"))
        m.add(types.InlineKeyboardButton("📋 Logs", callback_data=f"logs:{bid}"),
              types.InlineKeyboardButton("📥 Download", callback_data=f"dl:{bid}"))
        m.add(types.InlineKeyboardButton("🔍 Re-detect", callback_data=f"redetect:{bid}"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="mybots"))
    return m

def plan_kb():
    m = types.InlineKeyboardMarkup(row_width=1)
    for k,p in PLANS.items():
        if k == 'free': continue
        m.add(types.InlineKeyboardButton(f"{p['name']} — {p['price']} BDT/mo", callback_data=f"plan:{k}"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu"))
    return m

def pay_kb(pk):
    m = types.InlineKeyboardMarkup(row_width=2)
    for k,v in PAYMENTS.items():
        m.add(types.InlineKeyboardButton(f"{v['icon']} {v['name']}", callback_data=f"pay:{pk}:{k}"))
    m.add(types.InlineKeyboardButton("💰 Wallet Pay", callback_data=f"payw:{pk}"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="sub"))
    return m

def admin_kb():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👥 All Users", callback_data="a:users"),
          types.InlineKeyboardButton("📊 Full Stats", callback_data="a:stats"))
    m.add(types.InlineKeyboardButton("💳 Payments", callback_data="a:pay"),
          types.InlineKeyboardButton("📢 Broadcast", callback_data="a:bc"))
    m.add(types.InlineKeyboardButton("➕ Add Sub", callback_data="a:addsub"),
          types.InlineKeyboardButton("➖ Remove Sub", callback_data="a:remsub"))
    m.add(types.InlineKeyboardButton("🚫 Ban User", callback_data="a:ban"),
          types.InlineKeyboardButton("✅ Unban User", callback_data="a:unban"))
    m.add(types.InlineKeyboardButton("📢 Channels", callback_data="a:channels"),
          types.InlineKeyboardButton("🎟 Promo", callback_data="a:promo"))
    m.add(types.InlineKeyboardButton("🎫 Tickets", callback_data="a:tickets"),
          types.InlineKeyboardButton("🖥 System", callback_data="a:sys"))
    m.add(types.InlineKeyboardButton("🛑 Stop All Bots", callback_data="a:stopall"),
          types.InlineKeyboardButton("🔄 Restart All", callback_data="a:restartall"))
    m.add(types.InlineKeyboardButton("💾 Backup DB", callback_data="a:backup"),
          types.InlineKeyboardButton("👑 Add Admin", callback_data="a:addadmin"))
    m.add(types.InlineKeyboardButton("💰 Give Balance", callback_data="a:give"),
          types.InlineKeyboardButton("🔔 Notify User", callback_data="a:notify"))
    m.add(types.InlineKeyboardButton("👤 User Info", callback_data="a:userinfo"),
          types.InlineKeyboardButton("🛑 Stop Bot #", callback_data="a:stopbot"))
    fsub = settings.get_bool('force_sub', True)
    m.add(types.InlineKeyboardButton(f"{'🟢' if fsub else '🔴'} Force Sub", callback_data="a:fsub"))
    m.add(types.InlineKeyboardButton("🔙 Menu", callback_data="menu"))
    return m

def channels_kb():
    chs = db.get_all_channels()
    m = types.InlineKeyboardMarkup(row_width=1)
    for ch in chs:
        st = "🟢" if ch['is_active'] else "🔴"
        m.add(types.InlineKeyboardButton(f"{st} @{ch['channel_username']}", callback_data=f"chtoggle:{ch['channel_id']}"))
    m.add(types.InlineKeyboardButton("➕ Add Channel", callback_data="chadd"))
    m.add(types.InlineKeyboardButton("🗑 Remove Channel", callback_data="chrem"))
    m.add(types.InlineKeyboardButton("🔙 Admin", callback_data="admin"))
    return m

def approve_kb(pid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"appv:{pid}"),
          types.InlineKeyboardButton("❌ Reject", callback_data=f"rejt:{pid}"))
    return m

# ═══════════════════════════════════════════════════
#  /start COMMAND
# ═══════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid = msg.from_user.id
    un = msg.from_user.username or ''
    fn = f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip()
    active_users.add(uid)
    SM.clear_all(uid)

    joined, nj = check_joined(uid)
    if not joined: return force_sub_msg(msg.chat.id, nj)

    ex = db.get_user(uid)
    if ex and ex['is_banned']: return bot.reply_to(msg, f"🚫 Banned: {ex.get('ban_reason','')}")
    if bot_locked and uid not in admin_ids and uid != OWNER_ID:
        return bot.reply_to(msg, "🔒 Maintenance mode")

    is_new = ex is None
    ref_by = None
    args = msg.text.split()
    if len(args) > 1:
        rr = db.exe("SELECT user_id FROM users WHERE referral_code=?", (args[1].strip(),), one=True)
        if rr and rr['user_id'] != uid and is_new: ref_by = rr['user_id']

    code = gen_ref(uid)
    if is_new:
        db.create_user(uid, un, fn, code, ref_by)
        if ref_by:
            db.add_ref(ref_by, uid, REF_BONUS_DAYS, REF_COMMISSION)
            rd = db.get_user(ref_by)
            safe_send(ref_by, f"🎉 <b>NEW REFERRAL!</b>\n👤 {fn}\n💰 +{REF_COMMISSION} BDT\n👥 Total: {rd['referral_count'] if rd else '?'}")
    else:
        db.update_user(uid, username=un, full_name=fn, last_active=datetime.now().isoformat())
        if not ex.get('referral_code') or len(ex.get('referral_code','')) < 5:
            db.update_user(uid, referral_code=code)

    u = db.get_user(uid)
    pl = PLANS.get(u['plan'], PLANS['free']) if u else PLANS['free']
    bc = db.bot_count(uid)
    mx = '♾️' if pl['bots'] == -1 else str(pl['bots'])
    role = '👑 Owner' if uid == OWNER_ID else '⭐ Admin' if uid in admin_ids else pl['name']
    nc = db.unread_count(uid)

    safe_send(msg.chat.id,
        f"🌟 <b>APON HOSTING PANEL</b> {VER}\n"
        f"<i>Ultimate Bot Hosting Platform</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Welcome, <b>{fn}</b>!\n\n"
        f"📤 Deploy &amp; Host bots instantly\n"
        f"🐍 Python &amp; 🟨 Node.js support\n"
        f"🔍 Smart auto-detection\n"
        f"🔄 Auto-restart on crash\n"
        f"💳 bKash / Nagad / Binance\n"
        f"🎁 Earn with referrals\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <code>{uid}</code>\n"
        f"📦 {role}\n"
        f"🤖 Bots: {bc}/{mx}\n"
        f"💰 {u['wallet_balance'] if u else 0} BDT\n"
        f"👥 {u['referral_count'] if u else 0} referrals\n"
        f"🔑 <code>{u['referral_code'] if u else code}</code>"
        f"{f'{chr(10)}🔔 {nc} unread' if nc > 0 else ''}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━")
    safe_send(msg.chat.id, "⬇️ Choose:", reply_markup=main_kb(uid))

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    safe_send(msg.chat.id,
        f"📚 <b>HELP — {TAG}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📤 Deploy: Send ZIP/.py/.js\n🔍 Auto-detect entry file\n"
        f"🤖 Start/Stop/Restart/Logs\n🔄 Auto-restart on crash\n"
        f"💎 Plans: Free → Lifetime\n💳 bKash/Nagad/Binance\n"
        f"🎁 Earn {REF_COMMISSION} BDT per referral\n🎫 Support tickets\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"/start /help /id /ping /cancel /admin")

@bot.message_handler(commands=['id'])
def cmd_id(msg):
    safe_send(msg.chat.id, f"🆔 <code>{msg.from_user.id}</code>\n👤 {msg.from_user.first_name or ''}\n@{msg.from_user.username or 'N/A'}")

@bot.message_handler(commands=['ping'])
def cmd_ping(msg):
    s = time.time(); m = bot.reply_to(msg, "🏓...")
    safe_edit(f"🏓 <b>Pong!</b>\n⚡ {round((time.time()-s)*1000,2)}ms\n⏱ {get_uptime()}\n🤖 {len([k for k in bot_scripts if is_running(k)])} running",
        msg.chat.id, m.message_id)

@bot.message_handler(commands=['cancel'])
def cmd_cancel(msg):
    uid = msg.from_user.id
    had = SM.has(uid) or SM.has_pay(uid)
    SM.clear_all(uid)
    bot.reply_to(msg, "✅ Cancelled!" if had else "ℹ️ Nothing to cancel.", reply_markup=main_kb(uid))

@bot.message_handler(commands=['admin'])
def cmd_admin(msg):
    uid = msg.from_user.id
    if uid != OWNER_ID and uid not in admin_ids: return bot.reply_to(msg, "❌ Admin only!")
    show_admin_panel(uid)

# ═══════════════════════════════════════════════════
#  SHOW FUNCTIONS (with animations)
# ═══════════════════════════════════════════════════
def show_admin_panel(uid):
    s = db.stats(); rn = len([k for k in bot_scripts if is_running(k)])
    tk = len(db.open_tickets()); fsub = settings.get_bool('force_sub', True)
    safe_send(uid,
        f"👑 <b>ADMIN PANEL</b>\n{TAG}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Users: {s['users']} (+{s['today']})\n🤖 Running: {rn}\n"
        f"💎 Subs: {s['active_subs']}\n🚫 Banned: {s['banned']}\n"
        f"💳 Pending: {s['pending']}\n🎫 Tickets: {tk}\n"
        f"💰 Revenue: {s['revenue']} BDT\n"
        f"Force Sub: {'🟢' if fsub else '🔴'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━", reply_markup=admin_kb())

def show_bots(uid):
    bots_list = db.get_bots(uid); pl = db.get_plan(uid)
    mx = '♾️' if pl['bots'] == -1 else str(pl['bots'])
    if not bots_list:
        safe_send(uid, f"📭 <b>No bots!</b>\n📤 Send a file to deploy\n📦 Slots: 0/{mx}")
        return
    rn = sum(1 for b in bots_list if bot_running(uid, b['bot_name']))
    t = f"🤖 <b>My Bots</b> ({len(bots_list)}) | 🟢 {rn} 🔴 {len(bots_list)-rn}\n📦 Limit: {mx}\n━━━━━━━━━━━━━━━━━━━━\n"
    m = types.InlineKeyboardMarkup(row_width=1)
    for b in bots_list:
        r = bot_running(uid, b['bot_name'])
        ic = "🐍" if b['file_type']=='py' else "🟨"
        si = "🟢" if r else "🔴"
        t += f"{si} {ic} {b['bot_name'][:20]} #{b['bot_id']}\n"
        m.add(types.InlineKeyboardButton(f"{si} {b['bot_name'][:15]} #{b['bot_id']}", callback_data=f"detail:{b['bot_id']}"))
    m.add(types.InlineKeyboardButton("📤 Deploy New", callback_data="deploy"))
    safe_send(uid, t, reply_markup=m)

def show_deploy(uid):
    u = db.get_user(uid)
    if not u: return safe_send(uid, "/start first!")
    pl = db.get_plan(uid); cur = db.bot_count(uid); mx = pl['bots']
    if mx != -1 and cur >= mx: return safe_send(uid, f"⚠️ Limit ({cur}/{mx})! Upgrade.")
    rem = '♾️' if mx == -1 else str(mx-cur)
    safe_send(uid,
        f"📤 <b>DEPLOY BOT</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Send your file now!\n\n🐍 Python (.py)\n🟨 Node.js (.js)\n📦 ZIP (auto-detect)\n\n"
        f"🔍 Smart Detection:\nmain.py / app.py / bot.py\npackage.json / Procfile\n\n📦 Slots: {rem}")

def show_sub(uid):
    u = db.get_user(uid)
    if not u: return
    pl = PLANS.get(u['plan'], PLANS['free'])
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📋 View Plans", callback_data="plans"))
    safe_send(uid,
        f"💎 <b>SUBSCRIPTION</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 {pl['name']}\n📅 {time_left(u['subscription_end'])}\n"
        f"🤖 {'♾️' if pl['bots']==-1 else pl['bots']} bots\n💾 {pl['ram']}MB RAM\n"
        f"🔄 Auto: {'✅' if pl['restart'] else '❌'}\n💰 Spent: {u['total_spent']} BDT", reply_markup=m)

def show_wallet(uid):
    u = db.get_user(uid)
    if not u: return
    h = db.wallet_hist(uid, 5)
    t = f"💰 <b>WALLET</b>\n━━━━━━━━━━━━━━━━━━━━\n💵 <b>{u['wallet_balance']} BDT</b>\n💰 Earned: {u['referral_earnings']} BDT\n━━━━━━━━━━━━━━━━━━━━\n"
    for x in h:
        ic = "➕" if x['tx_type'] in ('credit','referral','bonus') else "➖"
        t += f"{ic} {x['amount']} BDT — {x['description'][:25]}\n"
    if not h: t += "No transactions\n"
    safe_send(uid, t)

def show_ref(uid):
    u = db.get_user(uid)
    if not u: return
    rc = u.get('referral_code') or gen_ref(uid)
    if not u.get('referral_code') or len(u.get('referral_code',''))<5:
        db.update_user(uid, referral_code=rc); u = db.get_user(uid); rc = u['referral_code']
    lnk = f"https://t.me/{BOT_USERNAME}?start={rc}"
    li = {'bronze':'🥉','silver':'🥈','gold':'🥇','platinum':'💠','diamond':'💎'}
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📋 Copy Link", callback_data=f"cpref:{rc}"),
          types.InlineKeyboardButton("🏆 Leaderboard", callback_data="board"),
          types.InlineKeyboardButton("📋 My Referrals", callback_data="myrefs"),
          types.InlineKeyboardButton("📤 Share", switch_inline_query=f"Join {BRAND}!\n{lnk}"))
    safe_send(uid,
        f"🎁 <b>REFERRAL</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 <code>{rc}</code>\n🔗 <code>{lnk}</code>\n\n"
        f"👥 {u['referral_count']} refs\n{li.get(u['referral_level'],'🥉')} {u['referral_level'].title()}\n"
        f"💰 {u['referral_earnings']} BDT earned\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 {REF_COMMISSION} BDT + 📅 {REF_BONUS_DAYS}d per ref", reply_markup=m)

def show_stats(uid):
    s = db.stats(); ss = sys_stats(); rn = len([k for k in bot_scripts if is_running(k)])
    safe_send(uid,
        f"📊 <b>STATISTICS</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🖥 CPU: {ss['cpu']}%\n🧠 RAM: {ss['mem']}% ({ss['mem_used']}/{ss['mem_total']})\n"
        f"💾 Disk: {ss['disk']}%\n⏱ {ss['up']}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Running: {rn}\n👥 Users: {s['users']}\n📅 Today: {s['today']}\n"
        f"💎 Subs: {s['active_subs']}\n💰 Revenue: {s['revenue']} BDT")

def show_running(uid):
    r = []
    for sk,i in bot_scripts.items():
        if is_running(sk) and (uid==OWNER_ID or uid in admin_ids or i.get('user_id')==uid):
            up = str(datetime.now()-i.get('start_time',datetime.now())).split('.')[0]
            ram,cpu = bot_res(sk)
            r.append(f"📄 {i.get('file_name','?')[:20]}\n   PID:{i['process'].pid} ⏱{up} 💾{ram}MB")
    safe_send(uid, f"🟢 <b>Running ({len(r)})</b>\n\n" + "\n".join(r) if r else "🔴 No bots running.")

def show_profile(uid):
    u = db.get_user(uid)
    if not u: return
    pl = PLANS.get(u['plan'], PLANS['free']); bc = db.bot_count(uid)
    bots_list = db.get_bots(uid); rn = sum(1 for b in bots_list if bot_running(uid,b['bot_name']))
    li = {'bronze':'🥉','silver':'🥈','gold':'🥇','platinum':'💠','diamond':'💎'}
    safe_send(uid,
        f"👤 <b>MY PROFILE</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 {u['full_name']}\n🆔 <code>{uid}</code>\n@{u['username'] or 'N/A'}\n\n"
        f"📦 {pl['name']}\n📅 {time_left(u['subscription_end'])}\n"
        f"🤖 {bc} bots (🟢 {rn})\n💰 {u['wallet_balance']} BDT\n💳 Spent: {u['total_spent']} BDT\n\n"
        f"👥 {u['referral_count']} refs\n{li.get(u['referral_level'],'🥉')} {u['referral_level'].title()}\n"
        f"📅 Joined: {u['created_at'][:10] if u.get('created_at') else '?'}")

def show_leaderboard(uid):
    lb = db.ref_board(10)
    medals = ['🥇','🥈','🥉']
    t = f"🏆 <b>LEADERBOARD</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for i,l in enumerate(lb):
        ic = medals[i] if i<3 else f"#{i+1}"
        t += f"{ic} {l['full_name'] or '?'} — {l['referral_count']} refs\n"
    if not lb: t += "No referrals yet!"
    safe_send(uid, t)

# ═══════════════════════════════════════════════════
#  TEXT HANDLER
# ═══════════════════════════════════════════════════
@bot.message_handler(content_types=['text'])
def handle_text(msg):
    uid = msg.from_user.id
    txt = msg.text.strip()
    active_users.add(uid)

    if not rate_check(uid): return
    if txt.startswith('/'): return

    joined, nj = check_joined(uid)
    if not joined: return force_sub_msg(msg.chat.id, nj)

    u = db.get_user(uid)
    if u and u['is_banned']: return
    if bot_locked and uid not in admin_ids and uid != OWNER_ID:
        return bot.reply_to(msg, "🔒 Maintenance")

    if SM.has_pay(uid): return handle_pay(msg)
    if SM.has(uid): return handle_state(msg)

    # Menu buttons
    handlers = {
        "🤖 My Bots": lambda: show_bots(uid),
        "📤 Deploy Bot": lambda: show_deploy(uid),
        "💎 Subscription": lambda: show_sub(uid),
        "💰 Wallet": lambda: show_wallet(uid),
        "🎁 Referral": lambda: show_ref(uid),
        "📊 Statistics": lambda: show_stats(uid),
        "🟢 Running Bots": lambda: show_running(uid),
        "⚡ Speed Test": lambda: safe_send(uid, f"⚡ <b>Speed</b>\n🖥 CPU: {sys_stats()['cpu']}%\n🧠 RAM: {sys_stats()['mem']}%\n⏱ {get_uptime()}"),
        "🔔 Notifications": lambda: (safe_send(uid, f"🔔 <b>Notifications</b>\n\n" + "\n".join(f"{'🔴' if not n['is_read'] else '⚪'} <b>{n['title']}</b>\n{n['message'][:50]}\n" for n in db.get_notifs(uid,10)) or "None!"), db.mark_read(uid)),
        "🎫 Support": lambda: (SM.set(uid, 'ticket'), safe_send(uid, "🎫 Send your issue:\n/cancel to cancel")),
        "📋 My Profile": lambda: show_profile(uid),
        "🏆 Leaderboard": lambda: show_leaderboard(uid),
        "👑 Admin Panel": lambda: show_admin_panel(uid) if uid in admin_ids or uid == OWNER_ID else None,
        "📢 Broadcast": lambda: (SM.set(uid, 'broadcast'), safe_send(uid, "📢 Send message:\n/cancel to cancel")) if uid in admin_ids or uid == OWNER_ID else None,
        "🔒 Lock Bot": lambda: lock_toggle(msg),
        "💳 Payments": lambda: show_payments(uid),
        "📢 Channels": lambda: safe_send(uid, "📢 Channels", reply_markup=channels_kb()) if uid in admin_ids else None,
        "🎟 Promo Codes": lambda: (SM.set(uid, 'a:promo'), safe_send(uid, "🎟 Send: CODE DISCOUNT% MAX\nEx: SAVE50 50 100\n/cancel")) if uid in admin_ids else None,
        "⚙️ Settings": lambda: show_settings(uid),
        "📞 Contact": lambda: safe_send(uid, f"📞 {DEV_USERNAME}\n📢 {UPDATE_CHANNEL}\n\n{TAG}"),
    }

    if txt in handlers:
        SM.clear_all(uid)
        h = handlers[txt]
        if h: h()
    else:
        safe_send(uid, "❓ Use buttons ⬇️\n/cancel to reset", reply_markup=main_kb(uid))

def lock_toggle(msg):
    global bot_locked
    uid = msg.from_user.id
    if uid not in admin_ids and uid != OWNER_ID: return
    bot_locked = not bot_locked
    bot.reply_to(msg, f"{'🔒 LOCKED' if bot_locked else '🔓 UNLOCKED'}")

def show_payments(uid):
    if uid not in admin_ids and uid != OWNER_ID: return
    pays = db.pending_pay()
    if not pays: return safe_send(uid, "💳 No pending payments!")
    t = f"💳 <b>Pending ({len(pays)})</b>\n\n"
    m = types.InlineKeyboardMarkup(row_width=2)
    for p in pays[:10]:
        pu = db.get_user(p['user_id']); name = pu['full_name'] if pu else str(p['user_id'])
        t += f"#{p['payment_id']} {name}\n💰 {p['amount']} {p['method']} TRX:{p['transaction_id'][:15]}\n\n"
        m.add(types.InlineKeyboardButton(f"✅ #{p['payment_id']}", callback_data=f"appv:{p['payment_id']}"),
              types.InlineKeyboardButton(f"❌ #{p['payment_id']}", callback_data=f"rejt:{p['payment_id']}"))
    safe_send(uid, t, reply_markup=m)

def show_settings(uid):
    u = db.get_user(uid)
    if not u: return
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="lang:en"),
          types.InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang:bn"))
    m.add(types.InlineKeyboardButton("📊 Profile", callback_data="profile"))
    m.add(types.InlineKeyboardButton("💳 Pay History", callback_data="payhist"))
    safe_send(uid, f"⚙️ <b>Settings</b>\n{u['full_name']}\n📦 {PLANS.get(u['plan'],PLANS['free'])['name']}", reply_markup=m)

# ═══════════════════════════════════════════════════
#  DOCUMENT HANDLER
# ═══════════════════════════════════════════════════
@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    uid = msg.from_user.id
    SM.clear_all(uid)
    joined, nj = check_joined(uid)
    if not joined: return force_sub_msg(msg.chat.id, nj)
    u = db.get_user(uid)
    if not u: return bot.reply_to(msg, "/start first!")
    if u['is_banned']: return
    pl = db.get_plan(uid); cur = db.bot_count(uid); mx = pl['bots']
    if mx != -1 and cur >= mx: return bot.reply_to(msg, f"❌ Limit ({cur}/{mx})!")

    fn = msg.document.file_name; fs = msg.document.file_size
    ext = fn.rsplit('.',1)[-1].lower() if '.' in fn else ''
    if ext not in ['py','js','zip','json','txt','env','yml','yaml','cfg','ini','toml']:
        return bot.reply_to(msg, f"❌ Unsupported: .{ext}")
    if fs > 100*1024*1024: return bot.reply_to(msg, "❌ Max 100MB!")

    pm = bot.reply_to(msg, f"📤 Uploading {fn[:25]}...")
    try:
        fi = bot.get_file(msg.document.file_id); dl = bot.download_file(fi.file_path)
        uf = user_dir(uid)

        if ext == 'zip':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                tmp.write(dl); tp = tmp.name
            try:
                with zipfile.ZipFile(tp,'r') as z:
                    for n in z.namelist():
                        if n.startswith('/') or '..' in n:
                            safe_edit("❌ Bad paths!", msg.chat.id, pm.message_id); os.unlink(tp); return
                    bn = fn.replace('.zip','').replace(' ','_')
                    ed = os.path.join(uf, bn)
                    if os.path.exists(ed): shutil.rmtree(ed, ignore_errors=True)
                    os.makedirs(ed, exist_ok=True); z.extractall(ed)
                    items = os.listdir(ed)
                    if len(items)==1 and os.path.isdir(os.path.join(ed,items[0])):
                        inner = os.path.join(ed,items[0])
                        for item in os.listdir(inner):
                            s,d = os.path.join(inner,item), os.path.join(ed,item)
                            if os.path.exists(d): shutil.rmtree(d) if os.path.isdir(d) else os.remove(d)
                            shutil.move(s,d)
                        try: os.rmdir(inner)
                        except: pass
                os.unlink(tp)
                entry, ft, report = det.report(ed)
                if not entry:
                    af = [os.path.relpath(os.path.join(r,f),ed) for r,_,fls in os.walk(ed) for f in fls if f.endswith(('.py','.js'))]
                    safe_edit(f"❌ No entry!\n\nFiles:\n"+"".join(f"• {f}\n" for f in af[:15]), msg.chat.id, pm.message_id); return
                bid = db.add_bot(uid, bn, ed, entry, ft, '', fs)
                mk = types.InlineKeyboardMarkup(row_width=2)
                mk.add(types.InlineKeyboardButton("▶️ Start", callback_data=f"start:{bid}"),
                       types.InlineKeyboardButton("🤖 Bots", callback_data="mybots"))
                mk.add(types.InlineKeyboardButton("🔍 Re-detect", callback_data=f"redetect:{bid}"))
                safe_edit(f"✅ <b>ZIP DEPLOYED!</b>\n\n📦 {bn[:20]}\n🆔 #{bid}\n\n{report}", msg.chat.id, pm.message_id, reply_markup=mk)
            except zipfile.BadZipFile:
                safe_edit("❌ Bad ZIP!", msg.chat.id, pm.message_id)
                try: os.unlink(tp)
                except: pass

        elif ext in ['py','js']:
            with open(os.path.join(uf,fn),'wb') as f: f.write(dl)
            bid = db.add_bot(uid, fn, uf, fn, ext, '', fs)
            mk = types.InlineKeyboardMarkup(row_width=2)
            mk.add(types.InlineKeyboardButton("▶️ Run", callback_data=f"start:{bid}"),
                   types.InlineKeyboardButton("🤖 Bots", callback_data="mybots"))
            safe_edit(f"✅ <b>UPLOADED!</b>\n📄 {fn[:25]}\n🆔 #{bid}\n{'🐍' if ext=='py' else '🟨'} {fmt_size(fs)}", msg.chat.id, pm.message_id, reply_markup=mk)
        else:
            with open(os.path.join(uf,fn),'wb') as f: f.write(dl)
            safe_edit(f"✅ {fn} saved!", msg.chat.id, pm.message_id)
    except Exception as e:
        logger.error(f"Upload: {e}", exc_info=True)
        safe_edit(f"❌ {str(e)[:100]}", msg.chat.id, pm.message_id)
       
# ═══════════════════════════════════════════════════
#  STATE HANDLER (All states - Bug free)
# ═══════════════════════════════════════════════════
def handle_state(msg):
    uid = msg.from_user.id
    s = SM.get(uid)
    if not s: return
    action = s.get('action', '')
    txt = msg.text.strip() if msg.text else ''

    if txt == '/cancel':
        SM.clear_all(uid)
        bot.reply_to(msg, "✅ Cancelled!", reply_markup=main_kb(uid))
        return

    # ── BROADCAST ──
    if action == 'broadcast':
        SM.clear(uid)
        if uid not in admin_ids and uid != OWNER_ID: return
        if not txt: return bot.reply_to(msg, "❌ Empty!")
        users = db.get_all_users()
        sent = fail = block = 0
        prog = bot.reply_to(msg, f"📢 Sending to {len(users)}...")
        for u in users:
            try:
                r = safe_send(u['user_id'], f"📢 <b>Announcement</b>\n\n{txt}\n\n{TAG}")
                if r: sent += 1
                else: block += 1
            except: fail += 1
            if (sent+fail+block) % 30 == 0:
                try: safe_edit(f"📢 {sent+fail+block}/{len(users)}\n✅{sent} ❌{fail} 🚫{block}", msg.chat.id, prog.message_id)
                except: pass
            time.sleep(0.05)
        safe_edit(f"📢 <b>Done!</b>\n✅ {sent} | ❌ {fail} | 🚫 {block} | 👥 {len(users)}", msg.chat.id, prog.message_id)
        db.admin_log(uid, 'broadcast', details=f"s:{sent} f:{fail}")
        return

    # ── ADD SUB (step 1: user id) ──
    if action == 'a:addsub':
        try:
            target = int(txt)
            tu = db.get_user(target)
            if not tu:
                bot.reply_to(msg, f"❌ User {target} not found!")
                SM.clear(uid); return
            SM.set(uid, 'a:addsub2', target=target)
            m = types.InlineKeyboardMarkup(row_width=2)
            for k, p in PLANS.items():
                if k != 'free':
                    m.add(types.InlineKeyboardButton(p['name'], callback_data=f"asub:{k}:{target}"))
            m.add(types.InlineKeyboardButton("❌ Cancel", callback_data="admin"))
            bot.reply_to(msg, f"👤 <code>{target}</code> — {tu['full_name']}\nSelect plan:", parse_mode='HTML', reply_markup=m)
            return
        except ValueError:
            bot.reply_to(msg, "❌ Invalid ID!")
            SM.clear(uid); return

    # ── ADD SUB (step 3: days) ──
    if action == 'a:addsub_days':
        SM.clear(uid)
        try:
            days = int(txt)
            target = s['target']; plan = s['plan']
            if days == 0:
                db.set_sub(target, 'lifetime')
                pn = "👑 Lifetime"
            else:
                db.set_sub(target, plan, days)
                pn = PLANS.get(plan, {}).get('name', plan)
            bot.reply_to(msg, f"✅ <b>Done!</b>\n👤 <code>{target}</code>\n📦 {pn}\n📅 {'Lifetime' if days==0 else f'{days}d'}", parse_mode='HTML')
            db.admin_log(uid, 'add_sub', target, f"{plan}/{days}d")
            safe_send(target, f"🎉 <b>Plan Upgraded!</b>\n📦 {pn}\n📅 {'Lifetime' if days==0 else f'{days} days'}\n\n{TAG}")
        except ValueError:
            bot.reply_to(msg, "❌ Send number (0=lifetime)")
        return

    # ── REMOVE SUB ──
    if action == 'a:remsub':
        SM.clear(uid)
        try:
            target = int(txt); db.rem_sub(target)
            bot.reply_to(msg, f"✅ Removed: <code>{target}</code>", parse_mode='HTML')
            db.admin_log(uid, 'remove_sub', target)
            safe_send(target, "⚠️ Subscription removed by admin.")
        except: bot.reply_to(msg, "❌ Invalid ID!")
        return

    # ── BAN ──
    if action == 'a:ban':
        SM.clear(uid)
        parts = txt.split(maxsplit=1)
        try:
            target = int(parts[0]); reason = parts[1] if len(parts)>1 else "Banned"
            db.ban(target, reason); db.admin_log(uid, 'ban', target, reason)
            for b in db.get_bots(target):
                sk = f"{target}_{b['bot_name']}"
                if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup_bot(sk)
                db.update_bot(b['bot_id'], status='stopped', should_run=0)
            bot.reply_to(msg, f"🚫 Banned <code>{target}</code>\n{reason}", parse_mode='HTML')
            safe_send(target, f"🚫 <b>Banned!</b>\n{reason}\nContact {DEV_USERNAME}")
        except: bot.reply_to(msg, "❌ Format: ID REASON")
        return

    # ── UNBAN ──
    if action == 'a:unban':
        SM.clear(uid)
        try:
            target = int(txt); db.unban(target); db.admin_log(uid, 'unban', target)
            bot.reply_to(msg, f"✅ Unbanned <code>{target}</code>", parse_mode='HTML')
            safe_send(target, "✅ You're unbanned!")
        except: bot.reply_to(msg, "❌ Invalid ID!")
        return

    # ── PROMO ──
    if action == 'a:promo':
        SM.clear(uid)
        parts = txt.split()
        if len(parts) >= 3:
            try:
                code, disc, mx = parts[0].upper(), int(parts[1]), int(parts[2])
                db.exe("INSERT OR IGNORE INTO promo_codes(code,discount_pct,max_uses,created_by) VALUES(?,?,?,?)", (code,disc,mx,uid))
                bot.reply_to(msg, f"✅ Promo: <code>{code}</code>\n💰 {disc}%\n🔢 Max: {mx}", parse_mode='HTML')
            except: bot.reply_to(msg, "❌ Error!")
        else: bot.reply_to(msg, "❌ Format: CODE DISC% MAX")
        return

    # ── ADD CHANNEL ──
    if action == 'chadd':
        SM.clear(uid)
        if not txt: bot.reply_to(msg, "❌ Empty!"); return
        parts = txt.split(maxsplit=1)
        cu = parts[0].lstrip('@').lower(); cn = parts[1] if len(parts)>1 else cu
        if not re.match(r'^[a-z][a-z0-9_]{3,}$', cu):
            bot.reply_to(msg, f"❌ Invalid: @{cu}"); return
        try:
            ci = bot.get_chat(f"@{cu}"); cn = ci.title or cn
        except: pass
        r = db.add_channel(cu, cn, uid)
        if r:
            db.admin_log(uid, 'add_channel', details=f"@{cu}")
            bot.reply_to(msg, f"✅ Added @{cu}\n⚠️ Bot must be admin!")
        else: bot.reply_to(msg, "❌ Invalid username!")
        return

    # ── REMOVE CHANNEL ──
    if action == 'chrem':
        SM.clear(uid)
        cu = txt.lstrip('@').lower()
        if cu: db.remove_channel(cu); bot.reply_to(msg, f"✅ Removed @{cu}")
        else: bot.reply_to(msg, "❌ Send username!")
        return

    # ── TICKET ──
    if action == 'ticket':
        SM.clear(uid)
        if len(txt) < 5: bot.reply_to(msg, "❌ Too short!"); return
        tid = db.add_ticket(uid, "Support", txt)
        bot.reply_to(msg, f"✅ Ticket #{tid} created!\n{DEV_USERNAME}", parse_mode='HTML')
        u = db.get_user(uid)
        for aid in admin_ids:
            safe_send(aid, f"🎫 <b>Ticket #{tid}</b>\n👤 {u['full_name'] if u else uid}\n📝 {txt[:200]}\n\n/reply {tid} message")
        return

    # ── TICKET REPLY ──
    if action == 'tkt_reply':
        tid = s.get('tid'); SM.clear(uid)
        if not txt or not tid: return
        tk = db.exe("SELECT * FROM tickets WHERE ticket_id=?", (tid,), one=True)
        if tk:
            db.reply_ticket(tid, txt)
            bot.reply_to(msg, f"✅ Replied #{tid}")
            safe_send(tk['user_id'], f"📩 <b>Ticket #{tid} Reply</b>\n\n💬 {txt}\n\n{TAG}")
        return

    # ── ADD ADMIN ──
    if action == 'a:addadmin':
        SM.clear(uid)
        try:
            target = int(txt); admin_ids.add(target)
            bot.reply_to(msg, f"✅ Admin: <code>{target}</code>", parse_mode='HTML')
            safe_send(target, f"👑 You're admin now!\n{TAG}")
        except: bot.reply_to(msg, "❌ Invalid ID!")
        return

    # ── GIVE BALANCE ──
    if action == 'a:give':
        SM.clear(uid)
        parts = txt.split()
        if len(parts) >= 2:
            try:
                target, amt = int(parts[0]), float(parts[1])
                if not db.get_user(target): bot.reply_to(msg, "❌ Not found!"); return
                db.wallet_tx(target, amt, 'bonus', f"Admin bonus")
                bot.reply_to(msg, f"✅ +{amt} BDT → <code>{target}</code>", parse_mode='HTML')
                safe_send(target, f"🎁 +{amt} BDT added!\n{TAG}")
            except: bot.reply_to(msg, "❌ Error!")
        else: bot.reply_to(msg, "❌ Format: USER_ID AMOUNT")
        return

    # ── NOTIFY USER ──
    if action == 'a:notify':
        SM.clear(uid)
        parts = txt.split(maxsplit=1)
        if len(parts) >= 2:
            try:
                target = int(parts[0]); text = parts[1]
                db.add_notif(target, "Admin Notice", text)
                bot.reply_to(msg, f"✅ Sent to <code>{target}</code>", parse_mode='HTML')
                safe_send(target, f"🔔 <b>Notice</b>\n\n{text}\n\n{TAG}")
            except: bot.reply_to(msg, "❌ Error!")
        else: bot.reply_to(msg, "❌ Format: USER_ID MESSAGE")
        return

    # ── USER INFO ──
    if action == 'a:userinfo':
        SM.clear(uid)
        try:
            target = int(txt)
            u = db.get_user(target)
            if not u: bot.reply_to(msg, "❌ Not found!"); return
            pl = PLANS.get(u['plan'], PLANS['free']); bc = db.bot_count(target)
            safe_send(uid,
                f"👤 <b>User Info</b>\n🆔 <code>{target}</code>\n📛 {u['full_name']}\n@{u['username'] or 'N/A'}\n"
                f"🚫 Banned: {'Yes' if u['is_banned'] else 'No'}\n📦 {pl['name']}\n📅 {time_left(u['subscription_end'])}\n"
                f"🤖 {bc} bots\n💰 {u['wallet_balance']} BDT\n👥 {u['referral_count']} refs")
        except: bot.reply_to(msg, "❌ Invalid ID!")
        return

    # ── STOP BOT BY ID ──
    if action == 'a:stopbot':
        SM.clear(uid)
        try:
            bid = int(txt); bd = db.get_bot(bid)
            if not bd: bot.reply_to(msg, "❌ Not found!"); return
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup_bot(sk)
            db.update_bot(bid, status='stopped', should_run=0)
            bot.reply_to(msg, f"✅ Stopped #{bid}")
        except: bot.reply_to(msg, "❌ Invalid!")
        return

    # ── UNKNOWN STATE ──
    SM.clear(uid)

# ═══════════════════════════════════════════════════
#  PAYMENT HANDLER
# ═══════════════════════════════════════════════════
def handle_pay(msg):
    uid = msg.from_user.id
    s = SM.get_pay(uid)
    if not s or s.get('step') != 'wait_trx': return
    trx = msg.text.strip() if msg.text else ''
    if not trx or len(trx) < 3:
        return bot.reply_to(msg, "❌ Send valid TRX ID!\n/cancel to cancel")
    SM.clear_pay(uid)
    pid = db.add_pay(uid, s['amount'], s['method'], trx, s['plan'], 30)
    safe_send(uid,
        f"✅ <b>PAYMENT SUBMITTED!</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 #{pid}\n💰 {s['amount']} BDT\n💳 {s['method']}\n📦 {s['plan']}\n"
        f"🔖 <code>{trx}</code>\n\n⏳ Waiting approval...")
    u = db.get_user(uid)
    for aid in admin_ids:
        pm = PAYMENTS.get(s['method'], {})
        safe_send(aid,
            f"💳 <b>NEW PAYMENT!</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 {u['full_name'] if u else '?'} (<code>{uid}</code>)\n"
            f"📦 {s['plan']} | 💰 {s['amount']} BDT\n"
            f"{pm.get('icon','💳')} {pm.get('name',s['method'])}\n"
            f"🔖 <code>{trx}</code>\n🆔 #{pid}", reply_markup=approve_kb(pid))

# ═══════════════════════════════════════════════════
#  ADMIN COMMANDS
# ═══════════════════════════════════════════════════
@bot.message_handler(commands=['reply'])
def cmd_reply(msg):
    uid = msg.from_user.id
    if uid not in admin_ids and uid != OWNER_ID: return
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3: return bot.reply_to(msg, "/reply TID MESSAGE")
    try:
        tid = int(parts[1]); txt = parts[2]
        tk = db.exe("SELECT * FROM tickets WHERE ticket_id=?", (tid,), one=True)
        if not tk: return bot.reply_to(msg, "❌ Not found!")
        db.reply_ticket(tid, txt)
        bot.reply_to(msg, f"✅ Replied #{tid}")
        safe_send(tk['user_id'], f"📩 <b>Ticket #{tid}</b>\n\n💬 {txt}\n\n{TAG}")
    except: bot.reply_to(msg, "❌ Error!")

@bot.message_handler(commands=['subscribe'])
def cmd_sub(msg):
    if msg.from_user.id not in admin_ids: return
    p = msg.text.split()
    if len(p)<3: return bot.reply_to(msg, "/subscribe UID DAYS")
    try: db.set_sub(int(p[1]), 'pro' if int(p[2])>0 else 'lifetime', int(p[2])); bot.reply_to(msg, "✅")
    except: bot.reply_to(msg, "❌")

@bot.message_handler(commands=['ban'])
def cmd_ban(msg):
    if msg.from_user.id not in admin_ids: return
    p = msg.text.split(maxsplit=2)
    if len(p)<2: return
    try: db.ban(int(p[1]), p[2] if len(p)>2 else "Banned"); bot.reply_to(msg, "🚫")
    except: pass

@bot.message_handler(commands=['unban'])
def cmd_unban(msg):
    if msg.from_user.id not in admin_ids: return
    try: db.unban(int(msg.text.split()[1])); bot.reply_to(msg, "✅")
    except: pass

@bot.message_handler(commands=['broadcast','bc'])
def cmd_bc(msg):
    uid = msg.from_user.id
    if uid not in admin_ids: return
    txt = msg.text.split(maxsplit=1)
    if len(txt) < 2:
        SM.set(uid, 'broadcast'); return bot.reply_to(msg, "📢 Send message:")
    users = db.get_all_users(); sent = fail = 0
    for u in users:
        try:
            if safe_send(u['user_id'], f"📢 <b>Announcement</b>\n\n{txt[1]}\n\n{TAG}"): sent += 1
            else: fail += 1
        except: fail += 1
        time.sleep(0.05)
    bot.reply_to(msg, f"📢 ✅{sent} ❌{fail}")

@bot.message_handler(commands=['userinfo'])
def cmd_userinfo(msg):
    uid = msg.from_user.id
    if uid not in admin_ids: return
    p = msg.text.split()
    if len(p)<2: return bot.reply_to(msg, "/userinfo UID")
    try:
        t = int(p[1]); u = db.get_user(t)
        if not u: return bot.reply_to(msg, "❌ Not found!")
        safe_send(uid, f"👤 <code>{t}</code>\n{u['full_name']}\n@{u['username'] or 'N/A'}\n{PLANS.get(u['plan'],PLANS['free'])['name']}\n💰{u['wallet_balance']} BDT\n🤖{db.bot_count(t)}")
    except: bot.reply_to(msg, "❌")

@bot.message_handler(commands=['give'])
def cmd_give(msg):
    if msg.from_user.id not in admin_ids: return
    p = msg.text.split()
    if len(p)<3: return bot.reply_to(msg, "/give UID AMOUNT")
    try:
        t,a = int(p[1]),float(p[2])
        db.wallet_tx(t, a, 'bonus', "Admin"); bot.reply_to(msg, f"✅ +{a}")
        safe_send(t, f"🎁 +{a} BDT!\n{TAG}")
    except: bot.reply_to(msg, "❌")

@bot.message_handler(commands=['notify'])
def cmd_notify(msg):
    if msg.from_user.id not in admin_ids: return
    p = msg.text.split(maxsplit=2)
    if len(p)<3: return bot.reply_to(msg, "/notify UID MSG")
    try:
        t = int(p[1]); db.add_notif(t, "Notice", p[2])
        bot.reply_to(msg, "✅"); safe_send(t, f"🔔 {p[2]}\n{TAG}")
    except: bot.reply_to(msg, "❌")

@bot.message_handler(commands=['addchannel'])
def cmd_addch(msg):
    if msg.from_user.id not in admin_ids: return
    p = msg.text.split(maxsplit=2)
    if len(p)<2: return bot.reply_to(msg, "/addchannel @username Name")
    cu = p[1].lstrip('@').lower(); cn = p[2] if len(p)>2 else cu
    try: ci = bot.get_chat(f"@{cu}"); cn = ci.title or cn
    except: pass
    if db.add_channel(cu, cn, msg.from_user.id): bot.reply_to(msg, f"✅ @{cu} added!")
    else: bot.reply_to(msg, "❌ Invalid!")

@bot.message_handler(commands=['removechannel','rmchannel'])
def cmd_rmch(msg):
    if msg.from_user.id not in admin_ids: return
    p = msg.text.split(maxsplit=1)
    if len(p)<2: return bot.reply_to(msg, "/removechannel @username")
    db.remove_channel(p[1].lstrip('@').lower()); bot.reply_to(msg, "✅")

@bot.message_handler(commands=['stopbot'])
def cmd_stopbot(msg):
    if msg.from_user.id not in admin_ids: return
    p = msg.text.split()
    if len(p)<2: return bot.reply_to(msg, "/stopbot BOT_ID")
    try:
        bid = int(p[1]); bd = db.get_bot(bid)
        if not bd: return bot.reply_to(msg, "❌")
        sk = f"{bd['user_id']}_{bd['bot_name']}"
        if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup_bot(sk)
        db.update_bot(bid, status='stopped', should_run=0); bot.reply_to(msg, f"✅ #{bid}")
    except: bot.reply_to(msg, "❌")

# ═══════════════════════════════════════════════════
#  CALLBACK HANDLER (Complete)
# ═══════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: True)
def handle_cb(call):
    uid = call.from_user.id
    data = call.data
    cid = call.message.chat.id
    mid = call.message.message_id

    try:
        # Clear state on most callbacks (prevents leaking)
        skip_clear = ['asub:', 'verify_join']
        if not any(data.startswith(p) for p in skip_clear):
            if SM.has(uid):
                SM.clear(uid)

        # ── VERIFY JOIN ──
        if data == "verify_join":
            j, nj = check_joined(uid)
            if j:
                safe_answer(call.id, "✅ Verified!", show_alert=True)
                safe_delete(cid, mid)
                class FM:
                    def __init__(s,c): s.from_user=c.from_user; s.chat=c.message.chat; s.text="/start"
                cmd_start(FM(call))
            else: safe_answer(call.id, "❌ Join all channels!", show_alert=True)
            return

        # ── MENU ──
        if data == "menu":
            safe_answer(call.id); SM.clear_all(uid); safe_delete(cid, mid)
            safe_send(uid, "🏠 Menu", reply_markup=main_kb(uid)); return

        # ── MY BOTS ──
        if data == "mybots":
            safe_answer(call.id); show_bots(uid); return

        # ── BOT DETAIL ──
        if data.startswith("detail:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return safe_answer(call.id, "❌!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"; rn = is_running(sk)
            ram, cpu = bot_res(sk) if rn else (0,0)
            up = "—"
            if rn and sk in bot_scripts:
                st = bot_scripts[sk].get('start_time')
                if st: up = str(datetime.now()-st).split('.')[0]
            ic = "🐍" if bd['file_type']=='py' else "🟨"
            safe_edit(
                f"{ic} <b>{bd['bot_name'][:22]}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 #{bid}\n📄 {bd['entry_file']}\n🔤 {bd['file_type'].upper()}\n"
                f"📊 {'🟢 Running' if rn else '🔴 Stopped'}\n"
                f"💾 {ram}MB | ⚡ {cpu}%\n⏱ {up}\n🔄 Restarts: {bd['total_restarts']}",
                cid, mid, reply_markup=bot_kb(bid, rn))
            safe_answer(call.id); return

        # ── START BOT ──
        if data.startswith("start:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return safe_answer(call.id, "❌!")
            if not db.is_active(bd['user_id']): return safe_answer(call.id, "⚠️ Expired!", show_alert=True)
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if is_running(sk): return safe_answer(call.id, "⚠️ Already running!")
            safe_answer(call.id, "🚀 Starting...")
            threading.Thread(target=run_bot, args=(bid,cid), daemon=True).start(); return

        # ── STOP BOT ──
        if data.startswith("stop:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return safe_answer(call.id, "❌!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup_bot(sk)
            db.update_bot(bid, status='stopped', should_run=0, last_stopped=datetime.now().isoformat())
            safe_answer(call.id, "✅ Stopped!")
            call.data = f"detail:{bid}"; handle_cb(call); return

        # ── RESTART ──
        if data.startswith("restart:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return safe_answer(call.id, "❌!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup_bot(sk)
            time.sleep(2); safe_answer(call.id, "🔄 Restarting...")
            threading.Thread(target=run_bot, args=(bid,cid), daemon=True).start(); return

        # ── LOGS ──
        if data.startswith("logs:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return safe_answer(call.id, "❌!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"; lp = os.path.join(LOGS_DIR, f"{sk}.log")
            logs = "📭 No logs."
            if os.path.exists(lp):
                try:
                    with open(lp,'r',encoding='utf-8',errors='ignore') as f: logs = f.read()[-1500:] or "📭 Empty"
                except: logs = "❌ Error"
            m = types.InlineKeyboardMarkup(row_width=2)
            m.add(types.InlineKeyboardButton("🔄 Refresh", callback_data=f"logs:{bid}"),
                  types.InlineKeyboardButton("🗑 Clear", callback_data=f"clrlogs:{bid}"))
            m.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"detail:{bid}"))
            safe_edit(f"📋 <b>Logs #{bid}</b>\n\n<code>{logs}</code>"[:4000], cid, mid, reply_markup=m)
            safe_answer(call.id); return

        if data.startswith("clrlogs:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if bd:
                lp = os.path.join(LOGS_DIR, f"{bd['user_id']}_{bd['bot_name']}.log")
                try:
                    with open(lp,'w') as f: f.write("")
                except: pass
            safe_answer(call.id, "🗑 Cleared!"); call.data = f"logs:{bid}"; handle_cb(call); return

        # ── RESOURCES ──
        if data.startswith("res:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return safe_answer(call.id, "!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"; ram,cpu = bot_res(sk)
            up = "—"
            if sk in bot_scripts and bot_scripts[sk].get('start_time'):
                up = str(datetime.now()-bot_scripts[sk]['start_time']).split('.')[0]
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔄", callback_data=f"res:{bid}"),
                  types.InlineKeyboardButton("🔙", callback_data=f"detail:{bid}"))
            safe_edit(f"📊 <b>#{bid}</b>\n💾 {ram}MB\n⚡ {cpu}%\n⏱ {up}\n🔄 {bd['total_restarts']}", cid, mid, reply_markup=m)
            safe_answer(call.id); return

        # ── RE-DETECT ──
        if data.startswith("redetect:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return safe_answer(call.id, "!")
            wd = bd['file_path'] if os.path.isdir(bd['file_path']) else user_dir(bd['user_id'])
            entry, ft, rp = det.report(wd)
            if entry:
                db.update_bot(bid, entry_file=entry, file_type=ft)
                m = types.InlineKeyboardMarkup(row_width=2)
                m.add(types.InlineKeyboardButton("▶️ Start", callback_data=f"start:{bid}"),
                      types.InlineKeyboardButton("🔙", callback_data=f"detail:{bid}"))
                safe_edit(f"🔍 <b>Re-detect</b>\n\n{rp}\n\n✅ Updated!", cid, mid, reply_markup=m)
            else:
                af = [os.path.relpath(os.path.join(r,f),wd) for r,_,fs in os.walk(wd) for f in fs if f.endswith(('.py','.js'))]
                m = types.InlineKeyboardMarkup(row_width=1)
                for f in af[:10]:
                    ft2 = 'js' if f.endswith('.js') else 'py'
                    m.add(types.InlineKeyboardButton(f"📄 {f}", callback_data=f"setentry:{bid}:{f}:{ft2}"))
                m.add(types.InlineKeyboardButton("🔙", callback_data=f"detail:{bid}"))
                safe_edit("🔍 Select entry:\n"+"".join(f"• {f}\n" for f in af[:10]), cid, mid, reply_markup=m)
            safe_answer(call.id); return

        if data.startswith("setentry:"):
            p = data.split(":"); bid,entry,ft = int(p[1]),p[2],p[3]
            db.update_bot(bid, entry_file=entry, file_type=ft)
            safe_answer(call.id, f"✅ {entry}"); call.data = f"detail:{bid}"; handle_cb(call); return

        # ── DELETE ──
        if data.startswith("del:"):
            bid = int(data.split(":")[1])
            m = types.InlineKeyboardMarkup(row_width=2)
            m.add(types.InlineKeyboardButton("✅ Yes", callback_data=f"cdel:{bid}"),
                  types.InlineKeyboardButton("❌ No", callback_data=f"detail:{bid}"))
            safe_edit(f"🗑 Delete #{bid}?", cid, mid, reply_markup=m); safe_answer(call.id); return

        if data.startswith("cdel:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if bd:
                sk = f"{bd['user_id']}_{bd['bot_name']}"
                if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup_bot(sk)
                if os.path.isdir(bd['file_path']): shutil.rmtree(bd['file_path'], ignore_errors=True)
                else:
                    try: os.remove(os.path.join(user_dir(bd['user_id']), bd['bot_name']))
                    except: pass
                db.del_bot(bid)
            safe_answer(call.id, "✅ Deleted!"); call.data = "mybots"; handle_cb(call); return

        # ── DOWNLOAD ──
        if data.startswith("dl:"):
            bid = int(data.split(":")[1]); bd = db.get_bot(bid)
            if bd:
                fp = os.path.join(bd['file_path'],bd['entry_file']) if os.path.isdir(bd['file_path']) else os.path.join(user_dir(bd['user_id']),bd['bot_name'])
                if os.path.exists(fp):
                    try:
                        with open(fp,'rb') as f: bot.send_document(uid, f, caption=f"📄 {bd['bot_name']}")
                    except: pass
            safe_answer(call.id, "📥"); return

        # ── DEPLOY ──
        if data == "deploy": safe_answer(call.id); show_deploy(uid); return

        # ── REFERRAL ──
        if data.startswith("cpref:"):
            rc = data.split(":",1)[1]; safe_answer(call.id)
            safe_send(uid, f"📋 <code>https://t.me/{BOT_USERNAME}?start={rc}</code>\n👆 Tap to copy!"); return

        if data == "myrefs":
            refs = db.user_refs(uid)
            t = f"📋 <b>Referrals ({len(refs)})</b>\n\n"
            for r in refs[:20]:
                ru = db.get_user(r['referred_id']); name = ru['full_name'] if ru else str(r['referred_id'])
                t += f"👤 {name} +{r['commission']} BDT\n"
            if not refs: t += "None yet!"
            safe_edit(t, cid, mid, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="menu")))
            safe_answer(call.id); return

        if data == "board":
            show_leaderboard(uid); safe_answer(call.id); return

        # ── PLANS ──
        if data in ("plans","sub"):
            t = f"📋 <b>Plans</b>\n\n"
            for k,p in PLANS.items():
                if k=='free': continue
                bx = '♾️' if p['bots']==-1 else str(p['bots'])
                t += f"{p['name']}\n  🤖 {bx} | 💾 {p['ram']}MB | 🔄{'✅' if p['restart'] else '❌'}\n  💰 {p['price']} BDT/mo\n\n"
            safe_edit(t, cid, mid, reply_markup=plan_kb()); safe_answer(call.id); return

        if data.startswith("plan:"):
            pk = data.split(":")[1]; p = PLANS.get(pk)
            if not p: return
            bx = '♾️' if p['bots']==-1 else str(p['bots'])
            safe_edit(f"{p['name']}\n🤖 {bx}\n💾 {p['ram']}MB\n🔄{'✅' if p['restart'] else '❌'}\n💰 {p['price']} BDT\n\nSelect payment:",
                cid, mid, reply_markup=pay_kb(pk)); safe_answer(call.id); return

        if data.startswith("pay:"):
            pts = data.split(":"); pk,mk = pts[1],pts[2]; p = PLANS.get(pk); pm = PAYMENTS.get(mk)
            if not p or not pm: return
            SM.set_pay(uid, step='wait_trx', plan=pk, method=mk, amount=p['price'])
            safe_edit(f"{pm['icon']} <b>{pm['name']}</b>\n━━━━━━━━━━━━━━━━━━━━\n📱 <code>{pm['num']}</code>\n📝 {pm['type']}\n💰 <b>{p['price']} BDT</b>\n📦 {p['name']}\n━━━━━━━━━━━━━━━━━━━━\n📤 Send TRX ID:\n/cancel to cancel",
                cid, mid); safe_answer(call.id); return

        if data.startswith("payw:"):
            pk = data.split(":")[1]; u = db.get_user(uid); p = PLANS.get(pk)
            if not u or not p: return
            if u['wallet_balance'] < p['price']:
                return safe_answer(call.id, f"❌ Need {p['price']}, have {u['wallet_balance']}", show_alert=True)
            db.wallet_tx(uid, p['price'], 'purchase', f"Plan: {pk}")
            db.set_sub(uid, pk if pk!='lifetime' else 'lifetime', 30)
            safe_answer(call.id, "✅"); safe_edit(f"✅ <b>Activated!</b>\n📦 {p['name']}\n💰 {p['price']} BDT\n\n{TAG}", cid, mid); return

        # ── PAYMENT APPROVE/REJECT ──
        if data.startswith("appv:"):
            if uid not in admin_ids: return
            pid = int(data.split(":")[1]); p = db.approve_pay(pid, uid)
            if p:
                safe_answer(call.id, "✅")
                safe_edit((call.message.text or '')+"\n\n✅ APPROVED", cid, mid)
                safe_send(p['user_id'], f"🎉 <b>Approved!</b>\n📦 {PLANS.get(p['plan'],{}).get('name',p['plan'])}\n📅 {p['duration_days']}d\n\n{TAG}")
            return

        if data.startswith("rejt:"):
            if uid not in admin_ids: return
            pid = int(data.split(":")[1]); pay = db.get_pay(pid); db.reject_pay(pid, uid)
            safe_answer(call.id, "❌"); safe_edit((call.message.text or '')+"\n\n❌ REJECTED", cid, mid)
            if pay: safe_send(pay['user_id'], f"❌ Payment #{pid} rejected.\n{DEV_USERNAME}")
            return

        # ── SETTINGS ──
        if data.startswith("lang:"): db.update_user(uid, language=data.split(":")[1]); safe_answer(call.id, "✅"); return

        if data == "profile": safe_answer(call.id); show_profile(uid); return

        if data == "payhist":
            pays = db.exe("SELECT * FROM payments WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (uid,), fetch=True) or []
            t = "💳 <b>History</b>\n\n"
            for p in pays:
                si = "✅" if p['status']=='approved' else "❌" if p['status']=='rejected' else "⏳"
                t += f"{si} #{p['payment_id']} {p['amount']} BDT {p['status']}\n"
            if not pays: t += "None"
            safe_edit(t, cid, mid, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="menu")))
            safe_answer(call.id); return

        # ── ADMIN CALLBACKS ──
        if data == "admin":
            if uid not in admin_ids and uid != OWNER_ID: return
            safe_answer(call.id); SM.clear_all(uid)
            s = db.stats(); rn = len([k for k in bot_scripts if is_running(k)]); tk = len(db.open_tickets())
            fsub = settings.get_bool('force_sub', True)
            safe_edit(f"👑 <b>ADMIN</b>\n{TAG}\n━━━━━━━━━━━━━━━━━━━━\n👥 {s['users']} (+{s['today']})\n🤖 {rn}\n💎 {s['active_subs']}\n🚫 {s['banned']}\n💳 {s['pending']}\n🎫 {tk}\n💰 {s['revenue']} BDT\nFSub: {'🟢' if fsub else '🔴'}",
                cid, mid, reply_markup=admin_kb()); return

        if data == "a:users":
            if uid not in admin_ids: return
            users = db.get_all_users()
            t = f"👥 <b>Users ({len(users)})</b>\n\n"
            for u in users[:30]:
                si = "🚫" if u['is_banned'] else "💎" if u['plan']!='free' else "✅"
                t += f"{si} <code>{u['user_id']}</code> {u['full_name'] or '-'} [{u['plan']}]\n"
            if len(users)>30: t += f"\n+{len(users)-30} more"
            m = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="admin"))
            safe_edit(t[:4000], cid, mid, reply_markup=m); safe_answer(call.id); return

        if data == "a:stats": safe_answer(call.id); show_stats(uid); return
        if data == "a:pay": safe_answer(call.id); show_payments(uid); return

        if data == "a:bc": SM.set(uid, 'broadcast'); safe_answer(call.id); safe_send(uid, "📢 Send message:\n/cancel"); return
        if data == "a:addsub": SM.set(uid, 'a:addsub'); safe_answer(call.id); safe_send(uid, "➕ User ID:\n/cancel"); return
        if data == "a:remsub": SM.set(uid, 'a:remsub'); safe_answer(call.id); safe_send(uid, "➖ User ID:\n/cancel"); return
        if data == "a:ban": SM.set(uid, 'a:ban'); safe_answer(call.id); safe_send(uid, "🚫 ID REASON:\n/cancel"); return
        if data == "a:unban": SM.set(uid, 'a:unban'); safe_answer(call.id); safe_send(uid, "✅ User ID:\n/cancel"); return
        if data == "a:promo": SM.set(uid, 'a:promo'); safe_answer(call.id); safe_send(uid, "🎟 CODE DISC% MAX:\n/cancel"); return
        if data == "a:give": SM.set(uid, 'a:give'); safe_answer(call.id); safe_send(uid, "💰 UID AMOUNT:\n/cancel"); return
        if data == "a:notify": SM.set(uid, 'a:notify'); safe_answer(call.id); safe_send(uid, "🔔 UID MSG:\n/cancel"); return
        if data == "a:userinfo": SM.set(uid, 'a:userinfo'); safe_answer(call.id); safe_send(uid, "👤 User ID:\n/cancel"); return
        if data == "a:stopbot": SM.set(uid, 'a:stopbot'); safe_answer(call.id); safe_send(uid, "🛑 Bot ID:\n/cancel"); return

        if data == "a:addadmin":
            if uid != OWNER_ID: return safe_answer(call.id, "❌ Owner only!", show_alert=True)
            SM.set(uid, 'a:addadmin'); safe_answer(call.id); safe_send(uid, "👑 User ID:\n/cancel"); return

        if data.startswith("asub:"):
            pts = data.split(":"); plan,target = pts[1],int(pts[2])
            SM.set(uid, 'a:addsub_days', target=target, plan=plan)
            safe_answer(call.id); safe_send(uid, f"📦 {PLANS[plan]['name']}\n👤 <code>{target}</code>\nDays (0=lifetime):\n/cancel"); return

        if data == "a:channels":
            if uid not in admin_ids: return
            safe_edit("📢 <b>Channels</b>\nFSub: {'🟢' if settings.get_bool('force_sub',True) else '🔴'}",
                cid, mid, reply_markup=channels_kb()); safe_answer(call.id); return

        if data.startswith("chtoggle:"):
            cid2 = int(data.split(":")[1]); ns = db.toggle_channel(cid2)
            safe_answer(call.id, f"{'🟢' if ns else '🔴'}"); call.data = "a:channels"; handle_cb(call); return

        if data == "chadd": SM.set(uid, 'chadd'); safe_answer(call.id); safe_send(uid, "➕ @username Name:\n/cancel"); return

        if data == "chrem":
            chs = db.get_channels()
            if not chs: return safe_answer(call.id, "None!")
            m = types.InlineKeyboardMarkup(row_width=1)
            for ch in chs: m.add(types.InlineKeyboardButton(f"🗑 @{ch['channel_username']}", callback_data=f"chdel:{ch['channel_id']}"))
            m.add(types.InlineKeyboardButton("🔙", callback_data="a:channels"))
            safe_edit("🗑 Select:", cid, mid, reply_markup=m); safe_answer(call.id); return

        if data.startswith("chdel:"):
            c2 = int(data.split(":")[1]); db.delete_channel(c2)
            safe_answer(call.id, "✅"); call.data = "a:channels"; handle_cb(call); return

        if data == "a:fsub":
            cur = settings.get_bool('force_sub', True); settings.set_bool('force_sub', not cur)
            safe_answer(call.id, f"FSub: {'🟢' if not cur else '🔴'}"); call.data = "admin"; handle_cb(call); return

        if data == "a:tickets":
            if uid not in admin_ids: return
            tks = db.open_tickets()
            t = f"🎫 <b>Tickets ({len(tks)})</b>\n\n"
            m = types.InlineKeyboardMarkup(row_width=1)
            for tk in tks[:10]:
                tu = db.get_user(tk['user_id']); name = tu['full_name'] if tu else str(tk['user_id'])
                t += f"#{tk['ticket_id']} {name}\n📝 {tk['message'][:50]}\n\n"
                m.add(types.InlineKeyboardButton(f"💬 #{tk['ticket_id']}", callback_data=f"tktreply:{tk['ticket_id']}"))
            if not tks: t += "None! 🎉"
            m.add(types.InlineKeyboardButton("🔙", callback_data="admin"))
            safe_edit(t, cid, mid, reply_markup=m); safe_answer(call.id); return

        if data.startswith("tktreply:"):
            tid = int(data.split(":")[1]); SM.set(uid, 'tkt_reply', tid=tid)
            safe_answer(call.id)
            tk = db.exe("SELECT * FROM tickets WHERE ticket_id=?", (tid,), one=True)
            if tk: safe_send(uid, f"💬 Reply #{tid}\n📝 {tk['message'][:200]}\n\nSend reply:\n/cancel")
            return

        if data == "a:sys":
            ss = sys_stats(); rn = len([k for k in bot_scripts if is_running(k)])
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔄", callback_data="a:sys"), types.InlineKeyboardButton("🔙", callback_data="admin"))
            safe_edit(f"🖥 <b>System</b>\n🖥 CPU: {ss['cpu']}%\n🧠 RAM: {ss['mem']}% ({ss['mem_used']}/{ss['mem_total']})\n💾 Disk: {ss['disk']}%\n⏱ {ss['up']}\n🤖 {rn} running",
                cid, mid, reply_markup=m); safe_answer(call.id); return

        if data == "a:stopall":
            if uid not in admin_ids: return
            cnt = 0
            for sk in list(bot_scripts.keys()):
                try:
                    bi = bot_scripts[sk].get('bot_id')
                    kill_tree(bot_scripts[sk]); cleanup_bot(sk)
                    if bi: db.update_bot(bi, status='stopped', should_run=0)
                    cnt += 1
                except: pass
            safe_answer(call.id, f"🛑 {cnt} stopped"); call.data = "admin"; handle_cb(call); return

        if data == "a:restartall":
            if uid not in admin_ids: return
            safe_answer(call.id, "🔄 Restarting...")
            threading.Thread(target=auto_restart_bots, daemon=True).start(); return

        if data == "a:backup":
            if uid not in admin_ids: return
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            bp = os.path.join(BACKUP_DIR, f"bk_{ts}.db"); shutil.copy2(DB_PATH, bp)
            safe_answer(call.id, "💾 Done!")
            try:
                with open(bp,'rb') as f: bot.send_document(uid, f, caption=f"💾 {ts}")
            except: pass
            return

        if data == "noop": safe_answer(call.id); return

        safe_answer(call.id)

    except Exception as e:
        logger.error(f"CB [{data}]: {e}", exc_info=True)
        safe_answer(call.id, "❌ Error!")

# ═══════════════════════════════════════════════════
#  CLEANUP
# ═══════════════════════════════════════════════════
def cleanup_all():
    logger.info("🛑 Shutting down...")
    for sk in list(bot_scripts.keys()):
        try: kill_tree(bot_scripts[sk])
        except: pass
    logger.info("🛑 Done")

atexit.register(cleanup_all)

# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════
def main():
    logger.info("=" * 50)
    logger.info(f"  {BRAND} {VER}")
    logger.info("=" * 50)

    # Seed channels
    if not db.get_all_channels():
        for cu, cn in DEFAULT_CHANNELS.items():
            db.add_channel(cu, cn, OWNER_ID)

    # Fix ref codes
    fixed = 0
    for u in db.get_all_users():
        if not u.get('referral_code') or len(u.get('referral_code','')) < 5:
            try: db.update_user(u['user_id'], referral_code=gen_ref(u['user_id'])); fixed += 1
            except: pass
    if fixed: logger.info(f"🔧 Fixed {fixed} ref codes")

    # Threads
    threading.Thread(target=thread_monitor, daemon=True, name="Monitor").start()
    threading.Thread(target=thread_backup, daemon=True, name="Backup").start()
    threading.Thread(target=thread_expiry, daemon=True, name="Expiry").start()
    threading.Thread(target=thread_ping, daemon=True, name="Ping").start()

    keep_alive()

    # Auto-restart bots
    threading.Thread(target=auto_restart_bots, daemon=True, name="AutoRestart").start()

    # Notify admin
    s = db.stats(); sr = len(db.should_run_bots())
    fsub = settings.get_bool('force_sub', True)
    for aid in admin_ids:
        safe_send(aid,
            f"🚀 <b>{BRAND} {VER} STARTED!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ All systems online\n"
            f"👥 {s['users']} users | 🤖 {s['bots']} bots\n"
            f"🔄 Auto-restart: {sr}\n"
            f"💰 Revenue: {s['revenue']} BDT\n"
            f"FSub: {'🟢' if fsub else '🔴'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━")

    logger.info(f"🟢 READY! Auto-restart: {sr}")

    # Polling
    retry = 0
    while True:
        try:
            retry = 0
            bot.infinity_polling(timeout=60, long_polling_timeout=30,
                allowed_updates=["message","callback_query"], skip_pending=True)
        except requests.exceptions.ConnectionError:
            retry += 1; d = min(10*retry, 60)
            logger.error(f"🔴 Connection! Retry {d}s..."); time.sleep(d)
        except requests.exceptions.ReadTimeout:
            retry += 1; d = min(5*retry, 60)
            logger.error(f"🔴 Timeout! Retry {d}s..."); time.sleep(d)
        except telebot.apihelper.ApiTelegramException as e:
            err = str(e).lower()
            if 'conflict' in err: logger.error("🔴 Another instance! 30s..."); time.sleep(30)
            elif 'too many' in err: logger.error("🔴 Rate limit! 60s..."); time.sleep(60)
            else: retry += 1; time.sleep(min(10*retry, 60))
        except KeyboardInterrupt: break
        except Exception as e:
            retry += 1; logger.error(f"🔴 {e}", exc_info=True); time.sleep(min(5*retry, 60))

if __name__ == "__main__":
    main()