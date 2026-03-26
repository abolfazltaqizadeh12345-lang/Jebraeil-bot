import random
import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# =========================
# تنظیمات
# =========================
TOKEN = os.environ.get("TOKEN")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")

if not TOKEN:
    raise ValueError("❌ TOKEN پیدا نشد")

ADMIN_ID = 7801959849
user_states = {}
user_xp = {}
last_message_time = {}
group_users = {}

# =========================
# پیام‌های رندوم
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
# AI
# =========================
async def ask_ai(prompt):
    url = "https://api.together.xyz/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        print("AI RAW:", response.text)  # 👈 خیلی مهم

        result = response.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return "❌ پاسخ نامعتبر از AI"

    except Exception as e:
        print("AI Error:", e)
        return "❌ خطا در پاسخ AI"

# =========================
# لول
# =========================
def get_level(xp):
    return xp // 100

# =========================
# منوی اصلی
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

        keyboard = [
            [InlineKeyboardButton("ثبت پیشنهاد ✅", callback_data="back_to_menu")]
        ]

        await query.message.edit_text(
            "پیشنهادت رو بنویس ( میتونی چند پیام بفرستی ) و بعد ثبت کن 🙂",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "back_to_menu":
        user_states.pop(user_id, None)
        await query.message.delete()
        await start(update, context)

# =========================
# نمایش لول
# =========================
async def show_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    xp = user_xp.get(user_id, 0)
    lvl = get_level(xp)

    await update.message.reply_text(f"🎮 Level: {lvl}\n⭐ XP: {xp}")

# =========================
# پاسخ ساده
# =========================
responses = {
    "ربات": ["چی موگی 🫩", "رباتم اما منم دل دارم 😔", "بوگو میشنوم 🥴"],
    "سلام": ["سلام 👋", "درود 😎", "سلام رفیق ❤️"],
    "خوبی": ["مرسی خوبم 😁", "تو خوبی؟ 😎"],
    "چطوری": ["عالی‌ام 😎", "مرسی، تو چطوری؟ ❤️"]
}

# =========================
# پاسخ ادمین
# =========================
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    text = update.message.reply_to_message.text or ""

    if "ID:" in text:
        try:
            user_id = int(text.split("ID:")[1].strip())

            await context.bot.send_message(
                chat_id=user_id,
                text=f"📩 پاسخ ادمین:\n\n{update.message.text}"
            )

            await update.message.reply_text("✅ پاسخ ارسال شد")

        except:
            await update.message.reply_text("❌ خطا در ارسال")

# =========================
# پیام‌ها
# =========================
async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text.strip().replace("!", "").replace("؟", "").replace("?", "")
    chat_id = update.message.chat.id

    # ذخیره کاربران گروه
    if update.message.chat.type in ["group", "supergroup"]:
        if chat_id not in group_users:
            group_users[chat_id] = set()
        group_users[chat_id].add(user_id)

    # XP ضد اسپم
    now = time.time()
    if user_id not in last_message_time or now - last_message_time[user_id] > 5:
        user_xp[user_id] = user_xp.get(user_id, 0) + 5
        last_message_time[user_id] = now

    # پیشنهادات
    if user_states.get(user_id) == "waiting_for_suggestion":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 پیشنهاد:\n\n{text}\n\n👤 {update.message.from_user.first_name}\nID:{user_id}"
        )
        return

    # AI
    if text.startswith("ربات:"):
        user_text = text.replace("ربات:", "").strip()

        if not user_text:
            await update.message.reply_text("بعد از ربات: یه چیزی بنویس")
            return

        await update.message.reply_text("🤖 دارم فکر می‌کنم...")
        ai_reply = await ask_ai(user_text)
        await update.message.reply_text(ai_reply)
        return

    # لول
    if text == "لول":
        await show_level(update, context)
        return

    # پاسخ ساده
    for key in responses:
        if text == key:
            await update.message.reply_text(random.choice(responses[key]))
            return

# =========================
# پیام رندوم هر ۵۵ دقیقه
# =========================
async def send_random_message(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, users in group_users.items():

        if not users:
            continue

        user_id = random.choice(list(users))
        text = random.choice(random_messages)

        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name
        except:
            name = "یه نفر"

        mention = f"<a href='tg://user?id={user_id}'>{name}</a>"

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{text}\n\n{mention}",
                parse_mode="HTML"
            )
        except Exception as e:
            print("Error:", e)

# =========================
# خوش‌آمدگویی
# =========================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            await update.message.reply_text(f"{member.first_name} خوش اومدی ❤️")

# =========================
# اجرا
# =========================
def main():
    from telegram.ext import JobQueue

    job_queue = JobQueue()
    app = ApplicationBuilder().token(TOKEN).job_queue(job_queue).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_messages))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    app.job_queue.run_repeating(send_random_message, interval=6600, first=60)

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
