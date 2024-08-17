import requests
import uuid
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from telegram import Update
from telegram.ext import ContextTypes

from utils import api_base_url, isAdmin
from common import change_provider_data
# URL для запросов
base_url = f"{api_base_url}/backend-api/v2"

# Файл для сохранения успешных провайдеров
output_file = "success_providers.txt"

# Функция для получения списка провайдеров


def get_providers():
    url = f"{base_url}/providers"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Функция для получения списка моделей у конкретного провайдера


def get_models(provider):
    url = f"{base_url}/models/{provider}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Функция для отправки запроса к модели


def send_request_to_model(provider, model):
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
    response = requests.post(url, json=body, headers=headers, stream=True)

    # Парсинг EventStream
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if "error" in decoded_line:
                return False, provider, model
            if "content" in decoded_line:
                return True, provider, model
    return False, provider, model

# Функция сортировки провайдеров по модели


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

# Основная функция


async def check_providers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (not isAdmin(update, context)):
        await update.message.reply_text(text="Nah, you're not admin")
        return

    await update.message.reply_text(text="Смотрю какие провайдеры доступны...")

    providers = get_providers()
    successful_providers = []

    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []

            for provider, provider_value in providers.items():
                if 'webdriver' in provider_value.lower() or 'ddg' in provider_value.lower():
                    continue
                try:
                    print(f"Checking provider: {provider} {provider_value}")
                    models = get_models(provider)
                    for model_info in models:
                        model = model_info['model']
                        print(f"Testing model: {model}")
                        # Добавляем задачу в пул потоков
                        futures.append(executor.submit(
                            send_request_to_model, provider, model))
                except Exception as e:
                    print(f"Error with provider {provider}: {e}")

            # Обработка завершенных задач
            for future in as_completed(futures):
                success, provider, model = future.result()
                if success:
                    successful_providers.append(
                        {"provider": provider, "model": model})
                    time.sleep(1)  # Задержка перед следующим запросом

            # Сортировка успешных провайдеров по приоритету моделей
            sorted_providers = sort_providers(successful_providers)

            # Сохранение результатов в файл
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(sorted_providers, file, ensure_ascii=False, indent=4)

            # Отображение успешных провайдеров и моделей целым списком в одном сообщении
            message = "Успешные провайдеры и модели:\n"
            for ent in sorted_providers:
                message += f"Провайдер: {ent['provider']
                                          }, модель: {ent['model']}\n"

            await update.message.reply_text(text=message)

            print(f"Successful providers and models saved to {output_file}")

            await change_provider_data(update=update, context=context, provider=sorted_providers[0]['provider'], model=sorted_providers[0]['model'], withNotificationMsg=True)
    except Exception as e:
        await update.message.reply_text(
            text=f"Ошибка! {e}")

if __name__ == "__main__":
    check_providers()
