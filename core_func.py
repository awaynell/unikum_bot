
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from utils import show_main_menu, set_mode, get_models
from constants import default_img_model, default_img_model_flow2
from respond_to_user import respond_to_user
from generateImg import getImgFromAPI


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    reply_keyboard = [
        [KeyboardButton('Рисовать')],
        [KeyboardButton('Спросить')]
    ]

    reply_markup = ReplyKeyboardMarkup(
        reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text('Привет! Готов ответить на твои вопросы.', reply_markup=reply_markup)
    await show_main_menu(update, context, {
        "help": "Помощь",
        "clear": "Очистить контекст чата (1-й поток, сейчас контекст 30 сообщений)",
        "mode": "Сменить режим работы бота (есть 2 мода 'draw' и 'text'). Например, /mode draw",
    })


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if "@" in user_message:
        user_message = user_message.split(" ", 1)[1].strip()

    bot_username = context.bot.username

    if (user_message.lower() == 'спросить'):
        await set_mode(update, context, 'text')
        return
    elif (user_message.lower() == 'рисовать'):
        await set_mode(update, context, 'draw')
        return
    elif (user_message.lower().startswith('нарисуй')):
        await set_mode(update, context, 'draw')
        await respond_to_user(update, context, user_message)
        return

    # Проверка типа чата: личный или групповой
    if update.message.chat.type in ['group', 'supergroup']:
        # Ответ только на сообщения, содержащие имя бота или упоминание, или если ответ на сообщение бота
        if bot_username.lower() in update.message.text.lower() or (update.message.reply_to_message and update.message.reply_to_message.from_user.username == bot_username):
            await respond_to_user(update, context, user_message)
    else:
        # Ответ на все сообщения в личных чатах
        await respond_to_user(update, context, user_message)


async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    context.user_data[f"history-{user_id}-{chat_id}"] = []
    await update.message.reply_text(f"Контекст чата {chat_id} очищен.")


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        draw_message = await update.message.reply_text('Начинаю рисовать...')

        img_model_key = context.user_data.get(
            'img_model', default_img_model_flow2)

        print('img_model_key', img_model_key)

        chat_id = update.message.chat_id
        message_id = update.message.message_id

        if len(context.args) == 0:
            await update.message.reply_text('Пожалуйста, укажите запрос.')
            return

        prompt = ' '.join(context.args) if context.args else None
        image_paths, _ = await getImgFromAPI(prompt, update, context, img_model_key)

        media = []  # Создаем новый список media на каждой итерации

        for path in image_paths:

            image_path = path['image']

            print('image_path', image_path)

            with open(image_path, 'rb') as photo:
                media.append(InputMediaPhoto(media=photo))

        await context.bot.send_media_group(chat_id=chat_id, media=media, caption=f"Сгенерированные изображения по запросу: {prompt}\n\nvia {img_model_key}", reply_to_message_id=message_id)

        await draw_message.delete()
    except Exception as e:
        print(f"Error sending photo: {e}")
        await draw_message.edit_text(f"Ошибка при отправке изображения: {e}\nТекущая модель: {img_model_key}")


async def handle_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    command, name = query.data.split()
    if command == '/model':
        context.bot_data['model'] = name
        await query.edit_message_text(text=f"Вы выбрали модель: {name}")
    if command == '/provider':
        context.bot_data['provider'] = name
        await query.edit_message_text(text=f"Вы выбрали провайдер: {name}")
        await get_models(update, context, query.message.message_id)


async def sex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Секс — это псиоп')
