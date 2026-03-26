import random
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

TOKEN = os.environ.get("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN پیدا نشد")

ADMIN_ID = 7801959849
user_states = {}
user_xp = {}
last_message_time = {}
group_users = {}
user_memory = {}

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
# پاسخ ساده
# =========================
responses = {
    "سلام": ["سلام 👋", "درود 😎"],
    "خوبی": ["مرسی خوبم 😁", "تو خوبی؟ 😎"],
    "چطوری": ["عالی‌ام 😎", "تو چطوری؟ ❤️"]
}

# =========================
# دیتابیس
# =========================
knowledge_base = {
    "آسمان چرا آبی است": "آسمان به خاطر پراکندگی نور خورشید آبی دیده می‌شود.",
    "آمریکا کجاست": "آمریکا در قاره آمریکای شمالی قرار دارد.",
    "ایران کجاست": "ایران در قاره آسیا قرار دارد.",
    "افغانستان کجاست": "افغانستان در جنوب آسیا است و پایتخت آن کابل است."
}

countries_info = {
    "ایران": "پایتخت: تهران 🇮🇷",
    "افغانستان": "پایتخت: کابل 🇦🇫",
    "آمریکا": "پایتخت: واشنگتن 🇺🇸"
}

attitude = [
    "تو خیلی سوالای عجیبی می‌پرسی 😏",
    "فکر کردی من همه چی رو می‌دونم؟ 😂",
    "جالبه 👀"
]

# =========================
# تمیز کردن متن
# =========================
def clean_text(text):
    return text.strip().replace("!", "").replace("؟", "").replace("?", "").replace(".", "").replace("،", "")

# =========================
# AI ساده‌تر و طبیعی‌تر
# =========================
def smart_ai(text, user_id, name):
    text_clean = clean_text(text)

    user_memory[user_id] = text_clean

    # جواب ساده داخل AI
    if text_clean in responses:
        return random.choice(responses[text_clean])

    # سوال نبود → چرت نگو!
    question_words = ["چرا", "چطور", "چگونه", "کجاست", "چیست"]
    if not any(q in text_clean for q in question_words):
        return random.choice([
            "منظورتو واضح‌تر بگو 🤔",
            "دقیق متوجه نشدم 😐",
            "یه کم بیشتر توضیح بده 👀"
        ])

    # دیتابیس
    for key in knowledge_base:
        if key in text_clean:
            return knowledge_base[key]

    for country in countries_info:
        if country in text_clean:
            return countries_info[country]

    # fallback
    return random.choice([
        "سوال جالبی بود 😏",
        "این موضوع بستگی به شرایط داره 🤔",
        "می‌تونه چند دلیل داشته باشه 👀"
    ])

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

    if query.data == "suggestions":
        user_states[query.from_user.id] = "waiting_for_suggestion"
        await query.message.edit_text("پیشنهادتو بفرست")

# =========================
# پیام‌ها
# =========================
async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text.strip()
    chat_id = update.message.chat.id

    # ذخیره اعضا
    if update.message.chat.type in ["group", "supergroup"]:
        group_users.setdefault(chat_id, set()).add(user_id)

    # پیشنهاد
    if user_states.get(user_id):
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"{text}\nID:{user_id}"
        )
        return

    # پاسخ ساده
    cleaned = clean_text(text)
    if cleaned in responses:
        await update.message.reply_text(random.choice(responses[cleaned]))
        return

    # AI
    if text.startswith("ربات:"):
        user_text = text.replace("ربات:", "").strip()
        reply = smart_ai(user_text, user_id, update.message.from_user.first_name)
        await update.message.reply_text(reply)
        return

# =========================
# پیام رندوم (اصلاح شده)
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
            name = "دوست"

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_messages))

    app.job_queue.run_repeating(send_random_message, interval=6600, first=60)

    print("🚀 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
