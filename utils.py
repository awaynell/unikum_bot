from telegram import Update, BotCommand, MenuButtonCommands, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import aiohttp
import asyncio
import random
import json
import re

from constants import admin_id, api_base_url, default_img_model, default_img_provider, prompt_predict, prompt_for_translate_message, emoji_slots
from img_models import img_models
from common import change_provider_data
from providers import img_providers


async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    context.user_data[f"history-{user_id}-{chat_id}"] = []
    await update.message.reply_text(f"Контекст чата {chat_id} очищен.")


def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context._user_id

    if (user_id == None):
        return False

    if (int(user_id) == int(admin_id)):
        return True

    return False


async def set_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import constants

    is_admin = isAdmin(update, context)

    current_provider = context.bot_data.get(
        'provider', constants.default_provider)
    current_model = context.bot_data.get('model', constants.default_model)

    if is_admin == False:
        await update.message.reply_text(f'Текущий провайдер: {current_provider}, модель по умолчанию: {current_model}')
        return

    provider = context.args[0] if context.args else None

    if provider:
        await change_provider_data(update=update, context=context, provider=provider)

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
                        await change_provider_data(update=update, context=context, model=df_model)

                        await update.message.reply_text(f'Провайдер установлен: {provider}, модель по умолчанию: {constants.default_model}')
                    else:
                        await update.message.reply_text(f'Провайдер установлен: {provider}, но модель по умолчанию не найдена.')
                else:
                    await update.message.reply_text("Произошла ошибка при получении списка моделей.")
    else:
        await update.message.reply_text(f'Текущий провайдер: {current_provider}, модель по умолчанию: {current_model}')


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE, isDefaultAdmin: bool = False, model: str = None):
    import constants

    is_admin = isAdmin(update, context) or isDefaultAdmin

    if is_admin == False:
        await update.message.reply_text(f'Текущая модель: {context.bot_data.get('model', constants.default_model)}')
        return

    model = context.args[0] if context.args else (model if model else None)

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
        context.user_data['modetype'] = command
    if command == 'text':
        context.user_data['modetype'] = command

    if command == 'clear':
        clear_context(update=update, context=context)


async def predict_user_message_context(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message, chat_id, message_id):
    predict_message = await context.bot.send_message(chat_id=chat_id, text="Определяю контекст сообщения...", reply_to_message_id=message_id)

    loop = asyncio.get_event_loop()

    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": "gpt-4o-mini",
        "provider": "Pizzagpt",
        "messages": [{"role": "user", "content": f"{prompt_predict} {user_message}"}],
        "temperature": 0.1,
        "auto_continue": False,
        "conversation_id": random.random(),
        "id": random.random()
    }

    temp_reply = ''
    predict_model_reply = ''
    # значение по умолчанию
    predict = 'text'

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
                            temp_reply += response_json["content"]

                    # text. draw. clear.
                    predict_model_reply = temp_reply.lower()

                    # print('=======================================')
                    # print('predict_model_reply: ', predict_model_reply)
                    # print('=======================================')

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
        "model": 'gpt-4o-mini',
        "provider": "Pizzagpt",
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
                            temp_reply += response_json["content"]
                    return temp_reply

                else:
                    raise Exception(
                        f"Возникла ошибка на стадии перевода сообщения: {response.status}")
    except Exception as e:
        print(f"Error: {e}")


async def set_defimgm(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str = ''):
    global default_img_provider, default_img_model

    is_admin = isAdmin(update, context)

    if is_admin == False:
        await update.message.reply_text(f'Текущий провайдер: {context.user_data.get("imgprovider", default_img_provider)}, текущая модель: {context.user_data.get("imgmodel", default_img_model)}')
        return

    # Если аргументы не переданы, показываем кнопки с ключами
    if (context.args != None and len(context.args) == 0 and key == ''):
        # Получаем ключи из словаря и формируем кнопки по 2 в ряд
        keys = list(img_providers.keys())
        buttons = [
            [InlineKeyboardButton(
                k, callback_data=f'/defimgm {k}') for k in keys[i:i+2]]
            for i in range(0, len(keys), 2)
        ]

        reply_markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(f'Текущий провайдер: {context.user_data.get("imgprovider", default_img_provider)}, текущая модель: {context.user_data.get("imgmodel", default_img_model)}')

        await update.message.reply_text(text="Выберите ключ для установки imgprovider и imgmodel по умолчанию:", reply_markup=reply_markup)
        return

    # Проверка, существует ли ключ в словаре img_providers
    if key in img_providers:
        imgprovider = img_providers[key]["provider"]
        imgmodel = img_providers[key]["model"]

        # Сохранение значений в контексте и глобальных переменных
        context.bot_data['imgprovider'] = imgprovider
        context.bot_data['imgmodel'] = imgmodel

        default_img_provider = imgprovider
        default_img_model = imgmodel

        # Определение, как был вызван обработчик (через сообщение или нажатие кнопки)
        if update.message:
            await update.message.reply_text(
                text=f"Вы установили {default_img_provider} и {
                    default_img_model} для генерации изображений по умолчанию."
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                text=f"Вы установили {default_img_provider} и {
                    default_img_model} для генерации изображений по умолчанию."
            )
    else:
        if update.message:
            await update.message.reply_text(text=f"Ключ '{key}' не найден в списке доступных моделей.")
        elif update.callback_query:
            await update.callback_query.message.reply_text(text=f"Ключ '{key}' не найден в списке доступных моделей.")


def escape_markdown(text: str) -> str:
    """
    Экранирует символы, которые могут вызвать проблемы при использовании Markdown.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


def generate_slot_display(reels):
    return "\n".join([" | ".join(row) for row in zip(*reels)])


async def slot_machine(update: Update, context: CallbackContext) -> None:
    message = await update.message.reply_text("🎰 Запуск слот-машины...")

    # Изначальные позиции для каждого столбца
    reels = [
        [random.choice(emoji_slots) for _ in range(3)] for _ in range(3)
    ]

    for _ in range(15):  # Количество "вращений"
        for reel in reels:
            reel.pop(0)
            reel.append(random.choice(emoji_slots))

        slot_display = generate_slot_display(reels)
        # Случайная задержка для более естественной анимации
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await message.edit_text(f"🎰\n{slot_display}")

    # Финальный результат
    final_display = generate_slot_display(reels)
    # Проверка, совпадают ли все элементы в центре
    is_win = len(set(reel[1] for reel in reels)) == 1

    await asyncio.sleep(0.5)
    await message.edit_text(f"🎰\n{final_display}\n\n{'🎉 Вы выиграли!' if is_win else '😢 Попробуйте еще раз!'}")
