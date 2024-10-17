import logging
import os
from dotenv import load_dotenv
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from PIL import Image

load_dotenv()
TOKEN = os.getenv("TOKEN")
user_photos = {}
report_name = {}
default_name = "report"
A4_SIZE = (595, 842)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_menu(update, context)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    current_name = report_name.get(user_id, default_name)
    current_count = len(user_photos.get(user_id, []))
    keyboard = [
        [InlineKeyboardButton(f"Изменить имя отчета (Текущее: {current_name})", callback_data='change_name')],
        [InlineKeyboardButton(f"Очистить буфер (Фотографий: {current_count})", callback_data='delete_photos')],
        [InlineKeyboardButton("Конвертировать в PDF", callback_data='convert')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    menu_text = 'Отправьте мне фотографии, и я верну их в формате PDF. Для завершения отправьте команду /convert'
    if update.message:
        await update.message.reply_text(menu_text, reply_markup=reply_markup)
    elif update.callback_query:
        current_message = update.callback_query.message
        if current_message is not None and (
                current_message.text != menu_text or current_message.reply_markup != reply_markup):
            await current_message.edit_text(text=menu_text, reply_markup=reply_markup)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = BytesIO()
    await photo_file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)
    with Image.open(photo_bytes) as img:
        if user_id not in user_photos:
            user_photos[user_id] = []
        user_photos[user_id].append(img.convert('RGB'))
    if len(user_photos[user_id]) == 1:
        await update.message.reply_text('Фотография добавлена! Отправьте еще или введите /convert для завершения')
        await show_menu(update, context)


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    message = update.message if update.message else update.callback_query.message
    if user_id in user_photos and user_photos[user_id]:
        pdf_bytes = BytesIO()
        images = user_photos[user_id]
        pdf_images = []
        for img in images:
            img = img.convert('RGB')
            img.thumbnail(A4_SIZE, Image.Resampling.LANCZOS)
            a4_image = Image.new('RGB', A4_SIZE, (255, 255, 255))
            x_offset = (A4_SIZE[0] - img.width) // 2
            y_offset = (A4_SIZE[1] - img.height) // 2
            a4_image.paste(img, (x_offset, y_offset))
            pdf_images.append(a4_image)
        pdf_images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=pdf_images[1:])
        pdf_bytes.seek(0)
        report_name_to_use = report_name.get(user_id, default_name)
        await message.reply_document(document=pdf_bytes, filename=f"{report_name_to_use}.pdf")
        del user_photos[user_id]
        await show_menu(update, context)
    else:
        await message.reply_text('Вы еще не отправили фотографии!')
        await show_menu(update, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'change_name':
        await query.edit_message_text(text="Введите новое имя отчета:")
        context.user_data['change_name'] = True
    elif query.data == 'convert':
        await convert(update, context)
    elif query.data == 'delete_photos':
        user_id = query.from_user.id
        user_photos.pop(user_id, None)
        await show_menu(update, context)


async def handle_name_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if context.user_data.get('change_name'):
        new_name = update.message.text.strip()
        if new_name:
            report_name[user_id] = new_name
            await update.message.reply_text(f'Имя отчета изменено на: {new_name}')
        else:
            await update.message.reply_text('Имя отчета не может быть пустым. Попробуйте еще раз.')
        context.user_data['change_name'] = False
    await show_menu(update, context)


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler('convert', convert))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_change))
    app.run_polling()

if __name__ == '__main__':
    main()
