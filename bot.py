import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8650092381:AAHkP3bcqs1sNby-XPzjn-njLnnGgH_zyCM"

# هندلر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"سلام به ربات اختصاصی جبرئیل من خوش آمدی {update.effective_user.first_name} 👋\n"
        "چطوری می‌تونم کمکت کنم؟"
    )
     
    # دکمه‌های اینلاین
    keyboard = [
        [InlineKeyboardButton("📜 قوانین ربات", callback_data="rules")],
        [InlineKeyboardButton("➕ اضافه کردن ربات به گروه", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("👤 مالک ربات", url="https://t.me/itxxabolfazl")],
        [InlineKeyboardButton("💡 پیشنهادات", callback_data="suggestions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


# 👇 اینو بیار بیرون (بدون فاصله اضافی)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rules":
        rules_text = (
            "📜 قوانین ربات:\n"
            "1️⃣ احترام به اعضای گروه\n"
            "2️⃣ اسپم ممنوع\n"
            "3️⃣ استفاده صحیح از ربات\n"
            "4️⃣ هرگونه مزاحمت حذف خواهد شد"
        )
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(rules_text, reply_markup=reply_markup)

    elif query.data == "suggestions":
        suggestions_text = "💡 در آپدیت بعدی اعمال می‌شود!"
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(suggestions_text, reply_markup=reply_markup)

    elif query.data == "back_to_menu":
        # پاک کردن پیام قبلی
        await query.message.delete()
        # دوباره منوی اصلی
        await start(update, context)

# هندلر پاسخ به پیام‌ها (سلام، خوبی، چطوری)
responses = {
    "سلام": ["سلام چطوری ؟", "درود بر تو 👋", "سلام رفیق 😎"],
    "خوبی": ["مرسی خوبم تو چطوری؟ 😁", "داکتری ؟", "نه 😐"],
    "چطوری": ["عالییی ام 😎", "خدت چطوری 😐", "مرسی، روزت خوب باشه ❤️"]
}

async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    for key in responses:
        if key in text:
            random_response = random.choice(responses[key])
            await update.message.reply_text(random_response)
            break

# خوش آمدگویی عضو جدید
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        name = member.first_name
        await update.message.reply_text(f"{name} خوش اومدی به گروه جبرئیل من ❤️")

# ساخت اپلیکیشن ربات
app = ApplicationBuilder().token(TOKEN).build()

# اضافه کردن هندلرها
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT, reply_messages))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

# اجرای ربات
app.run_polling()
