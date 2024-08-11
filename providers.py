providers = [
    {"provider": "HuggingChat", "model": "meta-llama/Meta-Llama-3.1-70B-Instruct"},
    {"provider": "HuggingChat", "model": "meta-llama/Meta-Llama-3-70B-Instruct"},
    {"provider": "Liaobots", "model": "gpt-4o"},
    {"provider": "LiteIcoding", "model": "gpt-4o"},
    {"provider": "Pi", "model": "gpt-4o"},
    {"provider": "Blackbox", "model": "Blackbox"},
    {"provider": "FreeNetfly", "model": "gpt-4"},
    {"provider": "DDG", "model": "claude-3-haiku-20240307"},
    {"provider": "You", "model": "claude-3-opus"},
    {"provider": "DDG", "model": "meta-llama/Llama-3-70b-chat-hf"},
    {"provider": "You", "model": "llama3"},
    {"provider": "You", "model": "gemini-pro"},
    {"provider": "GeminiProChat", "model": ""},
    {"provider": "HuggingChat", "model": "Nous-Hermes-2-Mixtral-8x7B-DPO"},
    {"provider": "LiteIcoding", "model": "gpt-4-turbo"},
    {"provider": "Chatgpt4o", "model": "gpt-4o"},
    {"provider": "Pi", "model": "gpt-4"},
    {"provider": "Koala", "model": "gpt-3.5-turbo"},
    {"provider": "Pi", "model": "llama3-70b"},
    {"provider": "Pi", "model": "codellama-70b-instruct"},
    {"provider": "Pi", "model": "nemotron-4-340b-instruct"},
    {"provider": "Pi", "model": "meta-ai"},
    {"provider": "Pi", "model": "gigachat"},
    {"provider": "Pi", "model": "gemini-pro"},
    {"provider": "Pi", "model": "claude-3-opus"},
    {"provider": "Marsyoo", "model": "gpt-4o"},
    {"provider": "Pi", "model": "claude-3-sonnet"},
    {"provider": "Pi", "model": "claude-3-haiku"},
    {"provider": "Pi", "model": ""},
    {"provider": "You", "model": "gpt-3.5-turbo"},
    {"provider": "Pizzagpt", "model": "gpt-3.5-turbo"},
    {"provider": "ChatgptFree", "model": "gpt-3.5-turbo"},
    {"provider": "FreeNetfly", "model": "gpt-3.5-turbo"},
    {"provider": "FreeChatgpt", "model": "gpt-3.5-turbo"},
    {"provider": "DDG", "model": "gpt-3.5-turbo-0125"},
    {"provider": "Koala", "model": "gpt-3.5-turbo"},
    {"provider": "FreeChatgpt", "model": "Qwen2-7B-Instruct"},
    {"provider": "FreeChatgpt", "model": "SparkDesk-v1.1"},
    {"provider": "FreeChatgpt", "model": "glm4-9B-chat"},
    {"provider": "FreeChatgpt", "model": "chatglm3-6B"},
    {"provider": "FreeChatgpt", "model": "Yi-1.5-9B-Chat"},
    {"provider": "HuggingChat", "model": "CohereForAI/c4ai-command-r-plus"},
    {"provider": "HuggingChat", "model": "mistralai/Mixtral-8x7B-Instruct-v0.1"},
    {"provider": "Marsyoo", "model": "gpt-4o"},
    {"provider": "DDG", "model": "mistralai/Mixtral-8x7B-Instruct-v0.1"},
]

img_providers = {
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
