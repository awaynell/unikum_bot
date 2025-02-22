import asyncio
from gradio_client import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
from os import getenv
from img_models import img_models


load_dotenv()

chromedriver_path = getenv('CHROMEDRIVER_PATH')


# Настройки для headless режима
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")

# Инициализация сервиса
service = Service(chromedriver_path)


def generateImg(prompt):
    # Инициализация браузера
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('https://www.midgenai.com')

    # Даем странице загрузиться
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "promptInput"))
    )

    # Находим текстовое поле по ID и вводим текст
    element = driver.find_element(By.ID, "promptInput")
    element.send_keys(prompt)

    # Находим кнопку генерации по классу и прокручиваем страницу до кнопки
    generate_button = driver.find_element(By.CLASS_NAME, 'gbtn')
    driver.execute_script("arguments[0].scrollIntoView();", generate_button)

    time.sleep(5)

    # Ожидаем кликабельности кнопки и кликаем её
    generate_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'gbtn'))
    )
    generate_button.click()

    # Ожидаем появления всех изображений с id, начинающимся с 'image-'
    images = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "img[id^='image-']"))
    )

    # Извлекаем blob URL и преобразуем их в Base64
    image_urls = []
    for image in images:
        blob_url = image.get_attribute('src')
        script = """
      var blob_url = arguments[0];
      var callback = arguments[1];
      var xhr = new XMLHttpRequest();
      xhr.open('GET', blob_url, true);
      xhr.responseType = 'blob';
      xhr.onload = function() {
          var reader = new FileReader();
          reader.readAsDataURL(xhr.response);
          reader.onload = function() {
              callback(reader.result);
          };
      };
      xhr.send();
      """
        base64_image = driver.execute_async_script(script, blob_url)
        image_urls.append(base64_image)

    # Закрываем браузер
    driver.quit()

    return image_urls


async def getImgFromAPI(prompt, update, context, model_key="imagineo"):
    try:
        # Получаем параметры модели
        model = img_models.get(model_key)

        if not model:
            raise ValueError(f"Модель с ключом {model_key} не найдена")

        client = Client(model["name"])

        # Добавляем prompt к параметрам модели
        params = model["params"].copy()
        params["prompt"] = prompt

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: client.predict(**params))

        return result
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(f"Произошла ошибка: {e}\nТекущая модель: {model_key}")
