from telegram import Update, BotCommand, MenuButtonCommands, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp

from constants import admin_id, api_base_url, default_model, default_provider, default_img_model, default_img_provider
from img_models import img_models

def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    print('user_id: ', user_id, 'admin_id', admin_id)

    if (int(user_id) == int(admin_id)):
        return True

    return False


async def set_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text(f'Текущий провайдер: {context.user_data.get("provider", default_provider)}')
        return

    provider = context.args[0] if context.args else None
    if provider:
        context.bot_data['provider'] = provider

        api_url = f"{api_base_url}/backend-api/v2/models/{provider}"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    models = await response.json()
                    for model in models:
                        if model.get("default", False):
                            df_model = model.get("model")
                            break

                    if df_model:
                        context.bot_data['model'] = default_model
                        await update.message.reply_text(f'Провайдер установлен: {provider}, модель по умолчанию: {default_model}')
                    else:
                        await update.message.reply_text(f'Провайдер установлен: {provider}, но модель по умолчанию не найдена.')
                else:
                    await update.message.reply_text("Произошла ошибка при получении списка моделей.")
    else:
        current_provider = context.bot_data.get('provider', default_provider)
        current_model = context.bot_data.get('model', default_model)
        await update.message.reply_text(f'Текущий провайдер: {current_provider}, модель по умолчанию: {current_model}')


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text(f'Текущая модель: {context.bot_data.get('model', default_model)}')
        return

    model = context.args[0] if context.args else None
    if model:
        context.bot_data['model'] = model
        await update.message.reply_text(f'Модель установлена: {model}')
    else:
        await update.message.reply_text(f'Текущая модель: {context.bot_data.get('model', default_model)}')


async def set_img_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    img_model = context.args[0] if context.args else None

    if bool(img_model) & bool(img_models.get(img_model)):
        context.user_data['img_model'] = img_model
        await update.message.reply_text(f'Модель установлена: {img_model}')
    else:
        await update.message.reply_text(f'Текущая модель: {context.user_data.get("img_model", default_img_model)}')


async def send_img_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    models_list = "\n".join(f"- {model}" for model in img_models)
    message = f"Доступные модели txt2img:\n{models_list}\n\nТекущая модель: {
        context.user_data.get('img_model', default_img_model)}"
    await update.message.reply_text(message)


async def send_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message1 = (
        "У бота есть 2 потока работы: \n \n"
        "1. Через личное API и провайдеров, предоставляющих набор моделей. У каждого провайдера свой набор моделей. У некоторых провайдеров также доступны модели для генерации картинок (`DeepInfraImage` и `ReplicateHome`)  \n \n К этому потоку относятся команды: \n \n - /providers - Получить список доступных провайдеров\n - /models - Получить список доступных моделей (зависит от провайдера)\n - /provider - Посмотреть или установить (после команды вписать) провайдера для модели\n - /model - Посмотреть или установить (после команды вписать) текущую модель\n\n"
    )
    help_message2 = (
        "2. С помощью HuggingFace Spaces. Внимание! Генерация картинок ограничена лимитами HuggingFace Spaces. Для генерации без ограничений рекомендую 1 поток. Для этого потока доступны следующие команды:\n \n"
        "- /draw <prompt> - Сгенерировать картинку по запросу (через модель из HuggingFace Spaces)\n"
        "- /getimgm - Список доступных моделей из HuggingFace Spaces\n"
        "- /imgmodel - Посмотреть или установить (после команды вписать) модель из (HuggingFace Spaces)\n \n"
    )
    help_message3 = (
        "Также, боту можно написать 'рисовать' или 'спросить' для смены режима общения. \n \n"
        "Общие команды: \n \n"
        "- /clear - Очищает контекст чата (1 поток, сейчас контекст 30 сообщений)\n"
    )
    await update.message.reply_text(help_message1)
    await update.message.reply_text(help_message2)
    await update.message.reply_text(help_message3)


async def get_models(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int = None):
    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text("Nah, you're not an admin.")
        return

    chat_id = update.effective_chat.id

    current_message_id = message_id or update.message.message_id

    api_url = f"{api_base_url}/backend-api/v2/models/{
        context.user_data.get('provider', default_provider)}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                models = await response.json()
                message = (
                    f"Доступные модели:\n\nТекущая модель: {
                        context.bot_data.get('model', default_model)}"
                )

                # Создание кнопок для каждой модели
                buttons = [
                    [InlineKeyboardButton(
                        model['model'], callback_data=f'/model {model["model"]}') for model in models[i:i+4]]
                    for i in range(0, len(models), 4)
                ]
                reply_markup = InlineKeyboardMarkup(buttons)

                await context.bot.send_message(text=message, reply_markup=reply_markup, parse_mode='Markdown', reply_to_message_id=current_message_id, chat_id=chat_id)
            else:
                await update.message.reply_text("Произошла ошибка при получении списка моделей.")


async def get_providers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text("Nah, you're not an admin.")
        return

    api_url = f"{api_base_url}/backend-api/v2/providers"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                providers = await response.json()
                available_providers = [key for key, value in providers.items(
                ) if 'Auth' not in value and 'WebDriver' not in value]

                buttons = [
                    [InlineKeyboardButton(
                        provider, callback_data=f'/provider {provider}') for provider in available_providers[i:i+4]]
                    for i in range(0, len(available_providers), 4)
                ]
                reply_markup = InlineKeyboardMarkup(buttons)

                message = f"Доступные провайдеры:\n\nТекущий провайдер: {
                    context.user_data.get('provider', default_provider)}"
                await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await update.message.reply_text("Произошла ошибка при получении списка моделей.")


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, commands: dict):
    command_list = [BotCommand(key, value) for key, value in commands.items()]
    await context.bot.set_my_commands(command_list, language_code="ru", scope=BotCommandScopeChat(chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonCommands(), chat_id=update.effective_chat.id)


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    command = mode or context.args[0]

    if command == 'draw':
        context.user_data['modetype'] = command
        context.bot_data['provider'] = default_img_provider
        context.bot_data['model'] = default_img_model

        df_provider = 'DeepInfraImage'
        df_model = 'stability-ai/sdxl'
    if command == 'text':
        context.user_data['modetype'] = command
        context.bot_data['provider'] = default_provider
        context.bot_data['model'] = default_model

        df_provider = default_provider
        df_model = default_model
    await update.message.reply_text(text=f"Провайдер {df_provider} и модель {df_model} установлена")
