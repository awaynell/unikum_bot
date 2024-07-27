from telegram.ext import ContextTypes
from telegram import Update


async def change_provider_data(update: Update, context: ContextTypes.DEFAULT_TYPE, provider: str = None, model: str = None, withNotificationMsg: bool = False):
    import constants

    _provider = provider or context.bot_data.get(
        'provider', constants.default_provider)
    _model = model or context.bot_data.get('model', constants.default_model)

    context.bot_data['provider'] = _provider
    context.bot_data['model'] = _model

    constants.default_model = model
    constants.default_provider = provider

    if (withNotificationMsg):
        await update.message.reply_text(f'Модель {model} и провайдер {provider} установлены')
