from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from utils import set_mode, get_providers, get_models, set_model, set_provider, set_img_model, send_img_models, send_help
from core_func import start, clear_context, draw, sex, handle_message, handle_model_selection


def register_handlers(application):
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