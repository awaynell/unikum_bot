from telegram import Update
from telegram.ext import ContextTypes

from dotenv import load_dotenv
from os import getenv

load_dotenv()

admin_id = getenv('TG_ADMIN_ID')

default_provider = "You"
default_model = "gpt-3.5-turbo"


async def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = await update.message.from_user.id

    if (int(user_id) == int(admin_id)):
        return True

    return False


async def set_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = await isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text(f'Текущий провайдер: {context.chat_data.get('provider', default_provider)}')
        return

    provider = context.args[0] if context.args else None
    if provider:
        context.chat_data['provider'] = provider
        await update.message.reply_text(f'Провайдер установлен: {provider}')
    else:
        await update.message.reply_text(f'Пожалуйста, укажи провайдера. Текущий провайдер: {context.chat_data.get('provider', default_provider)}')


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text(f'Текущая модель: {context.chat_data.get('model', default_model)}')
        return

    model = context.args[0] if context.args else None
    if model:
        context.chat_data['model'] = model
        await update.message.reply_text(f'Модель установлена: {model}')
    else:
        await update.message.reply_text(f'Пожалуйста, укажи модель. Текущая модель: {context.chat_data.get('model', default_model)}')
