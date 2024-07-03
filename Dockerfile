# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем зависимости
RUN pip install --no-cache-dir python-telegram-bot requests

# Копируем файлы бота в контейнер
COPY bot.py /app/bot.py

# Устанавливаем рабочую директорию
WORKDIR /app

# Запускаем бота
CMD ["python", "bot.py"]
