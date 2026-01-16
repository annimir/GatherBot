import logging
from config.bot import application
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler

# Импортируем обработчики из handlers
from handlers.commands import start_command, help_command, menu_command
from handlers.messages import handle_text
from handlers.states import (
    start_game_creation,
    process_game_title,
    process_game_date,
    process_game_location,
    process_game_players,
    cancel_game_creation,
    GAME_TITLE, GAME_DATE, GAME_LOCATION, GAME_PLAYERS
)
from handlers.keyboards import CREATE_GAME

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_handlers():
    """Регистрация всех обработчиков"""
    
    # ConversationHandler для создания игры
    game_creation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^{CREATE_GAME}$'), start_game_creation)],
        states={
            GAME_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_game_title)],
            GAME_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_game_date)],
            GAME_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_game_location)],
            GAME_PLAYERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_game_players)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("menu", menu_command),
            MessageHandler(filters.Regex('^⬅️ Назад в меню$'), cancel_game_creation),
            MessageHandler(filters.COMMAND, cancel_game_creation)
        ],
        allow_reentry=True
    )
    
    # Регистрируем команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Регистрируем ConversationHandler для создания игры
    application.add_handler(game_creation_handler)
    
    # Регистрируем общий обработчик текста
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

def main():
    """Основная функция запуска бота"""
    logger.info("Настройка обработчиков...")
    setup_handlers()
    
    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == '__main__':
    main()