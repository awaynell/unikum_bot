import os
import aiohttp
from telegram.constants import ChatAction
import re

from logger import logger


async def handle_images(bot_reply, chat_id, context, update, api_base_url, user_message):
    image_links = re.findall(r'\[!\[.*?\]\((.*?)\)\]', bot_reply)

    async with aiohttp.ClientSession() as session:
        for image_link in image_links:
            full_image_url = f"{api_base_url}{image_link}"
            async with session.get(full_image_url) as img_response:
                if img_response.status == 200:
                    image_data = await img_response.read()
                    file_name = os.path.basename(image_link)
                    with open(file_name, 'wb') as f:
                        f.write(image_data)

                    try:
                        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
                        with open(file_name, 'rb') as photo_file:
                            await context.bot.send_photo(chat_id=chat_id, photo=photo_file, reply_to_message_id=update.message.message_id, caption=f"Сгенерированные изображения по запросу: {user_message}\n")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке изображения: {e}")

                        await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка при отправке изображения: {e}", reply_to_message_id=update.message.message_id)
                    finally:
                        # Удаление файла с сервера
                        os.remove(file_name)
                else:
                    logger.error(f"Ошибка при загрузке изображения: {
                                 img_response.status}")
                    await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка при отправке изображения: {e}", reply_to_message_id=update.message.message_id)
