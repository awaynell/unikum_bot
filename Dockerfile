# Используем официальный образ Python
FROM python:3.12-alpine

# Устанавливаем необходимые пакеты для Python-зависимостей
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    udev \
    ttf-freefont \
    wget \
    unzip

# Если нужен Chromedriver:
# RUN apk add --no-cache chromium chromium-chromedriver
# ENV CHROMEDRIVER_PATH=/usr/lib/chromium/chromedriver

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]
