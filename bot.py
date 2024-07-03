import logging
import requests
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Настройки логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для обработки команды /start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот, который использует API ChatGPT. Напиши мне что-нибудь!')

# Функция для обработки сообщений


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id
    bot_username = context.bot.username

    # Проверка типа чата: личный или групповой
    if update.message.chat.type in ['group', 'supergroup']:
        # Ответ только на сообщения, содержащие имя бота или упоминание
        if bot_username.lower() in user_message.lower():
            await respond_to_user(update, context, user_message)
    else:
        # Ответ на все сообщения в личных чатах
        await respond_to_user(update, context, user_message)


async def respond_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    chat_id = update.message.chat_id

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Отправка запроса к API ChatGPT
    api_url = "http://212.113.101.93:1337/v1/chat/completions"
    payload = {
        "model": "gpt-3.5-turbo",
        "provider": "You",
        "web_search": True,
        "messages": [{"role": "user", "content": user_message}]
    }
    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        bot_reply = response.json()["choices"][0]["message"]["content"]
    else:
        bot_reply = "Извините, произошла ошибка при обращении к API."

    # Отправка ответа пользователю
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await context.bot.send_message(chat_id=chat_id, text=bot_reply)


def main():
    # Вставь свой токен здесь
    token = '6728773804:AAEQ-pJpPvx1Q72ynoa1k4WnGCKPPZJzbhI'

    # Создаем приложение
    application = ApplicationBuilder().token(token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
