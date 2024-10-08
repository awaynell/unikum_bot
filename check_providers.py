import aiohttp
import asyncio
import uuid
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
import time

from utils import api_base_url, isAdmin
from common import change_provider_data

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# URL для запросов
base_url = f"{api_base_url}/backend-api/v2"

# Файл для сохранения успешных провайдеров
output_file = "success_providers.txt"


# Семафор для ограничения количества одновременных запросов
semaphore = asyncio.Semaphore(2)


async def get_providers(session):
    url = f"{base_url}/providers"
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


async def get_models(session, provider):
    url = f"{base_url}/models/{provider}"
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


async def send_request_to_model(session, provider, model):
    await asyncio.sleep(1)

    async with semaphore:
        conversation_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        url = f"{base_url}/conversation"
        body = {
            "id": request_id,
            "conversation_id": conversation_id,
            "model": model,
            "web_search": False,
            "provider": provider,
            "messages": [{"role": "user", "content": "ping"}],
            "auto_continue": True,
            "api_key": None
        }

        headers = {"Content-Type": "application/json"}
        try:
            async with session.post(url, json=body, headers=headers, timeout=10) as response:
                async for line in response.content:
                    decoded_line = line.decode('utf-8')
                    if "error" in decoded_line:
                        return False, provider, model
                    if "content" in decoded_line:
                        return True, provider, model
        except asyncio.TimeoutError:
            logging.error(f"Timeout error occurred while checking model {
                          model} of provider {provider}")
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Connection error: {e}")
        except OSError as e:
            logging.error(f"OS error: {e}")
        return False, provider, model


def sort_providers(providers):
    def sort_key(item):
        model = item['model'].lower()
        if 'gpt-4o' in model:
            return 1
        elif 'llama-3.1' in model:
            return 2
        elif 'llama-3' in model:
            return 3
        else:
            return 4
    return sorted(providers, key=sort_key)


async def check_providers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not isAdmin(update, context):
        await update.message.reply_text(text="Nah, you're not admin")
        return

    await update.message.reply_text(text="Смотрю какие провайдеры доступны...")

    async with aiohttp.ClientSession() as session:
        providers = await get_providers(session)

        successful_providers = []

        tasks = []
        for provider_name, provider_info in providers.items():
            if any(keyword in provider_info.lower() for keyword in ('webdriver', 'ddg', 'auth', 'airforce')):
                continue
            try:
                logging.info(f"Checking provider {provider_name}...")
                models = await get_models(session, provider_name)
                for model_data in models:
                    model = model_data['model']

                    logging.info(f"Checking model {model}...")

                    tasks.append(send_request_to_model(
                        session, provider_name, model))
            except Exception as e:
                logging.error(f"Error with provider {provider_name}: {e}")

        results = await asyncio.gather(*tasks)

        for success, provider, model in results:
            if success:
                successful_providers.append(
                    {"provider": provider, "model": model})

        available_providers = sort_providers(successful_providers)

        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(available_providers, file, ensure_ascii=False, indent=4)

        message = "Успешные провайдеры и модели:\n"
        for provider_info in available_providers:
            message += f"Провайдер: {provider_info['provider']
                                     }, модель: {provider_info['model']}\n"

        await update.message.reply_text(text=message)

        if available_providers:
            await change_provider_data(update=update, context=context, provider=available_providers[0]['provider'], model=available_providers[0]['model'], withNotificationMsg=True)
        else:
            await update.message.reply_text(text="Не удалось найти успешные модели.")

if __name__ == "__main__":
    asyncio.run(check_providers())
