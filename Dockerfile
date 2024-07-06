# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем файлы бота в контейнер
COPY . .

# Запускаем бота
CMD ["python", "bot.py"]
