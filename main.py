import os
import json
import asyncio
from datetime import datetime, time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler,
    ConversationHandler
)

load_dotenv()

# Configs
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_DATE = datetime.strptime(os.getenv("TARGET_DATE"), "%Y-%m-%d")
GIRL_NAME = os.getenv("GIRL_NAME")
BOT_NAME = os.getenv("BOT_NAME")
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")

# Load keyword responses
with open("messages.json", "r") as f:
    MESSAGES = json.load(f)

used_responses = set()
AUTHORIZED_USERS = set()

# Step 1: Countdown calculator
def calculate_countdown():
    now = datetime.now()
    delta = TARGET_DATE - now
    years = delta.days // 365
    months = (delta.days % 365) // 30
    days = (delta.days % 365) % 30
    return f"🕰 Countdown till June 2028:\n\n❤️ {years} years, {months} months, {days} days left.\nI’m working for us every second, {GIRL_NAME}."

# Step 2: Password-Protected Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in AUTHORIZED_USERS:
        return await show_menu(update)
    await update.message.reply_text("🔐 Enter password to unlock the bot:")
    return 1  # Password state

async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ACCESS_PASSWORD:
        AUTHORIZED_USERS.add(update.message.from_user.id)
        await update.message.reply_text("✅ Access granted!")
        return await show_menu(update)
    else:
        await update.message.reply_text("❌ Incorrect password. Try again:")
        return 1

# Step 3: Show main menu
async def show_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("🕰 View Countdown", callback_data="countdown")],
        [InlineKeyboardButton("💌 Talk to Me", callback_data="talk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hey {GIRL_NAME}, this is your {BOT_NAME}.\n\nI'm here till 2028. Tap an option below to start.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# Step 4: Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "countdown":
        await query.edit_message_text(text=calculate_countdown())
    elif query.data == "talk":
        await query.edit_message_text(text="Just type how you feel... I'll reply with love.")

# Step 5: Keyword matcher
def get_response(message):
    msg_lower = message.lower()
    for keyword, replies in MESSAGES.items():
        if keyword in msg_lower:
            for r in replies:
                if r not in used_responses:
                    used_responses.add(r)
                    return r
    return "I may not have the perfect words, but I’m always listening to you. ❤️"

# Step 6: Text response
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    reply = get_response(user_msg)
    await update.message.reply_text(reply)

# Step 7: Voice note handler
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file_id = voice.file_id
    await update.message.reply_text("🎙 Your voice is saved forever. I’ll listen to it again and again. ❤️")

# Step 8: Scheduled daily countdown message
async def daily_countdown(context: ContextTypes.DEFAULT_TYPE):
    for user_id in AUTHORIZED_USERS:
        try:
            await context.bot.send_message(chat_id=user_id, text=calculate_countdown())
        except:
            continue

# Step 9: Main bot execution
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password)]},
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Schedule daily countdown message at 8 AM
    app.job_queue.run_daily(daily_countdown, time=time(hour=8, minute=0))

    await app.initialize()
    await app.start()
    print("Bot is running.")
    await app.updater.start_polling()
    await app.updater.idle()

# Async compatibility patch
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(main())
