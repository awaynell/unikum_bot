import os
import re
import aiohttp
import asyncio
from telegram.constants import ChatAction
from telegram import InputMediaPhoto
import logging

from constants import max_generate_images_count

logger = logging.getLogger(__name__)


async def handle_images(bot_reply, chat_id, context, update, api_base_url, user_message):
    image_links = re.findall(r'\[!\[.*?\]\((.*?)\)\]', bot_reply)

    print('image_links', image_links)

    async with aiohttp.ClientSession() as session:
        await fetch_and_send_images(session, image_links, chat_id, context, update, api_base_url, user_message)


async def fetch_and_send_images(session, image_links, chat_id, context, update, api_base_url, user_message):
    media_group = []
    temp_files = []

    for image_link in image_links:
        full_image_url = f"{api_base_url}{image_link}"
        try:
            async with session.get(full_image_url) as img_response:
                if img_response.status == 200:
                    image_data = await img_response.read()
                    file_name = os.path.basename(full_image_url)
                    with open(file_name, 'wb') as f:
                        f.write(image_data)
                    temp_files.append(file_name)
                else:
                    logger.error(f"Ошибка при загрузке изображения: {
                                 img_response.status}")
                    await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка при отправке изображения: {img_response.status}", reply_to_message_id=update.message.message_id)
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка при отправке изображения: {e}", reply_to_message_id=update.message.message_id)

    for file_name in temp_files:
        try:
            with open(file_name, 'rb') as photo_file:
                media_group.append(InputMediaPhoto(media=photo_file.read()))
        except Exception as e:
            logger.error(f"Ошибка при чтении файла: {e}")

    if (len(media_group) > max_generate_images_count - 1):
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
        await context.bot.send_media_group(chat_id=chat_id, media=media_group, reply_to_message_id=update.message.message_id, caption=f"Сгенерированные изображения по запросу: {user_message}\n")
        # Удаление файлов после отправки
        for file_name in temp_files:
            try:
                os.remove(file_name)
            except Exception as e:
                logger.error(f"Ошибка при удалении файла: {e}")
