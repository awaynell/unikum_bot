import aiohttp
import asyncio
import uuid
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils import api_base_url, isAdmin
from common import change_provider_data

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# URL для запросов
base_url = f"{api_base_url}/backend-api/v2"

# Файл для сохранения успешных провайдеров
output_file = "success_providers.txt"

# Семафор для ограничения количества одновременных запросов
# Уменьшим конкурентность: теперь только по одному запросу одновременно
semaphore = asyncio.Semaphore(1)

# Максимальное количество моделей на провайдера, которое будем проверять
MAX_MODELS_PER_PROVIDER = 3

# Максимальное количество провайдеров, которое будем проверять
MAX_PROVIDERS_TO_CHECK = 5

# Задержка между проверками провайдеров, чтобы не перегружать сервер
DELAY_BETWEEN_PROVIDERS = 2  # секунды


async def get_providers(session: aiohttp.ClientSession) -> list[dict]:
    """
    Запрашивает список провайдеров из бекенда.
    Ожидается, что бекенд вернёт массив объектов, например:
    [
      {
        "audio": 0,
        "auth": false,
        "hf_space": false,
        "image": 48,
        "label": "ARTA",
        "login_url": null,
        "name": "ARTA",
        "nodriver": false,
        "parent": null,
        "video": 0,
        "vision": false
      },
      ...
    ]
    """
    url = f"{base_url}/providers"
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


async def get_models(session: aiohttp.ClientSession, provider_name: str) -> list[dict]:
    """
    Запрашивает список моделей для конкретного провайдера.
    Ожидается, что бекенд вернёт список словарей с ключом "model".
    """
    url = f"{base_url}/models/{provider_name}"
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


async def send_request_to_model(
    session: aiohttp.ClientSession,
    provider_name: str,
    model_name: str
) -> tuple[bool, str, str]:
    """
    Делаем тестовый запрос к модели (ping).
    Если в потоке ответа появилась строка с "content",
    и содержимое не начинается с "[!", считаем, что модель отвечает успешно.
    Если содержимое "content" начинается с "[!", считаем модель некорректной и пропускаем её.
    """
    # Небольшая задержка перед каждым запросом, чтобы сгладить нагрузку
    await asyncio.sleep(1)

    async with semaphore:
        conversation_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        url = f"{base_url}/conversation"
        body = {
            "id": request_id,
            "conversation_id": conversation_id,
            "model": model_name,
            "web_search": False,
            "provider": provider_name,
            "messages": [{"role": "user", "content": "ping"}],
            "auto_continue": True,
            "api_key": None
        }

        headers = {"Content-Type": "application/json"}
        try:
            async with session.post(url, json=body, headers=headers, timeout=10) as response:
                async for line in response.content:
                    decoded_line = line.decode("utf-8").strip()
                    try:
                        data = json.loads(decoded_line)
                    except json.JSONDecodeError:
                        continue

                    if data.get("type") == "error":
                        return False, provider_name, model_name

                    if data.get("type") == "content":
                        content_text = data.get("content", "")
                        if content_text.startswith("[!"):
                            return False, provider_name, model_name
                        return True, provider_name, model_name

        except asyncio.TimeoutError:
            logging.error(
                f"Timeout error occurred while checking model '{model_name}' of provider '{provider_name}'"
            )
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Connection error: {e}")
        except OSError as e:
            logging.error(f"OS error: {e}")

        return False, provider_name, model_name


def sort_providers(providers_list: list[dict]) -> list[dict]:
    """
    Сортирует список удачных провайдеров по приоритету модели.
    Каждый элемент ожидается как {"provider": "<provider_name>", "model": "<model_name>"}.
    """
    def sort_key(item: dict) -> int:
        model = item["model"].lower()
        if "gpt-4o" in model:
            return 1
        elif "llama-3.1" in model:
            return 2
        elif "llama-3" in model:
            return 3
        else:
            return 4

    return sorted(providers_list, key=sort_key)


async def check_providers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что пользователь – админ
    if not isAdmin(update, context):
        await update.message.reply_text("Nah, you're not admin")
        return

    await update.message.reply_text("Смотрю, какие провайдеры доступны...")

    async with aiohttp.ClientSession() as session:
        try:
            raw_providers = await get_providers(session)
        except Exception as e:
            logging.error(f"Ошибка при запросе провайдеров: {e}")
            await update.message.reply_text("Не удалось получить список провайдеров.")
            return

        successful_providers: list[dict] = []
        tasks: list[asyncio.Task] = []

        checked_providers = 0

        for provider_info in raw_providers:
            if checked_providers >= MAX_PROVIDERS_TO_CHECK:
                break  # не проверяем больше провайдеров
            provider_name = provider_info.get("name")
            if not provider_name:
                continue

            provider_key_lower = provider_name.lower()
            label_lower = provider_info.get("label", "").lower()
            combined = provider_key_lower + " " + label_lower

            # Фильтрация по ключевым словам
            if any(keyword in combined for keyword in ("webdriver", "ddg", "auth", "airforce", "arta")):
                continue

            try:
                logging.info(
                    f"Checking provider '{provider_name}' ({checked_providers + 1}/{MAX_PROVIDERS_TO_CHECK})...")
                models = await get_models(session, provider_name)
                # Ограничиваем число моделей для одного провайдера
                models_to_check = models[:MAX_MODELS_PER_PROVIDER]

                for model_data in models_to_check:
                    model_name = model_data.get("model")
                    if not model_name:
                        continue

                    logging.info(f"  → Checking model '{model_name}'...")
                    task = send_request_to_model(
                        session, provider_name, model_name)
                    tasks.append(task)

                checked_providers += 1

                # После того как добавили задачи для этого провайдера, ждём перед следующим
                await asyncio.sleep(DELAY_BETWEEN_PROVIDERS)

            except Exception as e:
                logging.error(f"Error with provider '{provider_name}': {e}")

        if not tasks:
            await update.message.reply_text("После фильтрации не осталось провайдеров для проверки.")
            return

        results = await asyncio.gather(*tasks)

        for success, provider_name, model_name in results:
            if success:
                successful_providers.append(
                    {"provider": provider_name, "model": model_name})

        available_providers = sort_providers(successful_providers)

        try:
            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(available_providers, file,
                          ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Не удалось записать в файл '{output_file}': {e}")

        if available_providers:
            message_lines = ["Успешные провайдеры и модели:"]
            for info in available_providers:
                message_lines.append(
                    f"Провайдер: {info['provider']}, модель: {info['model']}")
            await update.message.reply_text("\n".join(message_lines))

            first = available_providers[0]
            await change_provider_data(
                update=update,
                context=context,
                provider=first["provider"],
                model=first["model"],
                withNotificationMsg=True
            )
        else:
            await update.message.reply_text("Не удалось найти успешные модели.")
