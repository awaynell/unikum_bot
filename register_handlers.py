from telegram.ext import CommandHandler

from utils import birthday


def register_handlers(application):
    application.add_handler(CommandHandler(
        ["vadim_s_dnukhoy", "VADIM_S_DNUKHOY"], birthday, block=True))
