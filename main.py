import logging
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler

# Импортируем настройки из config
from config.bot import create_application

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
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_handlers(application):
    """
    Настройка и регистрация всех обработчиков бота
    """
    logger.info("🛠️ Настройка обработчиков...")
    
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
            CommandHandler("help", help_command),
            MessageHandler(filters.Regex('^⬅️ Назад в меню$'), cancel_game_creation),
            MessageHandler(filters.COMMAND, cancel_game_creation)
        ],
        allow_reentry=True,
        name="game_creation",
        persistent=False
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
    
    logger.info("✅ Обработчики настроены")

def main():
    """
    Главная функция запуска бота
    """
    try:
        # Создаем приложение
        application = create_application()
        
        # Настраиваем обработчики
        setup_handlers(application)
        
        # Запускаем бота
        logger.info("🚀 Бот запущен и готов к работе!")
        logger.info("📱 Отправьте /start в Telegram для начала")
        logger.info("📝 Логи записываются в файл bot.log")
        
        print("\n" + "="*50)
        print("🎮 GATHERBOT ЗАПУЩЕН!")
        print("="*50)
        print("📋 УПРОЩЕННЫЙ ФУНКЦИОНАЛ:")
        print("  1. Прямой вход в игру")
        print("  2. Уведомления участникам о входе/выходе")
        print("  3. Уведомление о сборе комнаты")
        print("  4. Уведомление об отмене игры")
        print("  5. Нет ограничений по времени")
        print("="*50)
        print("🎯 Подтвержденные игры = игры где все участники собрались")
        print("="*50)
        
        application.run_polling(
            allowed_updates=None,
            drop_pending_updates=True
        )
        
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        print(f"\n❌ ОШИБКА: {e}")
        print("🔧 РЕШЕНИЕ: Создайте файл .env в корне проекта")
        print("Содержимое:")
        print("TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        print("\nПолучите токен у @BotFather в Telegram")
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
        print("\n🛑 Бот остановлен")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("Проверьте файл bot.log для деталей")

if __name__ == '__main__':
    main()