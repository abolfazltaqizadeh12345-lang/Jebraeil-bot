import random
import os
import time
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# =========================
# توکن‌ها
# =========================
TOKEN = os.environ.get("TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ API KEY پیدا نشد")

client = OpenAI(api_key=OPENAI_API_KEY)

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
# استارت
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"سلام {update.effective_user.first_name} 👋"

    keyboard = [
        [InlineKeyboardButton("📜 قوانین", callback_data="rules")],
        [InlineKeyboardButton("💡 پیشنهاد", callback_data="suggestions")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "rules":
        await query.message.edit_text("📜 قوانین:\nاسپم نکن 😐")

    elif query.data == "suggestions":
        user_states[user_id] = "waiting"
        await query.message.edit_text("💡 پیشنهادتو بفرست")

# =========================
# لول
# =========================
async def show_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    xp = user_xp.get(user_id, 0)
    lvl = get_level(xp)

    await update.message.reply_text(f"🎮 Level: {lvl}\n⭐ XP: {xp}")

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

    # پیشنهاد
    if user_states.get(user_id) == "waiting":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 پیشنهاد:\n{text}"
        )
        await update.message.reply_text("✅ ارسال شد")
        user_states.pop(user_id, None)
        return

    # AI
    if text.startswith("ربات بگو:"):
        user_text = text.replace("ربات بگو:", "").strip()

        if not user_text:
            await update.message.reply_text("❗ یه چیزی بنویس")
            return

        await update.message.reply_text("🤖 ...")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": user_text}],
                temperature=0.7,
                max_tokens=300
            )

            ai_reply = response.choices[0].message.content
            await update.message.reply_text(ai_reply)

        except Exception as e:
            print("ERROR:", e)
            await update.message.reply_text(f"❌ خطا:\n{e}")

        return

    # لول
    if text == "لول":
        await show_level(update, context)
        return

    # پاسخ ساده
    if "سلام" in text:
        await update.message.reply_text("سلام 👋")

# =========================
# اجرا
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_messages))

    print("ربات اجرا شد 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
