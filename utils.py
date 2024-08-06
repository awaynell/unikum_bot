from telegram import Update, BotCommand, MenuButtonCommands, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import asyncio
import random
import json

from constants import admin_id, api_base_url, default_img_model, default_img_provider, prompt_predict, prompt_for_translate_message
from img_models import img_models
from common import change_provider_data


async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    context.user_data[f"history-{user_id}-{chat_id}"] = []
    await update.message.reply_text(f"Контекст чата {chat_id} очищен.")


def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context._user_id

    print('userID', user_id)

    if (user_id == None):
        return False

    print('user_id: ', user_id, 'admin_id', admin_id)

    if (int(user_id) == int(admin_id)):
        return True

    return False


async def set_provider(update: Update, context: ContextTypes.DEFAULT_TYPE, provider: str = None):
    import constants

    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text(f'Текущий провайдер: {context.user_data.get("provider", constants.default_provider)}')
        return

    provider = context.args[0] if context.args else (
        provider if provider else None)
    print('provider', provider)
    if provider:
        await change_provider_data(update=update, context=context, provider=provider)

        api_url = f"{api_base_url}/backend-api/v2/models/{provider}"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                print('response', response)
                if response.status == 200:
                    models = await response.json()
                    print('models', models)
                    for model in models:
                        if model.get("default", False):
                            df_model = model.get("model")
                            break

                    if df_model:
                        await change_provider_data(update=update, context=context, model=df_model)

                        await update.message.reply_text(f'Провайдер установлен: {provider}, модель по умолчанию: {constants.default_model}')
                    else:
                        await update.message.reply_text(f'Провайдер установлен: {provider}, но модель по умолчанию не найдена.')
                else:
                    await update.message.reply_text("Произошла ошибка при получении списка моделей.")
    else:
        current_provider = context.bot_data.get(
            'provider', constants.default_provider)
        current_model = context.bot_data.get('model', constants.default_model)
        await update.message.reply_text(f'Текущий провайдер: {current_provider}, модель по умолчанию: {current_model}')


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE, isDefaultAdmin: bool = False, model: str = None):
    import constants

    is_admin = isAdmin(update, context) or isDefaultAdmin

    if is_admin == False:
        await update.message.reply_text(f'Текущая модель: {context.bot_data.get('model', constants.default_model)}')
        return

    model = context.args[0] if context.args else (model if model else None)
    print('model', model)

    if model:
        change_provider_data(update=update, context=context, model=model)

        await update.message.reply_text(f'Модель установлена: {constants.default_model}')
    else:
        await update.message.reply_text(f'Текущая модель: {context.bot_data.get('model', constants.default_model)}')


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
        "1. Через личное API и провайдеров, предоставляющих набор моделей. У каждого провайдера свой набор моделей. Никаких команд вписывать не требуется. Просто общайтесь с ботом также, как с человеком.\n\n"
    )
    help_message2 = (
        "2. С помощью HuggingFace Spaces. Внимание! Генерация картинок ограничена лимитами HuggingFace Spaces. Для генерации без ограничений рекомендую 1 поток. Для этого потока доступны следующие команды:\n \n"
        "- /draw <prompt> - Сгенерировать картинку по запросу (через модель из HuggingFace Spaces)\n"
        "- /getimgm - Список доступных моделей из HuggingFace Spaces\n"
        "- /imgmodel - Посмотреть или установить (после команды вписать) модель из (HuggingFace Spaces)\n \n"
    )
    help_message3 = (
        "Общие команды: \n \n"
        "- /clear - Очищает контекст чата (1 поток, сейчас контекст 30 сообщений)\n"
    )
    await update.message.reply_text(help_message1)
    await update.message.reply_text(help_message2)
    await update.message.reply_text(help_message3)


async def get_models(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int = None):
    import constants

    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text("Nah, you're not an admin.")
        return

    chat_id = update.effective_chat.id

    current_message_id = message_id or update.message.message_id

    api_url = f"{api_base_url}/backend-api/v2/models/{
        context.bot_data.get('provider', constants.default_provider)}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                models = await response.json()
                message = (
                    f"Доступные модели:\n\nТекущая модель: {
                        context.bot_data.get('model', constants.default_model)}"
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
    import constants

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
                    context.bot_data.get('provider', constants.default_provider)}"
                await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await update.message.reply_text("Произошла ошибка при получении списка моделей.")


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, commands: dict):
    command_list = [BotCommand(key, value) for key, value in commands.items()]
    await context.bot.set_my_commands(command_list, language_code="ru", scope=BotCommandScopeChat(chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonCommands(), chat_id=update.effective_chat.id)


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str, send_notifications: bool = True):
    import constants

    command = mode or context.args[0]

    if command == 'draw':
        print('==================')
        print('inside DRAW mode change')
        print('==================')
        context.user_data['modetype'] = command

        context.bot_data['provider'] = default_img_provider
        context.bot_data['model'] = default_img_model

        df_provider = default_img_provider
        df_model = default_img_model
    if command == 'text':
        print('==================')
        print('inside TEXT mode change')
        print('==================')
        context.user_data['modetype'] = command

        await change_provider_data(update=update, context=context,
                                   provider=constants.default_provider, model=constants.default_model)

        df_provider = constants.default_provider
        df_model = constants.default_model

    if command == 'clear':
        clear_context(update=update, context=context)

    if send_notifications == True:
        await update.message.reply_text(text=f"Провайдер {df_provider} и модель {df_model} установлена")


async def predict_user_message_context(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message, chat_id, message_id):
    predict_message = await context.bot.send_message(chat_id=chat_id, text="Определяю контекст сообщения...", reply_to_message_id=message_id)

    print('Внутри predict_user_message_context', user_message)

    loop = asyncio.get_event_loop()

    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": "gpt-3.5-turbo",
        "provider": "Pizzagpt",
        "messages": [{"role": "user", "content": f"{prompt_predict} {user_message}"}],
        "temperature": 0.1,
        "auto_continue": False,
        "conversation_id": random.random(),
        "id": random.random()
    }

    print('API data', f"api_url: {api_url}, payload: {payload}")

    temp_reply = ''
    predict_model_reply = ''
    # значение по умолчанию
    predict = 'text'

    try:
        # send request to AI API
        async with aiohttp.ClientSession(read_timeout=None) as session:
            async with await loop.run_in_executor(None, lambda: session.post(api_url, json=payload)) as response:
                if response.status == 200:
                    print('response.status == 200')
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        response_json = json.loads(decoded_line)
                        print('predict_response_json', response_json)
                        if (response_json.get("type") == "provider"):
                            print('predict_response_json.get("type") == "provider"')
                            continue
                        if response_json.get("type") == "content":
                            print('predict: ', response_json["content"])
                            temp_reply += response_json["content"]

                    # text. draw. clear.
                    predict_model_reply = temp_reply.lower()

                    print('=======================================')
                    print('predict_model_reply: ', predict_model_reply)
                    print('=======================================')

                    text_rules = ['text', 'текст']
                    draw_rules = ['draw', 'рисовать', 'отрисовать', 'нарисуй']

                    # Разделяем ответ на слова
                    words = predict_model_reply.split(' ')

                    # Проверяем, содержатся ли какие-либо из правил в ответе
                    isText = any(rule in words for rule in text_rules)
                    isDraw = any(rule in words for rule in draw_rules)

                    predict = 'draw' if isDraw else 'text'

                    await predict_message.delete()
                else:
                    raise Exception(
                        f"Возникла ошибка на стадии анализа сообщения: {response.status}")
    except Exception as e:
        print(f"Error: {e}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=predict_message.message_id, text=e)
    finally:
        await set_mode(update, context, predict, False)


async def translate_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message, chat_id, message_id):
    loop = asyncio.get_event_loop()

    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": 'Blackbox',
        "provider": "Blackbox",
        "messages": [{"role": "user", "content": f"{prompt_for_translate_message} {user_message}"}],
        "temperature": 0.1,
        "auto_continue": False,
        "conversation_id": random.random(),
        "id": random.random()
    }

    temp_reply = ''

    try:
        # send request to AI API
        async with aiohttp.ClientSession(read_timeout=None) as session:
            async with await loop.run_in_executor(None, lambda: session.post(api_url, json=payload)) as response:
                if response.status == 200:
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        response_json = json.loads(decoded_line)
                        if (response_json.get("type") == "provider"):
                            continue
                        if response_json.get("type") == "content":
                            print('predict: ', response_json["content"])
                            temp_reply += response_json["content"]
                    print(f"Перевод: {temp_reply}")
                    return temp_reply

                else:
                    raise Exception(
                        f"Возникла ошибка на стадии перевода сообщения: {response.status}")
    except Exception as e:
        print(f"Error: {e}")


async def set_defimgm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global default_img_provider, default_img_model
    provider, model = context.args

    default_img_provider = provider
    default_img_model = model

    await update.message.reply_text(text=f"Вы установили {default_img_provider} и {default_img_model} для генерации изображений по умолчанию.")
