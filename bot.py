import requests
import logging
from logging.handlers import TimedRotatingFileHandler
from telegram import Update, InputMediaPhoto
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from os import getenv, remove
from generateImg import generateImg, getImgFromAPI
import base64

from utils import set_model, set_provider, default_model, default_provider

load_dotenv()

tg_bot_token = getenv('TG_BOT_TOKEN')

# Настройки логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 'W0' означает каждую неделю в воскресенье
handler = TimedRotatingFileHandler('bot.log', when='W0', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


# Функция для обработки команды /start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Готов ответить на твои вопросы.')

# Функция для обработки сообщений


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    bot_username = context.bot.username

    # Проверка типа чата: личный или групповой
    if update.message.chat.type in ['group', 'supergroup']:
        # Ответ только на сообщения, содержащие имя бота или упоминание, или если ответ на сообщение бота
        if bot_username.lower() in user_message.lower() or (update.message.reply_to_message and update.message.reply_to_message.from_user.username == bot_username):
            await respond_to_user(update, context, user_message)
    else:
        # Ответ на все сообщения в личных чатах
        await respond_to_user(update, context, user_message)


async def respond_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    username = update.message.from_user.username

    # Отправка состояния "печатает..."
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    provider = context.chat_data.get('provider', default_provider)
    model = context.chat_data.get('model', default_model)

    # Инициализация истории сообщений, если её ещё нет
    if "history" not in context.chat_data:
        context.chat_data["history"] = []

    # Добавление нового сообщения пользователя в историю
    context.chat_data["history"].append(
        {"role": "user", "content": user_message})

    # Ограничение истории, чтобы не превышать лимиты API
    max_history_length = 30  # Можно настроить по необходимости
    context.chat_data["history"] = context.chat_data["history"][-max_history_length:]

    logger.info("USERNAME: %s", username, 'DIALOG_history: %s',
                context.chat_data["history"])

    # Отправка запроса к API ChatGPT
    api_url = "http://212.113.101.93:1337/v1/chat/completions"
    payload = {
        "model": model,
        "provider": provider,
        "messages": context.chat_data["history"],
        "temperature": 0.4,
        "auto_continue": True,
        "conversation_id": chat_id,
        "id": f"{chat_id}-{message_id}"
    }

    logger.info('API_payload: %s', payload)

    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        logger.debug("API response: %s", response.json())
        bot_reply = response.json()["choices"][0]["message"]["content"]
        # Добавление ответа бота в историю
        context.chat_data["history"].append(
            {"role": "assistant", "content": bot_reply})

        logger.info('DIALOG_history: %s', context.chat_data["history"])
    else:
        bot_reply = "Извините, произошла ошибка при обращении к API."

    print('bot_reply', bot_reply)

    # Отправка ответа пользователю
    await context.bot.send_message(chat_id=chat_id, text=bot_reply, reply_to_message_id=update.message.message_id, parse_mode='Markdown')


async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['history'] = []
    await update.message.reply_text('Контекст чата очищен.')


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        draw_message = await update.message.reply_text('Начинаю рисовать...')

        chat_id = update.message.chat_id
        message_id = update.message.message_id

        if len(context.args) == 0:
            await update.message.reply_text('Пожалуйста, укажите запрос.')
            return

        prompt = ' '.join(context.args) if context.args else None
        image_paths, _ = await getImgFromAPI(prompt, update, context)

        media = []  # Создаем новый список media на каждой итерации

        for path in image_paths:

            image_path = path['image']

            print('image_path', image_path)

            with open(image_path, 'rb') as photo:
                media.append(InputMediaPhoto(media=photo))

            # Удаляем временный файл после отправки
            remove(image_path)

        await context.bot.send_media_group(chat_id=chat_id, media=media, caption=f"Сгенерированные изображения по запросу: {prompt}", reply_to_message_id=message_id)

        await draw_message.delete()
    except Exception as e:
        print(f"Error sending photo: {e}")
        await draw_message.edit_text(f"Ошибка при отправке изображения: {e}")
    # for path in image_paths:

    #     print('image_path', image_path)

    #     try:
    #         with open(image_path, 'rb') as photo:
    #             await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=f"Сгенерированное изображение по запросу: {prompt}", reply_to_message_id=message_id)

    #         remove(image_path)

    #         await draw_message.delete()

    #     except Exception as e:
    #         print(f"Error sending photo: {e}")
    #         await draw_message.edit_text(f"Ошибка при отправке изображения: {e}")

    # await context.bot.send_photo(chat_id=chat_id, photo=image, caption=f"Сгенерированное изображение по запросу: {prompt}", reply_to_message_id=message_id)

    # images_base64 = generateImg(prompt=prompt)

    # await context.bot.sendChatAction(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    # for b64 in images_base64:
    #     try:
    #         base64_string = b64.split(',')[1]

    #         # Decode the base64 string into binary data
    #         image_binary = base64.b64decode(base64_string)

    #         await context.bot.send_photo(chat_id=chat_id, photo=image_binary, caption=f"Сгенерированное изображение по запросу: {prompt}", reply_to_message_id=message_id)

    #         await draw_message.delete()
    #     except Exception as e:
    #         print(f"Error sending photo: {e}")
    #         await draw_message.edit_text(f"Ошибка при отправке изображения: {e}")


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
    application.add_handler(CommandHandler("draw", draw))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
