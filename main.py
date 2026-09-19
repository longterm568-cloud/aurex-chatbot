import os
import asyncio
import random
import threading
from flask import Flask
from google import genai
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ----------------- CONFIGURATION ----------------- #
BOT_TOKEN = "8600761951:AAEIhkCcWvMxFexkrpHbWH_MPP2T42JbsMs"
GEMINI_API_KEY = "AQ.Ab8RN6IGNBx5NElUpaohHX7LZv8GN4H21nyfjeaci7U8NOly6w"

STICKER_PACKS = [
    "Cat_stk_by_yoon",
    "SUJAL_STICKER_PACK_47be_by_offstikbot",
    "GOJO_NEVER_DIE_by_fStikBot"
]

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# ----------------- FLASK (24/7 UPTIME) ----------------- #
app = Flask(__name__)

@app.route("/")
def home():
    return "Aurex Chatbot is Alive & Vibing!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ----------------- AI FUNNY REPLY ----------------- #
def get_funny_reply(user_text: str, user_name: str) -> str:
    system_prompt = (
        "You are 'Aurex Chatbot', an extremely funny, sarcastic, witty, and playful AI friend. "
        "Chat casually like a cool best friend in group chats. "
        "Keep your replies punchy and concise (1 to 2 sentences max). "
        "Drop savage roasts, funny comebacks, and pure banter. "
        "Never speak like an assistant or robot. Never give long lectures."
    )
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Sender: {user_name}\nMessage: {user_text}",
            config={"system_instruction": system_prompt}
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Network cha issue distoy re bhava! परत बोल जरा! 😂"

# ----------------- STICKER SENDER ----------------- #
async def send_random_sticker(context: ContextTypes.DEFAULT_TYPE, chat_id: int, reply_to_id: int):
    try:
        pack_name = random.choice(STICKER_PACKS)
        sticker_set = await context.bot.get_sticker_set(pack_name)
        if sticker_set and sticker_set.stickers:
            random_stk = random.choice(sticker_set.stickers)
            await context.bot.send_sticker(
                chat_id=chat_id,
                sticker=random_stk.file_id,
                reply_to_message_id=reply_to_id
            )
    except Exception as e:
        print(f"Sticker Error: {e}")

# ----------------- HANDLERS ----------------- #
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    welcome_text = (
        f"Arey wah {name}! Swagat nahi karoge hamara? 😎\n\n"
        "Me ahe <b>Aurex Chatbot</b>! Chala shuru kara mag maja masti.\n"
        "Mala DM kara, group madhe tag kara (@) kiva reply kara!"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")
    await send_random_sticker(context, update.effective_chat.id, update.message.message_id)

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat_type = update.effective_chat.type
    bot_obj = await context.bot.get_me()
    bot_username = bot_obj.username.lower()
    text = message.text.strip()
    user_name = update.effective_user.first_name

    should_reply = False

    if chat_type == "private":
        should_reply = True
    elif chat_type in ["group", "supergroup"]:
        if f"@{bot_username}" in text.lower():
            should_reply = True
            text = text.replace(f"@{bot_username}", "").strip()
        elif message.reply_to_message and message.reply_to_message.from_user.id == bot_obj.id:
            should_reply = True

    if should_reply:
        if not text:
            await send_random_sticker(context, update.effective_chat.id, message.message_id)
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply_msg = get_funny_reply(text, user_name)
        sent = await message.reply_text(reply_msg, reply_to_message_id=message.message_id)

        if random.random() < 0.40:
            await send_random_sticker(context, update.effective_chat.id, sent.message_id)

# ----------------- MAIN RUNNER ----------------- #
async def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    print("Aurex Chatbot is running smoothly...")

    # Keep running forever
    while True:
        await asyncio.sleep(3600)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
