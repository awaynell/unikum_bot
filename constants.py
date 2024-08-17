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

default_img_provider = img_providers['replsd3']['provider']
default_img_model = img_providers['replsd3']['model']

default_img_model_flow2 = 'midjourney'

prompt_predict = "Next, I'll give you a message. You have to define the context of the message and what the user wants. You have 2 possible answers to choose from: text and draw. Answer only one of these two options. ANSWER IN ONE WORD. Here is the user's message:"

max_generate_images_count = 2

prompt_for_translate_message = "Translate into English and reply only with a translated message without this request and other comments. The text is further, here is the text:"

prompt_for_russian_AI_answer = "напиши ответ на русском если я не просил обратного ранее в тексте, не комментируй это"

emoji_slots = ["🍒", "🍋", "🍊", "🍉", "⭐", "🔔", "🍇"]
