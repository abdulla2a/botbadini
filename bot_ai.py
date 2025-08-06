import os
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
import google.generativeai as genai
from flask import Flask
from threading import Thread
import asyncio

# تفعيل nest_asyncio
nest_asyncio.apply()

# تحميل متغيرات البيئة
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# إعداد Google Generative AI
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("[LOG] Available models:")
    try:
        for m in genai.list_models():
            print(f"- {m.name} | supports: {m.supported_generation_methods}")
    except Exception as e:
        import traceback
        print(f"[LOG] Error listing models: {e}")
        traceback.print_exc()
    print("[LOG] Using model: models/gemini-2.5-pro")
    model = genai.GenerativeModel('models/gemini-2.5-pro')
else:
    model = None

# دالة الرد على الرسائل النصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"[LOG] Received message: {user_message}")
    reply = "عذرًا، حدث خطأ داخلي. (model is None)"
    if model:
        try:
            print("[LOG] Sending message to Gemini AI...")
            custom_prompt = f"""
ئه‌ز بۆتی بادينى مه كو ژیریا دەستکردم، کۆ ژ لایێ عبدالله ڤه‌هاتیمه‌ چێکرن.
            جاوب على الأسئلة بشكل ذكي، محترم، وسهل الفهم.
            السؤال: {user_message}
            """
            response = model.generate_content(custom_prompt)
            try:
                if response.candidates and response.candidates[0].content.parts:
                    reply = response.candidates[0].content.parts[0].text
                    print(f"[LOG] Gemini AI response: {reply}")
                else:
                    print("[LOG] Gemini API full response:", response)
                    safety_ratings = getattr(response.candidates[0], 'safety_ratings', None) if response.candidates else None
                    if safety_ratings:
                        print("[LOG] Safety ratings:", safety_ratings)
                    reply = "عذراً، لم يتم إرجاع نص من الذكاء الاصطناعي. قد يكون السبب فلترة أو مشكلة في اللغة."
            except Exception as e:
                print(f"[LOG] Exception while parsing response: {e}")
                print("[LOG] Gemini API full response:", response)
                reply = f"حدث خطأ أثناء معالجة الرد: {e}"
        except Exception as e:
            print(f"[LOG] Exception: {e}")
            reply = f"حدث خطأ: {e}"
    else:
        print("[LOG] Gemini model is None!")
    await update.message.reply_text(reply)
    print("[LOG] Reply sent.")

# دالة أمر /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في بوت باديني! أرسل سؤالك للذكاء الاصطناعي.")

# إعداد البوت
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # أوامر البوت
    app.add_handler(CommandHandler("start", start_command))

    # الرسائل النصية العادية (ما عدا الأوامر)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...")
    await app.run_polling()

# إعداد Flask لبيئة Replit أو سيرفر خارجي
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Hello, I am alive!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# تشغيل البوت
if name == "__main__":
    print(f"[LOG] TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
    print(f"[LOG] GOOGLE_API_KEY: {GOOGLE_API_KEY}")

    # Flask يعمل في thread منفصل
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # تشغيل البوت
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[FATAL ERROR] {e}")