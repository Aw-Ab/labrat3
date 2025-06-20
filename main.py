import os
import json
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ApplicationBuilder
from dotenv import load_dotenv

load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")

with open('fields.json', 'r', encoding='utf-8') as file:
    data = json.load(file)


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    for field in data["fields"]:
        keyboard.append([InlineKeyboardButton(field["name"], callback_data=f"field_{field['name']}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handle both direct command and callback query
    if update.message:
        await update.message.reply_text("اختر مجالاً:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("اختر مجالاً:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Handle back to main menu
    if callback_data == "back_to_main":
        await start_command(update, context)
        return

    # Handle field selection
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

    # Handle back to field menu
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

    # Handle field details
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
                # Fallback if markdown parsing fails
                await query.edit_message_text(text, reply_markup=reply_markup)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error: {context.error}")


async def post_init(app: Application) -> None:
    print("Bot is running!")


def main() -> None:
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .post_init(post_init) \
        .build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    # Single callback handler for all button interactions
    app.add_handler(CallbackQueryHandler(button_handler))

    # Error handler
    app.add_error_handler(error)

    try:
        print("Polling...")
        app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
        print("Bot stopped by user")
    finally:
        print("Cleaning up...")


if __name__ == '__main__':
    main()