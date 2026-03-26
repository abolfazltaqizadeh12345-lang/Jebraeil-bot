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
last_message_time = {}

# =========================
# دیتابیس
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS group_users (
    chat_id INTEGER,
    user_id INTEGER
)
""")

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
# منو
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📜 قوانین", callback_data="rules")],
        [InlineKeyboardButton("💡 پیشنهادات", callback_data="suggestions")]
    ]
    await update.message.reply_text("سلام 👋", reply_markup=InlineKeyboardMarkup(keyboard))

# =========================
# دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rules":
        await query.message.edit_text("📜 احترام + اسپم ممنوع")

    elif query.data == "suggestions":
        await query.message.edit_text("پیشنهادتو بفرست")

# =========================
# لول خود
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
    users = [row[0] for row in cursor.fetchall()]

    if not users:
        await update.message.reply_text("❌ داده‌ای نیست")
        return

    leaderboard = []

    for user_id in users:
        cursor.execute("SELECT xp FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        xp = row[0] if row else 0
        leaderboard.append((user_id, xp))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    text = "🏆 رتبه‌بندی:\n\n"

    for i, (user_id, xp) in enumerate(leaderboard[:10], start=1):
        lvl = get_level(xp)

        try:
            user = await context.bot.get_chat(user_id)
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

    if update.message.text.strip() == "لول":
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
    if not update.message:
        return

    user_id = update.message.from_user.id
    text = update.message.text.strip()
    clean_text = normalize(text)
    chat_id = update.message.chat.id

    # ذخیره کاربر گروه
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

    # دستورات
    if clean_text == "لول":
        await show_level(update, context)
        return

    if clean_text == "رتبه":
        await show_leaderboard(update, context)
        return

    # پاسخ ساده (دقیق)
    for key in responses:
        if clean_text == key:
            await update.message.reply_text(random.choice(responses[key]))
            return

# =========================
# پیام رندوم
# =========================
async def send_random_message(context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("SELECT DISTINCT chat_id FROM group_users")
    chats = [row[0] for row in cursor.fetchall()]

    for chat_id in chats:

        cursor.execute("SELECT user_id FROM group_users WHERE chat_id=?", (chat_id,))
        users = [row[0] for row in cursor.fetchall()]

        if not users:
            continue

        user_id = random.choice(users)
        text = random.choice(random_messages)

        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name
        except:
            name = "کاربر"

        mention = f"<a href='tg://user?id={user_id}'>{name}</a>"

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{text}\n\n{mention}",
            parse_mode="HTML"
        )

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

    print("🚀 Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
