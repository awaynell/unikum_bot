# Используем официальный образ Python
FROM python:3.12-alpine

# Устанавливаем необходимые пакеты для работы
RUN apk update && apk add --no-cache \
    # chromium \
    # chromium-chromedriver \
    udev \
    ttf-freefont \
    wget \
    unzip

# Устанавливаем переменную окружения для пути к chromedriver
# ENV CHROMEDRIVER_PATH /usr/lib/chromium/chromedriver

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы бота в контейнер
COPY . .

# Устанавливаем зависимости Python в виртуальной среде
# RUN python3 -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]
