import random
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

TOKEN = os.environ.get("TOKEN")

# 👇 آیدی عددی خودتو بزار
ADMIN_ID = 7801959849

# ذخیره وضعیت کاربر
user_states = {}

# =========================
# منوی اصلی
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"سلام به ربات اختصاصی جبرئیل من خوش آمدی {update.effective_user.first_name} 👋\n"
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
        text = (
            "📜 قوانین ربات:\n"
            "1️⃣ احترام به اعضای گروه\n"
            "2️⃣ اسپم ممنوع\n"
            "3️⃣ استفاده صحیح از ربات\n"
            "4️⃣ هرگونه مزاحمت حذف خواهد شد"
        )

        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "suggestions":
        user_states[user_id] = "waiting_for_suggestion"

        await query.message.edit_text(
            "💡 پیشنهادت رو بنویس و بفرست:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data="back_to_menu")]])
        )

    elif query.data == "back_to_menu":
        user_states.pop(user_id, None)
        await start(update, context)

# =========================
# پاسخ به پیام‌ها + پیشنهادات
# =========================
responses = {
    "سلام": ["سلام چطوری ؟", "درود بر تو 👋", "سلام رفیق 😎"],
    "خوبی": ["مرسی خوبم تو چطوری؟ 😁", "داکتری ؟", "نه 😐"],
    "چطوری": ["عالییی ام 😎", "خدت چطوری 😐", "مرسی، روزت خوب باشه ❤️"]
}

async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text

    # 📩 اگر کاربر در حال ارسال پیشنهاد است
    if user_states.get(user_id) == "waiting_for_suggestion":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 پیشنهاد جدید:\n\n{text}\n\n👤 از: {update.message.from_user.first_name}"
        )

        await update.message.reply_text("✅ پیشنهادت ارسال شد، ممنون ❤️")
        user_states.pop(user_id, None)
        return

    # 💬 پاسخ‌های معمولی
    text_lower = text.lower()
    for key in responses:
        if key in text_lower:
            await update.message.reply_text(random.choice(responses[key]))
            break

# =========================
# خوش‌آمدگویی
# =========================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            await update.message.reply_text(f"{member.first_name} خوش اومدی به گروه جبرئیل من ❤️")

# =========================
# اجرای ربات
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_messages))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    print("ربات اجرا شد 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
