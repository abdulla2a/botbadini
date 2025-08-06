import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import google.generativeai as genai
import nest_asyncio
nest_asyncio.apply()
from flask import Flask
from threading import Thread

# تحميل متغيرات البيئة
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# تهيئة Google Generative AI
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    # طباعة قائمة النماذج المتاحة
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"[LOG] Received message: {user_message}")
    reply = "عذرًا، حدث خطأ داخلي. (model is None)"
    if model:
        try:
            print("[LOG] Sending message to Gemini AI...")
            response = model.generate_content(user_message)
            # معالجة الاستجابة بشكل آمن
            try:
                # تحقق من وجود المرشح وجزء النص
                if response.candidates and response.candidates[0].content.parts:
                    reply = response.candidates[0].content.parts[0].text
                    print(f"[LOG] Gemini AI response: {reply}")
                else:
                    # طباعة الرد الكامل للمساعدة في التشخيص
                    print("[LOG] Gemini API full response:", response)
                    # تحقق من وجود أسباب الحجب
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

import asyncio

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is running...")
    await app.run_polling()


# إعداد Flask
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Hello, I am alive!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    print(f"[LOG] TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
    print(f"[LOG] GOOGLE_API_KEY: {GOOGLE_API_KEY}")
    # تشغيل Flask في thread منفصل
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
