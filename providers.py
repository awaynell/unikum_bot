providers = [{"provider": "DDG", "model": "gpt-3.5-turbo"},
             {"provider": "HuggingChat", "model": "meta-llama/Meta-Llama-3-70B-Instruct"}, {"provider": "Blackbox", "model": "Blackbox"}, {"provider": "Pizzagpt", "model": "gpt-3.5-turbo"}]

max_retry_count = 10

current_retry_count = 0


def reset_retry_count():
    global current_retry_count
    current_retry_count = 0


def increment_retry_count():
    global current_retry_count
    current_retry_count += 1
