from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

from dotenv import load_dotenv
from os import getenv
from img_models import img_models
import aiohttp

load_dotenv()

admin_id = getenv('TG_ADMIN_ID')
api_base_url = getenv('API_BASE_URL')

default_provider = "Pizzagpt"
default_model = "gpt-3.5-turbo"
default_img_model = 'imagineo'


# def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.message.from_user.id

#     print('user_id: ', user_id, 'admin_id', admin_id)

#     if (int(user_id) == int(admin_id)):
#         return True

#     return False


async def set_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # is_admin = isAdmin(update, context)

    # if is_admin == False:
    #     await update.message.reply_text(f'Текущий провайдер: {context.chat_data.get("provider", default_provider)}')
    #     return

    provider = context.args[0] if context.args else None
    if provider:
        context.chat_data['provider'] = provider

        api_url = f"{api_base_url}/backend-api/v2/models/{provider}"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    models = await response.json()
                    default_model = None
                    for model in models:
                        if model.get("default", False):
                            default_model = model.get("model")
                            break

                    if default_model:
                        context.chat_data['model'] = default_model
                        await update.message.reply_text(f'Провайдер установлен: {provider}, модель по умолчанию: {default_model}')
                    else:
                        await update.message.reply_text(f'Провайдер установлен: {provider}, но модель по умолчанию не найдена.')
                else:
                    await update.message.reply_text("Произошла ошибка при получении списка моделей.")
    else:
        current_provider = context.chat_data.get('provider', default_provider)
        current_model = context.chat_data.get('model', default_model)
        await update.message.reply_text(f'Текущий провайдер: {current_provider}, модель по умолчанию: {current_model}')


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


async def send_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "Список доступных команд: \n\n"
        "/clear - Очищает контекст чата\n"
        "/providers - Получить список доступных провайдеров\n"
        "/models - Получить список доступных моделей (зависит от провайдера)\n"
        "/provider - Посмотреть или установить (после команды вписать) провайдера для текстовой модели\n"
        "/model - Посмотреть или установить (после команды вписать) текстовую модель\n"
        "/draw <prompt> - Сгенерировать картинку по запросу\n"
        "/getimgm - Список доступных моделей txt2img\n"
        "/imgmodel - Посмотреть или установить (после команды вписать) txt2img модель\n \n"
        "Для вопросов к текстовой модели просто напишите свой вопрос боту"
    )
    await update.message.reply_text(help_message)


async def get_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = f"{api_base_url}/backend-api/v2/models/{
        context.chat_data.get('provider', default_provider)}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                models = await response.json()
                models_list = "\n".join(
                    f"— `{model['model']}`" for model in models)
                message = f"Доступные модели:\n{models_list}\n\nТекущая модель: {
                    context.chat_data.get('model', default_model)}"
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("Произошла ошибка при получении списка моделей.")


async def get_providers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = f"{api_base_url}/backend-api/v2/providers"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                providers = await response.json()
                providers_list = "\n".join(
                    f"— `{provider}`" for provider in providers)
                message = f"Доступные провайдеры:\n{providers_list}\n\nТекущий провайдер: {
                    context.chat_data.get('provider', default_provider)}"
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("Произошла ошибка при получении списка моделей.")
