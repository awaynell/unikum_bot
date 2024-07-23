from telegram import Update, InputMediaPhoto, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from os import getenv
from generateImg import getImgFromAPI

from respond_to_user import respond_to_user
from utils import set_mode, show_main_menu, get_providers, get_models, set_model, set_provider, default_model, default_provider, default_img_model, set_img_model, send_img_models, send_help

load_dotenv()

tg_bot_token = getenv('TG_BOT_TOKEN')
api_base_url = getenv('API_BASE_URL')


# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    reply_keyboard = [
        [KeyboardButton('Рисовать'), KeyboardButton('Спросить')],
    ]
    markup = ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True, vertical=True)

    await update.message.reply_text('Привет! Готов ответить на твои вопросы.', reply_markup=markup)
    await show_main_menu(update, context, {
        "help": "Помощь",
        "providers": "Список провайдеров",
        "models": "Список моделей",
        "model": "Установить модель (пример /model gpt3.5-turbo)",
        "provider": "Установить провайдера (пример /provider ReplicateHome)",
        "clear": "Очистить контекст чата (1-й поток, сейчас контекст 30 сообщений)",
        "mode": "Сменить режим работы бота (есть 2 мода 'draw' и 'text'). Например, /mode draw",
    })

# Функция для обработки сообщений


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if "@" in user_message:
        user_message = user_message.split(" ", 1)[1].strip()
    ru_user_message = F"{user_message} отвечай на все сообщения на русском языке"
    modetype = context.user_data.get('modetype', "text")
    print('user_message', user_message)

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
        print('я тут')
        # Ответ только на сообщения, содержащие имя бота или упоминание, или если ответ на сообщение бота
        if bot_username.lower() in update.message.text.lower() or (update.message.reply_to_message and update.message.reply_to_message.from_user.username == bot_username):
            await respond_to_user(update, context,  ru_user_message if modetype == 'text' else user_message)
    else:
        # Ответ на все сообщения в личных чатах
        await respond_to_user(update, context,  ru_user_message if modetype == 'text' else user_message)


async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    context.user_data[f"history-{user_id}-{chat_id}"] = []
    await update.message.reply_text(f"Контекст чата {chat_id} очищен.")


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        draw_message = await update.message.reply_text('Начинаю рисовать...')

        img_model_key = context.user_data.get('img_model', default_img_model)

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
        context.user_data['model'] = name
        await query.edit_message_text(text=f"Вы выбрали модель: {name}")
    if command == '/provider':
        context.user_data['provider'] = name
        await query.edit_message_text(text=f"Вы выбрали провайдер: {name}")
        await get_models(update, context, query.message.message_id)


async def sex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Секс — это псиоп')


def main():
    # Вставь свой токен здесь
    token = tg_bot_token

    # Создаем приложение
    application = ApplicationBuilder().token(token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_context))
    application.add_handler(CommandHandler("provider", set_provider))
    application.add_handler(CommandHandler("model", set_model))
    application.add_handler(CommandHandler("models", get_models))
    application.add_handler(CommandHandler("providers", get_providers))
    application.add_handler(CommandHandler("draw", draw, block=False))
    application.add_handler(CommandHandler("imgmodel", set_img_model))
    application.add_handler(CommandHandler("getimgm", send_img_models))
    application.add_handler(CommandHandler("help", send_help))
    application.add_handler(CommandHandler("sex", sex))
    application.add_handler(CommandHandler("mode", set_mode))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message, block=False))

    application.add_handler(CallbackQueryHandler(handle_model_selection))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
