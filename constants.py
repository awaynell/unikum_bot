from dotenv import load_dotenv
from os import getenv

load_dotenv()

admin_id = getenv('TG_ADMIN_ID')
tg_bot_token = getenv('TG_BOT_TOKEN')
api_base_url = getenv('API_BASE_URL')

default_provider = "Pi"
default_model = "gpt-4o"

default_img_provider = "DeepInfraImage"
default_img_model = "stability-ai/sdxl"

default_img_model_flow2 = 'midjourney'

prompt_predict = "Write "draw" or "text" based on the user's request below:"

max_generate_images_count = 2

prompt_for_translate_message = "Translate into English and reply only with a translated message without this request and other comments. The text is further, here is the text:"

prompt_for_russian_AI_answer = "напиши ответ на русском если я не просил обратного ранее в тексте, не комментируй это"
