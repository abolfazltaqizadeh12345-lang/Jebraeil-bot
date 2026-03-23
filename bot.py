import random
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

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

    # هندل برای پیام و دکمه
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup)


# =========================
# دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
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
        text = "💡 در آپدیت بعدی اعمال می‌شود!"

        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back_to_menu":
        await start(update, context)


# =========================
# پاسخ به پیام‌ها
# =========================
responses = {
    "سلام": ["سلام چطوری ؟", "درود بر تو 👋", "سلام رفیق 😎"],
    "خوبی": ["مرسی خوبم تو چطوری؟ 😁", "داکتری ؟", "نه 😐"],
    "چطوری": ["عالییی ام 😎", "خدت چطوری 😐", "مرسی، روزت خوب باشه ❤️"]
}

async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()

    for key in responses:
        if key in text:
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
