import os
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

# AI Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# ----------------- FLASK (FOR 24/7 UPTIME) ----------------- #
app = Flask(__name__)

@app.route("/")
def home():
    return "Aurex Chatbot is Alive & Vibing!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ----------------- AI FUNNY HINDI REPLY ----------------- #
def get_funny_reply(user_text: str, user_name: str) -> str:
    system_prompt = (
        "You are 'Aurex Chatbot', an ultra-funny, witty, sarcastic, and roast-loving AI friend. "
        "Language: Speak STRICTLY in Hindi (written in casual Hinglish/Roman script or natural conversational Hindi). "
        "Tone: Like a funny, savage friend who loves funny roasts, memes, and banter. "
        "Rule: Keep replies very short, punchy, and hilarious (1 to 2 lines maximum). Never act formal or like a robot."
    )
    
    # Models to try if one hits rate-limit
    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
    
    for model_name in models_to_try:
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=f"User name: {user_name}\nMessage: {user_text}",
                config={"system_instruction": system_prompt}
            )
            if response.text:
                return response.text.strip()
        except Exception as err:
            print(f"Error with {model_name}: {err}")
            continue

    fallback_replies = [
        "Abe kehna kya chahte ho? Seedha bolo na! 😂",
        "Itna dimag mat chala, dhuaan nikal aayega tera! 💀",
        "Bhai thoda dhang ka sawaal pooch le, mere brain cells fuse mat kar! 🤣",
        "Arey wah, kya baat boli hai! Award dilaun kya ab? 🏆"
    ]
    return random.choice(fallback_replies)

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

# ----------------- TELEGRAM HANDLERS ----------------- #
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    welcome_text = (
        f"Arey wah {name}! Swagat nahi karoge humara? 😎\n\n"
        "Main hoon <b>Aurex Chatbot</b>! Dosti, roast aur full bakchodi yahi milegi.\n"
        "Mujhe DM karo, group me tag karo ya reply karo!"
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

    # DM
    if chat_type == "private":
        should_reply = True
    # Groups
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

        # 40% chance to send sticker
        if random.random() < 0.40:
            await send_random_sticker(context, update.effective_chat.id, sent.message_id)

# ----------------- MAIN RUNNER ----------------- #
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    bot_app = Application.builder().token(BOT_TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    print("Aurex Chatbot is running smoothly...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
