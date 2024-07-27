providers = [
    {"provider": "Pi", "model": "gpt-4o"},
    {"provider": "Chatgpt4o", "model": "gpt-4o"},
    {"provider": "Pi", "model": "gpt-4"},
    {"provider": "DDG", "model": "claude-3-haiku-20240307"},
    {"provider": "Pi", "model": "claude-3-opus"},
    {"provider": "Pi", "model": "claude-3-sonnet"},
    {"provider": "Pi", "model": "claude-3-haiku"},
    {"provider": "You", "model": "claude-3-opus"},
    {"provider": "DDG", "model": "meta-llama/Llama-3-70b-chat-hf"},
    {"provider": "Pi", "model": "llama3-70b"},
    {"provider": "HuggingChat", "model": "meta-llama/Meta-Llama-3-70B-Instruct"},
    {"provider": "You", "model": "llama3"},
    {"provider": "Pi", "model": "codellama-70b-instruct"},
    {"provider": "Pi", "model": "nemotron-4-340b-instruct"},
    {"provider": "Pi", "model": "gigachat"},
    {"provider": "Pi", "model": "gemini-pro"},
    {"provider": "You", "model": "gemini-pro"},
    {"provider": "Pi", "model": "meta-ai"},
    {"provider": "DDG", "model": "mistralai/Mixtral-8x7B-Instruct-v0.1"},
    {"provider": "GeminiProChat", "model": ""},
    {"provider": "FreeChatgpt", "model": "SparkDesk-v1.1"},
    {"provider": "FreeChatgpt", "model": "Qwen2-7B-Instruct"},
    {"provider": "FreeChatgpt", "model": "glm4-9B-chat"},
    {"provider": "FreeChatgpt", "model": "chatglm3-6B"},
    {"provider": "FreeChatgpt", "model": "Yi-1.5-9B-Chat"},
    {"provider": "HuggingChat", "model": "CohereForAI/c4ai-command-r-plus"},
    {"provider": "HuggingChat", "model": "mistralai/Mixtral-8x7B-Instruct-v0.1"},
    {"provider": "HuggingChat", "model": "Nous-Hermes-2-Mixtral-8x7B-DPO"},
    {"provider": "Blackbox", "model": "Blackbox"},
    {"provider": "Pi", "model": ""},
    {"provider": "Koala", "model": "gpt-3.5-turbo"},
    {"provider": "You", "model": "gpt-3.5-turbo"},
    {"provider": "Pizzagpt", "model": "gpt-3.5-turbo"},
    {"provider": "ChatgptFree", "model": "gpt-3.5-turbo"},
    {"provider": "FreeChatgpt", "model": "gpt-3.5-turbo"},
    {"provider": "DDG", "model": "gpt-3.5-turbo-0125"},
    {"provider": "Koala", "model": "gpt-3.5-turbo"},
]

max_retry_count = 30
current_retry_count = 0


def reset_retry_count():
    global current_retry_count
    current_retry_count = 0


def increment_retry_count():
    global current_retry_count
    current_retry_count += 1
