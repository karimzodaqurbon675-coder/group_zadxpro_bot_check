import telebot
import requests
import time
import json
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import os
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

# 1. ТОКЕН ВА ТАНЗИМОТ
BOT_TOKEN = "8555983030:AAGZSv3GDQ1ykoVs7nz-lMdcRhioG-kFEoc"
bot = telebot.TeleBot(BOT_TOKEN)

# МАҲДУДИЯТ: ID-и гурӯҳи ту
ALLOWED_GROUP_ID = -1003564455189

API_INFO_URL = "https://info-ob49.onrender.com/api/account/"

REQUIRED_CHATS = [
    {"id": "@zadxproooo", "name": "Канал 1", "url": "https://t.me/zadxproooo"},
    {"id": "@zadxprootziv", "name": "Канал 2", "url": "https://t.me/zadxprootziv"},
    {"id": "@groupzadxpro", "name": "Гуруҳи мо", "url": "https://t.me/groupzadxpro"}
]

ALL_REGIONS = ["ru", "sg", "ind", "br", "me", "us", "id", "pk", "bd", "cis", "tw", "vn", "th"]

# --- ФУНКСИЯҲОИ ТЕХНИКӢ ---

def escape_md(text):
    """Тоза кардани символҳои хатарнок барои пешгирии хатогӣ"""
    if not text: return "Холӣ"
    return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')

def get_avatar_name(avatar_id):
    try:
        with open('avatars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if str(item.get('id')) == str(avatar_id):
                    return escape_md(item.get('name_text'))
    except: pass
    return "Аватар ёфт нашуд"

def format_date(unix_timestamp):
    try:
        if not unix_timestamp or int(unix_timestamp) == 0: return "Маълумот нест"
        return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%d.%m.%Y %H:%M')
    except: return "Маълумот нест"

def get_not_subscribed(user_id):
    not_joined = []
    for chat in REQUIRED_CHATS:
        try:
            member = bot.get_chat_member(chat['id'], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(chat)
        except: not_joined.append(chat)
    return not_joined

def get_ff_player(player_id):
    for reg in ALL_REGIONS:
        try:
            r = requests.get(API_INFO_URL, params={"uid": player_id, "region": reg}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("basicInfo", {}).get("nickname"): return data, reg.upper()
        except: continue
    return None, None

# --- ҲЕНДЛЕРҲО ---

# 1. Функсияи САЛОМ (Вақте одами нав медарояд)
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    if message.chat.id != ALLOWED_GROUP_ID: return
    for new_user in message.new_chat_members:
        if new_user.id == bot.get_me().id: continue
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="📜 КОМАНДАҲО", callback_data="show_help"))
        bot.send_message(
            message.chat.id, 
            f"Ассалому алейкум, {escape_md(new_user.first_name)}! 👋\nХуш омадед ба гурӯҳи мо. Барои дидани командаҳо тугмаро пахш кунед.", 
            reply_markup=markup,
            parse_mode="Markdown"
        )

# 2. Функсияи HELP (Командаҳо)
@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda m: m.text == "/" and m.chat.id == ALLOWED_GROUP_ID)
def help_handler(message):
    help_text = (
        "📜 **ДАСТУРАМАЛИ КОМАНДАҲО:**\n\n"
        "👉 `/check ID` - Тафтиши пурраи акант\n"
        "👉 `/start` - Оғози бот (танҳо дар личка)\n\n"
        "📢 *Бот танҳо барои аъзоёни каналҳои мо кор мекунад!*"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# 3. Функсияи CHECK ID
@bot.message_handler(commands=['check'])
def check_id_command(message):
    if message.chat.id != ALLOWED_GROUP_ID: return 

    if get_not_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ Аввал ба каналҳо обуна шавед! (Дар личка /start нависед)")
        return

    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "❓ Намуна: `/check 8898233939`", parse_mode="Markdown")
        return

    player_id = args[-1]
    wait_msg = bot.reply_to(message, f"📡 **Ҷустуҷӯ:** `{player_id}`...")

    data, region = get_ff_player(player_id)
    if not data:
        bot.edit_message_text(f"❌ ID ёфт нашуд!", message.chat.id, wait_msg.message_id)
        return

    b = data.get("basicInfo", {})
    s = data.get("socialInfo", {})
    c = data.get("clanBasicInfo", {})
    cr = data.get("creditScoreInfo", {})
    
    # Безарар кардани матнҳо
    nickname = escape_md(b.get('nickname', '?'))
    bio = escape_md(s.get('signature', 'Холӣ'))
    clan_name = escape_md(c.get('clanName', 'Нест'))
    avatar_name = get_avatar_name(b.get('headPic', 0))

    last_log = int(b.get("lastLoginAt", 0))
    days_off = int((time.time() - last_log) / 86400) if last_log > 0 else 0
    status = "🟢 ФАЪОЛ" if days_off < 7 else "🔴 ОФЛАЙН"

    text = (
        f"📂 **МАЪЛУМОТИ ПУРРАИ АККАУНТ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Никнейм:** {nickname}\n"
        f"🆔 **ID:** {player_id}\n"
        f"🌍 **Регион:** {region}\n"
        f"🛡️ **Статус:** {status}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🖼️ **Аватар:** {avatar_name}\n"
        f"📊 **Сатҳ (Level):** {b.get('level','?')}\n"
        f"📈 **Таҷриба (Exp):** {b.get('exp','?')}\n"
        f"❤️ **Лайкҳо:** {b.get('liked',0)}\n"
        f"🏆 **Ранг (Rank):** {b.get('rank', '?')}\n"
        f"📉 **Кредит:** {cr.get('creditScore', 100)}/100\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 **Клан:** {clan_name}\n"
        f"🆔 **ID Клан:** {c.get('clanId','0')}\n"
        f"🎖️ **Сатҳи Клан:** {c.get('clanLevel','?')}\n"
        f"👥 **Аъзоёни Клан:** {c.get('memberNum','?')}/{c.get('capacity','?')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 **Охирин бор:** {format_date(last_log)}\n"
        f"📅 **Сохта шуд:** {format_date(b.get('createTime', 0))}\n"
        f"⏳ **Офлайн:** {days_off} рӯз\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 **Оми (Bio):** {bio}\n"
        f"🌐 **Забон:** {s.get('language','?')}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    try:
        bot.edit_message_text(text, message.chat.id, wait_msg.message_id, parse_mode="Markdown")
    except:
        bot.edit_message_text(text, message.chat.id, wait_msg.message_id)

# Callback барои тугмаи Салом
@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def callback_help(call):
    bot.answer_callback_query(call.id)
    help_handler(call.message)

print("🚀 Бот фаъол шуд!")

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

import threading

threading.Thread(target=run_web).start()

bot.infinity_polling()