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
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

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
# پاسخ ساده
# =========================
responses = {
    "ربات": ["چی موگی 🫩", "رباتم اما منم دل دارم 😔", "بوگو میشنوم 🥴"],
    "سلام": ["سلام 👋", "درود 😎", "سلام رفیق ❤️"],
    "خوبی": ["مرسی خوبم 😁", "تو خوبی؟ 😎"],
    "چطوری": ["عالی‌ام 😎", "مرسی، تو چطوری؟ ❤️"]
}

# =========================
# AI واقعی (HuggingFace)
# =========================
def ask_ai(prompt):
    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

    headers = {
        "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY')}"
    }

    payload = {
        "inputs": f"Answer in Persian: {prompt}"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        result = response.json()

        print("AI RESPONSE:", result)  # برای دیباگ

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]

        if "error" in result:
            return f"❌ AI Error: {result['error']}"

        return "❌ جواب مناسب نگرفتم"

    except Exception as e:
        print("AI ERROR:", e)
        return "❌ خطا در اتصال به AI"

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
            "پیشنهادت رو بنویس ( میتونی با چند پیام بنویسی ) و دکمه ثبت رو بزن ، بزودی پاسخ میدهیم 🙂",
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
# پاسخ ادمین
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

    # لول
    if text == "لول":
        await show_level(update, context)
        return

    # قوانین لول
    if text == "قوانین لول ربات":
        await update.message.reply_text(
            "📜 قوانین:\nهر پیام = 5 XP\nهر 100 XP = 1 Level"
        )
        return

    # پاسخ ساده
    for key in responses:
        if text == key:
            await update.message.reply_text(random.choice(responses[key]))
            return

    # 🤖 AI
    if text.startswith("ربات:"):
        user_text = text.replace("ربات:", "").strip()

        await update.message.reply_text("🤖 صبر کن...")

        reply = ask_ai(user_text)

        await update.message.reply_text(reply)
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

    app = ApplicationBuilder().token(TOKEN).job_queue(JobQueue()).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_messages))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    app.job_queue.run_repeating(send_random_message, interval=3300, first=60)

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
