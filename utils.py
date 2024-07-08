from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

from dotenv import load_dotenv
from os import getenv
from img_models import img_models
import asyncio

load_dotenv()

admin_id = getenv('TG_ADMIN_ID')

default_provider = "You"
default_model = "gpt-3.5-turbo"
default_img_model = 'imagineo'


def aexec(func):
    def wrapper(update: Update, context: CallbackContext):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(update, context))
        loop.close()
    return wrapper


# def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.message.from_user.id

#     print('user_id: ', user_id, 'admin_id', admin_id)

#     if (int(user_id) == int(admin_id)):
#         return True

#     return False


async def set_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # is_admin = isAdmin(update, context)

    # if is_admin == False:
    #     await update.message.reply_text(f'Текущий провайдер: {context.chat_data.get('provider', default_provider)}')
    #     return

    provider = context.args[0] if context.args else None
    if provider:
        context.chat_data['provider'] = provider
        await update.message.reply_text(f'Провайдер установлен: {provider}')
    else:
        await update.message.reply_text(f'Текущий провайдер: {context.chat_data.get('provider', default_provider)}')


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # is_admin = isAdmin(update, context)

    # if is_admin == False:
    #     await update.message.reply_text(f'Текущая модель: {context.chat_data.get('model', default_model)}')
    #     return

    model = context.args[0] if context.args else None
    if model:
        context.chat_data['model'] = model
        await update.message.reply_text(f'Модель установлена: {model}')
    else:
        await update.message.reply_text(f'Текущая модель: {context.chat_data.get('model', default_model)}')


async def set_img_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    img_model = context.args[0] if context.args else None

    if bool(img_model) & bool(img_models.get(img_model)):
        context.chat_data['img_model'] = img_model
        await update.message.reply_text(f'Модель установлена: {img_model}')
    else:
        await update.message.reply_text(f'Текущая модель: {context.chat_data.get("img_model", default_img_model)}')


async def send_img_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    models_list = "\n".join(f"- {model}" for model in img_models)
    message = f"Доступные модели txt2img:\n{models_list}\n\nТекущая модель: {
        context.chat_data.get('img_model', default_img_model)}"
    await update.message.reply_text(message)
