import random
import os
import time
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
    "ربات": ["چی موگی 🫩", "رباتم اما منم دل دارم 😔"],
    "سلام": ["سلام 👋", "درود 😎", "سلام رفیق ❤️"],
    "خوبی": ["مرسی خوبم 😁", "تو خوبی؟ 😎"],
    "چطوری": ["عالی‌ام 😎", "مرسی، تو چطوری؟ ❤️"]
}

# =========================
# دیتابیس علمی
# =========================
knowledge_base = {
    "آسمان چرا آبی است": "آسمان به خاطر پراکندگی نور خورشید در جو زمین آبی دیده می‌شود.",
    "آمریکا کجاست": "آمریکا در قاره آمریکای شمالی قرار دارد.",
    "ایران کجاست": "ایران در خاورمیانه و در قاره آسیا قرار دارد.",
    "افغانستان کجاست": "افغانستان در جنوب آسیا قرار دارد و پایتخت آن کابل است.",
}

countries_info = {
    "ایران": "پایتخت: تهران 🇮🇷\nجمعیت: حدود ۸۵ میلیون",
    "افغانستان": "پایتخت: کابل 🇦🇫\nجمعیت: حدود ۴۰ میلیون",
    "آمریکا": "پایتخت: واشنگتن 🇺🇸\nجمعیت: حدود ۳۳۰ میلیون",
}

attitude = [
    "تو خیلی سوالای عجیبی می‌پرسی 😏",
    "فکر کردی من همه چی رو می‌دونم؟ 😂",
    "بد نیست سوالای بهتر بپرسی 😎",
    "جالبه 👀 ادامه بده"
]

# =========================
# تمیز کردن متن برای پاسخ ساده
# =========================
def clean_text(text):
    return text.strip().replace("!", "").replace("؟", "").replace("?", "").replace(".", "").replace("،", "")

# =========================
# AI فیک
# =========================
def fake_ai_response(text, name=""):
    return f"ببین 🤔\nاین موضوع بستگی به شرایط مختلف داره و میشه از چند زاویه بررسیش کرد.\n\nسوال جالبی بود 😏"

# =========================
# AI هوشمند
# =========================
def smart_ai(text, user_id, name):
    text_clean = text.strip()

    user_memory[user_id] = text_clean

    if "اسم من چیه" in text_clean:
        return f"اسم تو {name} هست 😎"

    if "چی گفتم" in text_clean:
        return f"آخرین چیزی که گفتی:\n{text_clean}"

    for key in knowledge_base:
        if key in text_clean:
            return f"{name} 👀\n{knowledge_base[key]}"

    for country in countries_info:
        if country in text_clean:
            return f"{name} 🌍\n{countries_info[country]}"

    if random.random() < 0.3:
        return random.choice(attitude)

    return fake_ai_response(text_clean, name)

# =========================
# منوی اصلی
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"سلام {update.effective_user.first_name} 👋"

    keyboard = [
        [InlineKeyboardButton("📜 قوانین ربات", callback_data="rules")],
        [InlineKeyboardButton("➕ اضافه کردن ربات به گروه", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("👤 مالک ربات", url="https://t.me/itxxabolfazl")],
        [InlineKeyboardButton("💡 پیشنهادات", callback_data="suggestions")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# =========================
# دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rules":
        await query.message.edit_text("📜 قوانین:\n1️⃣ احترام\n2️⃣ اسپم ممنوع")

    elif query.data == "suggestions":
        user_states[query.from_user.id] = "waiting_for_suggestion"
        await query.message.edit_text("پیشنهادت رو بفرست")

    elif query.data == "back_to_menu":
        user_states.pop(query.from_user.id, None)
        await start(update, context)

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
        user_id = int(text.split("ID:")[1])
        await context.bot.send_message(chat_id=user_id, text=update.message.text)

# =========================
# پیام‌ها
# =========================
async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text.strip()
    chat_id = update.message.chat.id

    # ذخیره کاربران گروه
    if update.message.chat.type in ["group", "supergroup"]:
        group_users.setdefault(chat_id, set()).add(user_id)

    # پیشنهادات
    if user_states.get(user_id) == "waiting_for_suggestion":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"{text}\nID:{user_id}"
        )
        return

    # 🔥 پاسخ ساده (هوشمند با حذف ! ؟)
    cleaned = clean_text(text)
    if cleaned in responses:
        await update.message.reply_text(random.choice(responses[cleaned]))
        return

    # 🤖 AI
    if text.startswith("ربات:"):
        user_text = text.replace("ربات:", "").strip()
        reply = smart_ai(user_text, user_id, update.message.from_user.first_name)
        await update.message.reply_text(reply)
        return

# =========================
# پیام رندوم
# =========================
async def send_random_message(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, users in group_users.items():
        if not users:
            continue

        user_id = random.choice(list(users))
        text = random.choice(random_messages)

        mention = f"<a href='tg://user?id={user_id}'>کاربر</a>"

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

    app.job_queue.run_repeating(send_random_message, interval=6600, first=60)

    print("🚀 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
