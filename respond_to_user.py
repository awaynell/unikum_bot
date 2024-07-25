import aiohttp
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
import json
import asyncio
import time

from constants import default_model, default_provider, api_base_url
from logger import logger
from handle_images import handle_images
from utils import predict_user_message_context


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

    logger.info("USERNAME: %s", username, "DIALOG_history: %s",
                context.chat_data[context_history_key])

    await predict_user_message_context(update, context, user_message)

    provider = context.bot_data.get('provider', default_provider)
    model = context.bot_data.get('model', default_model)

    # Отправка запроса к API ChatGPT
    api_url = f"{api_base_url}/backend-api/v2/conversation"
    payload = {
        "model": model,
        "provider": provider,
        "messages": context.chat_data[context_history_key],
        "temperature": 0.4,
        "auto_continue": True,
        "conversation_id": chat_id,
        "id": f"{chat_id}-{message_id}"
    }

    modetype = context.user_data.get('modetype', "text")

    placeholder_answer = "Рисую..." if modetype == 'draw' else "Думаю..."

    sent_message = await context.bot.send_message(chat_id=chat_id, text=placeholder_answer, reply_to_message_id=message_id)

    temp_reply = ''

    try:
        await handle_model_response(temp_reply=temp_reply, chat_id=chat_id, context=context, update=update, api_url=api_url, payload=payload, user_message=user_message, sent_message=sent_message, context_history_key=context_history_key)
    except Exception as e:
        print(f"Error: {e}")

        response_message = temp_reply if len(temp_reply) > 0 else e

        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=response_message)
        return


async def handle_model_response(temp_reply, chat_id, context, update, api_url, payload, user_message, sent_message, context_history_key):
    loop = asyncio.get_event_loop()

    async with aiohttp.ClientSession(read_timeout=None) as session:
        async with await loop.run_in_executor(None, lambda: session.post(api_url, json=payload)) as response:
            if response.status == 200:
                # Отправка начального сообщения
                last_edit_time = time.time()  # Время последнего редактирования

                async for line in response.content:
                    decoded_line = line.decode('utf-8').strip()
                    try:
                        response_json = json.loads(decoded_line)
                        if response_json.get("type") == "content":
                            temp_reply += response_json["content"]

                            current_time = time.time()
                            # Проверка времени для редактирования сообщения
                            if current_time - last_edit_time >= 3:
                                try:
                                    await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=temp_reply, parse_mode='Markdown')
                                    last_edit_time = current_time
                                except Exception as e:
                                    print(f"Error: {e}")
                                finally:
                                    continue

                            # Обработка изображений
                            if "\n<!-- generated images start" in temp_reply:
                                await handle_images(temp_reply, chat_id, context, update, api_base_url, user_message)
                                await sent_message.delete()
                                return
                        elif response_json.get("type") == "error":
                            raise ValueError(response_json["error"])
                    except Exception as e:
                        print(f"Error: {e}")
                        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=str(e))
                try:
                    # Финальное редактирование сообщения после завершения цикла
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=f"{temp_reply}", parse_mode='Markdown')
                    bot_reply = temp_reply
                    context.chat_data[context_history_key].append(
                        {"role": "assistant", "content": bot_reply})
                except Exception as e:
                    print(f"Error: {e}")
                    raise ValueError(e)
            else:
                raise ValueError(e)
