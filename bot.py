import os
import aiohttp
import logging
from logging.handlers import TimedRotatingFileHandler
from telegram import Update, InputMediaPhoto, InputFile, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from os import getenv
from generateImg import getImgFromAPI
import json
import asyncio
import re
import time

from utils import show_main_menu, get_providers, get_models, set_model, set_provider, default_model, default_provider, default_img_model, set_img_model, send_img_models, send_help

load_dotenv()

tg_bot_token = getenv('TG_BOT_TOKEN')
api_base_url = getenv('API_BASE_URL')

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

    reply_keyboard = [
        [KeyboardButton('/providers'), KeyboardButton('/help')],
        [KeyboardButton('/models')]
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

    await update.message.reply_text('Привет! Готов ответить на твои вопросы.', reply_markup=markup)
    await show_main_menu(update, context, {
        "help": "Помощь",
        "providers": "Список провайдеров",
        "models": "Список моделей",
        "model": "Установить модель (пример /model gpt3.5-turbo)",
        "provider": "Установить провайдера (пример /provider ReplicateHome)",
        "clear": "Очистить контекст чата (1-й поток, сейчас контекст 30 сообщений)",
    })

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

    provider = context.user_data.get('provider', default_provider)
    model = context.user_data.get('model', default_model)

    # Инициализация истории сообщений, если её ещё нет
    if "history" not in context.user_data:
        context.user_data["history"] = []

    # Добавление нового сообщения пользователя в историю
    context.user_data["history"].append(
        {"role": "user", "content": user_message})

    # Ограничение истории, чтобы не превышать лимиты API
    max_history_length = 30  # Можно настроить по необходимости
    context.user_data["history"] = context.user_data["history"][-max_history_length:]

    logger.info("USERNAME: %s", username)
    logger.info("DIALOG_history: %s", context.user_data["history"])

    # Отправка запроса к API ChatGPT
    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": model,
        "provider": provider,
        "messages": context.user_data["history"],
        "temperature": 0.4,
        "auto_continue": True,
        "conversation_id": chat_id,
        "id": f"{chat_id}-{message_id}"
    }

    logger.info('API_payload: %s', payload)

    loop = asyncio.get_event_loop()

    bot_reply = None

    try:
        async with aiohttp.ClientSession(read_timeout=None) as session:
            async with await loop.run_in_executor(None, lambda: session.post(api_url, json=payload)) as response:
                if response.status == 200:
                    temp_reply = ''
                    # Отправка начального сообщения
                    sent_message = await context.bot.send_message(chat_id=chat_id, text="Думаю...", reply_to_message_id=message_id)
                    last_edit_time = time.time()  # Время последнего редактирования

                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        print('decoded_line', decoded_line)
                        try:
                            response_json = json.loads(decoded_line)
                            print('response_json', response_json)
                            if response_json.get("type") == "content":
                                temp_reply += response_json["content"]

                                current_time = time.time()
                                # Проверка времени для редактирования сообщения
                                if current_time - last_edit_time >= 3:
                                    try:
                                        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=temp_reply, parse_mode='Markdown')
                                        last_edit_time = current_time
                                    except Exception as e:
                                        print(f"Error: {e}")
                                    finally:
                                        continue

                                # Обработка изображений
                                if "\n<!-- generated images start" in temp_reply:
                                    await handle_images(temp_reply, chat_id, context, update, api_base_url, user_message)
                                    await sent_message.delete()
                                    return
                            else:
                                raise ValueError(
                                    "Некорректное сообщение от API.")

                        except json.JSONDecodeError:
                            raise ValueError("Некорректное сообщение от API.")
                    try:
                        # Финальное редактирование сообщения после завершения цикла
                        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=temp_reply, parse_mode='Markdown')
                        bot_reply = temp_reply
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    raise ValueError("Некорректное сообщение от API.")
    except Exception as e:
        print(f"Error: {e}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text="Некорректное сообщение от API.")
        return

    print('bot_reply', bot_reply)

    context.user_data["history"].append(
        {"role": "assistant", "content": bot_reply})

    # Отправка ответа пользователю
    # await context.bot.send_message(chat_id=chat_id, text=bot_reply, reply_to_message_id=update.message.message_id, parse_mode='Markdown')


async def handle_images(bot_reply, chat_id, context, update, api_base_url, user_message):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    print('inside handle images')

    image_links = re.findall(r'\[!\[.*?\]\((.*?)\)\]', bot_reply)

    print('image_links', image_links)

    async with aiohttp.ClientSession() as session:
        for image_link in image_links:
            full_image_url = f"{api_base_url}{image_link}"
            async with session.get(full_image_url) as img_response:
                if img_response.status == 200:
                    image_data = await img_response.read()
                    file_name = os.path.basename(image_link)
                    with open(file_name, 'wb') as f:
                        f.write(image_data)

                    try:
                        with open(file_name, 'rb') as photo_file:
                            await context.bot.send_photo(chat_id=chat_id, photo=photo_file, reply_to_message_id=update.message.message_id, caption=f"Сгенерированные изображения по запросу: {user_message}\n")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке изображения: {e}")
                    finally:
                        # Удаление файла с сервера
                        os.remove(file_name)
                else:
                    logger.error(f"Ошибка при загрузке изображения: {
                                 img_response.status}")


async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['history'] = []
    await update.message.reply_text('Контекст чата очищен.')


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

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message, block=False))

    application.add_handler(CallbackQueryHandler(handle_model_selection))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
