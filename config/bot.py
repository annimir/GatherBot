import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_application() -> Application:

    # Получаем токен из переменных окружения
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в .env файле!")
        raise ValueError("Токен бота не указан")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    return application

# Глобальная переменная application
application = create_application()
users = {}
users_language = {}
user_chat_ids = set()