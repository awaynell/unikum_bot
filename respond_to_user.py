import aiohttp
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
import json
import asyncio
import time

from utils import default_model, default_provider, api_base_url
from logger import logger
from handle_images import handle_images


async def respond_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Отправка состояния "печатает..."
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    provider = context.user_data.get('provider', default_provider)
    model = context.user_data.get('model', default_model)

    context_history_key = f"history-{user_id}-{chat_id}"

    # Инициализация истории сообщений, если её ещё нет
    if context_history_key not in context.chat_data:
        context.chat_data[context_history_key] = []

    # Добавление нового сообщения пользователя в историю
    context.chat_data[context_history_key].append(
        {"role": "user", "content": user_message})

    # Ограничение истории, чтобы не превышать лимиты API
    max_history_length = 30  # Можно настроить по необходимости
    context.chat_data[context_history_key] = context.chat_data[context_history_key][-max_history_length:]

    logger.info("USERNAME: %s", username)
    logger.info("DIALOG_history: %s", context.chat_data[context_history_key])

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

    logger.info('API_payload: %s', payload)

    loop = asyncio.get_event_loop()

    bot_reply = None

    try:
        async with aiohttp.ClientSession(read_timeout=None) as session:
            async with await loop.run_in_executor(None, lambda: session.post(api_url, json=payload)) as response:
                print('response', response)
                if response.status == 200:
                    temp_reply = ''
                    # Отправка начального сообщения
                    last_edit_time = time.time()  # Время последнего редактирования

                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        print('decoded_line', decoded_line)
                        try:
                            response_json = json.loads(decoded_line)
                            print('response_json', response_json)
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
                    except Exception as e:
                        print(f"Error: {e}")
                        raise ValueError(e)
                else:
                    raise ValueError(e)
    except Exception as e:
        print(f"Error: {e}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=sent_message.message_id, text=temp_reply)
        return

    print('bot_reply', bot_reply)

    context.chat_data[context_history_key].append(
        {"role": "assistant", "content": bot_reply})

    # Отправка ответа пользователю
    # await context.bot.send_message(chat_id=chat_id, text=bot_reply, reply_to_message_id=update.message.message_id, parse_mode='Markdown')
