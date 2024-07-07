# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы бота в контейнер
COPY . .

COPY chromedriver /app/chromedriver

RUN chmod +x /app/chromedriver

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]
