import logging
from config.bot import application
from handlers.commands import start_command, help_command, echo_command
from handlers.messages import handle_message
from telegram.ext import CommandHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_handlers():
    """Регистрация всех обработчиков"""
    
    # Регистрация команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("echo", echo_command))
    
    # Регистрация обработчика сообщений
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

def main():
    """Основная функция запуска бота"""
    logger.info("Настройка обработчиков...")
    setup_handlers()
    
    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == '__main__':
    main()