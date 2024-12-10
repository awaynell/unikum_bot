
import random
from telegram import Update
from telegram.ext import ContextTypes


class RaffleManager:
    def __init__(self, limit=4):
        self.array = []
        self.limit = limit

    def add_item(self, id, name):
        if len(self.array) >= self.limit:
            return "Массив достиг предела. Добавление невозможно."

        if any(item['id'] == id for item in self.array):
            return f"Номер {id} уже используется. Выберите другой."

        new_item = {"id": id, "name": name}
        self.array.append(new_item)
        return 1

    def get_array(self):
        return self.array

    def set_limit(self, new_limit):
        if new_limit < len(self.array):
            return "Невозможно уменьшить предел ниже текущего количества элементов."
        self.limit = new_limit
        print(f"Предел массива изменён на {new_limit}")

    def get_winners(self, limit):
        if not self.array:
            return []
        return random.sample(self.array, min(limit, len(self.array)))


raffle_manager = RaffleManager()


async def raffle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = int(context.args[0]) if context.args else 1
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите число победителей, например: /raffle 5")
        return

    winners = raffle_manager.get_winners(limit)
    if not winners:
        await update.message.reply_text("Нет участников для проведения розыгрыша.")
        return

    result = "\n".join(
        [f"{i+1}. {winner['name']} (ID: {winner['id']})" for i, winner in enumerate(winners)])
    await update.message.reply_text(f"Победители:\n{result}")


async def add_raffle_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Использование: /choose_item_raffle <номер>")
        return

    name = " ".join(context.args)
    user_id = update.effective_user.id
    res = raffle_manager.add_item(name, user_id)
    await update.message.reply_text(f"Добавлено: {name} (от {user_id})" if res == 1 else res)
