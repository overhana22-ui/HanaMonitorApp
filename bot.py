import os
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request

# Env vars
TOKEN = os.getenv('TELEGRAM_TOKEN')  # در Render ست کنید
FIREBASE_URL = "https://hanamonitorapp-30c38-default-rtdb.firebaseio.com/children"

app = Flask(__name__)

keyboard = [
    [InlineKeyboardButton("موقعیت فرزند", callback_data="locations")],
    [InlineKeyboardButton("استفاده اپ‌ها", callback_data="app_usage")],
    [InlineKeyboardButton("هشدارها", callback_data="alerts")],
    [InlineKeyboardButton("مخاطبین", callback_data="contacts")],
    [InlineKeyboardButton("تماس‌ها", callback_data="calls")],
    [InlineKeyboardButton("پیامک‌ها", callback_data="sms")],
    [InlineKeyboardButton("عکس‌های اخیر", callback_data="photos")]
]
reply_markup = InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به ربات نظارت HanaMonitorApp خوش آمدید!\n"
        "داده‌های فرزند شما از Firebase لود می‌شود.\n"
        "از دکمه‌های زیر استفاده کنید:", 
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_type = query.data
    chat_id = "5601310517"  # هاردکد chatID

    try:
        response = requests.get(f"{FIREBASE_URL}/{chat_id}/{data_type}.json")
        data = response.json()

        if isinstance(data, dict) and "secret" in data:
            del data["secret"]

        if data:
            if data_type == "locations":
                text = f"📍 موقعیت فعلی:\nعرض: {data.get('lat', 'نامشخص')}, طول: {data.get('lon', 'نامشخص')}\n⏰ زمان: {data.get('time', 'نامشخص')}"
            elif data_type == "app_usage":
                text = "📊 استفاده از اپ‌ها (دقیقه در ۱ ساعت اخیر):\n"
                for app, minutes in data.items():
                    if app != "secret":
                        text += f"• {app}: {minutes} دقیقه\n"
            elif data_type == "alerts":
                text = "🚨 هشدارهای اخیر:\n"
                if isinstance(data, dict):
                    for _, alert in data.items():
                        text += f"• {alert.get('app', 'نامشخص')}: {alert.get('minutes', 0)} دقیقه (⏰ {alert.get('time', 'نامشخص')})\n"
                else:
                    text += "هیچ هشداری موجود نیست."
            elif data_type == "photos":
                storage_url = f"https://firebasestorage.googleapis.com/v0/b/hanamonitorapp-30c38.appspot.com/o/children%2F{chat_id}%2Fphotos"
                response = requests.get(storage_url)
                photos = response.json().get('items', [])
                if photos:
                    text = "🖼 عکس‌های اخیر:\n"
                    for photo in photos[:3]:  # ۳ عکس آخر
                        name = photo['name']
                        text += f"• {name}\n"
                    text += "برای دانلود، به Firebase Storage مراجعه کنید."
                else:
                    text = "هیچ عکسی موجود نیست."
            else:
                text = f"داده‌های {data_type}:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
        else:
            text = f"هیچ داده‌ای برای {data_type} موجود نیست."

        await query.edit_message_text(text)
    except Exception as e:
        await query.edit_message_text(f"❌ خطا: {str(e)}\nلطفاً Firebase یا Render را چک کنید.")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.process_update(update)
    return 'OK'

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
