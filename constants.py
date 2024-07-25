from dotenv import load_dotenv
from os import getenv

load_dotenv()

admin_id = getenv('TG_ADMIN_ID')
tg_bot_token = getenv('TG_BOT_TOKEN')
api_base_url = getenv('API_BASE_URL')

default_provider = "Blackbox"
default_model = "Blackbox"

default_img_provider = "DeepInfraImage"
default_img_model = "stability-ai/sdxl"

default_img_model_flow2 = 'midjourney'

prompt_predict = "The user will then write his request based on what he wrote, determine what action the user wants to perform, draw a picture or receive a response from a text model. After that, answer with one word to draw or text Here's the message:"
