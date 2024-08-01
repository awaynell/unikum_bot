from dotenv import load_dotenv
from os import getenv

from providers import providers, img_providers

load_dotenv()

admin_id = getenv('TG_ADMIN_ID')
tg_bot_token = getenv('TG_BOT_TOKEN')
api_base_url = getenv('API_BASE_URL')

default_provider = providers[0]['provider']
default_model = providers[0]['model']

default_img_provider = img_providers[0]['provider']
default_img_model = img_providers[0]['model']

default_img_model_flow2 = 'midjourney'

prompt_predict = "The user will then write his request based on what he wrote, determine what action the user wants to perform, draw a picture or receive a response from a text model. After that, answer with one word to draw or text Here's the message:"

max_generate_images_count = 2

prompt_for_translate_message = "Translate into English and reply only with a translated message without this request and other comments. The text is further, here is the text:"

prompt_for_russian_AI_answer = "напиши ответ на русском если я не просил обратного ранее в тексте, не комментируй это"
