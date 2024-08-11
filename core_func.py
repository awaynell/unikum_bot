
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from utils import get_models
from constants import default_img_model_flow2, prompt_for_russian_AI_answer
from respond_to_user import respond_to_user
from generateImg import getImgFromAPI
from utils import predict_user_message_context, translate_user_message, show_main_menu, set_defimgm


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text('Привет! ')
    await show_main_menu(update, context, {
        "help": "Помощь",
        "clear": "Очистить контекст чата (1-й поток, сейчас контекст 30 сообщений)",
        # "mode": "Сменить режим работы бота (есть 2 мода 'draw' и 'text'). Например, /mode draw",
    })


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    bot_username = context.bot.username

    isConferenation = update.message.chat.type in ['group', 'supergroup']

    if (isConferenation and bot_username.lower() not in update.message.text.lower()) and isConferenation and (not update.message.reply_to_message or update.message.reply_to_message.from_user.username != bot_username):
        return

    if user_message == None:
        return

    if "@" in user_message:
        user_message = user_message.split(" ", 1)[1].strip()
    ru_user_message = f"{
        user_message}, {prompt_for_russian_AI_answer}"

    await predict_user_message_context(update, context, user_message, chat_id, message_id)

    translated_user_message = ''

    mode_type = context.user_data["modetype"]
    if mode_type == 'draw':
        translated_user_message = await translate_user_message(update, context, user_message, chat_id, message_id)
    result_message = translated_user_message if mode_type == 'draw' else ru_user_message

    # Проверка типа чата: личный или групповой
    if isConferenation:
        # Ответ только на сообщения, содержащие имя бота или упоминание, или если ответ на сообщение бота
        if bot_username.lower() in update.message.text.lower() or (update.message.reply_to_message and update.message.reply_to_message.from_user.username == bot_username):
            await respond_to_user(update, context, result_message)
    else:
        # Ответ на все сообщения в личных чатах
        await respond_to_user(update, context, result_message)


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        draw_message = await update.message.reply_text('Начинаю рисовать...')

        img_model_key = context.user_data.get(
            'img_model', default_img_model_flow2)

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
    print('query', query)
    await query.answer()

    command, name = query.data.split()
    if command == '/model':
        context.bot_data['model'] = name
        await query.edit_message_text(text=f"Вы выбрали модель: {name}")
    if command == '/provider':
        context.bot_data['provider'] = name
        await query.edit_message_text(text=f"Вы выбрали провайдер: {name}")
        await get_models(update, context, query.message.message_id)
    if command == '/defimgm':
        await set_defimgm(update, context, key=name)


async def sex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Секс — это псиоп')
