#『ＴＯＸＩＣ』 - NETFLIX BOT (FULL: FIXES + REFERRAL + SUPPORT MEDIA + REPLY MEDIA)
import os
import re
import json
import gzip
import zipfile
import io
import time
import random
import urllib.parse
import warnings
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List

warnings.filterwarnings("ignore")
import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from telegram import (
    Update, BotCommand, BotCommandScopeChat,
    KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# ========== LOGGING ==========
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== RAR SUPPORT ==========
try:
    import rarfile
    RAR_SUPPORT = True
except ImportError:
    RAR_SUPPORT = False

# ========== CONFIGURATION ==========
BOT_TOKEN = "8647089365:AAGsdq3JvE-LQ03-0HEl4M23rf5l2Uypdsw"
ADMIN_IDS = [6484964627]

REQUIRED_CHANNELS = [
    {"username": "@ToxicXPremium", "invite_link": "https://t.me/+KvNfyJvLPEY0NWY1"}
]

COOKIES_FILE = "cookies_store.json"
USER_STATS_FILE = "user_stats.json"
USER_INFO_FILE = "user_info.json"
CREDITS_FILE = "credits.json"
REFERRALS_FILE = "referrals.json"
PENDING_REFS_FILE = "pending_refs.json"
BANNED_FILE = "banned.json"
CODES_FILE = "codes.json"
HISTORY_FILE = "history.json"
PHONE_LOGIN_FILE = "phone_login.json"
SUPPORT_FILE = "support.json"
PENDING_PHOTO_FILE = "pending_photos.json"

REQUEST_TIMEOUT = 15
MAX_USAGE_PER_COOKIE = 1
MAX_COOKIES_TO_TRY = 5
PENDING_PHOTO_TIMEOUT = 300

WELCOME_CREDITS = 2
LOGIN_COST = 1
REFERRAL_BONUS = 1
PHONE_LOGIN_REQUIRED_REFS = 5

# ========== FOOTER ==========
FOOTER = (
    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "👑 『Ｍａｄｅ Ｂｙ ＴＯＸＩＣ』\n"
    "💀 ⚡ 𝕋𝕙𝕒𝕟𝕜𝕤 𝕥𝕠 『 ℙ𝕊𝕐ℂℍ𝕆 』 ⚡ 💀\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━"
)

# ========== HEADERS ==========
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-IN,en;q=0.8",
    "Cache-Control": "max-age=0",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-GPC": "1",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Sec-Ch-Ua": '"Quetta";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"',
    "Priority": "u=0, i",
}

# ========== HELPERS ==========
async def safe_reply(message, text, **kwargs):
    try:
        if message and hasattr(message, 'reply_text'):
            return await message.reply_text(text, **kwargs)
    except Exception as e:
        logger.warning(f"Safe reply failed: {e}")
    return None

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def now_utc_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# ========== USER INFO ==========
def save_user_info(user_id, username):
    info = load_json(USER_INFO_FILE, {})
    info[str(user_id)] = username or "Unknown"
    save_json(USER_INFO_FILE, info)

def get_user_info(user_id):
    info = load_json(USER_INFO_FILE, {})
    return info.get(str(user_id), "Unknown")

# ========== CREDITS ==========
def get_credits(user_id):
    data = load_json(CREDITS_FILE, {})
    return data.get(str(user_id), {}).get("balance", 0)

def set_credits(user_id, amount):
    data = load_json(CREDITS_FILE, {})
    key = str(user_id)
    if key not in data:
        data[key] = {"balance": 0}
    data[key]["balance"] = max(0, amount)
    save_json(CREDITS_FILE, data)

def add_credits(user_id, amount):
    set_credits(user_id, get_credits(user_id) + amount)

def deduct_credits(user_id, amount):
    current = get_credits(user_id)
    if current < amount:
        return False
    set_credits(user_id, current - amount)
    return True

def register_user(user_id):
    data = load_json(CREDITS_FILE, {})
    key = str(user_id)
    is_new = key not in data
    if is_new:
        data[key] = {"balance": WELCOME_CREDITS}
        save_json(CREDITS_FILE, data)
    return is_new

# ========== REFERRAL SYSTEM ==========
def save_pending_ref(new_user_id, referrer_id):
    pending = load_json(PENDING_REFS_FILE, {})
    pending[str(new_user_id)] = str(referrer_id)
    save_json(PENDING_REFS_FILE, pending)

def get_pending_ref(new_user_id):
    pending = load_json(PENDING_REFS_FILE, {})
    return pending.get(str(new_user_id))

def clear_pending_ref(new_user_id):
    pending = load_json(PENDING_REFS_FILE, {})
    if str(new_user_id) in pending:
        del pending[str(new_user_id)]
        save_json(PENDING_REFS_FILE, pending)

def add_referral(referrer_id, new_user_id):
    refs = load_json(REFERRALS_FILE, {})
    referrer_key = str(referrer_id)
    new_key = str(new_user_id)
    if referrer_key not in refs:
        refs[referrer_key] = []
    if new_key in refs[referrer_key]:
        return False
    refs[referrer_key].append(new_key)
    save_json(REFERRALS_FILE, refs)
    add_credits(referrer_id, REFERRAL_BONUS)
    return True

def get_referral_count(user_id):
    refs = load_json(REFERRALS_FILE, {})
    return len(refs.get(str(user_id), []))

def get_total_user_count():
    return len(load_json(CREDITS_FILE, {}))

# ========== BAN ==========
def is_banned(user_id):
    return str(user_id) in load_json(BANNED_FILE, {})

def ban_user(user_id, admin_id):
    banned = load_json(BANNED_FILE, {})
    banned[str(user_id)] = {"by": str(admin_id), "at": time.time()}
    save_json(BANNED_FILE, banned)

def unban_user(user_id):
    banned = load_json(BANNED_FILE, {})
    if str(user_id) in banned:
        del banned[str(user_id)]
        save_json(BANNED_FILE, banned)
        return True
    return False

# ========== CODES ==========
def generate_code(credits, uses):
    codes = load_json(CODES_FILE, {})
    code = "TOXIC-" + ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
    codes[code] = {"credits": credits, "uses_left": uses}
    save_json(CODES_FILE, codes)
    return code

def redeem_code(user_id, code):
    codes = load_json(CODES_FILE, {})
    code = code.upper().strip()
    if code not in codes:
        return False, 0
    if codes[code]["uses_left"] <= 0:
        return False, 0
    add_credits(user_id, codes[code]["credits"])
    codes[code]["uses_left"] -= 1
    if codes[code]["uses_left"] <= 0:
        del codes[code]
    save_json(CODES_FILE, codes)
    return True, codes[code]["credits"] if code in codes else 0

# ========== HISTORY ==========
def add_history(user_id, entry):
    hist = load_json(HISTORY_FILE, {})
    key = str(user_id)
    if key not in hist:
        hist[key] = []
    hist[key].insert(0, {"date": time.strftime("%Y-%m-%d"), **entry})
    hist[key] = hist[key][:20]
    save_json(HISTORY_FILE, hist)

# ========== PHONE LOGIN ==========
def get_phone_login_status(user_id):
    data = load_json(PHONE_LOGIN_FILE, {})
    return data.get(str(user_id))

def create_phone_login_request(user_id, username, refs):
    data = load_json(PHONE_LOGIN_FILE, {})
    if str(user_id) in data and data[str(user_id)]["status"] == "pending":
        return False
    data[str(user_id)] = {
        "username": username or "N/A",
        "referrals": refs,
        "requested_at": time.time(),
        "status": "pending"
    }
    save_json(PHONE_LOGIN_FILE, data)
    return True

def mark_phone_provided(user_id):
    data = load_json(PHONE_LOGIN_FILE, {})
    if str(user_id) in data:
        data[str(user_id)]["status"] = "provided"
        save_json(PHONE_LOGIN_FILE, data)
        return True
    return False

# ========== SUPPORT ==========
def save_support_message(user_id, username, message, msg_type="text"):
    data = load_json(SUPPORT_FILE, [])
    data.insert(0, {
        "user_id": str(user_id),
        "username": username or "N/A",
        "message": message,
        "type": msg_type,
        "time": now_utc_str()
    })
    data = data[:50]
    save_json(SUPPORT_FILE, data)

# ========== PENDING PHOTO ==========
def save_pending_photo(admin_id, file_id, media_type="photo"):
    data = load_json(PENDING_PHOTO_FILE, {})
    data[str(admin_id)] = {"file_id": file_id, "type": media_type, "at": time.time()}
    save_json(PENDING_PHOTO_FILE, data)

def get_pending_photo(admin_id):
    data = load_json(PENDING_PHOTO_FILE, {})
    entry = data.get(str(admin_id))
    if entry and (time.time() - entry["at"]) < PENDING_PHOTO_TIMEOUT:
        return entry
    return None

def clear_pending_photo(admin_id):
    data = load_json(PENDING_PHOTO_FILE, {})
    if str(admin_id) in data:
        del data[str(admin_id)]
        save_json(PENDING_PHOTO_FILE, data)

# ========== FORCE JOIN ==========
async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not REQUIRED_CHANNELS:
        return True
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        return True
    not_joined = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel["username"], user_id)
            if member.status not in ("member", "administrator", "creator"):
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)
    if not_joined:
        msg = "⚠️ *JOIN REQUIRED*\n\nYou must join our channel to use this bot:\n\n"
        for ch in not_joined:
            msg += f"👉 [Toxic X Premium]({ch['invite_link']})\n"
        msg += "\nAfter joining, send /start again."
        await safe_reply(update.message, msg, parse_mode="Markdown", disable_web_page_preview=True)
        return False
    return True

async def check_channel_joined_only(user_id, context) -> bool:
    if not REQUIRED_CHANNELS:
        return True
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel["username"], user_id)
            if member.status in ("member", "administrator", "creator"):
                return True
        except:
            pass
    return False

# ========== COOKIE EXTRACTION ==========
def extract_netflix_id_from_text(text: str) -> Optional[str]:
    match = re.search(r"netflixid\s*=\s*([^\s;]+)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.startswith("#") and not line_stripped.startswith("#HttpOnly_"):
            continue
        if line_stripped.startswith("#HttpOnly_"):
            line_stripped = line_stripped[len("#HttpOnly_"):]
        parts = line_stripped.split()
        if len(parts) >= 7 and parts[5].lower() == "netflixid":
            return parts[6]
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if data.get("name") == "NetflixId":
                return data.get("value")
            data = data.get("cookies") or data.get("items") or [data]
        if isinstance(data, list):
            for cookie in data:
                if cookie.get("name") == "NetflixId":
                    return cookie.get("value")
    except:
        pass
    if text.startswith("v%3D") or text.startswith("%"):
        return text
    return None

# ========== COOKIE STORAGE ==========
def load_cookies_store() -> Dict:
    return load_json(COOKIES_FILE, {})

def save_cookies_store(store: Dict):
    save_json(COOKIES_FILE, store)

def add_cookie_with_metadata(admin_id: int, filename: str, netflix_id: str) -> Tuple[bool, str]:
    store = load_cookies_store()
    admin_key = str(admin_id)
    if admin_key not in store:
        store[admin_key] = []
    for entry in store[admin_key]:
        if entry.get("NetflixId") == netflix_id:
            return False, "duplicate"
    store[admin_key].append({"filename": filename, "NetflixId": netflix_id, "usage_count": 0})
    save_cookies_store(store)
    return True, "ok"

def get_all_cookies_with_metadata() -> List[Dict]:
    store = load_cookies_store()
    out = []
    for admin_id, entries in store.items():
        for entry in entries:
            out.append({
                "filename": entry["filename"],
                "NetflixId": entry["NetflixId"],
                "usage_count": entry.get("usage_count", 0),
                "admin_id": admin_id
            })
    return out

def increment_cookie_usage(netflix_id: str) -> bool:
    store = load_cookies_store()
    for admin_id, entries in store.items():
        for i, entry in enumerate(entries):
            if entry.get("NetflixId") == netflix_id:
                entry["usage_count"] = entry.get("usage_count", 0) + 1
                if entry["usage_count"] >= MAX_USAGE_PER_COOKIE:
                    del entries[i]
                    save_cookies_store(store)
                    return False
                save_cookies_store(store)
                return True
    return False

def get_total_remaining_uses() -> int:
    total = 0
    for c in get_all_cookies_with_metadata():
        remaining = MAX_USAGE_PER_COOKIE - c["usage_count"]
        if remaining > 0:
            total += remaining
    return total

def get_total_cookie_count() -> int:
    return len(get_all_cookies_with_metadata())

def delete_all_cookies() -> bool:
    if os.path.exists(COOKIES_FILE):
        os.remove(COOKIES_FILE)
        return True
    return False

def remove_cookie_by_netflixid(admin_id: int, netflix_id: str) -> bool:
    store = load_cookies_store()
    admin_key = str(admin_id)
    if admin_key not in store:
        return False
    original = len(store[admin_key])
    store[admin_key] = [e for e in store[admin_key] if e.get("NetflixId") != netflix_id]
    if len(store[admin_key]) < original:
        save_cookies_store(store)
        return True
    return False

# ========== TV ACTIVATION ==========
def extract_auth_url_from_tv2(html: str) -> Optional[str]:
    patterns = [
        r'name="authURL"\s+value="([^"]+)"',
        r'authURL["\']?\s*[:=]\s*["\']([^"]+)["\']',
        r'authURL=([^&\s"\']+)',
        r'value="(c1\.[^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            return urllib.parse.unquote(m.group(1))
    return None

def submit_tv_code(netflix_id: str, tv_code: str):
    session = requests.Session()
    session.cookies.clear()
    session.cookies.set("NetflixId", netflix_id, domain=".netflix.com", path="/")
    headers = BASE_HEADERS.copy()
    headers["Referer"] = "https://www.netflix.com/tv2"
    headers["Origin"] = "https://www.netflix.com"

    try:
        r = session.get("https://www.netflix.com/tv2", headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        if r.status_code != 200:
            return False, None, None, f"GET /tv2 returned {r.status_code}", r.status_code
    except Exception as e:
        return False, None, None, f"GET error: {e}", None

    auth_url = extract_auth_url_from_tv2(r.text)
    if not auth_url:
        return False, None, None, "authURL not found", r.status_code

    payload = {
        "flow": "websiteSignUp",
        "authURL": auth_url,
        "flowMode": "enterTvLoginRendezvousCode",
        "withFields": "tvLoginRendezvousCode,isTvUrl2",
        "code": tv_code,
        "tvLoginRendezvousCode": tv_code,
        "isTvUrl2": "true",
        "action": "nextAction",
    }
    post_headers = headers.copy()
    post_headers["Content-Type"] = "application/x-www-form-urlencoded"

    try:
        r = session.post("https://www.netflix.com/tv2", data=payload, headers=post_headers,
                         timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=True)
    except Exception as e:
        return False, None, None, f"POST error: {e}", None

    final_url = r.url
    status = r.status_code
    cleaned = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
    cleaned = re.sub(r'<style[^>]*>.*?</style>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if "/tv/out/success" in final_url:
        return True, final_url, cleaned, None, status
    lower = r.text.lower()
    if "your tv is ready to watch" in lower or "you're ready to watch" in lower:
        return True, final_url, cleaned, None, status
    if "that code wasn't right" in lower or "invalid code" in lower:
        return False, final_url, cleaned, "Invalid code", status
    return False, final_url, cleaned, "Unknown result", status

# ========== PLAN & COUNTRY ==========
def fetch_page(netflix_id: str, url: str):
    sess = requests.Session()
    sess.cookies.clear()
    sess.cookies.set("NetflixId", netflix_id, domain=".netflix.com", path="/")
    headers = {
        "User-Agent": BASE_HEADERS["User-Agent"],
        "Accept": BASE_HEADERS["Accept"],
        "Accept-Encoding": BASE_HEADERS["Accept-Encoding"],
        "Accept-Language": BASE_HEADERS["Accept-Language"],
        "Referer": "https://www.netflix.com/",
    }
    try:
        r = sess.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        content = r.content
        if len(content) >= 2 and content[0] == 0x1f and content[1] == 0x8b:
            html = gzip.decompress(content).decode('utf-8')
        else:
            html = r.text
        return html, None
    except Exception as e:
        return None, str(e)

def get_country_and_plan(netflix_id: str):
    html, err = fetch_page(netflix_id, "https://www.netflix.com/account/membership")
    if err or not html:
        return None, None
    country = re.search(r'"currentCountry"\s*:\s*"([^"]+)"', html)
    if not country:
        country = re.search(r'"countryOfSignup":\s*"([^"]+)"', html)
    if not country:
        return None, None
    m = re.search(r'"MemberPlan".*?"localizedPlanName".*?"value":"([^"]+)"', html, re.DOTALL)
    if not m:
        m = re.search(r'"localizedPlanName"\s*:\s*"([^"]+)"', html)
    if not m:
        m = re.search(r'"planName"\s*:\s*"([^"]+)"', html)
    if m:
        return country.group(1), m.group(1)
    return country.group(1), "Unknown"

# ========== KEYBOARD ==========
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🎬 Login TV")],
        [KeyboardButton("💰 My Credits"), KeyboardButton("🎁 Referral")],
        [KeyboardButton("📱 Phone Login"), KeyboardButton("📊 My Stats")],
        [KeyboardButton("📅 History"), KeyboardButton("📞 Support")],
        [KeyboardButton("❓ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== WELCOME ==========
def build_welcome_text(username, credits):
    name = username if username else "User"
    return (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃  👑 ℕ𝔼𝕋𝔽𝕃𝕀𝕏 ℙℝ𝔼𝕄𝕀𝕌𝕄 👑  ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👋 𝕎𝕖𝕝𝕔𝕠𝕞𝕖, {name}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ Instant TV Login – no password needed\n"
        "🔑 Cookie-Powered – premium accounts\n"
        "🌍 Country & Plan Info – shown after login\n"
        "🎁 Free to Use – just enter your TV code\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Your Credits: {credits} (welcome bonus)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 How to use:\n"
        "1️⃣ Open Netflix on your TV\n"
        "2️⃣ Get the 8-digit TV code\n"
        "3️⃣ Send /login 1234-5678\n"
        "4️⃣ Enjoy!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💎 Earn Credits:\n"
        "• 👥 Referral – 1 credit per friend\n"
        "• 📱 Phone Login – refer 5 users to unlock\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💎 Commands:\n"
        "• /login <code> – Activate TV (1 credit)\n"
        "• /credits – Check balance\n"
        "• /redeem <code> – Redeem code\n"
        "• /gift <user_id> <amount> – Gift credits\n"
        "• /leaderboard – Top users\n"
        "• /richlist – Top richest\n"
        "• /panel – Your stats\n"
        "• /help – Show this message\n\n"
        f"{FOOTER}"
    )

# ========== NOTIFY NEW USER ==========
async def notify_admins_new_user(context: ContextTypes.DEFAULT_TYPE, user):
    msg = (
        "🆕 *NEW USER STARTED BOT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Username: @{user.username or 'N/A'}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"📛 Name: {user.first_name or 'N/A'}\n"
        f"📅 Time: `{now_utc_str()}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: `{get_total_user_count()}`"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")

# ========== START (WITH NEW REFERRAL) ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_banned(user.id):
        await safe_reply(update.message, "🚫 *YOU ARE BANNED*\n\nContact admin if this is a mistake.", parse_mode="Markdown")
        return

    referrer_id = None
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].split("_")[1])
        except:
            pass

    if referrer_id and referrer_id != user.id:
        save_pending_ref(user.id, referrer_id)

    joined = await check_channel_joined_only(user.id, context)
    if not joined:
        await check_force_join(update, context)
        return

    pending = get_pending_ref(user.id)
    if pending:
        added = add_referral(int(pending), user.id)
        if added:
            try:
                new_username = user.username or user.first_name or "User"
                await context.bot.send_message(
                    int(pending),
                    f"🎉 *REFERRAL JOINED!*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 @{new_username} joined via your link!\n"
                    f"💰 +{REFERRAL_BONUS} credit added\n"
                    "━━━━━━━━━━━━━━━━━━━━━━",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Referrer notify failed: {e}")
        clear_pending_ref(user.id)

    is_new = register_user(user.id)
    credits = get_credits(user.id)
    save_user_info(user.id, user.username or user.first_name or "User")

    display_name = user.username if user.username else (user.first_name or "User")
    if user.username:
        display_name = "@" + user.username

    await safe_reply(update.message, build_welcome_text(display_name, credits),
                     reply_markup=get_main_keyboard())

    if is_new:
        await notify_admins_new_user(context, user)

# ========== LOGIN ==========
async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_banned(user.id):
        await safe_reply(update.message, "🚫 You are banned.")
        return
    try:
        if not await check_force_join(update, context):
            return
    except:
        pass

    if not context.args:
        await safe_reply(update.message,
            "⚡ *Supported Format*\n\n/login 12345678\n/login 1234-5678",
            parse_mode="Markdown")
        return

    tv_code = context.args[0].replace("-", "").strip()
    if not tv_code.isdigit() or len(tv_code) < 5:
        await safe_reply(update.message, "❌ Invalid code format.")
        return

    if get_credits(user.id) < LOGIN_COST:
        await safe_reply(update.message,
            "❌ *INSUFFICIENT CREDITS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Balance: `{get_credits(user.id)}`\n"
            f"🔒 Cost per login: `{LOGIN_COST}` credit\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📈 Earn credits:\n• 👥 Referral",
            parse_mode="Markdown")
        return

    deduct_credits(user.id, LOGIN_COST)
    success = False
    tried_ids = set()

    for attempt in range(MAX_COOKIES_TO_TRY):
        all_cookies = get_all_cookies_with_metadata()
        if not all_cookies:
            break

        cookie_entry = None
        for c in all_cookies:
            if c["usage_count"] < MAX_USAGE_PER_COOKIE and c["NetflixId"] not in tried_ids:
                cookie_entry = c
                break

        if not cookie_entry:
            break

        netflix_id = cookie_entry["NetflixId"]
        tried_ids.add(netflix_id)

        ok, final_url, cleaned, err_msg, status = submit_tv_code(netflix_id, tv_code)
        if ok:
            increment_cookie_usage(netflix_id)
            stats = load_json(USER_STATS_FILE, {})
            stats[str(user.id)] = stats.get(str(user.id), 0) + 1
            save_json(USER_STATS_FILE, stats)
            country, plan = get_country_and_plan(netflix_id)
            country = country or "Unknown"
            plan = plan or "Unknown"
            add_history(user.id, {"country": country, "plan": plan, "code": tv_code})
            await safe_reply(update.message,
                f"✅ *LOGIN SUCCESSFUL!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍 Country: `{country.upper()}`\n"
                f"📺 Plan: `{plan.upper()}`\n"
                f"💰 Credits Left: `{get_credits(user.id)}`\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Enjoy your Netflix!",
                parse_mode="Markdown")
            success = True
            break

    if not success:
        add_credits(user.id, LOGIN_COST)
        await safe_reply(update.message,
            "❌ *LOGIN FAILED*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            "The TV code is invalid or expired.\n"
            "💰 1 credit refunded.\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Try again with a fresh code.",
            parse_mode="Markdown")

# ========== MENU HANDLERS ==========
async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await safe_reply(update.message,
        f"💰 *YOUR CREDITS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 Balance: `{get_credits(user.id)}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user.id}"
    count = get_referral_count(user.id)
    await safe_reply(update.message,
        f"🎁 *YOUR REFERRAL LINK*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"`{link}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Referrals: `{count}`\n"
        f"💰 Earned: `{count * REFERRAL_BONUS}` credits\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Share to earn {REFERRAL_BONUS} credit per user\n"
        "_(credit added only after they join our channel)_",
        parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = load_json(USER_STATS_FILE, {})
    logins = stats.get(str(user.id), 0)
    refs = get_referral_count(user.id)
    await safe_reply(update.message,
        f"📊 *YOUR STATS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Successful Logins: `{logins}`\n"
        f"💰 Credits: `{get_credits(user.id)}`\n"
        f"👥 Referrals: `{refs}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    hist = load_json(HISTORY_FILE, {}).get(str(user.id), [])
    if not hist:
        await safe_reply(update.message, "📭 No login history.")
        return
    lines = ["📅 *YOUR LOGIN HISTORY*\n━━━━━━━━━━━━━━━━━━━━━━"]
    for i, h in enumerate(hist[:10], 1):
        lines.append(f"{i}. `{h['date']}` – {h.get('country','?')} – {h.get('plan','?')}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if len(context.args) < 2:
        await safe_reply(update.message, "Usage: `/gift <user_id> <amount>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        amount = int(context.args[1])
    except:
        await safe_reply(update.message, "❌ Invalid input.")
        return
    if amount <= 0:
        await safe_reply(update.message, "❌ Amount must be positive.")
        return
    if get_credits(user.id) < amount:
        await safe_reply(update.message, "❌ Insufficient credits.")
        return
    deduct_credits(user.id, amount)
    add_credits(target, amount)
    await safe_reply(update.message,
        f"🎁 *GIFT SENT!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Sent `{amount}` credits to `{target}`\n"
        f"💰 Your new balance: `{get_credits(user.id)}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await safe_reply(update.message, "Usage: `/redeem <code>`", parse_mode="Markdown")
        return
    ok, amount = redeem_code(user.id, context.args[0])
    if ok:
        await safe_reply(update.message,
            f"🎟️ *CODE REDEEMED!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Credits added\n"
            f"💎 Total: `{get_credits(user.id)}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown")
    else:
        await safe_reply(update.message, "❌ Invalid or used code.")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = load_json(USER_STATS_FILE, {})
    if not stats:
        await safe_reply(update.message, "📭 No data yet.")
        return
    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
    lines = ["🏆 *TOP 10 USERS (Logins)*\n━━━━━━━━━━━━━━━━━━━━━━"]
    for i, (uid, count) in enumerate(top, 1):
        uname = get_user_info(uid)
        lines.append(f"{i}. @{uname} – {count} logins")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

async def richlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_json(CREDITS_FILE, {})
    if not data:
        await safe_reply(update.message, "📭 No data yet.")
        return
    top = sorted(data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]
    lines = ["💎 *TOP 10 RICHEST*\n━━━━━━━━━━━━━━━━━━━━━━"]
    for i, (uid, info) in enumerate(top, 1):
        uname = get_user_info(uid)
        lines.append(f"{i}. @{uname} – {info.get('balance', 0)} credits")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    credits = get_credits(user.id)
    stats = load_json(USER_STATS_FILE, {})
    logins = stats.get(str(user.id), 0)
    username = user.username or "User"
    text = f"📊 *Panel for {username}*\n\n✅ Your logins: `{logins}`\n💰 Credits: `{credits}`"
    if user.id in ADMIN_IDS:
        text += (
            f"\n\n--- *Admin Stats* ---\n"
            f"🍪 Cookies: `{get_total_cookie_count()}`\n"
            f"🔁 Remaining uses: `{get_total_remaining_uses()}`\n"
            f"👥 Total Users: `{get_total_user_count()}`"
        )
    await safe_reply(update.message, text, parse_mode="Markdown")

# ========== PHONE LOGIN ==========
async def phone_login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    refs = get_referral_count(user.id)
    existing = get_phone_login_status(user.id)

    if existing and existing["status"] == "pending":
        await safe_reply(update.message,
            "⏳ *REQUEST ALREADY PENDING*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            "Your phone login request is already under review.\n"
            "Please wait for admin approval.",
            parse_mode="Markdown")
        return

    if existing and existing["status"] == "provided":
        await safe_reply(update.message,
            "✅ *PHONE LOGIN PROVIDED*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            "Admin has already provided your phone login.",
            parse_mode="Markdown")
        return

    if refs < PHONE_LOGIN_REQUIRED_REFS:
        remaining = PHONE_LOGIN_REQUIRED_REFS - refs
        await safe_reply(update.message,
            f"🔒 *PHONE LOGIN LOCKED*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Your Referrals: `{refs}/{PHONE_LOGIN_REQUIRED_REFS}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Refer `{remaining}` more to unlock a FREE phone login!\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 Get your link: `/referral`",
            parse_mode="Markdown")
        return

    created = create_phone_login_request(user.id, user.username, refs)
    if created:
        await safe_reply(update.message,
            "🎉 *CONGRATULATIONS!* 🎉\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ You have referred `{refs}` users!\n"
            "📩 Your PHONE LOGIN request has been\n"
            "sent to admin.\n"
            "⏳ Please wait for approval.\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown")

        admin_msg = (
            "🎁 *PHONE LOGIN REQUEST*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Username: @{user.username or 'N/A'}\n"
            f"🆔 User ID: `{user.id}`\n"
            f"👥 Referrals: `{refs}`\n"
            f"📅 Date: `{now_utc_str()}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "User is eligible for a PHONE LOGIN."
        )
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Admin notify failed: {e}")

# ========== SUPPORT (TEXT + PHOTO + VIDEO) ==========
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["awaiting_support"] = True
    await safe_reply(update.message,
        "📞 *SUPPORT CENTER*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "Send your message below.\n\n"
        "You can send:\n"
        "• 📝 Text\n"
        "• 📸 Photo\n"
        "• 🎥 Video\n\n"
        "It will be forwarded to our admin team.\n"
        "They will reply as soon as possible.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ Do not send spam or useless messages.",
        parse_mode="Markdown")

async def handle_support_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    context.user_data.pop("awaiting_support", None)
    save_support_message(user.id, user.username, text, "text")

    await safe_reply(update.message,
        "✅ *Message sent to admin!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ Please wait for a reply.\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")

    admin_msg = (
        "📩 *SUPPORT MESSAGE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 From: @{user.username or 'N/A'}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"📅 Time: `{now_utc_str()}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 {text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Reply: `/reply {user.id} <message>`"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Support notify failed: {e}")

async def handle_support_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.pop("awaiting_support", None)

    media_type = None
    file_id = None
    caption = update.message.caption or ""

    if update.message.photo:
        media_type = "photo"
        file_id = update.message.photo[-1].file_id
    elif update.message.video:
        media_type = "video"
        file_id = update.message.video.file_id
    else:
        return

    save_support_message(user.id, user.username, caption or f"[{media_type}]", media_type)

    await safe_reply(update.message,
        f"✅ *{media_type.title()} sent to admin!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ Please wait for a reply.\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")

    header = (
        "📩 *SUPPORT MESSAGE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 From: @{user.username or 'N/A'}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"📅 Time: `{now_utc_str()}`\n"
        f"📎 Type: {media_type.title()}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Reply: `/reply {user.id} <message>`"
    )

    for admin_id in ADMIN_IDS:
        try:
            if media_type == "photo":
                await context.bot.send_photo(admin_id, photo=file_id, caption=header, parse_mode="Markdown")
            elif media_type == "video":
                await context.bot.send_video(admin_id, video=file_id, caption=header, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Media forward failed: {e}")

# ========== TEXT HANDLER ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_support"):
        await handle_support_text(update, context)
        return

    text = update.message.text
    if text in ("💰 My Credits", "💰 Credits"):
        await credits_command(update, context)
    elif text == "🎁 Referral":
        await referral_command(update, context)
    elif text == "📊 My Stats":
        await stats_command(update, context)
    elif text == "📅 History":
        await history_command(update, context)
    elif text == "📱 Phone Login":
        await phone_login_command(update, context)
    elif text == "📞 Support":
        await support_command(update, context)
    elif text == "❓ Help":
        await help_command(update, context)
    elif text == "🎬 Login TV":
        await safe_reply(update.message,
            "📞 *Enter the 8-digit TV code from your Netflix app.*\n\nFormat: `/login 1234-5678`",
            parse_mode="Markdown")
    else:
        await safe_reply(update.message, "❌ Please use the menu buttons.")

# ========== SUPPORT MEDIA HANDLER ==========
async def handle_support_media_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_support"):
        await handle_support_media(update, context)

# ========== REPLY COMMAND ==========
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) < 2:
        await safe_reply(update.message, "Usage: `/reply <user_id> <message>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        msg = " ".join(context.args[1:])

        # Check pending photo
        pending = get_pending_photo(update.effective_user.id)

        if pending:
            # Forward pending photo with this message as caption
            if pending["type"] == "photo":
                await context.bot.send_photo(target, photo=pending["file_id"], caption=msg)
            elif pending["type"] == "video":
                await context.bot.send_video(target, video=pending["file_id"], caption=msg)
            clear_pending_photo(update.effective_user.id)
        else:
            # Text reply with header, no parse_mode → preserves all chars
            await context.bot.send_message(target,
                f"📬 ADMIN REPLY\n━━━━━━━━━━━━━━━━━━━━━━\n{msg}\n━━━━━━━━━━━━━━━━━━━━━━")
        await safe_reply(update.message, f"✅ Reply sent to `{target}`.", parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update.message, f"❌ Failed: {e}")

async def reply_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    if context.user_data.get("awaiting_support"):
        return

    caption = update.message.caption or ""
    if caption.startswith("/reply"):
        parts = caption.split(maxsplit=2)
        if len(parts) >= 2:
            try:
                target = int(parts[1])
                msg = parts[2] if len(parts) > 2 else ""
                if update.message.photo:
                    await context.bot.send_photo(target, photo=update.message.photo[-1].file_id, caption=msg)
                elif update.message.video:
                    await context.bot.send_video(target, video=update.message.video.file_id, caption=msg)
                await safe_reply(update.message, f"✅ Media sent to `{target}`.", parse_mode="Markdown")
                return
            except:
                pass

    # Save as pending
    if update.message.photo:
        save_pending_photo(user.id, update.message.photo[-1].file_id, "photo")
    elif update.message.video:
        save_pending_photo(user.id, update.message.video.file_id, "video")

    await safe_reply(update.message,
        "📸 *MEDIA DETECTED*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Who should I send this to?\n\n"
        "Reply with:\n"
        "`/reply <user_id> <optional_caption>`\n\n"
        "Or send: `/cancel`",
        parse_mode="Markdown")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_pending_photo(update.effective_user.id)
    context.user_data.pop("awaiting_support", None)
    await safe_reply(update.message, "❌ Cancelled.")

# ========== BACKUP / RESTORE ==========
async def backupcookies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    all_cookies = get_all_cookies_with_metadata()
    if not all_cookies:
        await safe_reply(update.message, "📭 No cookies to backup.")
        return

    backup = {
        "backup_date": time.strftime("%Y-%m-%d"),
        "total": len(all_cookies),
        "cookies": [
            {"filename": c["filename"], "NetflixId": c["NetflixId"], "admin_id": c["admin_id"]}
            for c in all_cookies
        ]
    }

    filename = f"cookies_backup_{time.strftime('%Y-%m-%d_%H-%M')}.json"
    with open(filename, "w") as f:
        json.dump(backup, f, indent=2)

    with open(filename, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=filename,
            caption=(
                "📦 *COOKIE BACKUP*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🍪 Total: `{len(all_cookies)}`\n"
                f"📅 Date: `{backup['backup_date']}`\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            parse_mode="Markdown"
        )

    try:
        os.remove(filename)
    except:
        pass

async def restorecookies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    context.user_data["awaiting_restore"] = True
    await safe_reply(update.message, "📤 Send the backup JSON file to restore cookies.")

async def restore_handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    document = update.message.document
    if not document:
        return
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    try:
        data = json.loads(file_bytes.decode("utf-8", errors="ignore"))
    except:
        await safe_reply(update.message, "❌ Invalid backup file.")
        return
    cookies = data.get("cookies", [])
    if not isinstance(cookies, list):
        await safe_reply(update.message, "❌ Invalid backup format.")
        return
    added = 0
    for c in cookies:
        nid = c.get("NetflixId")
        fname = c.get("filename", "restored.txt")
        if nid:
            s, _ = add_cookie_with_metadata(user.id, fname, nid)
            if s:
                added += 1
    await safe_reply(update.message, f"✅ Restored {added} cookies.", parse_mode="Markdown")

# ========== USER STATS (FIXED - Option C) ==========
async def userstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    info = load_json(USER_INFO_FILE, {})
    stats = load_json(USER_STATS_FILE, {})
    if not info and not stats:
        await safe_reply(update.message, "📭 No user data yet.")
        return

    # Combine: all users who started bot + login counts
    lines = ["👥 *USER STATS*\n━━━━━━━━━━━━━━━━━━━━━━"]
    all_uids = set(list(info.keys()) + list(stats.keys()))
    combined = []
    for uid in all_uids:
        uname = info.get(uid, "Unknown")
        count = stats.get(uid, 0)
        combined.append((uid, uname, count))
    combined.sort(key=lambda x: x[2], reverse=True)

    for i, (uid, uname, count) in enumerate(combined[:30], 1):
        lines.append(f"{i}. @{uname} (`{uid}`) – {count} logins")
    if len(combined) > 30:
        lines.append(f"... and {len(combined) - 30} more.")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"👥 Total users: `{len(all_uids)}`")
    lines.append(f"✅ Total logins: `{sum(stats.values())}`")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

# ========== ADMIN COMMANDS ==========
async def addsingle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    context.user_data["awaiting_single_file"] = True
    await safe_reply(update.message, "📤 Send the cookie file (.txt or .json)")

async def bulkadd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    await safe_reply(update.message, "📦 Send .zip or .rar file with cookies")
    context.user_data["awaiting_bulk_file"] = True

async def delall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    await safe_reply(update.message, "⚠️ Send `/delall_confirm` to delete ALL cookies.", parse_mode="Markdown")

async def delall_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if delete_all_cookies():
        await safe_reply(update.message, "🗑️✅ All cookies deleted.")
    else:
        await safe_reply(update.message, "ℹ️ No cookies present.")

async def list_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    all_cookies = get_all_cookies_with_metadata()
    if not all_cookies:
        await safe_reply(update.message, "📭 No cookies stored.")
        return
    lines = ["📋🍪 *STORED COOKIES* 🍪📋\n"]
    for c in all_cookies:
        lines.append(f"• `{c['filename']}` → used {c['usage_count']}/{MAX_USAGE_PER_COOKIE}")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

async def del_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if not context.args:
        await safe_reply(update.message, "Usage: `/delcookie <NetflixId>`", parse_mode="Markdown")
        return
    if remove_cookie_by_netflixid(update.effective_user.id, context.args[0]):
        await safe_reply(update.message, "🗑️✅ Cookie removed.")
    else:
        await safe_reply(update.message, "❌ Cookie not found or not yours.")

async def addcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if len(context.args) < 2:
        await safe_reply(update.message, "Usage: `/addcredits <user_id> <amount>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        amount = int(context.args[1])
        add_credits(target, amount)
        await safe_reply(update.message, f"✅ Added {amount} credits to `{target}`.\nNew: `{get_credits(target)}`", parse_mode="Markdown")
    except:
        await safe_reply(update.message, "❌ Invalid input.")

async def removecredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if len(context.args) < 2:
        await safe_reply(update.message, "Usage: `/removecredits <user_id> <amount>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        amount = int(context.args[1])
        if deduct_credits(target, amount):
            await safe_reply(update.message, f"✅ Removed {amount} from `{target}`.\nNew: `{get_credits(target)}`", parse_mode="Markdown")
        else:
            await safe_reply(update.message, "❌ Insufficient credits.")
    except:
        await safe_reply(update.message, "❌ Invalid input.")

async def checkcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if not context.args:
        await safe_reply(update.message, "Usage: `/checkcredits <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        await safe_reply(update.message, f"💰 User `{target}` has `{get_credits(target)}` credits.", parse_mode="Markdown")
    except:
        await safe_reply(update.message, "❌ Invalid user ID.")

async def resetcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if not context.args:
        await safe_reply(update.message, "Usage: `/resetcredits <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        set_credits(target, 0)
        await safe_reply(update.message, f"✅ Reset credits for `{target}`.", parse_mode="Markdown")
    except:
        await safe_reply(update.message, "❌ Invalid user ID.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if not context.args:
        await safe_reply(update.message, "Usage: `/ban <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        ban_user(target, update.effective_user.id)
        await safe_reply(update.message, f"🚫 User `{target}` banned.", parse_mode="Markdown")
    except:
        await safe_reply(update.message, "❌ Invalid user ID.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if not context.args:
        await safe_reply(update.message, "Usage: `/unban <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        if unban_user(target):
            await safe_reply(update.message, f"✅ User `{target}` unbanned.", parse_mode="Markdown")
        else:
            await safe_reply(update.message, "❌ User was not banned.")
    except:
        await safe_reply(update.message, "❌ Invalid user ID.")

async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    banned = load_json(BANNED_FILE, {})
    if not banned:
        await safe_reply(update.message, "📭 No banned users.")
        return
    lines = [f"🚫 *BANNED USERS ({len(banned)})*\n━━━━━━━━━━━━━━━━━━━━━━"]
    for i, (uid, info) in enumerate(banned.items(), 1):
        lines.append(f"{i}. `{uid}` – by `{info.get('by','?')}`")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

async def gencode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if len(context.args) < 2:
        await safe_reply(update.message, "Usage: `/gencode <credits> <uses>`", parse_mode="Markdown")
        return
    try:
        credits = int(context.args[0])
        uses = int(context.args[1])
        code = generate_code(credits, uses)
        await safe_reply(update.message,
            f"🎟️ *CODE GENERATED*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Code: `{code}`\nCredits: `{credits}`\nUses: `{uses}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown")
    except:
        await safe_reply(update.message, "❌ Invalid input.")

async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if not context.args:
        await safe_reply(update.message, "Usage: `/notify <message>`", parse_mode="Markdown")
        return
    msg = " ".join(context.args)
    data = load_json(CREDITS_FILE, {})
    success = 0
    failed = 0
    for uid in data.keys():
        try:
            await context.bot.send_message(int(uid), f"📢 *NOTICE*\n\n{msg}", parse_mode="Markdown")
            success += 1
        except:
            failed += 1
    await safe_reply(update.message, f"✅ Sent: `{success}` | ❌ Failed: `{failed}`", parse_mode="Markdown")

async def phonelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    data = load_json(PHONE_LOGIN_FILE, {})
    if not data:
        await safe_reply(update.message, "📭 No phone login requests.")
        return
    lines = ["📱 *PHONE LOGIN REQUESTS*\n━━━━━━━━━━━━━━━━━━━━━━"]
    for i, (uid, info) in enumerate(data.items(), 1):
        lines.append(f"{i}. @{info.get('username','N/A')} – `{uid}` – {info.get('referrals',0)} refs – {info.get('status','?').upper()}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

async def phonemark_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    if not context.args:
        await safe_reply(update.message, "Usage: `/phonemark <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(context.args[0])
        if mark_phone_provided(target):
            await safe_reply(update.message, f"✅ Marked `{target}` as provided.", parse_mode="Markdown")
        else:
            await safe_reply(update.message, "❌ User not found in phone login requests.")
    except:
        await safe_reply(update.message, "❌ Invalid user ID.")

async def supportlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    data = load_json(SUPPORT_FILE, [])
    if not data:
        await safe_reply(update.message,
            "📭 *NO SUPPORT MESSAGES YET*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "No users have contacted support.",
            parse_mode="Markdown")
        return
    lines = ["📩 *LAST SUPPORT MESSAGES*\n━━━━━━━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(data[:10], 1):
        lines.append(f"{i}. @{item.get('username','N/A')} (`{item.get('user_id','?')}`)\n   💬 {item.get('message','')[:60]}...\n   🕐 {item.get('time','')}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    await safe_reply(update.message, "\n".join(lines), parse_mode="Markdown")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await safe_reply(update.message, "⛔ Admins only.")
        return
    await safe_reply(update.message, f"👥 Total Users: `{get_total_user_count()}`", parse_mode="Markdown")

# ========== FILE HANDLER ==========
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    document = update.message.document
    if not document:
        return

    if context.user_data.get("awaiting_restore"):
        context.user_data.pop("awaiting_restore")
        await restore_handle_document(update, context)
        return

    file_name = document.file_name.lower()
    if document.file_size > 5 * 1024 * 1024:
        await safe_reply(update.message, "❌ File too large (max 5 MB).")
        return

    if context.user_data.get("awaiting_single_file"):
        context.user_data.pop("awaiting_single_file")
        if not (file_name.endswith(".txt") or file_name.endswith(".json")):
            await safe_reply(update.message, "❌ Only .txt or .json files.")
            return
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        content = file_bytes.decode("utf-8", errors="ignore")
        netflix_id = extract_netflix_id_from_text(content)
        if not netflix_id:
            await safe_reply(update.message, "❌ No valid NetflixId found.")
            return
        success, msg = add_cookie_with_metadata(user.id, document.file_name, netflix_id)
        if success:
            await safe_reply(update.message, f"✅ Cookie added: `{document.file_name}`", parse_mode="Markdown")
        else:
            await safe_reply(update.message, "⚠️ Cookie already exists.")
        return

    if context.user_data.get("awaiting_bulk_file"):
        context.user_data.pop("awaiting_bulk_file")
        if not (file_name.endswith(".zip") or (RAR_SUPPORT and file_name.endswith(".rar"))):
            await safe_reply(update.message, "❌ Please upload .zip or .rar.")
            return
        file = await context.bot.get_file(document.file_id)
        raw_data = await file.download_as_bytearray()
        added = 0
        if file_name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw_data)) as zf:
                for fname in zf.namelist():
                    if fname.lower().endswith((".txt", ".json")):
                        content = zf.read(fname).decode("utf-8", errors="ignore")
                        nid = extract_netflix_id_from_text(content)
                        if nid:
                            s, _ = add_cookie_with_metadata(user.id, fname, nid)
                            if s:
                                added += 1
        elif RAR_SUPPORT and file_name.endswith(".rar"):
            with rarfile.RarFile(io.BytesIO(raw_data)) as rf:
                for fname in rf.namelist():
                    if fname.lower().endswith((".txt", ".json")):
                        content = rf.read(fname).decode("utf-8", errors="ignore")
                        nid = extract_netflix_id_from_text(content)
                        if nid:
                            s, _ = add_cookie_with_metadata(user.id, fname, nid)
                            if s:
                                added += 1
        await safe_reply(update.message, f"✅ Added {added} cookie(s).")
        return

    await safe_reply(update.message, "Use /addsingle or /bulkadd first.")

# ========== SET COMMANDS ==========
async def set_commands(app: Application):
    default_commands = [
        BotCommand("start", "Welcome"),
        BotCommand("help", "Show help"),
        BotCommand("login", "Activate TV code"),
        BotCommand("credits", "Check balance"),
        BotCommand("redeem", "Redeem a code"),
        BotCommand("gift", "Gift credits"),
        BotCommand("leaderboard", "Top users"),
        BotCommand("richlist", "Top richest"),
        BotCommand("panel", "Your stats"),
        BotCommand("history", "Login history"),
        BotCommand("support", "Contact admin"),
    ]
    await app.bot.set_my_commands(default_commands)

    admin_commands = default_commands + [
        BotCommand("addsingle", "Add single cookie"),
        BotCommand("bulkadd", "Add ZIP/RAR cookies"),
        BotCommand("listcookies", "List all cookies"),
        BotCommand("delcookie", "Delete a cookie"),
        BotCommand("delall", "Delete all cookies"),
        BotCommand("userstats", "User login stats"),
        BotCommand("backupcookies", "Backup all cookies"),
        BotCommand("restorecookies", "Restore cookies"),
        BotCommand("addcredits", "Add credits"),
        BotCommand("removecredits", "Remove credits"),
        BotCommand("checkcredits", "Check user credits"),
        BotCommand("resetcredits", "Reset user credits"),
        BotCommand("ban", "Ban a user"),
        BotCommand("unban", "Unban a user"),
        BotCommand("banlist", "List banned users"),
        BotCommand("gencode", "Generate redeem code"),
        BotCommand("notify", "Broadcast to all users"),
        BotCommand("phonelist", "Phone login requests"),
        BotCommand("phonemark", "Mark phone provided"),
        BotCommand("reply", "Reply to a user"),
        BotCommand("supportlist", "Last support messages"),
        BotCommand("cancel", "Cancel pending action"),
        BotCommand("users", "Total user count"),
    ]
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as e:
            logger.warning(f"Could not set commands for admin {admin_id}: {e}")

# ========== MAIN ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("credits", credits_command))
    app.add_handler(CommandHandler("redeem", redeem_command))
    app.add_handler(CommandHandler("gift", gift_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("richlist", richlist_command))
    app.add_handler(CommandHandler("panel", panel_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Admin commands
    app.add_handler(CommandHandler("addsingle", addsingle_command))
    app.add_handler(CommandHandler("bulkadd", bulkadd_command))
    app.add_handler(CommandHandler("delall", delall_command))
    app.add_handler(CommandHandler("delall_confirm", delall_confirm))
    app.add_handler(CommandHandler("listcookies", list_cookies))
    app.add_handler(CommandHandler("delcookie", del_cookie))
    app.add_handler(CommandHandler("userstats", userstats_command))
    app.add_handler(CommandHandler("backupcookies", backupcookies_command))
    app.add_handler(CommandHandler("restorecookies", restorecookies_command))
    app.add_handler(CommandHandler("addcredits", addcredits_command))
    app.add_handler(CommandHandler("removecredits", removecredits_command))
    app.add_handler(CommandHandler("checkcredits", checkcredits_command))
    app.add_handler(CommandHandler("resetcredits", resetcredits_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("banlist", banlist_command))
    app.add_handler(CommandHandler("gencode", gencode_command))
    app.add_handler(CommandHandler("notify", notify_command))
    app.add_handler(CommandHandler("phonelist", phonelist_command))
    app.add_handler(CommandHandler("phonemark", phonemark_command))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(CommandHandler("supportlist", supportlist_command))
    app.add_handler(CommandHandler("users", users_command))

    # Text & Media handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_support_media_entry))
    app.add_handler(MessageHandler(filters.VIDEO, handle_support_media_entry))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.post_init = set_commands
    print("✅ Toxic Netflix Bot running – full features.")
    app.run_polling()

if __name__ == "__main__":
    main()