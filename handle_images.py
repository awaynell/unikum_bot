import os
import re
import aiohttp
from telegram.constants import ChatAction
from telegram import InputMediaPhoto
import logging

from constants import default_img_provider, default_img_model

logger = logging.getLogger(__name__)


async def handle_images(image_links, chat_id, context, update, api_base_url, user_message, sent_message):
    """
    Обрабатывает и отправляет изображения пользователю.

    Args:
        image_links: Список словарей с данными об изображениях в формате:
                     [{"content": "...", "urls": [...], "alt": "..."}]
                     или список строк (для обратной совместимости)
    """
    # Собираем все URLs из всех image_links
    all_urls = []

    for item in image_links:
        if isinstance(item, dict):
            # Новый формат: dict с urls
            urls = item.get("urls", [])
            all_urls.extend(urls)

            # Также парсим старый формат из content (для совместимости)
            content = item.get("content", "")
            old_format_urls = re.findall(r'\[!\[.*?\]\((.*?)\)\]', content)
            all_urls.extend(old_format_urls)

        elif isinstance(item, str):
            # Старый формат: строка с markdown
            old_format_urls = re.findall(r'\[!\[.*?\]\((.*?)\)\]', item)
            all_urls.extend(old_format_urls)

    # Удаляем дубликаты
    all_urls = list(set(all_urls))

    if not all_urls:
        logger.warning("No image URLs found in image_links")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_message.message_id,
            text="Не удалось найти ссылки на изображения"
        )
        return

    async with aiohttp.ClientSession() as session:
        await fetch_and_send_images(
            session, all_urls, chat_id, context, update,
            api_base_url, user_message, sent_message
        )


async def fetch_and_send_images(session, image_links, chat_id, context, update, api_base_url, user_message, sent_message):
    media_group = []
    temp_files = []

    current_provider = context.bot_data.get(
        'imgprovider', default_img_provider)
    current_model = context.bot_data.get('imgmodel', default_img_model)

    for image_link in image_links:
        # Формируем полный URL
        if image_link.startswith('http'):
            full_image_url = image_link
        else:
            # Убираем начальный слеш если есть, чтобы избежать двойных слешей
            image_link = image_link.lstrip('/')
            full_image_url = f"{api_base_url}/{image_link}"

        try:
            async with session.get(full_image_url) as img_response:
                if img_response.status == 200:
                    image_data = await img_response.read()
                    # Генерируем безопасное имя файла
                    file_name = f"temp_image_{len(temp_files)}_{os.path.basename(image_link)}"
                    # Ограничиваем длину имени файла
                    if len(file_name) > 200:
                        ext = os.path.splitext(file_name)[1]
                        file_name = f"temp_image_{len(temp_files)}{ext}"

                    with open(file_name, 'wb') as f:
                        f.write(image_data)
                    temp_files.append(file_name)
                    logger.info(
                        f"Successfully downloaded image: {full_image_url}")
                else:
                    logger.error(
                        f"Ошибка при загрузке изображения: {img_response.status} - {full_image_url}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"Произошла ошибка при загрузке изображения: {img_response.status}",
                        reply_to_message_id=update.message.message_id
                    )

        except Exception as e:
            logger.error(
                f"Ошибка при загрузке изображения {full_image_url}: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Произошла ошибка при отправке изображения: {e}",
                reply_to_message_id=update.message.message_id
            )

    if not temp_files:
        logger.error("No images were downloaded successfully")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_message.message_id,
            text="Не удалось загрузить изображения"
        )
        return

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=sent_message.message_id,
        text=f"Последние штрихи..."
    )

    # ✅ ИСПРАВЛЕНО: Формируем caption заранее
    caption_text = f"Сгенерированные изображения по запросу: {user_message}\n\n`via {current_provider} {current_model}`"

    for idx, file_name in enumerate(temp_files):
        try:
            with open(file_name, 'rb') as photo_file:
                # ✅ ИСПРАВЛЕНО: Передаём caption только для первого изображения при создании объекта
                if idx == 0:
                    media_group.append(
                        InputMediaPhoto(
                            media=photo_file.read(),
                            caption=caption_text,
                            parse_mode="Markdown"
                        )
                    )
                else:
                    media_group.append(
                        InputMediaPhoto(media=photo_file.read())
                    )
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_name}: {e}")

    if not media_group:
        logger.error("No media to send")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_message.message_id,
            text="Не удалось подготовить изображения для отправки"
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    try:
        await context.bot.send_media_group(
            chat_id=chat_id,
            media=media_group,
            reply_to_message_id=update.message.message_id
        )

        await sent_message.delete()
    except Exception as e:
        logger.error(f"Ошибка при отправке медиагруппы: {e}")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_message.message_id,
            text=f"Ошибка при отправке изображений: {e}"
        )

    # Удаление файлов после отправки
    for file_name in temp_files:
        try:
            os.remove(file_name)
            logger.debug(f"Deleted temp file: {file_name}")
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {file_name}: {e}")
