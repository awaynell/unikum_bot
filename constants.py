from dotenv import load_dotenv
from os import getenv

from providers import img_providers, load_successful_providers

file_path = "success_providers.txt"
successful_providers = load_successful_providers(file_path)

load_dotenv()

admin_id = getenv('TG_ADMIN_ID')
tg_bot_token = getenv('TG_BOT_TOKEN')
api_base_url = getenv('API_BASE_URL')

default_provider = successful_providers[0]['provider']
default_model = successful_providers[0]['model']

default_img_provider = img_providers['flux']['provider']
default_img_model = img_providers['flux']['model']

default_img_model_flow2 = 'midjourney'

prompt_predict = (
    "Next you will receive a user message. Your task is to decide whether the user is "
    "asking for a written/text response or for an image/drawing. There are exactly two "
    "possible outputs:\n"
    "- text (if the request requires a textual answer)\n"
    "- draw (if the request requires generating an image or drawing)\n\n"
    "Respond with exactly one of these words, in lowercase, and nothing else. "
    "Here is the user’s message:"
)

max_generate_images_count = 1

prompt_for_translate_message = "Translate into English and reply only with a translated message without this request and other comments. The text is further, here is the text:"

prompt_for_russian_AI_answer = "напиши ответ на русском если я не просил обратного ранее в тексте, не комментируй то, что я попросил отвечать на русском."

emoji_slots = ["🍒", "🍋", "🍊", "🍉", "⭐", "🔔", "🍇"]
