import os
import json
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ApplicationBuilder
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
PORT = int(os.environ.get('PORT', 10000))

with open('fields.json', 'r', encoding='utf-8') as file:
    data = json.load(file)


# Simple HTTP handler to keep Render happy
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')

    def log_message(self, format, *args):
        # Suppress HTTP server logs
        return


# Commands (same as before)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    for field in data["fields"]:
        keyboard.append([InlineKeyboardButton(field["name"], callback_data=f"field_{field['name']}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("اختر مجالاً:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("اختر مجالاً:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "back_to_main":
        await start_command(update, context)
        return

    if callback_data.startswith("field_"):
        field_name = callback_data.replace("field_", "")
        selected_field = next((field for field in data['fields'] if field['name'] == field_name), None)

        if selected_field:
            keyboard = [
                [InlineKeyboardButton("الوصف", callback_data=f"desc_{field_name}")],
                [InlineKeyboardButton("الأدوات الشهيرة", callback_data=f"tools_{field_name}")],
                [InlineKeyboardButton("الموارد المجانية", callback_data=f"resources_{field_name}")],
                [InlineKeyboardButton("خطة التعلم", callback_data=f"roadmap_{field_name}")],
                [InlineKeyboardButton("العودة للقائمة الرئيسية", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"اختر ما تريد معرفته عن {field_name}:", reply_markup=reply_markup)
        return

    if callback_data.startswith("back_to_"):
        field_name = callback_data.replace("back_to_", "")
        keyboard = [
            [InlineKeyboardButton("الوصف", callback_data=f"desc_{field_name}")],
            [InlineKeyboardButton("الأدوات الشهيرة", callback_data=f"tools_{field_name}")],
            [InlineKeyboardButton("الموارد المجانية", callback_data=f"resources_{field_name}")],
            [InlineKeyboardButton("خطة التعلم", callback_data=f"roadmap_{field_name}")],
            [InlineKeyboardButton("العودة للقائمة الرئيسية", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"اختر ما تريد معرفته عن {field_name}:", reply_markup=reply_markup)
        return

    if "_" in callback_data:
        action, field_name = callback_data.split("_", 1)
        selected_field = next((field for field in data["fields"] if field["name"] == field_name), None)

        if selected_field:
            if action == "desc":
                text = f"📌 **الوصف**:\n{selected_field['description']}"
            elif action == "tools":
                tools_text = "\n".join([f"• {tool}" for tool in selected_field['popular_tools']])
                text = f"🛠 **الأدوات الشهيرة**:\n{tools_text}"
            elif action == "resources":
                resources = "\n".join([f"• [{res['name']}]({res['url']})" for res in selected_field['free_resources']])
                text = f"🔗 **الموارد المجانية**:\n{resources}"
            elif action == "roadmap":
                roadmap_text = "\n".join([f"• {step}" for step in selected_field['roadmap']])
                text = f"🗺 **خطة التعلم**:\n{roadmap_text}"
            else:
                text = "خطأ في البيانات"

            keyboard = [[InlineKeyboardButton("العودة", callback_data=f"back_to_{field_name}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            except Exception as e:
                await query.edit_message_text(text, reply_markup=reply_markup)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error: {context.error}")


async def post_init(app: Application) -> None:
    print("Bot is running!")


def run_bot():
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .post_init(post_init) \
        .build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error)

    try:
        print("Bot polling started...")
        app.run_polling()
    except KeyboardInterrupt:
        print("Bot stopped by user")
    finally:
        print("Cleaning up...")


def run_http_server():
    server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
    print(f"HTTP server running on port {PORT}")
    server.serve_forever()


if __name__ == '__main__':
    # Start HTTP server in a separate thread to satisfy Render
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Run the bot
    run_bot()