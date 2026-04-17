from telegram import BotCommand
from telegram.ext import Application, ApplicationBuilder

from register_handlers import register_handlers
from constants import tg_bot_token


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("vadim_s_dnukhoy", "Поздравить Вадима как легенду")
    ])


def main():
    token = tg_bot_token
    application = ApplicationBuilder().token(token).post_init(post_init).build()

    register_handlers(application=application)
    application.run_polling()


if __name__ == '__main__':
    main()
