import json

img_providers = {
    "flux": {
        "provider": "PollinationsAI",
        "model": "flux"
    }
}

max_retry_count = 10
current_retry_count = 0


def reset_retry_count():
    global current_retry_count
    current_retry_count = 0


def increment_retry_count():
    global current_retry_count
    current_retry_count += 1


def load_successful_providers(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data
