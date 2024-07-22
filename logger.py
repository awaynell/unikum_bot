import logging
from logging.handlers import TimedRotatingFileHandler

# Настройки логирования

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
# 'W0' означает каждую неделю в воскресенье
handler = TimedRotatingFileHandler('bot.log', when='W0', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
