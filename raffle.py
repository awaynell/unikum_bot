
import random
from telegram import Update
from telegram.ext import ContextTypes


class RaffleManager:
    def __init__(self, limit):
        self.arr_places = []
        self.limit = limit

    def add_item(self, id, name):
        if (not id.isdigit() or int(id) <= 0 or int(id) > self.limit):
            return "Номер должен быть целым числом от 1 до предела массива."

        if len(self.arr_places) >= self.limit:
            return "Все места заняты"

        if any(item['id'] == id for item in self.arr_places):
            return f"Место {id} уже забронировано. Выберите другое."

        new_item = {"id": id, "name": f"@{name}"}
        self.arr_places.append(new_item)
        return 1

    def get_array(self):
        return self.arr_places

    def set_limit(self, new_limit):
        if new_limit < len(self.arr_places):
            return "Невозможно уменьшить предел ниже текущего количества элементов."
        self.limit = new_limit
        print(f"Предел массива изменён на {new_limit}")

    def get_winners(self, limit):
        if not self.arr_places:
            return []
        return random.sample(self.arr_places, min(limit, len(self.arr_places)))

    def clear_raffle(self):
        self.arr_places = []


raffle_manager = RaffleManager(10)


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
        [f"{i+1}. {winner['name']} (Место: {winner['id']})" for i, winner in enumerate(winners)])
    await update.message.reply_text(f"Победители:\n{result}")


async def add_raffle_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Использование: /choose_item_raffle <номер>")
        return

    name = " ".join(context.args)
    username = update.effective_user.username
    res = raffle_manager.add_item(name, username)
    await update.message.reply_text(
        f"Добавлено: {
            name} (от @{username or 'неизвестного пользователя'})" if res == 1 else res
    )


async def get_raffle_array(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arr_places = raffle_manager.get_array()
    if not arr_places:
        await update.message.reply_text("Участников нет.")
        return
    result = "\n".join(
        [f"{item['id']}. {item['name']}" for item in arr_places])
    await update.message.reply_text(f"Участники:\n{result}")


async def change_raffle_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Использование: /change_limit_raffle <предел>")
        return

    new_limit = int(context.args[0])
    raffle_manager.set_limit(new_limit)
    await update.message.reply_text(f"Количество мест изменено на {new_limit}")
    raffle_manager.clear_raffle()


async def clear_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raffle_manager.clear_raffle()
    await update.message.reply_text("Розыгрыш очищен.")
