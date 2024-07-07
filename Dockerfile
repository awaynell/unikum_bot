# Используем Alpine Linux в качестве базового образа
FROM alpine:latest

# Устанавливаем необходимые пакеты для работы
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    wget \
    unzip \
    gnupg \
    chromium \
    udev \
    ttf-freefont \
    chromium-chromedriver

# Устанавливаем переменную окружения CHROMEDRIVER_PATH
ENV CHROMEDRIVER_PATH /usr/bin/chromedriver

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы бота в контейнер
COPY . .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота
CMD ["python3", "bot.py"]
