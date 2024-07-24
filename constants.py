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
