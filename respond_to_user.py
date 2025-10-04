import aiohttp
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
import json
import asyncio
import time
import random
from providers import img_providers
from logger import logger
import telegram

from constants import default_model, default_provider, api_base_url, max_generate_images_count, default_img_model, default_img_provider
from handle_images import handle_images
from autoreplace_provider import autoreplace_provider
import providers
from utils import escape_markdown


async def respond_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    context_history_key = f"history-{chat_id}"

    # ✅ ИЗМЕНЕНО: Инициализация истории с системным промптом
    if context_history_key not in context.chat_data:
        context.chat_data[context_history_key] = [
            {
                "role": "system",
                "content": "Ты полезный AI-ассистент. Отвечай на русском языке, учитывай контекст предыдущих сообщений в диалоге."
            }
        ]

    # Добавление нового сообщения пользователя в историю
    context.chat_data[context_history_key].append(
        {"role": "user", "content": user_message})

    # Ограничение истории (но сохраняем системный промпт)
    max_history_length = 30
    if len(context.chat_data[context_history_key]) > max_history_length:
        # Сохраняем первое сообщение (system) и последние N сообщений
        system_msg = context.chat_data[context_history_key][0]
        context.chat_data[context_history_key] = [
            system_msg] + context.chat_data[context_history_key][-(max_history_length-1):]

    dialog_history = context.chat_data[context_history_key]

    logger.info("USERNAME: %s, DIALOG_history: %s", username, dialog_history)

    modetype = context.user_data.get('modetype', "text")

    placeholder_answer = "Рисую..." if modetype == 'draw' else "Думаю..."

    sent_message = await context.bot.send_message(chat_id=chat_id, text=placeholder_answer, reply_to_message_id=message_id)

    temp_reply = ''

    try:
        await handle_model_response(temp_reply=temp_reply, chat_id=chat_id, context=context, update=update, user_message=user_message, sent_message=sent_message, context_history_key=context_history_key, dialog_history=dialog_history, message_id=message_id)
    except Exception as e:
        print(f"Error: {e}")

        response_message = temp_reply if len(temp_reply) > 0 else e

        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=response_message)
        return


async def handle_model_response(
    temp_reply: str,
    chat_id,
    message_id,
    dialog_history,
    context,
    update,
    user_message: str,
    sent_message,
    context_history_key: str,
    current_img_count: int = 0,
    image_links: list | None = None,
):
    """
    Стримит ответ модели/генератора картинок, обновляет сообщение в Telegram и
    по необходимости переключает провайдера. Без фоновых блокировок и с защитой от UnboundLocalError.
    """
    if not api_base_url:
        raise RuntimeError("api_base_url не задан в context.bot_data")

    # Приводим image_links к списку
    if image_links is None:
        image_links = []

    modetype = context.user_data.get("modetype", "text")

    # Лимит количества картинок на одну команду
    if current_img_count >= max_generate_images_count:
        # Последняя склейка/обработка перед выходом
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent_message.message_id,
                text="Еще немного...",
            )
        except Exception:
            pass
        await handle_images(image_links, chat_id, context, update, api_base_url, user_message, sent_message)
        return

    # ---------- Разруливание провайдера/модели ----------
    if modetype == "draw":
        # Выбираем случайного провайдера для изображений
        key = random.choice(list(img_providers.keys()))
        rp = img_providers[key].get("provider") or default_img_provider
        rm = img_providers[key].get("model") or default_img_model

        provider = rp
        model = rm

        context.bot_data["imgprovider"] = provider
        context.bot_data["imgmodel"] = model
    else:
        # Текстовый режим: используем сохранённые или дефолтные
        provider = context.bot_data.get("provider") or default_provider
        model = context.bot_data.get("model") or default_model

        context.bot_data["provider"] = provider
        context.bot_data["model"] = model

    api_url = f"{api_base_url}/backend-api/v2/conversation"

    payload = {
        "model": model,
        "provider": provider,
        "messages": dialog_history,
        "temperature": 0.4,
        "auto_continue": True,
        "conversation_id": chat_id,
        "id": f"{chat_id}-{message_id}",
        "action": "next",
    }

    logger.info(f"🔍 Sending payload to API:")
    logger.info(f"Provider: {provider}, Model: {model}")
    logger.info(f"Messages count: {len(dialog_history)}")
    logger.info(
        f"Full messages: {json.dumps(dialog_history, ensure_ascii=False, indent=2)}")

    # Подпись процесса для картинок
    if image_links:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent_message.message_id,
                text=f"Рисую... {current_img_count}/{max_generate_images_count}",
            )
        except Exception:
            pass

    # Для автопереключения провайдера при ошибке
    autoreplace_provider_arguments = {
        "temp_reply": temp_reply,
        "chat_id": chat_id,
        "message_id": message_id,
        "dialog_history": dialog_history,
        "context": context,
        "update": update,
        "user_message": user_message,
        "sent_message": sent_message,
        "context_history_key": context_history_key,
        "handle_model_response": handle_model_response,
    }

    # ---------- Стрим запроса ----------
    buffer = ""
    last_edit_time = 0.0  # троттлинг
    edit_interval = 0.5   # сек
    last_sent_text = ""   # ✅ ДОБАВЛЕНО: отслеживание последнего отправленного текста

    try:
        async with aiohttp.ClientSession(read_timeout=None) as session:
            async with session.post(api_url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise ValueError(f"HTTP {response.status}: {text}")

                # Стримим построчно (NDJSON/SSE-подобный поток)
                async for chunk in response.content.iter_any():
                    if not chunk:
                        continue
                    buffer += chunk.decode("utf-8", errors="ignore")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        # Каждая строка — JSON-объект
                        try:
                            response_json = json.loads(line)
                        except Exception:
                            # Если прилетело что-то не-JSON (серверный шум) — пропускаем
                            continue

                        type = response_json.get("type")

                        # Обработка ошибок
                        if type == "error":
                            err_msg = response_json.get(
                                "error", "Неизвестная ошибка")
                            if modetype == "draw":
                                # Показываем ошибку пользователю
                                try:
                                    await context.bot.edit_message_text(
                                        chat_id=chat_id,
                                        message_id=sent_message.message_id,
                                        text=f'Ошибка: {err_msg}',
                                    )
                                except Exception:
                                    pass
                                return
                            # Текстовый режим — пробуем автосмену провайдера
                            await autoreplace_provider(**autoreplace_provider_arguments)
                            return

                        # Основной поток контента
                        if type == "content":
                            piece = response_json.get("content", "")
                            if not isinstance(piece, str):
                                piece = str(piece)
                            temp_reply += piece

                            # ✅ ИЗМЕНЕНО: Детектор сигнала для картинок - поддержка нового формата
                            # Новый формат с массивом URLs
                            urls = response_json.get("urls")

                            # Проверяем оба формата: новый (urls) и старый ([!, <a href)
                            if urls or "[!" in temp_reply or "<a href" in temp_reply:
                                # Сохраняем данные о картинке
                                image_data = {
                                    "content": temp_reply,
                                    "urls": urls or [],  # URLs из нового формата
                                    "alt": response_json.get("alt", "Generated image")
                                }
                                image_links.append(image_data)

                                # Небольшая пауза, чтобы сервер успел докинуть хвост
                                await asyncio.sleep(1.5)

                                # Рекурсивный вызов для следующего изображения
                                await handle_model_response(
                                    temp_reply=temp_reply,
                                    chat_id=chat_id,
                                    context=context,
                                    update=update,
                                    user_message=user_message,
                                    sent_message=sent_message,
                                    context_history_key=context_history_key,
                                    current_img_count=current_img_count + 1,
                                    dialog_history=dialog_history,
                                    message_id=message_id,
                                    image_links=image_links,
                                )
                                return  # важно: выходим из текущей корутины

                            # Ограничение на длину одного сообщения
                            if "One message exceeds the 1000chars per message limit" in temp_reply:
                                if modetype == "draw":
                                    try:
                                        await context.bot.edit_message_text(
                                            chat_id=chat_id,
                                            message_id=sent_message.message_id,
                                            text="Ошибка: сообщение превысило лимит длины",
                                        )
                                    except Exception:
                                        pass
                                    return
                                await autoreplace_provider(**autoreplace_provider_arguments)
                                return

                            # Периодически обновляем сообщение
                            now = time.time()
                            if now - last_edit_time >= edit_interval:
                                # ✅ ИЗМЕНЕНО: проверяем, изменился ли текст
                                escaped = escape_markdown(temp_reply)
                                if escaped != last_sent_text:  # Обновляем только если текст изменился
                                    try:
                                        await context.bot.edit_message_text(
                                            chat_id=chat_id,
                                            message_id=sent_message.message_id,
                                            text=escaped,
                                            parse_mode="MarkdownV2",
                                        )
                                        last_sent_text = escaped  # Сохраняем последний отправленный текст
                                    except telegram.error.BadRequest as e:
                                        # ✅ ДОБАВЛЕНО: специальная обработка BadRequest
                                        if "message is not modified" in str(e).lower():
                                            logger.debug(
                                                f"Message not modified, skipping update")
                                        else:
                                            logger.warning(
                                                f"Telegram error during edit: {e}")
                                    except Exception as e:
                                        logger.error(
                                            f"Error editing message: {e}")
                                    finally:
                                        last_edit_time = now
                                else:
                                    last_edit_time = now  # Обновляем время, даже если не отправляли

                # Поток завершён — финализируем
                try:
                    # Сбрасываем счётчик ретраев провайдера (если есть такой модуль)
                    try:
                        providers.reset_retry_count()
                    except Exception:
                        pass

                    # Если у нас шёл режим картинок и уже есть ссылки — не дублируем финал
                    if image_links:
                        return

                    bot_reply = temp_reply
                    escaped_bot_reply = escape_markdown(bot_reply)

                    # ✅ ИЗМЕНЕНО: финальное обновление только если текст изменился
                    if escaped_bot_reply != last_sent_text:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=sent_message.message_id,
                            text=escaped_bot_reply,
                            parse_mode="MarkdownV2",
                        )

                    # Добавляем в историю чата
                    context.chat_data.setdefault(context_history_key, [])
                    context.chat_data[context_history_key].append(
                        {"role": "assistant", "content": bot_reply}
                    )

                except Exception as e:
                    # Если тут упадём — отдаём как ValueError выше по стеку
                    raise ValueError(e) from e

    except Exception as e:
        # Общее перехватывание сетевых/парсинговых ошибок
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent_message.message_id,
                text=str(e),
            )
        except Exception:
            pass
        # Пробросим, если нужно внешнее логирование
        # raise
