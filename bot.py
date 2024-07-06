import requests
import logging
from logging.handlers import TimedRotatingFileHandler
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from os import getenv

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

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
