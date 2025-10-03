import os
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request

# Env vars (در Render set می‌کنید)
TOKEN = os.getenv('TELEGRAM_TOKEN', '8262524272:AAEKFiekP_HHt4BzBmnryovuaZAq9g9QJn0')
FIREBASE_URL = os.getenv('FIREBASE_URL', 'https://hanamonitorapp-30c38-default-rtdb.firebaseio.com/children')


# اپ Flask برای webhook (Render Web Service)
app = Flask(__name__)

# پنل شیشه‌ای (inline keyboard) متناسب با پروژه HanaMonitorApp
keyboard = [
    [InlineKeyboardButton("موقعیت فرزند", callback_data="locations")],
    [InlineKeyboardButton("استفاده اپ‌ها", callback_data="app_usage")],
    [InlineKeyboardButton("هشدارها", callback_data="alerts")],
    [InlineKeyboardButton("مخاطبین", callback_data="contacts")],
    [InlineKeyboardButton("تماس‌ها", callback_data="calls")],
    [InlineKeyboardButton("پیامک‌ها", callback_data="sms")]
]
reply_markup = InlineKeyboardMarkup(keyboard)

# هندلر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به ربات نظارت HanaMonitorApp خوش آمدید!\n"
        "داده‌های فرزند شما از Firebase لود می‌شود.\n"
        "دستورات:", 
        reply_markup=reply_markup
    )

# هندلر کلیک دکمه‌ها (callback query)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # تأیید کلیک
    data_type = query.data
    chat_id = str(query.from_user.id)  # chat ID والدین

    try:
        # خواندن داده از Firebase
        response = requests.get(f"{FIREBASE_URL}/{chat_id}/{data_type}.json")
        data = response.json()

        if data and 'secret' in data:  # چک secret key از اپ فرزند
            del data['secret']  # حذف secret از نمایش

        if data:
            if data_type == "locations":
                text = f"موقعیت فعلی: عرض جغرافیایی {data.get('lat', 'نامشخص')}, طول جغرافیایی {data.get('lon', 'نامشخص')}\nزمان: {data.get('time', 'نامشخص')}"
            elif data_type == "app_usage":
                text = "استفاده از اپ‌ها (دقیقه، آخرین ساعت):\n"
                for app, minutes in data.items():
                    if app != "secret":
                        text += f"• {app}: {minutes} دقیقه\n"
            elif data_type == "alerts":
                text = "هشدارهای اخیر:\n"
                if isinstance(data, dict):
                    for alert_id, alert in data.items():
                        text += f"• {alert.get('app', 'نامشخص')}: {alert.get('minutes', 0)} دقیقه (زمان: {alert.get('time', 'نامشخص')})\n"
                else:
                    text += "هیچ هشداری موجود نیست."
            else:
                # برای بقیه (مخاطبین، تماس‌ها، پیامک‌ها): خلاصه JSON
                text = f"داده‌های {data_type}:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
        else:
            text = f"هیچ داده‌ای برای {data_type} موجود نیست. مطمئن شوید اپ فرزند فعال است."

        await query.edit_message_text(text)
    except Exception as e:
        await query.edit_message_text(f"خطا در بارگیری داده: {str(e)}\nچک کنید Firebase URL درست باشد.")

# Route برای webhook (تلگرام به اینجا POST می‌کنه)
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.process_update(update)
    return 'OK'

# ستاپ اپ تلگرام
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))

# ران Flask روی پورت Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
