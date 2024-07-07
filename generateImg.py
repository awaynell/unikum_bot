from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
from os import getenv

load_dotenv()

chromedriver_path = getenv('CHROMEDRIVER_PATH')


# Настройки для headless режима
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

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

    print('image_urls', image_urls)

    # Закрываем браузер
    driver.quit()

    return image_urls