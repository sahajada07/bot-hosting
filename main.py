"""
╔══════════════════════════════════════════════════════╗
║  🚀 EXU HOSTING PRO X — Bangladesh Premium Edition  ║
║  v2.4 FINAL — Binance + Referral Fixed              ║
╚══════════════════════════════════════════════════════╝
"""

import telebot, subprocess, os, zipfile, tempfile, shutil, time, psutil
import sqlite3, json, logging, signal, threading, re, sys, atexit
import requests, random, hashlib, string, traceback
from telebot import types
from datetime import datetime, timedelta
from flask import Flask, jsonify
from threading import Thread

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "🚀 EXU HOSTING PRO X Running!"

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy", "uptime": get_uptime(), "version": "2.4"})

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask started")

# ═══════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════
TOKEN = '8258702948:AAHCT3iI934w6MnLle72GPUxQTR2O3z6aWA'
OWNER_ID = 6678577936
ADMIN_ID = 6678577936
BOT_USERNAME = 'apon_vps_bot'
YOUR_USERNAME = '@developer_apon'
UPDATE_CHANNEL = 'https://t.me/developer_apon_07'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
DATA_DIR = os.path.join(BASE_DIR, 'exu_data')
DATABASE_PATH = os.path.join(DATA_DIR, 'exu_hosting.db')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')

PLAN_LIMITS = {
    'free': {'name': '🆓 Free Plan', 'max_bots': 1, 'storage_mb': 50, 'ram_mb': 128, 'restarts_per_day': 2, 'auto_restart': False, 'priority_support': False, 'price_bdt': 0},
    'basic': {'name': '⭐ Basic Plan', 'max_bots': 3, 'storage_mb': 256, 'ram_mb': 512, 'restarts_per_day': -1, 'auto_restart': True, 'priority_support': False, 'price_bdt': 199},
    'pro': {'name': '💎 Pro Plan', 'max_bots': 10, 'storage_mb': 1024, 'ram_mb': 2048, 'restarts_per_day': -1, 'auto_restart': True, 'priority_support': True, 'price_bdt': 499},
    'lifetime': {'name': '👑 Lifetime Plan', 'max_bots': -1, 'storage_mb': 5120, 'ram_mb': 4096, 'restarts_per_day': -1, 'auto_restart': True, 'priority_support': True, 'price_bdt': 1999},
}

PAYMENT_METHODS = {
    'bkash': {'name': 'bKash', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟪'},
    'nagad': {'name': 'Nagad', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟧'},
    'rocket': {'name': 'Rocket', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟦'},
    'upay': {'name': 'Upay', 'number': '01306633616', 'type': 'Send Money', 'icon': '🟩'},
    'binance': {'name': 'Binance Pay', 'number': 'Binance ID: 758637628', 'type': 'Binance Pay / USDT', 'icon': '🟡'},
    'bank': {'name': 'Bank Transfer', 'number': 'AC: XXXXXXXXXX', 'type': 'Transfer', 'icon': '🏦'},
}

REFERRAL_BONUS_DAYS = 3
REFERRAL_COMMISSION_BDT = 20

for d in [UPLOAD_BOTS_DIR, DATA_DIR, LOGS_DIR, BACKUPS_DIR]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)-12s | %(levelname)-7s | %(message)s',
    handlers=[logging.FileHandler(os.path.join(LOGS_DIR, 'exu.log')), logging.StreamHandler()])
logger = logging.getLogger('EXU')

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

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
#  SMART ENTRY DETECTOR
# ═══════════════════════════════════════════════════
class EntryFileDetector:
    PY = ['main.py','app.py','bot.py','run.py','start.py','server.py','index.py','manage.py','__main__.py']
    JS = ['index.js','app.js','bot.js','main.js','server.js','start.js','run.js']

    @staticmethod
    def detect_entry_file(directory):
        if not os.path.isdir(directory):
            if os.path.isfile(directory):
                return os.path.basename(directory), directory.rsplit('.',1)[-1].lower(), 'exact'
            return None, None, None
        top = os.listdir(directory)
        for e in EntryFileDetector.PY:
            if e in top and os.path.isfile(os.path.join(directory, e)):
                return e, 'py', 'high'
        for e in EntryFileDetector.JS:
            if e in top and os.path.isfile(os.path.join(directory, e)):
                return e, 'js', 'high'
        pj = os.path.join(directory, 'package.json')
        if os.path.exists(pj):
            try:
                with open(pj) as f:
                    pkg = json.load(f)
                if 'main' in pkg and os.path.exists(os.path.join(directory, pkg['main'])):
                    return pkg['main'], pkg['main'].rsplit('.',1)[-1].lower(), 'high'
                if 'scripts' in pkg and 'start' in pkg['scripts']:
                    cmd = pkg['scripts']['start']
                    m = re.search(r'node\s+(\S+\.js)', cmd)
                    if m and os.path.exists(os.path.join(directory, m.group(1))):
                        return m.group(1), 'js', 'high'
                    m = re.search(r'python[3]?\s+(\S+\.py)', cmd)
                    if m and os.path.exists(os.path.join(directory, m.group(1))):
                        return m.group(1), 'py', 'high'
            except: pass
        pf = os.path.join(directory, 'Procfile')
        if os.path.exists(pf):
            try:
                with open(pf) as f:
                    c = f.read()
                m = re.search(r'(?:worker|web):\s*python[3]?\s+(\S+\.py)', c)
                if m and os.path.exists(os.path.join(directory, m.group(1))):
                    return m.group(1), 'py', 'high'
                m = re.search(r'(?:worker|web):\s*node\s+(\S+\.js)', c)
                if m and os.path.exists(os.path.join(directory, m.group(1))):
                    return m.group(1), 'js', 'high'
            except: pass
        for root, dirs, files in os.walk(directory):
            if os.path.relpath(root, directory).count(os.sep) > 1: continue
            for e in EntryFileDetector.PY:
                if e in files:
                    return os.path.relpath(os.path.join(root, e), directory), 'py', 'medium'
            for e in EntryFileDetector.JS:
                if e in files:
                    return os.path.relpath(os.path.join(root, e), directory), 'js', 'medium'
        pyf, jsf = [], []
        for root, dirs, files in os.walk(directory):
            if os.path.relpath(root, directory).count(os.sep) > 1: continue
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, directory)
                if f.endswith('.py'): pyf.append((rel, full))
                elif f.endswith('.js'): jsf.append((rel, full))
        for rel, full in pyf:
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    c = f.read(5000)
                if sum(1 for i in ['infinity_polling','polling()','bot.polling','app.run(','if __name__','telebot.TeleBot','Bot(token'] if i in c) >= 2:
                    return rel, 'py', 'medium'
            except: pass
        for rel, full in jsf:
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    c = f.read(5000)
                if sum(1 for i in ['require(','app.listen','bot.launch','client.login','express()'] if i in c) >= 2:
                    return rel, 'js', 'medium'
            except: pass
        if pyf: return pyf[0][0], 'py', 'low'
        if jsf: return jsf[0][0], 'js', 'low'
        return None, None, None

    @staticmethod
    def install_requirements(d, cid=None):
        r = os.path.join(d, 'requirements.txt')
        if os.path.exists(r):
            if cid:
                try: bot.send_message(cid, "📦 Installing requirements...", parse_mode='HTML')
                except: pass
            try: subprocess.run([sys.executable,'-m','pip','install','-r',r,'--quiet'], capture_output=True, text=True, timeout=300, cwd=d)
            except: pass
        return True

    @staticmethod
    def install_npm(d, cid=None):
        if os.path.exists(os.path.join(d,'package.json')) and not os.path.exists(os.path.join(d,'node_modules')):
            if cid:
                try: bot.send_message(cid, "📦 npm install...", parse_mode='HTML')
                except: pass
            try: subprocess.run(['npm','install','--production'], capture_output=True, text=True, timeout=300, cwd=d)
            except: pass
        return True

    @staticmethod
    def get_report(d):
        entry, ft, conf = EntryFileDetector.detect_entry_file(d)
        if not entry: return None, None, "❌ No runnable file!"
        ci = {'exact':'🎯 Exact','high':'✅ High','medium':'🟡 Medium','low':'⚠️ Low'}
        ti = {'py':'🐍 Python','js':'🟨 Node.js'}
        return entry, ft, f"📄 <b>Entry:</b> <code>{entry}</code>\n🔤 <b>Type:</b> {ti.get(ft,ft)}\n🎯 <b>Conf:</b> {ci.get(conf,conf)}"

detector = EntryFileDetector()

# ═══════════════════════════════════════════════════
#  ANIMATIONS
# ═══════════════════════════════════════════════════
def send_animated_message(cid, final, atype="loading", dur=2, steps=4):
    try:
        am = {"loading":"Authenticating","upload":"Uploading","run":"Starting script","stop":"Stopping","install":"Installing","payment":"Processing"}
        at = am.get(atype, "Processing")
        msg = None
        for i in range(steps+1):
            pct = int((i/steps)*100)
            bar = "🟩"*i + "⬜"*(steps-i)
            d = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({pct}%)\n[{bar}] {at}..."
            if i == 0: msg = bot.send_message(cid, d)
            else:
                try: bot.edit_message_text(d, cid, msg.message_id)
                except: pass
            time.sleep(dur/steps)
        try: bot.edit_message_text(final, cid, msg.message_id, parse_mode='HTML')
        except: msg = bot.send_message(cid, final, parse_mode='HTML')
        return msg
    except: return bot.send_message(cid, final, parse_mode='HTML')

def send_progress(cid, text, steps=4):
    try:
        msg = None
        for i in range(steps+1):
            pct = int((i/steps)*100)
            bar = "🟩"*i + "⬜"*(steps-i)
            d = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({pct}%)\n[{bar}] {text}..."
            if i == 0: msg = bot.send_message(cid, d)
            else:
                try: bot.edit_message_text(d, cid, msg.message_id)
                except: pass
            time.sleep(0.4)
        return msg
    except: return None

# ═══════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════
def get_uptime():
    u = datetime.now() - bot_start_time
    h, r = divmod(u.seconds, 3600)
    m, s = divmod(r, 60)
    return f"{u.days}d {h}h {m}m {s}s"

def format_size(b):
    for u in ['B','KB','MB','GB','TB']:
        if b < 1024: return f"{b:.2f} {u}"
        b /= 1024
    return f"{b:.2f} PB"

def mini_bar(p, l=20):
    f = int((p/100)*l)
    return f"[{'█'*f}{'░'*(l-f)}]"

def generate_referral_code(uid):
    uid = int(uid)
    chars = string.digits + string.ascii_uppercase
    enc = ''
    t = uid
    if t == 0: enc = '0'
    else:
        while t > 0:
            enc = chars[t%36] + enc
            t //= 36
    salt = hashlib.md5(f"{uid}_exu_hosting".encode()).hexdigest()[:2].upper()
    return f"EXU{enc}{salt}"

def time_remaining(e):
    if not e: return "♾️ Lifetime"
    try:
        end = datetime.fromisoformat(e)
        if end <= datetime.now(): return "❌ Expired"
        d = end - datetime.now()
        return f"{d.days}d {d.seconds//3600}h"
    except: return "?"

def get_user_folder(uid):
    f = os.path.join(UPLOAD_BOTS_DIR, str(uid))
    os.makedirs(f, exist_ok=True)
    return f

def is_running(sk):
    i = bot_scripts.get(sk)
    if i and i.get('process'):
        try:
            p = psutil.Process(i['process'].pid)
            return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except: return False
    return False

def is_bot_running(uid, name): return is_running(f"{uid}_{name}")

def cleanup(sk):
    if sk in bot_scripts:
        i = bot_scripts[sk]
        try:
            if 'log_file' in i and hasattr(i['log_file'],'close') and not i['log_file'].closed:
                i['log_file'].close()
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
                parent = psutil.Process(p.pid)
                ch = parent.children(recursive=True)
                for c in ch:
                    try: c.terminate()
                    except: pass
                psutil.wait_procs(ch, timeout=3)
                for c in ch:
                    try: c.kill()
                    except: pass
                try:
                    parent.terminate()
                    parent.wait(timeout=3)
                except psutil.TimeoutExpired: parent.kill()
                except psutil.NoSuchProcess: pass
            except psutil.NoSuchProcess: pass
    except: pass

def sys_stats():
    try:
        c = psutil.cpu_percent(interval=1)
        m = psutil.virtual_memory()
        d = psutil.disk_usage('/')
        return {'cpu':c,'mem':m.percent,'disk':round(d.used/d.total*100,1),'uptime':get_uptime()}
    except: return {'cpu':0,'mem':0,'disk':0,'uptime':get_uptime()}

# ═══════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════
class DB:
    _lock = threading.Lock()
    def __init__(self):
        self.path = DATABASE_PATH
        self._init()
    def _conn(self):
        c = sqlite3.connect(self.path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        return c
    def exe(self, q, p=(), fetch=False, one=False):
        with self._lock:
            c = self._conn()
            cur = c.cursor()
            try:
                cur.execute(q, p)
                if fetch:
                    r = [dict(x) for x in cur.fetchall()]; c.close(); return r
                if one:
                    x = cur.fetchone(); c.close(); return dict(x) if x else None
                c.commit(); lid = cur.lastrowid; c.close(); return lid
            except Exception as e: c.close(); logger.error(f"DB: {e}"); return None
    def _init(self):
        self.exe("""CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT DEFAULT'',full_name TEXT DEFAULT'',language TEXT DEFAULT'en',plan TEXT DEFAULT'free',subscription_end TEXT,is_lifetime INTEGER DEFAULT 0,is_banned INTEGER DEFAULT 0,ban_reason TEXT DEFAULT'',wallet_balance REAL DEFAULT 0.0,referral_code TEXT UNIQUE,referred_by INTEGER,referral_count INTEGER DEFAULT 0,referral_level TEXT DEFAULT'bronze',referral_earnings REAL DEFAULT 0.0,created_at TEXT DEFAULT(datetime('now')),last_active TEXT DEFAULT(datetime('now')))""")
        self.exe("""CREATE TABLE IF NOT EXISTS bots(bot_id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,bot_name TEXT NOT NULL,bot_token TEXT DEFAULT'',file_path TEXT NOT NULL,entry_file TEXT DEFAULT'main.py',file_type TEXT DEFAULT'py',status TEXT DEFAULT'stopped',pid INTEGER,restarts_today INTEGER DEFAULT 0,total_restarts INTEGER DEFAULT 0,auto_restart INTEGER DEFAULT 1,last_started TEXT,last_stopped TEXT,last_crash TEXT,error_log TEXT DEFAULT'',file_size INTEGER DEFAULT 0,detection_confidence TEXT DEFAULT'',created_at TEXT DEFAULT(datetime('now')))""")
        self.exe("""CREATE TABLE IF NOT EXISTS payments(payment_id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,amount REAL NOT NULL,method TEXT NOT NULL,transaction_id TEXT NOT NULL,plan TEXT NOT NULL,duration_days INTEGER DEFAULT 30,status TEXT DEFAULT'pending',approved_by INTEGER,created_at TEXT DEFAULT(datetime('now')),processed_at TEXT)""")
        self.exe("""CREATE TABLE IF NOT EXISTS referrals(ref_id INTEGER PRIMARY KEY AUTOINCREMENT,referrer_id INTEGER NOT NULL,referred_id INTEGER NOT NULL,bonus_days INTEGER DEFAULT 0,commission REAL DEFAULT 0,created_at TEXT DEFAULT(datetime('now')))""")
        self.exe("""CREATE TABLE IF NOT EXISTS wallet_tx(tx_id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,amount REAL NOT NULL,tx_type TEXT NOT NULL,description TEXT DEFAULT'',created_at TEXT DEFAULT(datetime('now')))""")
        self.exe("""CREATE TABLE IF NOT EXISTS admin_logs(log_id INTEGER PRIMARY KEY AUTOINCREMENT,admin_id INTEGER NOT NULL,action TEXT NOT NULL,target_user INTEGER,details TEXT DEFAULT'',created_at TEXT DEFAULT(datetime('now')))""")
        logger.info("✅ DB ready")
    def get_user(self, uid): return self.exe("SELECT*FROM users WHERE user_id=?",(uid,),one=True)
    def create_user(self, uid, un='', fn='', rc='', rb=None): self.exe("INSERT OR IGNORE INTO users(user_id,username,full_name,referral_code,referred_by)VALUES(?,?,?,?,?)",(uid,un,fn,rc,rb))
    def update_user(self, uid, **kw):
        if not kw: return
        self.exe(f"UPDATE users SET {','.join(f'{k}=?' for k in kw)} WHERE user_id=?", list(kw.values())+[uid])
    def get_all_users(self): return self.exe("SELECT*FROM users",fetch=True) or []
    def ban(self, uid, r=''): self.update_user(uid, is_banned=1, ban_reason=r)
    def unban(self, uid): self.update_user(uid, is_banned=0, ban_reason='')
    def set_sub(self, uid, plan, days=30):
        if plan=='lifetime': self.update_user(uid, plan=plan, is_lifetime=1, subscription_end=None)
        else: self.update_user(uid, plan=plan, is_lifetime=0, subscription_end=(datetime.now()+timedelta(days=days)).isoformat())
    def rem_sub(self, uid): self.update_user(uid, plan='free', is_lifetime=0, subscription_end=None)
    def is_active(self, uid):
        u = self.get_user(uid)
        if not u: return False
        if u['is_lifetime'] or u['plan']=='free': return True
        if u['subscription_end']:
            try: return datetime.fromisoformat(u['subscription_end'])>datetime.now()
            except: return False
        return False
    def get_plan(self, uid):
        u = self.get_user(uid)
        if not u: return PLAN_LIMITS['free']
        if uid==OWNER_ID or uid in admin_ids: return PLAN_LIMITS['lifetime']
        return PLAN_LIMITS.get(u['plan'], PLAN_LIMITS['free'])
    def add_bot(self, uid, name, path, entry='main.py', ft='py', tok='', sz=0, conf=''):
        return self.exe("INSERT INTO bots(user_id,bot_name,file_path,entry_file,file_type,bot_token,file_size,detection_confidence)VALUES(?,?,?,?,?,?,?,?)",(uid,name,path,entry,ft,tok,sz,conf))
    def get_bots(self, uid): return self.exe("SELECT*FROM bots WHERE user_id=?",(uid,),fetch=True) or []
    def get_bot(self, bid): return self.exe("SELECT*FROM bots WHERE bot_id=?",(bid,),one=True)
    def update_bot(self, bid, **kw):
        if not kw: return
        self.exe(f"UPDATE bots SET {','.join(f'{k}=?' for k in kw)} WHERE bot_id=?", list(kw.values())+[bid])
    def del_bot(self, bid): self.exe("DELETE FROM bots WHERE bot_id=?",(bid,))
    def bot_count(self, uid): return (self.exe("SELECT COUNT(*)as c FROM bots WHERE user_id=?",(uid,),one=True) or {}).get('c',0)
    def add_pay(self, uid, amt, method, trx, plan, days=30):
        return self.exe("INSERT INTO payments(user_id,amount,method,transaction_id,plan,duration_days)VALUES(?,?,?,?,?,?)",(uid,amt,method,trx,plan,days))
    def pending_pay(self): return self.exe("SELECT*FROM payments WHERE status='pending' ORDER BY created_at DESC",fetch=True) or []
    def get_pay(self, pid): return self.exe("SELECT*FROM payments WHERE payment_id=?",(pid,),one=True)
    def approve_pay(self, pid, aid):
        p = self.get_pay(pid)
        if not p: return None
        self.exe("UPDATE payments SET status='approved',approved_by=?,processed_at=datetime('now')WHERE payment_id=?",(aid,pid))
        self.set_sub(p['user_id'], p['plan'], p['duration_days'])
        return p
    def reject_pay(self, pid, aid): self.exe("UPDATE payments SET status='rejected',approved_by=?,processed_at=datetime('now')WHERE payment_id=?",(aid,pid))
    def add_ref(self, rr, rd, days=3, comm=20):
        self.exe("INSERT INTO referrals(referrer_id,referred_id,bonus_days,commission)VALUES(?,?,?,?)",(rr,rd,days,comm))
        u = self.get_user(rr)
        if u:
            nc = u['referral_count']+1
            lv = 'gold' if nc>=50 else 'silver' if nc>=10 else 'bronze'
            self.update_user(rr, referral_count=nc, referral_earnings=u['referral_earnings']+comm, wallet_balance=u['wallet_balance']+comm, referral_level=lv)
    def ref_board(self, lim=10): return self.exe("SELECT*FROM users ORDER BY referral_count DESC LIMIT ?",(lim,),fetch=True) or []
    def user_refs(self, uid): return self.exe("SELECT*FROM referrals WHERE referrer_id=?",(uid,),fetch=True) or []
    def wallet_tx(self, uid, amt, tt, desc=''):
        self.exe("INSERT INTO wallet_tx(user_id,amount,tx_type,description)VALUES(?,?,?,?)",(uid,amt,tt,desc))
        if tt in ('credit','referral','refund'): self.exe("UPDATE users SET wallet_balance=wallet_balance+? WHERE user_id=?",(amt,uid))
        elif tt in ('debit','withdraw','purchase'): self.exe("UPDATE users SET wallet_balance=wallet_balance-? WHERE user_id=?",(amt,uid))
    def wallet_hist(self, uid, lim=20): return self.exe("SELECT*FROM wallet_tx WHERE user_id=? ORDER BY created_at DESC LIMIT ?",(uid,lim),fetch=True) or []
    def add_promo(self, code, disc=0, days=0, mx=-1, by=None): self.exe("INSERT OR IGNORE INTO promo_codes(code,discount_pct,bonus_days,max_uses,created_by)VALUES(?,?,?,?,?)",(code.upper(),disc,days,mx,by))
    def admin_log(self, aid, act, tgt=None, det=''): self.exe("INSERT INTO admin_logs(admin_id,action,target_user,details)VALUES(?,?,?,?)",(aid,act,tgt,det))
    def stats(self):
        tu = (self.exe("SELECT COUNT(*)as c FROM users",one=True) or {}).get('c',0)
        tb = (self.exe("SELECT COUNT(*)as c FROM bots",one=True) or {}).get('c',0)
        pp = (self.exe("SELECT COUNT(*)as c FROM payments WHERE status='pending'",one=True) or {}).get('c',0)
        rv = (self.exe("SELECT COALESCE(SUM(amount),0)as s FROM payments WHERE status='approved'",one=True) or {}).get('s',0)
        return {'users':tu,'bots':tb,'pending':pp,'revenue':rv}

db = DB()

# ═══════════════════════════════════════════════════
#  SCRIPT RUNNER
# ═══════════════════════════════════════════════════
def pip_install(mod, cid):
    pkg = TELEGRAM_MODULES.get(mod.split('.')[0].lower(), mod)
    try:
        msg = send_progress(cid, f"Installing {pkg}", 4)
        r = subprocess.run([sys.executable,'-m','pip','install',pkg,'--quiet'], capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            try: bot.edit_message_text(f"✅ <code>{pkg}</code>", cid, msg.message_id, parse_mode='HTML')
            except: pass
            return True
    except: pass
    return False

def run_bot(bid, cid, att=1):
    if att > 3:
        bot.send_message(cid, "❌ Failed 3 attempts. Check code!")
        return
    bd = db.get_bot(bid)
    if not bd: return bot.send_message(cid, "❌ Not found!")
    uid, bn, fp, ef, ft = bd['user_id'], bd['bot_name'], bd['file_path'], bd['entry_file'], bd['file_type']
    sk = f"{uid}_{bn}"
    wd = fp if os.path.isdir(fp) else get_user_folder(uid)
    if att == 1:
        de, dt, dr = detector.get_report(wd)
        if de:
            ef, ft = de, dt or 'py'
            db.update_bot(bid, entry_file=ef, file_type=ft)
    fsp = os.path.join(wd, ef)
    if not os.path.exists(fsp):
        found = False
        for root, dirs, files in os.walk(wd):
            if os.path.basename(ef) in files:
                fsp = os.path.join(root, os.path.basename(ef))
                ef = os.path.relpath(fsp, wd)
                db.update_bot(bid, entry_file=ef)
                found = True
                break
        if not found:
            af = [os.path.relpath(os.path.join(r,f),wd) for r,d,fs in os.walk(wd) for f in fs if f.endswith(('.py','.js'))]
            bot.send_message(cid, f"❌ <code>{ef}</code> not found!\n\n" + "\n".join(f"• <code>{f}</code>" for f in af[:10]), parse_mode='HTML')
            return
    if att == 1:
        if ft == 'py': detector.install_requirements(wd, cid)
        else: detector.install_npm(wd, cid)
    msg = send_animated_message(cid, f"🚀 Starting <code>{ef[:25]}</code>...", "run", 2)
    try:
        lp = os.path.join(LOGS_DIR, f"{sk}.log")
        lf = open(lp, 'w', encoding='utf-8', errors='ignore')
        cmd = ['node', fsp] if ft == 'js' else [sys.executable, '-u', fsp]
        env = os.environ.copy()
        if bd.get('bot_token'): env['BOT_TOKEN'] = bd['bot_token']
        env['PYTHONUNBUFFERED'] = '1'
        proc = subprocess.Popen(cmd, cwd=wd, stdout=lf, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore', env=env, preexec_fn=os.setsid if os.name!='nt' else None)
        bot_scripts[sk] = {'process':proc,'file_name':bn,'bot_id':bid,'user_id':uid,'start_time':datetime.now(),'log_file':lf,'log_path':lp,'script_path':fsp,'work_dir':wd,'entry_file':ef,'type':ft,'attempt':att}
        time.sleep(5)
        if proc.poll() is None:
            time.sleep(3)
            if proc.poll() is None:
                ok = f"✅ <b>RUNNING!</b>\n📄 <code>{ef[:25]}</code>\n🆔 PID: {proc.pid}\n⏱️ {datetime.now().strftime('%H:%M:%S')}"
                db.update_bot(bid, status='running', pid=proc.pid, last_started=datetime.now().isoformat(), entry_file=ef, file_type=ft)
                try: bot.edit_message_text(ok, cid, msg.message_id, parse_mode='HTML')
                except: bot.send_message(cid, ok, parse_mode='HTML')
                return
        lf.close()
        err = ""
        try:
            with open(lp,'r',encoding='utf-8',errors='ignore') as f: err = f.read()[-2000:]
        except: pass
        m = re.search(r"ModuleNotFoundError: No module named '([^']+)'", err)
        if m:
            cleanup(sk)
            if pip_install(m.group(1).split('.')[0], cid):
                time.sleep(1); run_bot(bid, cid, att+1); return
        m = re.search(r"Cannot find module '([^']+)'", err)
        if m and not m.group(1).startswith('.'):
            cleanup(sk)
            try:
                subprocess.run(['npm','install',m.group(1)], cwd=wd, capture_output=True, timeout=60)
                time.sleep(1); run_bot(bid, cid, att+1); return
            except: pass
        if att == 1:
            for alt in ['app.py','main.py','bot.py','run.py','index.js','app.js','bot.js']:
                if os.path.exists(os.path.join(wd, alt)) and alt != ef:
                    cleanup(sk)
                    db.update_bot(bid, entry_file=alt, file_type='js' if alt.endswith('.js') else 'py')
                    run_bot(bid, cid, att+1); return
        et = f"❌ <b>CRASHED!</b>\n📄 <code>{ef[:25]}</code>\n<code>{err[-800:] if err.strip() else 'No output'}</code>"
        db.update_bot(bid, status='crashed', last_crash=datetime.now().isoformat(), error_log=err[-500:])
        try: bot.edit_message_text(et, cid, msg.message_id, parse_mode='HTML')
        except: bot.send_message(cid, et, parse_mode='HTML')
        cleanup(sk)
    except Exception as e:
        logger.error(f"Run: {e}", exc_info=True)
        bot.send_message(cid, f"❌ {str(e)[:200]}")
        cleanup(sk)

# ═══════════════════════════════════════════════════
#  BACKGROUND THREADS
# ═══════════════════════════════════════════════════
def monitor():
    while True:
        try:
            for sk in list(bot_scripts.keys()):
                i = bot_scripts.get(sk)
                if not i: continue
                if i.get('process') and i['process'].poll() is not None:
                    bid = i.get('bot_id')
                    if bid: db.update_bot(bid, status='crashed', last_crash=datetime.now().isoformat())
                    uid = i.get('user_id')
                    if uid and bid:
                        u = db.get_user(uid)
                        if u and db.is_active(uid):
                            pl = PLAN_LIMITS.get(u['plan'], PLAN_LIMITS['free'])
                            if pl.get('auto_restart') and i.get('attempt',1) < 3:
                                cleanup(sk); time.sleep(5)
                                threading.Thread(target=run_bot, args=(bid,uid,i.get('attempt',1)+1), daemon=True).start()
                                continue
                    cleanup(sk)
        except: pass
        time.sleep(30)

def backup():
    while True:
        try:
            time.sleep(86400)
            shutil.copy2(DATABASE_PATH, os.path.join(BACKUPS_DIR, f"bk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"))
            for old in sorted([f for f in os.listdir(BACKUPS_DIR) if f.startswith('bk_')], reverse=True)[10:]:
                os.remove(os.path.join(BACKUPS_DIR, old))
        except: pass

def expiry():
    while True:
        try:
            time.sleep(3600)
            for u in db.exe("SELECT*FROM users WHERE subscription_end<=? AND is_lifetime=0 AND plan!='free'",(datetime.now().isoformat(),),fetch=True) or []:
                uid = u['user_id']; db.rem_sub(uid)
                for b in db.get_bots(uid):
                    sk = f"{uid}_{b['bot_name']}"
                    if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup(sk)
                    db.update_bot(b['bot_id'], status='stopped')
                try: bot.send_message(uid, "⚠️ Sub expired! Bots stopped.")
                except: pass
        except: pass

# ═══════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════
def main_kb(uid):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.row("🤖 My Bots","📤 Deploy Bot"); m.row("💎 Subscription","💰 Wallet")
    m.row("🎁 Referral","📊 Statistics"); m.row("🟢 Running Bots","⚡ Speed")
    if uid==OWNER_ID or uid in admin_ids:
        m.row("👑 Admin","📢 Broadcast"); m.row("🔒 Lock","💳 Payments")
    m.row("⚙️ Settings","📞 Contact")
    return m

def bot_kb(bid, st, fn):
    m = types.InlineKeyboardMarkup(row_width=2)
    if st == 'running':
        m.add(types.InlineKeyboardButton("🛑 Stop",callback_data=f"stop:{bid}"), types.InlineKeyboardButton("🔄 Restart",callback_data=f"restart:{bid}"))
        m.add(types.InlineKeyboardButton("📋 Logs",callback_data=f"logs:{bid}"), types.InlineKeyboardButton("📊 Res",callback_data=f"res:{bid}"))
    else:
        m.add(types.InlineKeyboardButton("▶️ Start",callback_data=f"start:{bid}"), types.InlineKeyboardButton("🗑️ Del",callback_data=f"del:{bid}"))
        m.add(types.InlineKeyboardButton("📥 DL",callback_data=f"dl:{bid}"), types.InlineKeyboardButton("📋 Logs",callback_data=f"logs:{bid}"))
        m.add(types.InlineKeyboardButton("🔍 Re-detect",callback_data=f"redetect:{bid}"))
    m.add(types.InlineKeyboardButton("🔙 Back",callback_data="mybots"))
    return m

def plan_kb():
    m = types.InlineKeyboardMarkup(row_width=1)
    for k,p in PLAN_LIMITS.items():
        if k!='free': m.add(types.InlineKeyboardButton(f"{p['name']} — {p['price_bdt']} BDT",callback_data=f"plan:{k}"))
    m.add(types.InlineKeyboardButton("🔙 Back",callback_data="menu"))
    return m

def pay_kb(pk):
    m = types.InlineKeyboardMarkup(row_width=2)
    for k,v in PAYMENT_METHODS.items():
        m.add(types.InlineKeyboardButton(f"{v['icon']} {v['name']}",callback_data=f"pay:{pk}:{k}"))
    m.add(types.InlineKeyboardButton("💰 Wallet",callback_data=f"payw:{pk}"))
    m.add(types.InlineKeyboardButton("🔙 Back",callback_data="sub"))
    return m

def admin_kb():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👥 Users",callback_data="a_users"), types.InlineKeyboardButton("📊 Stats",callback_data="a_stats"))
    m.add(types.InlineKeyboardButton("💳 Pay",callback_data="a_pay"), types.InlineKeyboardButton("📢 BC",callback_data="a_bc"))
    m.add(types.InlineKeyboardButton("➕ Sub",callback_data="a_addsub"), types.InlineKeyboardButton("➖ Sub",callback_data="a_remsub"))
    m.add(types.InlineKeyboardButton("🚫 Ban",callback_data="a_ban"), types.InlineKeyboardButton("✅ Unban",callback_data="a_unban"))
    m.add(types.InlineKeyboardButton("🎟 Promo",callback_data="a_promo"), types.InlineKeyboardButton("🖥 Sys",callback_data="a_sys"))
    m.add(types.InlineKeyboardButton("🛑 StopAll",callback_data="a_stopall"), types.InlineKeyboardButton("💾 Backup",callback_data="a_backup"))
    m.add(types.InlineKeyboardButton("🔙 Back",callback_data="menu"))
    return m

def pay_approve_kb(pid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("✅",callback_data=f"appv:{pid}"), types.InlineKeyboardButton("❌",callback_data=f"rejt:{pid}"))
    return m
    
    # ═══════════════════════════════════════════════════
#  COMMANDS & HANDLERS
# ═══════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid = msg.from_user.id
    un = msg.from_user.username or ''
    fn = f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip()
    active_users.add(uid)
    ex = db.get_user(uid)
    if ex and ex['is_banned']: return bot.reply_to(msg, f"🚫 Banned: {ex.get('ban_reason','')}")
    if bot_locked and uid not in admin_ids and uid!=OWNER_ID: return bot.reply_to(msg, "🔒")
    is_new = ex is None
    ref_by = None
    args = msg.text.split()
    if len(args)>1:
        rc = args[1].strip()
        logger.info(f"📨 Ref code: '{rc}' from {uid}")
        rr = db.exe("SELECT user_id FROM users WHERE referral_code=?",(rc,),one=True)
        if rr and rr['user_id']!=uid and is_new:
            ref_by = rr['user_id']
            logger.info(f"✅ Ref: {uid} by {ref_by}")
    code = generate_referral_code(uid)
    if is_new:
        db.create_user(uid, un, fn, code, ref_by)
        if ref_by:
            db.add_ref(ref_by, uid, REFERRAL_BONUS_DAYS, REFERRAL_COMMISSION_BDT)
            try:
                rd = db.get_user(ref_by)
                bot.send_message(ref_by, f"🎉 <b>NEW REFERRAL!</b>\n👤 {fn} joined!\n💰 +{REFERRAL_COMMISSION_BDT} BDT\n👥 Total: {rd['referral_count'] if rd else '?'}", parse_mode='HTML')
            except: pass
    else:
        db.update_user(uid, username=un, full_name=fn, last_active=datetime.now().isoformat())
        if not ex.get('referral_code') or len(ex.get('referral_code',''))<5:
            db.update_user(uid, referral_code=code)
    u = db.get_user(uid)
    pl = PLAN_LIMITS.get(u['plan'],PLAN_LIMITS['free']) if u else PLAN_LIMITS['free']
    bc = db.bot_count(uid)
    mx = '♾️' if pl['max_bots']==-1 else str(pl['max_bots'])
    st = '👑 Owner' if uid==OWNER_ID else '⭐ Admin' if uid in admin_ids else pl['name']
    w = f"""
╔══════════════════════════════════════╗
║  🚀 <b>EXU HOSTING PRO X v2.4</b>           ║
╠══════════════════════════════════════╣
║  👋 <b>{fn}</b>
║  🆔 <code>{uid}</code> | 📦 {st}
║  🤖 {bc}/{mx} | 💰 {u['wallet_balance'] if u else 0} BDT
║  👥 {u['referral_count'] if u else 0} refs
║  🔑 <code>{u['referral_code'] if u else code}</code>
╚══════════════════════════════════════╝"""
    send_animated_message(msg.chat.id, w, "loading", 2)
    bot.send_message(msg.chat.id, "⬇️", reply_markup=main_kb(uid))

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(msg.chat.id, f"📚 <b>Help</b>\n📤 Upload ZIP/PY/JS\n🔍 Auto-detect entry\n💳 bKash/Nagad/Binance\n🎁 Referral earn\n👑 /admin\n📞 {YOUR_USERNAME}", parse_mode='HTML')

@bot.message_handler(commands=['admin'])
def cmd_adm(msg): show_admin(msg)

@bot.message_handler(commands=['subscribe'])
def cmd_sub(msg):
    if msg.from_user.id not in admin_ids and msg.from_user.id!=OWNER_ID: return
    p = msg.text.split()
    if len(p)<3: return bot.reply_to(msg, "/subscribe UID DAYS")
    try: db.set_sub(int(p[1]),'pro' if int(p[2])>0 else 'lifetime',int(p[2])); bot.reply_to(msg,"✅")
    except: bot.reply_to(msg,"❌")

@bot.message_handler(commands=['ban'])
def cmd_ban(msg):
    if msg.from_user.id not in admin_ids and msg.from_user.id!=OWNER_ID: return
    p = msg.text.split(maxsplit=2)
    if len(p)<2: return
    try: db.ban(int(p[1]),p[2] if len(p)>2 else "Banned"); bot.reply_to(msg,"🚫")
    except: pass

@bot.message_handler(commands=['unban'])
def cmd_unban(msg):
    if msg.from_user.id not in admin_ids and msg.from_user.id!=OWNER_ID: return
    try: db.unban(int(msg.text.split()[1])); bot.reply_to(msg,"✅")
    except: pass

@bot.message_handler(content_types=['text'])
def handle_text(msg):
    uid = msg.from_user.id; txt = msg.text; active_users.add(uid)
    u = db.get_user(uid)
    if u and u['is_banned']: return
    if bot_locked and uid not in admin_ids and uid!=OWNER_ID: return
    if uid in payment_states: return handle_pay_text(msg)
    if uid in user_states: return handle_state(msg)
    h = {"🤖 My Bots":show_bots,"📤 Deploy Bot":show_deploy,"💎 Subscription":show_sub,"💰 Wallet":show_wallet,
         "🎁 Referral":show_ref,"📊 Statistics":show_stats,"🟢 Running Bots":show_running,"⚡ Speed":show_speed,
         "👑 Admin":show_admin,"📢 Broadcast":do_bc,"🔒 Lock":do_lock,"💳 Payments":show_pays,"⚙️ Settings":show_set}
    if txt in h: h[txt](msg)
    elif txt=="📞 Contact": bot.send_message(uid, f"📞 {YOUR_USERNAME}\n📢 {UPDATE_CHANNEL}")
    else: bot.send_message(uid, "❓ Use buttons ⬇️", reply_markup=main_kb(uid))

def show_bots(msg):
    uid = msg.from_user.id
    pm = send_progress(msg.chat.id, "Loading", 4)
    bots = db.get_bots(uid); pl = db.get_plan(uid)
    mx = '♾️' if pl['max_bots']==-1 else str(pl['max_bots'])
    if not bots:
        try: bot.edit_message_text(f"📭 No bots! Slots: 0/{mx}", msg.chat.id, pm.message_id)
        except: bot.send_message(msg.chat.id, f"📭 No bots!")
        return
    run = sum(1 for b in bots if is_bot_running(uid, b['bot_name']))
    t = f"🤖 <b>Bots</b> ({len(bots)}) 🟢{run} 🔴{len(bots)-run}\n📦 {mx}\n\n"
    m = types.InlineKeyboardMarkup(row_width=1)
    for b in bots:
        r = is_bot_running(uid, b['bot_name'])
        t += f"{'🟢' if r else '🔴'} {'🐍' if b['file_type']=='py' else '🟨'} <code>{b['bot_name'][:20]}</code> #{b['bot_id']} — {b['entry_file']}\n"
        m.add(types.InlineKeyboardButton(f"{'🟢' if r else '🔴'} {b['bot_name'][:15]} #{b['bot_id']}", callback_data=f"detail:{b['bot_id']}"))
    m.add(types.InlineKeyboardButton("📤 Deploy", callback_data="deploy"))
    try: bot.edit_message_text(t, msg.chat.id, pm.message_id, parse_mode='HTML', reply_markup=m)
    except: bot.send_message(msg.chat.id, t, parse_mode='HTML', reply_markup=m)

def show_deploy(msg):
    uid = msg.from_user.id
    u = db.get_user(uid)
    if not u: return bot.reply_to(msg, "/start")
    pl = db.get_plan(uid); cur = db.bot_count(uid); mx = pl['max_bots']
    if mx!=-1 and cur>=mx: return bot.reply_to(msg, f"⚠️ Limit ({cur}/{mx})!")
    rem = '♾️' if mx==-1 else str(mx-cur)
    bot.send_message(msg.chat.id, f"📤 <b>Send file!</b>\n🐍 .py | 🟨 .js | 📦 .zip\n🔍 Auto-detect entry\n📦 Slots: {rem}", parse_mode='HTML')

@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    uid = msg.from_user.id; u = db.get_user(uid)
    if not u: return bot.reply_to(msg, "/start")
    pl = db.get_plan(uid); cur = db.bot_count(uid); mx = pl['max_bots']
    if mx!=-1 and cur>=mx: return bot.reply_to(msg, f"❌ Limit!")
    fn = msg.document.file_name; fs = msg.document.file_size
    ext = fn.rsplit('.',1)[-1].lower() if '.' in fn else ''
    if ext not in ['py','js','zip','json','txt','env','yml','yaml','cfg','ini']:
        return bot.reply_to(msg, f"❌ .{ext}")
    hdr = f"📤 <code>{fn[:25]}</code> ({format_size(fs)})\n"
    pm = bot.reply_to(msg, hdr+"⏳...", parse_mode='HTML')
    try:
        fi = bot.get_file(msg.document.file_id); dl = bot.download_file(fi.file_path)
        uf = get_user_folder(uid)
        if ext=='zip':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                tmp.write(dl); tp = tmp.name
            try:
                with zipfile.ZipFile(tp,'r') as z:
                    for n in z.namelist():
                        if n.startswith('/') or '..' in n:
                            bot.edit_message_text(hdr+"❌ Bad paths!", msg.chat.id, pm.message_id, parse_mode='HTML')
                            os.unlink(tp); return
                    bn = fn.replace('.zip',''); ed = os.path.join(uf, bn)
                    if os.path.exists(ed): shutil.rmtree(ed, ignore_errors=True)
                    os.makedirs(ed, exist_ok=True); z.extractall(ed)
                    items = os.listdir(ed)
                    if len(items)==1 and os.path.isdir(os.path.join(ed,items[0])):
                        inner = os.path.join(ed, items[0])
                        for it in os.listdir(inner):
                            s,d = os.path.join(inner,it), os.path.join(ed,it)
                            if os.path.exists(d): shutil.rmtree(d) if os.path.isdir(d) else os.remove(d)
                            shutil.move(s,d)
                        os.rmdir(inner)
                os.unlink(tp)
                entry, ft, report = detector.get_report(ed)
                if not entry:
                    af = [os.path.relpath(os.path.join(r,f),ed) for r,d,fs in os.walk(ed) for f in fs if f.endswith(('.py','.js'))]
                    bot.edit_message_text(hdr+"❌ No entry!\n"+"\n".join(f"• <code>{f}</code>" for f in af[:10]), msg.chat.id, pm.message_id, parse_mode='HTML')
                    return
                bid = db.add_bot(uid, bn, ed, entry, ft, '', fs, report.split('\n')[-1] if report else '')
                mk = types.InlineKeyboardMarkup(row_width=2)
                mk.add(types.InlineKeyboardButton("▶️ Start",callback_data=f"start:{bid}"), types.InlineKeyboardButton("🤖 Bots",callback_data="mybots"))
                bot.edit_message_text(hdr+f"✅ #{bid}\n{report}", msg.chat.id, pm.message_id, parse_mode='HTML', reply_markup=mk)
            except zipfile.BadZipFile:
                bot.edit_message_text(hdr+"❌ Bad ZIP!", msg.chat.id, pm.message_id, parse_mode='HTML')
                try: os.unlink(tp)
                except: pass
        elif ext in ['py','js']:
            with open(os.path.join(uf,fn),'wb') as f: f.write(dl)
            bid = db.add_bot(uid, fn, uf, fn, ext, '', fs, 'exact')
            mk = types.InlineKeyboardMarkup(row_width=2)
            mk.add(types.InlineKeyboardButton("▶️ Run",callback_data=f"start:{bid}"), types.InlineKeyboardButton("🤖 Bots",callback_data="mybots"))
            bot.edit_message_text(hdr+f"✅ #{bid}", msg.chat.id, pm.message_id, parse_mode='HTML', reply_markup=mk)
        else:
            with open(os.path.join(uf,fn),'wb') as f: f.write(dl)
            bot.edit_message_text(hdr+"✅ Saved!", msg.chat.id, pm.message_id, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Upload: {e}", exc_info=True)
        try: bot.edit_message_text(hdr+f"❌ {str(e)[:50]}", msg.chat.id, pm.message_id, parse_mode='HTML')
        except: pass

def show_sub(msg):
    u = db.get_user(msg.from_user.id)
    if not u: return
    pl = PLAN_LIMITS.get(u['plan'],PLAN_LIMITS['free'])
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📋 Upgrade",callback_data="plans"))
    bot.send_message(msg.from_user.id, f"💎 {pl['name']}\n📅 {time_remaining(u['subscription_end'])}\n🤖 {'♾️' if pl['max_bots']==-1 else pl['max_bots']} | 💾 {pl['ram_mb']}MB", parse_mode='HTML', reply_markup=m)

def show_wallet(msg):
    u = db.get_user(msg.from_user.id)
    if not u: return
    h = db.wallet_hist(msg.from_user.id, 5)
    t = f"💰 <b>{u['wallet_balance']} BDT</b>\n"
    for x in h: t += f"\n{'➕' if x['tx_type'] in ('credit','referral') else '➖'} {x['amount']} — {x['description'][:20]}"
    bot.send_message(msg.from_user.id, t, parse_mode='HTML')

def show_ref(msg):
    uid = msg.from_user.id; u = db.get_user(uid)
    if not u: return bot.reply_to(msg, "/start")
    rc = u.get('referral_code')
    if not rc or len(rc)<5:
        rc = generate_referral_code(uid); db.update_user(uid, referral_code=rc); u = db.get_user(uid); rc = u['referral_code']
    lnk = f"https://t.me/{BOT_USERNAME}?start={rc}"
    ic = {'bronze':'🥉','silver':'🥈','gold':'🥇'}
    t = f"""
╔══════════════════════════════════════╗
║       🎁 <b>REFERRAL</b>                      ║
╠══════════════════════════════════════╣
║  🔑 <code>{rc}</code>
║  🔗 <code>{lnk}</code>
║  👥 {u['referral_count']} | {ic.get(u['referral_level'],'🥉')} {u['referral_level'].title()}
║  💰 {u['referral_earnings']} BDT earned
║  Reward: {REFERRAL_COMMISSION_BDT} BDT + {REFERRAL_BONUS_DAYS}d
╚══════════════════════════════════════╝"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📋 Copy",callback_data=f"cpref:{rc}"),
          types.InlineKeyboardButton("🏆 Board",callback_data="board"),
          types.InlineKeyboardButton("📋 My Refs",callback_data="myrefs"),
          types.InlineKeyboardButton("📤 Share",switch_inline_query=f"🚀 Join EXU Hosting!\n{lnk}"))
    bot.send_message(uid, t, parse_mode='HTML', reply_markup=m)

def show_stats(msg):
    pm = send_progress(msg.chat.id, "Stats", 4)
    s = db.stats(); ss = sys_stats(); rn = len([k for k in bot_scripts if is_running(k)])
    t = f"📊 CPU:{ss['cpu']}% {mini_bar(ss['cpu'])}\n🧠 RAM:{ss['mem']}% {mini_bar(ss['mem'])}\n💾 Disk:{ss['disk']}%\n⏱️ {ss['uptime']}\n🤖 {rn} running | 👥 {s['users']} | 💰 {s['revenue']} BDT"
    try: bot.edit_message_text(t, msg.chat.id, pm.message_id, parse_mode='HTML')
    except: pass

def show_running(msg):
    uid = msg.from_user.id; pm = send_progress(msg.chat.id, "Bots", 4)
    r = []
    for sk,i in bot_scripts.items():
        if is_running(sk) and (uid==OWNER_ID or uid in admin_ids or i.get('user_id')==uid):
            up = str(datetime.now()-i.get('start_time',datetime.now())).split('.')[0]
            r.append(f"📄 <code>{i.get('file_name','?')[:20]}</code> PID:{i['process'].pid} ⏱️{up}")
    t = f"🟢 <b>{len(r)}</b>\n\n"+"\n".join(r) if r else "🔴 None"
    try: bot.edit_message_text(t, msg.chat.id, pm.message_id, parse_mode='HTML')
    except: pass

def show_speed(msg):
    pm = send_progress(msg.chat.id, "Test", 4)
    t = f"⚡ CPU:{psutil.cpu_percent()}% RAM:{psutil.virtual_memory().percent}% ⏱️{get_uptime()}"
    try: bot.edit_message_text(t, msg.chat.id, pm.message_id, parse_mode='HTML')
    except: pass

def show_set(msg):
    u = db.get_user(msg.from_user.id)
    if not u: return
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🇺🇸 EN",callback_data="lang:en"), types.InlineKeyboardButton("🇧🇩 বাংলা",callback_data="lang:bn"))
    bot.send_message(msg.from_user.id, f"⚙️ {u['full_name']}\n🆔 <code>{msg.from_user.id}</code>", parse_mode='HTML', reply_markup=m)

def show_admin(msg):
    uid = msg.from_user.id
    if uid!=OWNER_ID and uid not in admin_ids: return bot.reply_to(msg, "❌")
    s = db.stats(); rn = len([k for k in bot_scripts if is_running(k)])
    bot.send_message(uid, f"👑 👥{s['users']} 🤖{rn} 💳{s['pending']} 💰{s['revenue']}BDT", parse_mode='HTML', reply_markup=admin_kb())

def do_bc(msg):
    if msg.from_user.id not in admin_ids and msg.from_user.id!=OWNER_ID: return
    user_states[msg.from_user.id] = {'action':'broadcast'}
    bot.reply_to(msg, "📢 Send message:")

def do_lock(msg):
    global bot_locked
    if msg.from_user.id not in admin_ids and msg.from_user.id!=OWNER_ID: return
    bot_locked = not bot_locked
    bot.reply_to(msg, f"{'🔒' if bot_locked else '🔓'}")

def show_pays(msg):
    uid = msg.from_user.id
    if uid not in admin_ids and uid!=OWNER_ID: return
    pays = db.pending_pay()
    if not pays: return bot.send_message(uid, "💳 None!")
    t = f"💳 <b>{len(pays)}</b>\n\n"
    m = types.InlineKeyboardMarkup(row_width=2)
    for p in pays[:10]:
        u = db.get_user(p['user_id'])
        t += f"#{p['payment_id']} {u['full_name'] if u else p['user_id']}\n💰{p['amount']} {p['method']} TRX:{p['transaction_id']}\n\n"
        m.add(types.InlineKeyboardButton(f"✅#{p['payment_id']}",callback_data=f"appv:{p['payment_id']}"),
              types.InlineKeyboardButton(f"❌#{p['payment_id']}",callback_data=f"rejt:{p['payment_id']}"))
    bot.send_message(uid, t, parse_mode='HTML', reply_markup=m)

def handle_state(msg):
    uid = msg.from_user.id; s = user_states.get(uid)
    if not s: return
    a = s.get('action')
    if a=='broadcast':
        users = db.get_all_users(); sent=fail=0
        for u in users:
            try: bot.send_message(u['user_id'],f"📢 <b>Broadcast</b>\n\n{msg.text}",parse_mode='HTML'); sent+=1
            except: fail+=1
        bot.reply_to(msg, f"✅{sent} ❌{fail}")
    elif a=='a_addsub' and s.get('step',1)==1:
        try:
            tgt = int(msg.text.strip()); user_states[uid] = {'action':'a_addsub','step':2,'target':tgt}
            m = types.InlineKeyboardMarkup(row_width=2)
            for k,p in PLAN_LIMITS.items():
                if k!='free': m.add(types.InlineKeyboardButton(p['name'],callback_data=f"asub:{k}:{tgt}"))
            bot.reply_to(msg, f"<code>{tgt}</code> Plan?", parse_mode='HTML', reply_markup=m); return
        except: bot.reply_to(msg,"❌")
    elif a=='a_addsub_days':
        try:
            d = int(msg.text.strip()); db.set_sub(s['target'], s['plan'] if d>0 else 'lifetime', d)
            bot.reply_to(msg, f"✅ {'Lifetime' if d==0 else f'{d}d'}")
            try: bot.send_message(s['target'], "🎉 Upgraded!")
            except: pass
        except: bot.reply_to(msg,"❌")
    elif a=='a_remsub':
        try: db.rem_sub(int(msg.text.strip())); bot.reply_to(msg,"✅")
        except: bot.reply_to(msg,"❌")
    elif a=='a_ban':
        p = msg.text.strip().split(maxsplit=1)
        try: db.ban(int(p[0]),p[1] if len(p)>1 else "Banned"); bot.reply_to(msg,"🚫")
        except: bot.reply_to(msg,"❌")
    elif a=='a_unban':
        try: db.unban(int(msg.text.strip())); bot.reply_to(msg,"✅")
        except: bot.reply_to(msg,"❌")
    elif a=='a_promo':
        p = msg.text.strip().split()
        if len(p)>=3:
            try: db.add_promo(p[0].upper(),int(p[1]),0,int(p[2]),uid); bot.reply_to(msg,f"✅ <code>{p[0].upper()}</code>",parse_mode='HTML')
            except: bot.reply_to(msg,"❌")
        else: bot.reply_to(msg,"❌")
    user_states.pop(uid, None)

def handle_pay_text(msg):
    uid = msg.from_user.id; s = payment_states.get(uid)
    if not s or s.get('step')!='wait_trx': return
    trx = msg.text.strip() if msg.text else 'SS'
    pid = db.add_pay(uid, s['amount'], s['method'], trx, s['plan'], 30)
    payment_states.pop(uid, None)
    bot.send_message(uid, f"✅ #{pid} submitted! ⏳")
    u = db.get_user(uid)
    for aid in admin_ids:
        try: bot.send_message(aid, f"💳 <b>Payment!</b>\n👤 {u['full_name']} (<code>{uid}</code>)\n📦 {s['plan']} 💰{s['amount']}BDT {s['method']}\nTRX:<code>{trx}</code> #{pid}", parse_mode='HTML', reply_markup=pay_approve_kb(pid))
        except: pass

# ═══════════════════════════════════════════════════
#  CALLBACKS
# ═══════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id; d = call.data
    try:
        if d=="menu":
            bot.answer_callback_query(call.id)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(uid, "🏠", reply_markup=main_kb(uid))
        elif d=="mybots":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s,c): s.chat=c.message.chat; s.from_user=c.from_user
            show_bots(M(call))
        elif d.startswith("detail:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return bot.answer_callback_query(call.id,"!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"; rn = is_running(sk)
            ram=cpu=0
            if rn and sk in bot_scripts:
                try: p=psutil.Process(bot_scripts[sk]['process'].pid); ram=round(p.memory_info().rss/(1024**2),1); cpu=round(p.cpu_percent(0.1),1)
                except: pass
            t = f"{'🐍' if bd['file_type']=='py' else '🟨'} <b>{bd['bot_name'][:20]}</b> #{bid}\n📄 <code>{bd['entry_file']}</code>\n{'🟢' if rn else '🔴'} 💾{ram}MB ⚡{cpu}%"
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=bot_kb(bid,'running' if rn else 'stopped',bd['bot_name']))
            except: pass
            bot.answer_callback_query(call.id)
        elif d.startswith("start:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return bot.answer_callback_query(call.id,"!")
            if not db.is_active(bd['user_id']): return bot.answer_callback_query(call.id,"⚠️ Expired!",show_alert=True)
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if is_running(sk): return bot.answer_callback_query(call.id,"Already running!")
            bot.answer_callback_query(call.id,"🚀")
            threading.Thread(target=run_bot,args=(bid,call.message.chat.id),daemon=True).start()
        elif d.startswith("stop:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return bot.answer_callback_query(call.id,"!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup(sk)
            db.update_bot(bid, status='stopped', last_stopped=datetime.now().isoformat())
            bot.answer_callback_query(call.id,"✅"); call.data=f"detail:{bid}"; cb(call)
        elif d.startswith("restart:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return bot.answer_callback_query(call.id,"!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"
            if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup(sk)
            time.sleep(2); bot.answer_callback_query(call.id,"🔄")
            threading.Thread(target=run_bot,args=(bid,call.message.chat.id),daemon=True).start()
        elif d.startswith("logs:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return bot.answer_callback_query(call.id,"!")
            sk = f"{bd['user_id']}_{bd['bot_name']}"; lp = os.path.join(LOGS_DIR,f"{sk}.log")
            logs = "No logs."
            if os.path.exists(lp):
                with open(lp,'r',encoding='utf-8',errors='ignore') as f: logs = f.read()[-1500:] or "Empty"
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔄",callback_data=f"logs:{bid}"), types.InlineKeyboardButton("🔙",callback_data=f"detail:{bid}"))
            try: bot.edit_message_text(f"📋 #{bid}\n<code>{logs}</code>"[:4000], call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)
        elif d.startswith("res:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return
            sk = f"{bd['user_id']}_{bd['bot_name']}"; ram=cpu=0
            if sk in bot_scripts:
                try: p=psutil.Process(bot_scripts[sk]['process'].pid); ram=round(p.memory_info().rss/(1024**2),1); cpu=round(p.cpu_percent(0.5),1)
                except: pass
            m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("🔙",callback_data=f"detail:{bid}"))
            try: bot.edit_message_text(f"📊 #{bid} 💾{ram}MB ⚡{cpu}%", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)
        elif d.startswith("redetect:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return bot.answer_callback_query(call.id,"!")
            wd = bd['file_path'] if os.path.isdir(bd['file_path']) else get_user_folder(bd['user_id'])
            e,ft,rp = detector.get_report(wd)
            if e:
                db.update_bot(bid, entry_file=e, file_type=ft)
                m = types.InlineKeyboardMarkup()
                m.add(types.InlineKeyboardButton("▶️",callback_data=f"start:{bid}"), types.InlineKeyboardButton("🔙",callback_data=f"detail:{bid}"))
                try: bot.edit_message_text(f"🔍\n{rp}\n✅ Updated!", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
                except: pass
            else:
                af = [os.path.relpath(os.path.join(r,f),wd) for r,d,fs in os.walk(wd) for f in fs if f.endswith(('.py','.js'))]
                m = types.InlineKeyboardMarkup(row_width=1)
                for f in af[:10]:
                    m.add(types.InlineKeyboardButton(f"📄 {f}",callback_data=f"setentry:{bid}:{f}:{'js' if f.endswith('.js') else 'py'}"))
                m.add(types.InlineKeyboardButton("🔙",callback_data=f"detail:{bid}"))
                try: bot.edit_message_text("🔍 ❌\n"+"\n".join(f"• <code>{f}</code>" for f in af[:10]), call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
                except: pass
            bot.answer_callback_query(call.id)
        elif d.startswith("setentry:"):
            p = d.split(":"); db.update_bot(int(p[1]), entry_file=p[2], file_type=p[3])
            bot.answer_callback_query(call.id,f"✅ {p[2]}"); call.data=f"detail:{p[1]}"; cb(call)
        elif d.startswith("del:"):
            bid = int(d.split(":")[1])
            m = types.InlineKeyboardMarkup(row_width=2)
            m.add(types.InlineKeyboardButton("✅",callback_data=f"cdel:{bid}"), types.InlineKeyboardButton("❌",callback_data=f"detail:{bid}"))
            try: bot.edit_message_text(f"🗑 #{bid}?", call.message.chat.id, call.message.message_id, reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)
        elif d.startswith("cdel:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if bd:
                sk = f"{bd['user_id']}_{bd['bot_name']}"
                if sk in bot_scripts: kill_tree(bot_scripts[sk]); cleanup(sk)
                if os.path.isdir(bd['file_path']): shutil.rmtree(bd['file_path'],ignore_errors=True)
                else:
                    try: os.remove(os.path.join(get_user_folder(bd['user_id']),bd['bot_name']))
                    except: pass
                db.del_bot(bid)
            bot.answer_callback_query(call.id,"✅"); call.data="mybots"; cb(call)
        elif d.startswith("dl:"):
            bid = int(d.split(":")[1]); bd = db.get_bot(bid)
            if not bd: return
            fp = os.path.join(bd['file_path'],bd['entry_file']) if os.path.isdir(bd['file_path']) else os.path.join(get_user_folder(bd['user_id']),bd['bot_name'])
            if os.path.exists(fp):
                with open(fp,'rb') as f: bot.send_document(uid,f,caption=f"📄 {bd['bot_name']}")
            bot.answer_callback_query(call.id,"📥")
        elif d=="deploy":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s,c): s.chat=c.message.chat; s.from_user=c.from_user
            show_deploy(M(call))
        elif d.startswith("cpref:"):
            rc = d.split(":",1)[1]; bot.answer_callback_query(call.id)
            bot.send_message(uid, f"📋\n\n<code>https://t.me/{BOT_USERNAME}?start={rc}</code>\n\n👆 Tap!", parse_mode='HTML')
        elif d=="myrefs":
            refs = db.user_refs(uid)
            t = f"📋 <b>Refs ({len(refs)})</b>\n\n"
            for r in refs[:20]:
                ru = db.get_user(r['referred_id']); t += f"👤 {ru['full_name'] if ru else r['referred_id']} +{r['commission']}BDT\n"
            if not refs: t += "None yet!"
            m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("🔙",callback_data="menu"))
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: bot.send_message(uid, t, parse_mode='HTML')
            bot.answer_callback_query(call.id)
        elif d=="board":
            lb = db.ref_board(10); t = "🏆 <b>Board</b>\n\n"
            md = ['🥇','🥈','🥉']
            for i,l in enumerate(lb): t += f"{md[i] if i<3 else f'#{i+1}'} {l['full_name'] or '?'} — {l['referral_count']}\n"
            if not lb: t += "None!"
            m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("🔙",callback_data="menu"))
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            except: pass
            bot.answer_callback_query(call.id)
        elif d in ("plans","sub"):
            t = "📋 <b>Plans:</b>\n\n"
            for k,p in PLAN_LIMITS.items():
                if k!='free': t += f"{p['name']}\n🤖{p['max_bots']} 💾{p['ram_mb']}MB 💰{p['price_bdt']}BDT\n\n"
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=plan_kb())
            except: bot.send_message(uid, t, parse_mode='HTML', reply_markup=plan_kb())
            bot.answer_callback_query(call.id)
        elif d.startswith("plan:"):
            pk = d.split(":")[1]; p = PLAN_LIMITS.get(pk)
            if not p: return
            try: bot.edit_message_text(f"{p['name']}\n🤖{'♾️' if p['max_bots']==-1 else p['max_bots']} 💾{p['ram_mb']}MB\n💰{p['price_bdt']}BDT\n\nPayment:", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=pay_kb(pk))
            except: pass
            bot.answer_callback_query(call.id)
        elif d.startswith("pay:"):
            pts = d.split(":"); p = PLAN_LIMITS.get(pts[1]); m = PAYMENT_METHODS.get(pts[2])
            if not p or not m: return
            payment_states[uid] = {'step':'wait_trx','plan':pts[1],'method':pts[2],'amount':p['price_bdt']}
            t = f"💳 <b>{m['name']}</b>\n📱 <code>{m['number']}</code>\n📝 {m['type']}\n💰 <b>{p['price_bdt']} BDT</b>\n\n📤 Send Transaction ID:"
            try: bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except: bot.send_message(uid, t, parse_mode='HTML')
            bot.answer_callback_query(call.id)
        elif d.startswith("payw:"):
            pk = d.split(":")[1]; u = db.get_user(uid); p = PLAN_LIMITS.get(pk)
            if not u or not p: return
            if u['wallet_balance']<p['price_bdt']: return bot.answer_callback_query(call.id,"❌ Low!",show_alert=True)
            db.wallet_tx(uid, p['price_bdt'],'purchase',f"Plan:{pk}")
            db.set_sub(uid, pk if pk!='lifetime' else 'lifetime', 30)
            bot.answer_callback_query(call.id,"✅")
            try: bot.edit_message_text(f"✅ {p['name']}!", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except: pass
        elif d.startswith("appv:"):
            if uid not in admin_ids and uid!=OWNER_ID: return
            p = db.approve_pay(int(d.split(":")[1]), uid)
            if p:
                bot.answer_callback_query(call.id,"✅")
                try: bot.edit_message_text(call.message.text+"\n\n✅ APPROVED", call.message.chat.id, call.message.message_id, parse_mode='HTML')
                except: pass
                try: bot.send_message(p['user_id'],"🎉 Approved!")
                except: pass
        elif d.startswith("rejt:"):
            if uid not in admin_ids and uid!=OWNER_ID: return
            db.reject_pay(int(d.split(":")[1]),uid); bot.answer_callback_query(call.id,"❌")
            try: bot.edit_message_text(call.message.text+"\n\n❌ REJECTED", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except: pass
        elif d.startswith("lang:"): db.update_user(uid, language=d.split(":")[1]); bot.answer_callback_query(call.id,"✅")
        elif d=="a_users":
            users = db.get_all_users()
            t = f"👥 {len(users)}\n\n"
            for u in users[:20]: t += f"{'🚫' if u['is_banned'] else '✅'} <code>{u['user_id']}</code> {u['full_name'] or '-'} [{u['plan']}]\n"
            bot.send_message(uid, t[:4000], parse_mode='HTML'); bot.answer_callback_query(call.id)
        elif d=="a_stats":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s,c): s.chat=c.message.chat; s.from_user=c.from_user
            show_stats(M(call))
        elif d=="a_pay":
            bot.answer_callback_query(call.id)
            class M:
                def __init__(s,c): s.chat=c.message.chat; s.from_user=c.from_user
            show_pays(M(call))
        elif d=="a_bc": user_states[uid]={'action':'broadcast'}; bot.answer_callback_query(call.id); bot.send_message(uid,"📢 Send:")
        elif d=="a_addsub": user_states[uid]={'action':'a_addsub','step':1}; bot.answer_callback_query(call.id); bot.send_message(uid,"➕ User ID:")
        elif d.startswith("asub:"):
            p = d.split(":"); user_states[uid]={'action':'a_addsub_days','target':int(p[2]),'plan':p[1]}
            bot.answer_callback_query(call.id); bot.send_message(uid,f"{PLAN_LIMITS[p[1]]['name']}\nDays (0=∞):")
        elif d=="a_remsub": user_states[uid]={'action':'a_remsub'}; bot.answer_callback_query(call.id); bot.send_message(uid,"➖ ID:")
        elif d=="a_ban": user_states[uid]={'action':'a_ban'}; bot.answer_callback_query(call.id); bot.send_message(uid,"🚫 ID REASON")
        elif d=="a_unban": user_states[uid]={'action':'a_unban'}; bot.answer_callback_query(call.id); bot.send_message(uid,"✅ ID:")
        elif d=="a_promo": user_states[uid]={'action':'a_promo'}; bot.answer_callback_query(call.id); bot.send_message(uid,"🎟 CODE DISC MAX")
        elif d=="a_sys":
            s = sys_stats(); bot.send_message(uid, f"🖥 CPU:{s['cpu']}% RAM:{s['mem']}% Disk:{s['disk']}% ⏱️{s['uptime']}")
            bot.answer_callback_query(call.id)
        elif d=="a_stopall":
            ct = 0
            for sk in list(bot_scripts.keys()):
                try: kill_tree(bot_scripts[sk]); cleanup(sk); ct+=1
                except: pass
            bot.answer_callback_query(call.id, f"🛑 {ct}")
        elif d=="a_backup":
            shutil.copy2(DATABASE_PATH, os.path.join(BACKUPS_DIR, f"bk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"))
            bot.answer_callback_query(call.id,"💾")
    except Exception as e:
        logger.error(f"CB: {e}", exc_info=True)
        bot.answer_callback_query(call.id, f"❌ {str(e)[:50]}")

# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════
atexit.register(lambda: [kill_tree(bot_scripts[sk]) for sk in list(bot_scripts.keys())])

def main():
    logger.info("═"*50)
    logger.info(f"🚀 EXU HOSTING PRO X v2.4")
    logger.info(f"👑 Owner: {OWNER_ID} | 🤖 @{BOT_USERNAME}")
    logger.info(f"💳 Binance ID: 758637628")
    logger.info("═"*50)

    # Fix old referral codes
    fixed = 0
    for u in db.get_all_users():
        if not u.get('referral_code') or len(u.get('referral_code',''))<5:
            try: db.update_user(u['user_id'], referral_code=generate_referral_code(u['user_id'])); fixed+=1
            except: pass
    if fixed: logger.info(f"🔧 Fixed {fixed} codes")

    threading.Thread(target=monitor, daemon=True).start()
    threading.Thread(target=backup, daemon=True).start()
    threading.Thread(target=expiry, daemon=True).start()
    keep_alive()

    for aid in admin_ids:
        try: bot.send_message(aid, f"🚀 <b>EXU v2.4 Started!</b>\n✅ All OK\n🤖 @{BOT_USERNAME}\n💳 Binance: 758637628", parse_mode='HTML')
        except: pass

    while True:
        try:
            logger.info("🟢 Polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except requests.exceptions.ConnectionError: time.sleep(10)
        except requests.exceptions.ReadTimeout: time.sleep(5)
        except Exception as e: logger.error(f"E: {e}"); time.sleep(5)

if __name__ == "__main__":
    main()