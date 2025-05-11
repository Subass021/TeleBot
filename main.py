import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler
)

# Load environment variables from .env (only works locally)
load_dotenv()

# Config from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_DATE = datetime.strptime(os.environ.get("TARGET_DATE"), "%Y-%m-%d")
GIRL_NAME = os.environ.get("GIRL_NAME")
BOT_NAME = os.environ.get("BOT_NAME")

# Load keyword responses
with open("messages.json", "r") as f:
    MESSAGES = json.load(f)

used_responses = set()

# Countdown calculator
def calculate_countdown():
    now = datetime.now()
    delta = TARGET_DATE - now
    years = delta.days // 365
    months = (delta.days % 365) // 30
    days = (delta.days % 365) % 30
    return f"🕰 Countdown till June 2028:\n\n❤️ {years} years, {months} months, {days} days left.\nI’m working for us every second, {GIRL_NAME}."

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🕰 View Countdown", callback_data="countdown")],
        [InlineKeyboardButton("💌 Talk to Me", callback_data="talk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hey {GIRL_NAME}, this is your {BOT_NAME}.\n\nI'm here till 2028. Tap an option below to start.",
        reply_markup=reply_markup
    )

# Button interactions
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "countdown":
        await query.edit_message_text(text=calculate_countdown())
    elif query.data == "talk":
        await query.edit_message_text(text="Just type how you feel... I'll reply with love.")

# Keyword match engine
def get_response(message):
    msg_lower = message.lower()
    for keyword, replies in MESSAGES.items():
        if keyword in msg_lower:
            for r in replies:
                if r not in used_responses:
                    used_responses.add(r)
                    return r
    return "I may not have the perfect words, but I’m always listening to you. ❤️"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    reply = get_response(user_msg)
    await update.message.reply_text(reply)

# Main entry
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()

# Runtime patch for some environments
if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()
        loop.run_until_complete(main())
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop_policy().get_event_loop()
        loop.run_until_complete(main())
