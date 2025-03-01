import requests
import telebot
from dotenv import load_dotenv
import os
import logging
import time
from typing import Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s %(levelname)s (%(asctime)s): %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_random_pet(api_url: str) -> Optional[str]:
    """
    Возвращает URL случайного фото животного.
    :param api_url: URL API для получения фото
    :return: URL фото или None в случае ошибки
    """
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            return response.json()[0]['url']
        else:
            logger.error(f"Ошибка при запросе к API: {response.status_code}")
            return None
    except requests.exceptions.SSLError as e:
        logger.error(f"Ошибка SSL при запросе к API: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return None

def get_random_cat() -> Optional[str]:
    """Возвращает URL случайного фото котика."""
    return get_random_pet('https://api.thecatapi.com/v1/images/search')

def get_random_dog() -> Optional[str]:
    """Возвращает URL случайного фото собачки."""
    return get_random_pet('https://api.thedogapi.com/v1/images/search')

load_dotenv()
TOKEN = os.getenv("TG_TOKEN")
if not TOKEN:
    logger.critical("Токен не найден. Проверьте переменную окружения TG_TOKEN.")
    exit(1)

bot = telebot.TeleBot(TOKEN)

def log_user_event(message, command: str):
    """Логирует событие от пользователя."""
    logger.info(f"Юзер {message.from_user.username} (ID: {message.from_user.id}) в чате {message.chat.id} написал команду: {command}. Текст: {message.text}")

def send_random_pet_photo(message, api_function, pet_type: str):
    """
    Отправляет случайное фото животного и логирует результат.
    :param message: Объект сообщения от пользователя
    :param api_function: Функция для получения URL фото
    :param pet_type: Тип животного (например, "cat" или "dog")
    """
    log_user_event(message, f"/{pet_type}")
    photo_url = api_function()
    if photo_url is not None:
        try:
            logger.info(f"Для юзера {message.from_user.username} (ID: {message.from_user.id}) отправлено фото {pet_type}: {photo_url}")
            bot.send_photo(message.chat.id, photo_url)
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Ошибка при отправке фото {pet_type}: {e}")
            bot.send_message(message.chat.id, text=f"Что-то пошло не так при отправке фото {pet_type}. Попробуй ещё раз.")
    else:
        logger.warning(f"Для юзера {message.from_user.username} (ID: {message.from_user.id}) фото {pet_type} не отправлено: API недоступно.")
        bot.send_message(message.chat.id, text=f"{pet_type.capitalize()} сбежал(а) =(, попробуй ещё раз.")

@bot.message_handler(commands=["start", "Start"])
def main(message):
    """Обработчик команды /start."""
    log_user_event(message, "/start")
    bot.send_message(message.chat.id, text="Привет! Напиши /cat или /dog чтобы получить рандомное фото котика или собаки =)")

@bot.message_handler(commands=["cat", "Cat"])
def cat(message):
    """Обработчик команды /cat."""
    send_random_pet_photo(message, get_random_cat, "cat")

@bot.message_handler(commands=["dog", "Dog"])
def dog(message):
    """Обработчик команды /dog."""
    send_random_pet_photo(message, get_random_dog, "dog")

if __name__ == "__main__":
    logger.info("Бот запущен.")
    MAX_RETRIES = 5
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            bot.infinity_polling()
        except Exception as e:
            logger.error(f"Ошибка в infinity_polling: {e}")
            retry_count += 1
            time.sleep(10)
    logger.critical("Бот остановлен после нескольких попыток перезапуска.")