import random
import os
import time
import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# =========================
# تنظیمات
# =========================
TOKEN = os.environ.get("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN پیدا نشد")

ADMIN_ID = 7801959849
user_states = {}
user_suggestions = {}
last_message_time = {}

# =========================
# دیتابیس
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, xp INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS group_users (chat_id INTEGER, user_id INTEGER)")
conn.commit()

# =========================
# پیام رندوم
# =========================
random_messages = [
    "جانم اسپند دود کو نظر نشی 😉",
    "جان جان چشمایت صدقه 😍",
    "مورده یی یا زنده ؟ 🙁",
    "زیبو دری یا گنگه یی ؟ 😐",
    "بلیبور تو شنوم 😍",
    "یگو دفه گپ بزن بفامیم زنده یی 👀",
    "چخبر مقبولک 😁"
]

# =========================
# پاسخ ساده
# =========================
responses = {
    "ربات": ["چی موگی 🫩", "رباتم اما منم دل دارم 😔", "بوگو میشنوم 🥴"],
    "سلام": ["سلام 👋", "درود 😎", "سلام رفیق ❤️"],
    "خوبی": ["مرسی خوبم 😁", "تو خوبی؟ 😎"],
    "چطوری": ["عالی‌ام 😎", "مرسی، تو چطوری؟ ❤️"]
}

def normalize(text):
    return re.sub(r'[^\w\s]', '', text).strip()

# =========================
# لول
# =========================
def get_level(xp):
    return xp // 100

# =========================
# منوی اصلی (بدون تغییر)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"سلام {update.effective_user.first_name} 👋\n"
        "چطوری می‌تونم کمکت کنم؟"
    )

    keyboard = [
        [InlineKeyboardButton("📜 قوانین ربات", callback_data="rules")],
        [InlineKeyboardButton("➕ اضافه کردن ربات به گروه", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("👤 مالک ربات", url="https://t.me/itxxabolfazl")],
        [InlineKeyboardButton("💡 پیشنهادات", callback_data="suggestions")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup)

# =========================
# دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "rules":
        keyboard = [[InlineKeyboardButton("🏠 برگشت", callback_data="back_to_menu")]]
        await query.message.edit_text(
            "📜 قوانین ربات:\n1️⃣ احترام\n2️⃣ اسپم ممنوع",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "suggestions":
        user_states[user_id] = "waiting_for_suggestion"
        user_suggestions[user_id] = []

        keyboard = [
            [InlineKeyboardButton("ثبت پیشنهاد ✅", callback_data="submit_suggestion")],
            [InlineKeyboardButton("🏠 بازگشت به منو", callback_data="back_to_menu")]
        ]

        await query.message.edit_text(
            "پیشنهادتو بنویس (می‌تونی چند پیام بفرستی) 🙂",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "submit_suggestion":

        if user_id not in user_suggestions or not user_suggestions[user_id]:
            await query.answer("❌ چیزی ننوشتی", show_alert=True)
            return

        full_text = "\n".join(user_suggestions[user_id])

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 پیشنهاد کامل:\n\n{full_text}\n\n👤 {query.from_user.first_name}\nID:{user_id}"
        )

        user_states.pop(user_id, None)
        user_suggestions.pop(user_id, None)

        await query.message.delete()
        await start(update, context)

    elif query.data == "back_to_menu":
        user_states.pop(user_id, None)
        user_suggestions.pop(user_id, None)

        await query.message.delete()
        await start(update, context)

# =========================
# لول
# =========================
async def show_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute("SELECT xp FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    xp = row[0] if row else 0
    lvl = get_level(xp)

    await update.message.reply_text(f"🎮 Level: {lvl}\n⭐ XP: {xp}")

# =========================
# رتبه‌بندی
# =========================
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id

    cursor.execute("SELECT user_id FROM group_users WHERE chat_id=?", (chat_id,))
    users = [u[0] for u in cursor.fetchall()]

    if not users:
        await update.message.reply_text("❌ هنوز داده‌ای ندارم")
        return

    data = []
    for uid in users:
        cursor.execute("SELECT xp FROM users WHERE user_id=?", (uid,))
        row = cursor.fetchone()
        xp = row[0] if row else 0
        data.append((uid, xp))

    data.sort(key=lambda x: x[1], reverse=True)

    text = "🏆 جدول رده‌بندی:\n\n"

    for i, (uid, xp) in enumerate(data[:10], start=1):
        lvl = get_level(xp)
        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = "کاربر"

        text += f"{i}. {name} | Level: {lvl} | XP: {xp}\n"

    await update.message.reply_text(text)

# =========================
# ادمین
# =========================
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    text = update.message.reply_to_message.text

    if "ID:" in text:
        try:
            user_id = int(text.split("ID:")[1])

            await context.bot.send_message(
                chat_id=user_id,
                text=f"📩 پاسخ ادمین:\n\n{update.message.text}"
            )

            await update.message.reply_text("✅ پاسخ ارسال شد")

        except:
            await update.message.reply_text("❌ خطا در ارسال")

    elif normalize(update.message.text) == "لول":
        target = update.message.reply_to_message.from_user

        cursor.execute("SELECT xp FROM users WHERE user_id=?", (target.id,))
        row = cursor.fetchone()

        xp = row[0] if row else 0
        lvl = get_level(xp)

        await update.message.reply_text(
            f"🎮 لول {target.first_name}:\nLevel: {lvl}\nXP: {xp}"
        )

# =========================
# پیام‌ها
# =========================
async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text.strip()
    clean = normalize(text)
    chat_id = update.message.chat.id

    # ذخیره کاربران گروه
    if update.message.chat.type in ["group", "supergroup"]:
        cursor.execute("SELECT * FROM group_users WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO group_users VALUES (?, ?)", (chat_id, user_id))
            conn.commit()

    # XP
    now = time.time()
    if user_id not in last_message_time or now - last_message_time[user_id] > 5:

        cursor.execute("SELECT xp FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        if row:
            cursor.execute("UPDATE users SET xp=? WHERE user_id=?", (row[0] + 5, user_id))
        else:
            cursor.execute("INSERT INTO users VALUES (?, ?)", (user_id, 5))

        conn.commit()
        last_message_time[user_id] = now

    # پیشنهاد چندپیامی
    if user_states.get(user_id) == "waiting_for_suggestion":
        user_suggestions.setdefault(user_id, []).append(text)
        return

    # دستورات
    if clean == "لول":
        await show_level(update, context)
        return

    if clean == "رتبه":
        await show_leaderboard(update, context)
        return

    # پاسخ ساده
    for key in responses:
        if clean == key:
            await update.message.reply_text(random.choice(responses[key]))
            return

# =========================
# پیام رندوم
# =========================
async def send_random_message(context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("SELECT DISTINCT chat_id FROM group_users")
    chats = [c[0] for c in cursor.fetchall()]

    for chat_id in chats:
        cursor.execute("SELECT user_id FROM group_users WHERE chat_id=?", (chat_id,))
        users = [u[0] for u in cursor.fetchall()]

        if not users:
            continue

        uid = random.choice(users)
        text = random.choice(random_messages)

        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = "کاربر"

        mention = f"<a href='tg://user?id={uid}'>{name}</a>"

        await context.bot.send_message(chat_id, f"{text}\n\n{mention}", parse_mode="HTML")

# =========================
# اجرا
# =========================
def main():
    from telegram.ext import JobQueue

    app = ApplicationBuilder().token(TOKEN).job_queue(JobQueue()).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_messages))

    app.job_queue.run_repeating(send_random_message, interval=3300, first=60)

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
