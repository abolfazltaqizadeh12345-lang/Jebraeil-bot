import random
import os
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# =========================
# توکن ربات و OpenAI
# =========================
TOKEN = os.environ.get("TOKEN")
OPENAI_API_KEY = os.environ.get("OPENROUTER_API_KEY")  # همان اسم متغیر قدیمی
openai.api_key = OPENAI_API_KEY

ADMIN_ID = 7801959849
user_states = {}
user_xp = {}

# =========================
# محاسبه لول
# =========================
def get_level(xp):
    return xp // 100

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
# نمایش لول
# =========================
async def show_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    xp = user_xp.get(user_id, 0)
    lvl = get_level(xp)
    text = f"🎮 لول شما: {lvl}\n⭐ XP: {xp}"
    if user_id == ADMIN_ID and update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_xp = user_xp.get(target_user.id, 0)
        target_lvl = get_level(target_xp)
        text += f"\n\n👤 لول {target_user.first_name}:\n🎮 {target_lvl}\n⭐ XP: {target_xp}"
    await update.message.reply_text(text)

# =========================
# پاسخ‌ها
# =========================
responses = {
    "سلام": ["سلام چطوری ؟", "درود بر تو 👋", "سلام رفیق 😎"],
    "خوبی": ["مرسی خوبم تو چطوری؟ 😁", "داکتری ؟", "نه 😐"],
    "چطوری": ["عالییی ام 😎", "خدت چطوری 😐", "مرسی، روزت خوب باشه ❤️"]
}

# =========================
# پیام‌ها + AI
# =========================
async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.message.from_user.id
    text = update.message.text.strip().lower()
    user_xp[user_id] = user_xp.get(user_id, 0) + 5
# پیشنهادات
    if user_states.get(user_id) == "waiting_for_suggestion":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 پیشنهاد جدید:\n\n{text}\n\n👤 از: {update.message.from_user.first_name}"
        )
        await update.message.reply_text("✅ پیشنهادت ارسال شد، ممنون ❤️")
        user_states.pop(user_id, None)
        return

    # AI OpenAI GPT-3.5
    if text.startswith("ربات بگو:"):
        user_text = text[len("ربات بگو:"):].strip()
        if not user_text:
            await update.message.reply_text("❗ بعد از 'ربات بگو:' یه چیزی بنویس")
            return
        await update.message.reply_text("🤖 دارم فکر می‌کنم...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_text}],
                temperature=0.7,
                max_tokens=300
            )
            ai_reply = response.choices[0].message.content
            if ai_reply:
                await update.message.reply_text(ai_reply)
            else:
                await update.message.reply_text("❌ متأسفم، نتونستم پاسخ بگیرم.")
        except Exception as e:
            print("OpenAI Error:", e)
            await update.message.reply_text("❌ خطا در دریافت پاسخ")
        return

    # لول
    if text == "لول":
        await show_level(update, context)
        return

    # قوانین لول
    if text == "قوانین لول ربات":
        await update.message.reply_text(
            "📜 قوانین لول و XP ربات:\n\n"
            "1️⃣ هر پیام = 5 XP\n"
            "2️⃣ هر 100 XP = 1 لول\n"
            "3️⃣ با 'لول' سطح خودتو ببین\n"
        )
        return

    # پاسخ دقیق
    for key in responses:
        if text == key:
            await update.message.reply_text(random.choice(responses[key]))
            break

# =========================
# خوش‌آمدگویی
# =========================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            await update.message.reply_text(f"{member.first_name} خوش اومدی ❤️")

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
