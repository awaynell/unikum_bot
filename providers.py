import json

img_providers = {
    "flux": {
        "provider": "Airforce",
        "model": "flux"
    },
    "flux_realism": {
        "provider": "Airforce",
        "model": "flux-realism"
    },
    "flux_anime": {
        "provider": "Airforce",
        "model": "flux-anime"
    },
    "flux_3d": {
        "provider": "Airforce",
        "model": "flux-3d"
    },
    "flux_disney": {
        "provider": "Airforce",
        "model": "flux-disney"
    },
    "flux_pixel": {
        "provider": "Airforce",
        "model": "flux-pixel"
    },
    "replsd3": {
        "provider": "ReplicateHome",
        "model": "stability-ai/stable-diffusion-3",
    },
    "replpg2.5": {
        "provider": "ReplicateHome",
        "model": "playgroundai/playground-v2.5-1024px-aesthetic",
    },
    "replsdlight4step": {
        "provider": "ReplicateHome",
        "model": "bytedance/sdxl-lightning-4step",
    },
    "diisd": {
        "provider": "DeepInfraImage",
        "model": "stability-ai/sdxl"
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
