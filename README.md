# Уникум: Нейробот для Telegram

## Описание

Уникум - это бот для Telegram, использующий нейросети для взаимодействия с пользователями. Бот способен отвечать на сообщения, используя модель GPT-3.5 Turbo, а также поддерживает функции сохранения истории сообщений.

## Установка через Python

1. **Клонирование репозитория и переход в директорию проекта:**

   ```
   git clone https://github.com/your/tg_ai_bot.git
   cd unicum-bot
   ```

2. **Установка зависимостей:**

   ```
   pip install -r requirements.txt
   ```

3. **Настройка переменных окружения:**

   - Создайте файл `.env`.
   - Вставьте свой токен Telegram Bot API в переменную `TG_BOT_TOKEN` в файле `.env`.

4. **Запуск бота:**
   ```
   python bot.py
   ```

## Установка через Docker

1. **Создание Docker образа:**

   - Убедитесь, что Docker установлен и запущен на вашем компьютере.
   - Соберите Docker образ из Dockerfile:
     ```
     docker build -t unicum-bot .
     ```

2. **Запуск контейнера:**

   ```
   docker run -e "TG_BOT_TOKEN=your_token" -e "TG_ADMIN_ID=your_id" -d unicum-bot
   ```

## Использование

После успешного запуска бота, он будет доступен в Telegram. Напишите `/start`, чтобы начать общение с Уникумом. Бот отвечает на сообщения, используя модель GPT-3.5 Turbo для генерации ответов на основе истории сообщений.

## Дополнительная информация

- **Требования к Python:** Python 3.12 и выше.
- **Требования к Docker:** Установленный Docker на вашей операционной системе.

---
