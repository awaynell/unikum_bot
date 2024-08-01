from telegram import Update
from telegram.ext import ContextTypes

import providers
from logger import logger
from common import change_provider_data


async def autoreplace_provider(temp_reply, chat_id, message_id, dialog_history, context, update, user_message, sent_message, context_history_key, handle_model_response):
    modetype = context.user_data.get('modetype', "text")

    providers.increment_retry_count()

    if providers.current_retry_count < providers.max_retry_count:
        new_provider = providers.providers[providers.current_retry_count %
                                           len(providers.providers)] if modetype == 'text' else providers.img_providers[providers.current_retry_count % len(providers.img_providers)]

        logger.info(f"NEW PROVIDER {new_provider}")

        await change_provider_data(update, context, provider=new_provider['provider'], model=new_provider['model'])

        handle_model_args = {
            'temp_reply': temp_reply,
            'chat_id': chat_id,
            'message_id': message_id,
            'dialog_history': dialog_history,
            'context': context,
            'update': update,
            'user_message': user_message,
            'sent_message': sent_message,
            'context_history_key': context_history_key,
        }

        await handle_model_response(**handle_model_args)
        return
    else:
        providers.reset_retry_count()
        await context.bot.send_message(chat_id=chat_id, text="Превышено максимальное количество попыток. Пожалуйста, попробуйте позже.")
