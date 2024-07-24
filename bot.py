from telegram.ext import ApplicationBuilder

from register_handlers import register_handlers
from constants import tg_bot_token


def main():
    # Вставь свой токен здесь
    token = tg_bot_token

    # Создаем приложение
    application = ApplicationBuilder().token(token).build()

    register_handlers(application=application)

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
