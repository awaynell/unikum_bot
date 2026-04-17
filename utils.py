from telegram import Update, BotCommand, MenuButtonCommands, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import aiohttp
import asyncio
import random
import json
import re

from constants import admin_id, api_base_url, default_img_model, default_img_provider, prompt_predict, prompt_for_translate_message, emoji_slots, default_model, default_provider
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


async def get_models(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int = None, from_callback: bool = False):
    import constants

    is_admin = isAdmin(update, context)

    if is_admin == False:
        # Исправлено: проверяем, откуда вызвана функция
        if from_callback:
            await update.callback_query.message.reply_text("Nah, you're not an admin.")
        else:
            await update.message.reply_text("Nah, you're not an admin.")
        return

    chat_id = update.effective_chat.id

    # Исправлено: правильное определение message_id
    if message_id is None:
        if from_callback:
            current_message_id = update.callback_query.message.message_id
        else:
            current_message_id = update.message.message_id
    else:
        current_message_id = message_id

    api_url = f"{api_base_url}/backend-api/v2/models/{context.bot_data.get('provider', constants.default_provider)}"

    # Добавлен таймаут для запроса
    timeout = aiohttp.ClientTimeout(total=30)  # 30 секунд таймаут

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    models = await response.json()
                    message = (
                        f"Доступные модели:\n\nТекущая модель: {context.bot_data.get('model', constants.default_model)}"
                    )

                    # Создание кнопок для каждой модели
                    buttons = [
                        [InlineKeyboardButton(
                            model['model'], callback_data=f'/model {model["model"]}') for model in models[i:i+4]]
                        for i in range(0, len(models), 4)
                    ]
                    reply_markup = InlineKeyboardMarkup(buttons)

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    error_msg = "Произошла ошибка при получении списка моделей."
                    if from_callback:
                        await update.callback_query.message.reply_text(error_msg)
                    else:
                        await update.message.reply_text(error_msg)
    except asyncio.TimeoutError:
        error_msg = "Таймаут при получении списка моделей. Попробуйте позже."
        if from_callback:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
    except Exception as e:
        error_msg = f"Ошибка: {str(e)}"
        if from_callback:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)


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
                available_providers = [
                    provider['name'] for provider in providers if not provider['auth']]

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

    _provider = context.bot_data.get(
        'provider', default_provider)
    _model = context.bot_data.get('model', default_model)

    loop = asyncio.get_event_loop()

    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": _model,
        "provider": _provider,
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
    _provider = context.bot_data.get(
        'provider', default_provider)
    _model = context.bot_data.get('model', default_model)

    loop = asyncio.get_event_loop()

    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": _model,
        "provider": _provider,
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


BIRTHDAY_MESSAGES = [
    "@VadimRagulin, братан, с днюхой! 🎉 Ты наш драгоценный перец, легенда улиц, король рофлов! Живи сто лет, как эльфийский лорд, и пускай твой вайб всегда будет на 100500! 🚀",
    "@VadimRagulin, Вадя, с днём рожденья, кореш! 😎 Ты как Wi-Fi — все к тебе подключаются, потому что ты раздаёшь только топовый вайб! Ебать, как ты хорош, продолжай жечь! 🔥",
    "@VadimRagulin, ооо, наш лучший друган, с днюхой тебя! 🎂 Ты как мемасик из 2010, всегда актуален и всех угораешь! Похер на возраст, ты вечно молодой рофлан! 😜",
    "@VadimRagulin, с днём варенья, наш золотой пацан! 🥳 Ты как шавуха в три утра — всегда в тему и всех спасает! Пусть твой путь будет таким же ярким, как твой рофляный настрой! 🌟",
    "@VadimRagulin, Вадимка, с днюхой, наш перечный король! 👑 Ты как пранк в чатике, всегда в яблочко! Желаю тебе кучу бабла, лулзов и чтобы твой рофл был мощнее, чем я в 7 утра без кофе! ☕",
    "@VadimRagulin, эй, наш главный рофло-маэстро, с днём рождения! 🎈 Ты как котик из мемов — все тебя любят, и ты всегда в центре тусы! Го дальше разносить этот мир своим эпичным вайбом! 😺",
    "@VadimRagulin, с днюшкой, легенда! 🦁 Ты как старый добрый мем про борща, всегда греешь душу! Пусть твоя жизнь будет такой же сочной, как твой юмор, и такой же мощной, как твой рофл! 💪",
    "@VadimRagulin, Вадя, с днём рожденья, наш алмазный кореш! 💎 Ты как тикток-тренд — взрываешь всё вокруг! Желаю тебе катать на максималках, рофлить без остановки и быть вечно в топе! 🏆",
    "@VadimRagulin, с днюхой, наш перец и душа компании! 🎁 Ты как анекдот на миллион — все ржут, никто не забывает! Пусть твой вайб всегда будет на уровне 'ебать, это гениально'! 😍",
    "@VadimRagulin, брат, с днём рождения! 🎉 Ты наш рофляный император, наш мемный гуру! Пусть твоя жизнь будет как спам в чате — бесконечной и полной угара! 🚀",
    "@VadimRagulin, с днюхой, наш главный бро! 😏 Ты как стикер в телеге — всегда к месту и вызывает лыбу! Желаю тебе тонну кайфа, рофлов и чтобы твой вайб был мощнее, чем финал 'Игры престолов'! 🗡️",
    "@VadimRagulin, Вадим, с днём рожденья, наш эпичный кореш! 🌈 Ты как радужный единорог в мире мемов — редкий и всех радуешь! Го дальше раздавать рофлы направо и налево! 🦄",
    "@VadimRagulin, с днюхой, наш рофляный титан! 💥 Ты как гифка с котом, падающим с дивана — вечно в тренде! Пусть твоя жизнь будет такой же угарной, как твой юмор! 😹",
    "@VadimRagulin, Вадя, с днём варенья, наш мемный гений! 🧠 Ты как нейросеть, которая генерит только топовые шутки! Желаю тебе бабок, угара и чтобы твой рофл бил все рекорды! 📈",
    "@VadimRagulin, с днём рождения, наш король тусовок! 🎉 Ты как диджей на вечеринке — заводишь всех с пол-оборота! Пусть твой вайб всегда качает, а рофлы бьют прямо в сердце! 🎶",
    "@VadimRagulin, с днюхой, наш драгоценный рофлан! 😝 Ты как мем про 'похер, пляшем' — всегда в настроении! Желаю тебе катать по жизни на чиле и разносить всех своим юмором! 🕺",
    "@VadimRagulin, Вадимка, с днём рожденья, наш легендарный пацан! 🏅 Ты как лайк в чатике — все тебя ценят! Пусть твоя жизнь будет как топовый ролик в ютубе — миллион лайков и куча просмотров! 📹",
    "@VadimRagulin, с днюхой, наш рофляный бог! ⚡ Ты как молния в ясном небе — всех шокируешь своим вайбом! Желаю тебе кайфовать, рофлить и быть вечно на волне! 🌊",
    "@VadimRagulin, с днём рождения, наш перечный император! 👑 Ты как мем, который репостят все — везде и всегда в топе! Пусть твоя жизнь будет такой же яркой, как твой рофл! ✨",
    "@VadimRagulin, Вадя, с днюхой, наш главный мемодел! 🖼️ Ты как фотошопленный кот в короне — эпичен и неподражаем! Желаю тебе угара, бабла и чтобы твой вайб был вечно на максимуме! 😻",
    "@VadimRagulin, с днюхой, машина вайба! 🛸 Ты как секретный чит-код на хорошее настроение: один раз ввёл, и весь чат орёт от счастья. Держи курс на лулзы и роскошь! ✨",
    "@VadimRagulin, Вадос, с праздником, ты мемный бизнес-класс! 🥂 Где ты появляешься, там сразу уровень прикола поднимается до неприличия. Желаю жить так, будто каждый день тебе аплодирует весь интернет! 🌍",
    "@VadimRagulin, братюнь, с днюхой! 🍰 Ты как идеальный плейлист: ни одного плохого трека, только хиты, рофлы и уверенная подача. Пусть у тебя всё играет жирно! 🔊",
    "@VadimRagulin, Вадимыч, поздравляю! 🚗 Ты как таксист удачи: подбираешь людей в грусти и довозишь до смеха без сдачи. Пусть жизнь везёт тебя только по VIP-полосе! 💸",
    "@VadimRagulin, с днём рождения, гроза скучных дней! 🌪️ Ты врываешься в любой чат так, будто тебе там уже выдали кубок за лучший вайб. Желаю бесконечного куража и красивых заносов по жизни! 🏁",
    "@VadimRagulin, Вадя, ты сегодня официальный министр угара! 🏛️ Подписываю указ: выдать тебе вагон счастья, склад удачи и безлимит на рофлы. Исполнять немедленно! 📜",
    "@VadimRagulin, с днюхой, лорд хорошего настроения! 🦾 Ты как турбонаддув для любой тусы: без тебя ехало, с тобой полетело. Пусть всё у тебя ускоряется только в сторону кайфа! 🚀",
    "@VadimRagulin, Вадимка, поздравляю, ты редкий артефакт! 🗿 В тебе сочетаются мем, стиль, прикол и внутренняя мощь, как будто тебя собирали лучшие инженеры юмора. Живи богато, ржи громко! 💥",
    "@VadimRagulin, с праздником, великий поставщик настроения! 📦 Ты как доставка радости: быстро, точно и всегда вовремя. Желаю, чтобы судьба так же щедро отправляла тебе успех пачками! 🎁",
    "@VadimRagulin, Вадосик, с днюхой! 🍻 Ты как апдейт без багов — редкость, которую все реально ждали. Пусть в новом году жизни у тебя будет только стабильный релиз счастья! ✅",
    "@VadimRagulin, брат, поздравляю, ты просто deluxe-версия человека! 💎 Харизма выкручена, юмор на ультрах, вайб официально признан опасно приятным. Пусть жизнь отвечает тебе тем же уровнем щедрости! 🌟",
    "@VadimRagulin, с днём рождения, вождь мемного племени! 🐺 Ты умеешь собрать людей вокруг себя лучше любого алгоритма рекомендаций. Пусть все лучшие сюжеты этой жизни сами находят тебя! 🎬",
    "@VadimRagulin, Вадя, с праздником, ты натуральный энерджайзер для чата! 🔋 Когда ты в онлайне, у скуки просто нет шансов. Желаю заряда, кайфа и приколов без просадки по мощности! ⚙️",
    "@VadimRagulin, с днюхой, сэр прикольный до невозможности! 🎩 Ты как случайный бонусный уровень, который оказался лучше всей основной игры. Пусть у тебя каждый день будет с таким же приятным перебором! 🕹️",
    "@VadimRagulin, Вадим, поздравляю, ты ходячая спецоперация по спасению настроения! 🚨 Один твой рофл, и люди уже забыли, что собирались грустить. Так и продолжай наводить добро и беспорядок в унынии! 😎",
    "@VadimRagulin, с праздником, главный специалист по красивому угару! 🎯 Ты попадаешь шутками ровно в центр души, без промаха и с аплодисментами. Пусть все твои планы так же чётко залетают в цель! 🏹",
    "@VadimRagulin, Вадя, с днюхой! 🧨 Ты как фейерверк после зарплаты: внезапно, ярко и все счастливы. Желаю тебе мощного года, где поводов кайфовать будет больше, чем сообщений в рабочем чате! 📲",
    "@VadimRagulin, именинник, ты чистый premium-content! 📺 Без рекламы, без провисаний, только плотный угар и крепкая харизма. Пусть подписка на удачу у тебя не заканчивается вообще никогда! 💳",
    "@VadimRagulin, с днюхой, верховный жрец хорошего вайба! 🔮 Ты как магический артефакт: где появился, там сразу +50 к настроению и -100 к скуке. Пусть судьба щедро дропает тебе только легендарный лут! 🪙",
    "@VadimRagulin, Вадос, поздравляю! 🧃 Ты как холодный сок в жару: появился вовремя и спас всем настроение. Желаю тебе жить вкусно, громко и без намека на пресность! 🌴",
    "@VadimRagulin, брат, с праздником! 🛠️ Ты как мастерская по ремонту уныния: принимаешь тоску, выдаешь ржач и бодрый настрой. Пусть у тебя самого все по жизни работает как часы! ⌚",
    "@VadimRagulin, с днюхой, генерал приколов! 🎖️ Под твоим командованием любой чат превращается в территорию смеха. Желаю тебе побед по всем фронтам, от бабла до кайфа! 🏴",
    "@VadimRagulin, Вадя, с днем рождения! 🥨 Ты как лучшая закуска к любой тусе: без тебя можно, но уже не то. Пусть в твоей жизни всегда будет с чем чокнуться и над чем поржать! 🍻",
    "@VadimRagulin, именинник, ты как солнечная панель на рофлах! ☀️ Собираешь любой луч позитива и превращаешь его в электричество для всей компании. Пусть у тебя заряд держится вечно! 🔋",
    "@VadimRagulin, с днюхой, человек-праздник! 🎪 Ты приходишь и сразу будто играет музыка, открывается бар и все становятся веселее. Пусть этот цирк жизни всегда крутится в твою пользу! 🎠",
    "@VadimRagulin, Вадимыч, поздравляю! 🥊 Ты как чемпион по тяжелому весу в дисциплине 'разнести скуку с одного удара'. Желаю тебе нокаутировать все проблемы и поднять пояс удовольствия! 🏆",
    "@VadimRagulin, с днем рождения, бро высшей пробы! 🧬 В тебе будто ученые смешали юмор, стиль и душевность в опасно эффективной пропорции. Пусть этот состав только дорожает! 💹",
    "@VadimRagulin, Вадя, с праздником! 🪩 Ты как диско-шар в темном зале: включаешься и все вокруг начинает блестеть и двигаться. Желаю тебе бесконечного света, музыки и красивой движухи! ✨",
    "@VadimRagulin, с днюхой, главный архитектор прикола! 🏗️ Ты строишь настроение даже там, где другие не нашли бы ни кирпича юмора. Пусть твоя жизнь будет сплошной элитной застройкой из кайфа! 🏡",
    "@VadimRagulin, Вадосик, поздравляю! 🎯 Ты как снайпер по шуткам: всегда точно, красиво и прямо в яблочко. Желаю тебе такой же меткости во всех целях на этот год! 🏹",
    "@VadimRagulin, братюня, с днем рождения! 🍕 Ты как лишний кусок пиццы на столе: никто не рассчитывал, но все искренне рады, что ты есть. Пусть жизнь угощает тебя только лучшим! 🤌",
    "@VadimRagulin, с днюхой, король уверенного чила! 🛋️ Ты умеешь держать вайб так, будто у тебя пожизненная подписка на комфорт и прикол. Желаю тебе такого же мягкого хода по жизни! 🧸",
    "@VadimRagulin, Вадим, поздравляю! 🛰️ Ты как спутник хорошего настроения: выходишь на орбиту и стабильно покрываешь всех сигналом угара. Пусть у тебя никогда не будет потери связи с кайфом! 📡",
    "@VadimRagulin, с праздником, золотой поставщик шуток! 🏦 У тебя такой запас харизмы, будто ты открыл банк рофлов и держишь контрольный пакет. Желаю дивидендов счастья каждый день! 💰",
    "@VadimRagulin, Вадя, с днюхой! 🚤 Ты как катер на полном ходу: шумно, красиво и невозможно не обернуться. Пусть этот год мчит тебя только по гладкой воде удачи! 🌊",
    "@VadimRagulin, брат, с днем рождения, ты ходячий boost! ⚙️ Рядом с тобой люди внезапно начинают шутить лучше, жить веселее и смотреть на мир бодрее. Пусть и тебя жизнь так же бафает без отката! 🆙",
    "@VadimRagulin, с днюхой, мастер внезапной радости! 🎁 Ты как подарок без повода, который оказался ровно тем, что нужно. Желаю тебе побольше приятных сюрпризов от самой жизни! 🎊",
    "@VadimRagulin, Вадос, поздравляю, ты как удачный дубль! 🎬 Без лишних пересъемок, сразу в цель и в архив лучших моментов. Пусть весь следующий сезон твоей жизни будет рейтинговым! 🍿",
    "@VadimRagulin, с праздником, командир хороших времен! ⏳ Ты умеешь превращать обычный день в маленькую легенду для пересказов. Пусть у тебя таких дней будет бесстыдно много! 📚",
    "@VadimRagulin, Вадимка, с днем рождения! 🪄 Ты как фокусник на максималках: достаешь из воздуха улыбки, вайб и готовую атмосферу праздника. Пусть в рукаве у судьбы для тебя тоже будут козыри! 🎩",
    "@VadimRagulin, с днюхой, абсолютный красавчик по версии народа! 🗳️ Голосование завершено, результаты очевидны: харизма зашкаливает, юмор сертифицирован. Желаю только расти в этом безобразно сильном стиле! 📈",
    "@VadimRagulin, Вадя, поздравляю! 🚀 Ты как старт ракеты в прямом эфире: все залипли, всем интересно и все ждут мощного взлета. Пусть этот год станет именно таким запуском! 🌌",
    "@VadimRagulin, братан, с праздником! 🧠 У тебя мозг работает в режиме 'генератор сильных реплик', а сердце в режиме 'свой человек'. Желаю, чтобы оба режима только усиливались! ❤️",
    "@VadimRagulin, с днем рождения, министр красивой жизни! 🏝️ Под твоим управлением даже будни выглядят как курорт с шутками и нормальным баром. Пусть отпуск по кайфу станет твоей постоянкой! 🍹",
    "@VadimRagulin, Вадосик, с днюхой! 🛎️ Ты как сервис уровня люкс: быстро поднимаешь настроение и не оставляешь шанса унынию. Пусть и тебе мир отвечает таким же классом обслуживания! 🏨",
    "@VadimRagulin, с праздником, человек-аплодисменты! 👏 Ты делаешь все вокруг чуть ярче просто фактом своего присутствия. Желаю тебе оваций от жизни за каждый хороший замес! 🎉",
    "@VadimRagulin, Вадим, с днем рождения! 🎮 Ты как скрытый персонаж, который оказался самым сильным в игре. Харизма открыта, стиль прокачан, приколы на максимуме. Играешь красиво, так и продолжай! 🕹️",
    "@VadimRagulin, с днюхой, шеф по атмосфере! 🍳 Ты умеешь замешать разговор так, что на выходе получается блюдо из смеха, тепла и мемов. Пусть твоя кухня жизни всегда пахнет победой! 🔥",
    "@VadimRagulin, Вадя, поздравляю, ты как редкий винил! 🎵 Стильный, самобытный и с настоящим звуком без пластмассы. Пусть тебя ценят, берегут и почаще ставят на громкость! 🔊",
    "@VadimRagulin, с днем рождения, бро на вес золота! 🪙 Ты как правильный совет и хороший рофл одновременно: и полезно, и приятно, и хочется еще. Пусть у тебя все будет в таком же жирном балансе! ⚖️",
    "@VadimRagulin, Вадос, с днюхой! 🧱 Ты как фундамент крепкой тусы: незаметно держишь на себе кучу хороших моментов. Желаю, чтобы и тебя жизнь держала так же надежно! 🏛️",
    "@VadimRagulin, брат, с праздником! 🌋 В тебе правильное сочетание спокойствия и внезапного эпика: вроде все тихо, а потом бац и всем весело. Пусть твои извержения удачи будут регулярными! 💥",
    "@VadimRagulin, Вадимыч, с днем рождения! 🧭 Ты как внутренний компас компании: рядом с тобой быстро понятно, где север, где бар и где хороший вайб. Пусть и тебя всегда ведет туда, где лучшее! 🗺️",
    "@VadimRagulin, с днюхой, главный коллекционер удачных моментов! 📸 Ты будто умеешь собирать в альбом все смешное, теплое и настоящее. Желаю тебе в новом году жизни только таких кадров! 🖼️",
    "@VadimRagulin, Вадя, с праздником! 🛡️ Ты как щит от плохого настроения: рядом с тобой вся муть просто отскакивает. Пусть и у тебя будет надежная защита от любой фигни! ⚔️",
    "@VadimRagulin, с днем рождения, человек с режимом 'топ' по умолчанию! 📟 Тебя даже не надо разгонять, ты уже на хорошем уровне по всем важным параметрам. Желаю дальше только апгрейдиться! 🧩",
    "@VadimRagulin, братюнь, с днюхой! 🎷 Ты как удачное соло в середине трека: внезапно, красиво и после него уже все понятно про уровень. Пусть и дальше звучишь так, чтобы все кивали с уважением! 🎶",
]


async def birthday(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_thread_id = getattr(update.message, "message_thread_id", None)

    selected_messages = random.sample(
        BIRTHDAY_MESSAGES,
        k=min(5, len(BIRTHDAY_MESSAGES)),
    )

    for birthday_message in selected_messages:
        await context.bot.send_message(
            chat_id=chat_id,
            text=birthday_message,
            message_thread_id=message_thread_id,
        )
        await asyncio.sleep(random.uniform(1, 2))

    final_message = (
        "@VadimRagulin, короче, ты топ, ты легенда, ты официальный амбассадор "
        "хорошего угара и красивой жизни! 🥂 С днём рождения, брат, продолжай "
        "разносить этот мир своим рофлом и кайфом. Любим, ценим, уважаем! 💥 "
        "#СтаринаВадим #РагуЛегенда #ВадимЖжёт"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=final_message,
        message_thread_id=message_thread_id,
    )


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
        # Увеличенная задержка перед редактированием для избежания блокировки API
        await asyncio.sleep(random.uniform(0.3, 0.5))
        try:
            await message.edit_text(f"🎰\n{slot_display}")
            # Задержка после редактирования, чтобы дать API время обработать запрос
            await asyncio.sleep(0.3)
        except Exception as e:
            # Если произошла ошибка (например, rate limit), увеличиваем задержку
            await asyncio.sleep(0.7)
            try:
                await message.edit_text(f"🎰\n{slot_display}")
            except Exception:
                pass  # Пропускаем, если не удалось отредактировать

    # Финальный результат
    final_display = generate_slot_display(reels)
    # Проверка, совпадают ли все элементы в центре
    is_win = len(set(reel[1] for reel in reels)) == 1

    await asyncio.sleep(0.5)
    await message.edit_text(f"🎰\n{final_display}\n\n{'🎉 Вы выиграли!' if is_win else '😢 Попробуйте еще раз!'}")
