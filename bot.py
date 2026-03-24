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
            [InlineKeyboardButton("🏠 برگشت به منو", callback_data="back_to_menu")]
        ]

        await query.message.edit_text(
            "💡 پیشنهاداتت رو بفرست (می‌تونی چند پیام بفرستی)\n\nبرای خروج روی دکمه زیر بزن 👇",
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

    # XP ضد اسپم
    now = time.time()
    if user_id not in last_message_time or now - last_message_time[user_id] > 5:
        user_xp[user_id] = user_xp.get(user_id, 0) + 5
        last_message_time[user_id] = now

    # پیشنهادات (بدون پیام مزاحم)
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
        if key in text:
            await update.message.reply_text(random.choice(responses[key]))
            return

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
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # مهم: اول ادمین
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_messages))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
