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

    # Отправка состояния "печатает..."
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    context_history_key = f"history-{chat_id}"

    # Инициализация истории сообщений, если её ещё нет
    if context_history_key not in context.chat_data:
        context.chat_data[context_history_key] = []

    # Добавление нового сообщения пользователя в историю
    context.chat_data[context_history_key].append(
        {"role": "user", "content": user_message})

    # Ограничение истории, чтобы не превышать лимиты API
    max_history_length = 30  # Можно настроить по необходимости
    context.chat_data[context_history_key] = context.chat_data[context_history_key][-max_history_length:]

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


async def handle_model_response(temp_reply, chat_id, message_id, dialog_history, context, update, user_message, sent_message, context_history_key, current_img_count: int = 0, image_links: list = []):
    loop = asyncio.get_event_loop()
    modetype = context.user_data.get('modetype', "text")

    if (modetype == 'draw'):
        keys = list(img_providers.keys())
        random_key = random.choice(keys)
        random_provider = img_providers[random_key]["provider"]
        random_model = img_providers[random_key]["model"]

    context.bot_data['provider'] = random_provider
    context.bot_data['model'] = random_model

    provider = context.bot_data.get(
        'provider', default_provider) if modetype == 'text' else context.bot_data.get(
        'imgprovider', default_img_provider)

    model = context.bot_data.get(
        'model', default_model) if modetype == 'text' else context.bot_data.get(
        'imgmodel', default_img_model)

    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": model,
        "provider": provider,
        "messages": dialog_history,
        "temperature": 0.4,
        "auto_continue": True,
        "conversation_id": chat_id,
        "id": f"{chat_id}-{message_id}"
    }

    if (len(image_links) > 0):
        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=f"Рисую... {current_img_count}/{max_generate_images_count}")

    if (current_img_count > max_generate_images_count - 1):
        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=f"Еще немного...")

        await handle_images(image_links, chat_id, context, update, api_base_url, user_message, sent_message)
        return

    logger.info("CURRENT PROVIDER: %s, CURRENT MODEL: %s", provider, model)

    async with aiohttp.ClientSession(read_timeout=None) as session:
        async with await loop.run_in_executor(None, lambda: session.post(api_url, json=payload)) as response:
            if response.status == 200:
                # Отправка начального сообщения
                last_edit_time = time.time()  # Время последнего редактирования

                autoreplace_provider_arguments = {
                    'temp_reply': temp_reply,
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'dialog_history': dialog_history,
                    'context': context,
                    'update': update,
                    'user_message': user_message,
                    'sent_message': sent_message,
                    'context_history_key': context_history_key,
                    'handle_model_response': handle_model_response
                }

                async for line in response.content:
                    decoded_line = line.decode('utf-8').strip()
                    try:
                        response_json = json.loads(decoded_line)

                        # handle error
                        if (response_json.get("type") == "error"):
                            if (modetype == "draw"):
                                await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=f"Ошибка: {response_json["error"]}")
                                return
                            await autoreplace_provider(**autoreplace_provider_arguments)
                            return
                        elif response_json.get("type") == "content":
                            temp_reply += response_json["content"]

                            # Обработка изображений
                            if "[!" in temp_reply:
                                image_links = temp_reply

                                await asyncio.sleep(1.5)

                                await handle_model_response(temp_reply=temp_reply, chat_id=chat_id, context=context, update=update, user_message=user_message, sent_message=sent_message, context_history_key=context_history_key, current_img_count=current_img_count + 1,
                                                            dialog_history=dialog_history,
                                                            message_id=message_id, image_links=image_links)
                                break

                            if "One message exceeds the 1000chars per message limit" in temp_reply:
                                if (modetype == "draw"):
                                    await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=f"Ошибка: {response_json["error"]}")
                                    return
                                await autoreplace_provider(**autoreplace_provider_arguments)
                                return

                            current_time = time.time()
                            # Проверка времени для редактирования сообщения
                            if current_time - last_edit_time >= 0.5:
                                try:
                                    # Экранирование текста перед отправкой
                                    escaped_temp_reply = escape_markdown(
                                        temp_reply)
                                    await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=escaped_temp_reply, parse_mode='MarkdownV2')
                                    last_edit_time = current_time
                                except Exception as e:
                                    print(f"Error: {e}")
                                finally:
                                    continue
                    except Exception as e:
                        print(f"Error: {e}")
                        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=str(e))
                try:
                    providers.reset_retry_count()

                    if (len(image_links) > 0):
                        return

                    bot_reply = temp_reply
                    # Финальное редактирование сообщения после завершения цикла
                    escaped_bot_reply = escape_markdown(bot_reply)
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=f"{escaped_bot_reply}", parse_mode='MarkdownV2')
                    context.chat_data[context_history_key].append(
                        {"role": "assistant", "content": bot_reply})
                except Exception as e:
                    print(f"Error: {e}")
                    raise ValueError(e)
            else:
                raise ValueError(e)
