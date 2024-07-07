# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы бота в контейнер
COPY . .

# Копируем Chromedriver
COPY /root/chromedriver .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]
