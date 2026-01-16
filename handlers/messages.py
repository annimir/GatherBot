from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import logging
from .keyboards import (
    get_main_keyboard, 
    CREATE_GAME, 
    GAME_LIST, 
    CONFIRMED_GAMES, 
    MY_GAMES,
    BACK_TO_MENU,
    get_active_games,
    get_confirmed_games,
    get_user_games,
    get_games_keyboard,
    get_game_by_id,
    parse_game_button,
    join_game,
    leave_game,
    delete_game,
    get_notifications,
    clear_notifications
)

logger = logging.getLogger(__name__)

async def handle_my_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Мои игры'"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"👤 Пользователь {user_id} ({user_name}) запросил 'Мои игры'")
    
    # Проверяем уведомления
    notifications = get_notifications(user_id)
    if notifications:
        await show_notifications(update, context, user_id)
        return
    
    user_games = get_user_games(user_id)
    
    response = "👤 <b>МОИ ИГРЫ</b>\n\n"
    
    # Созданные игры
    if user_games['created']:
        response += "👑 <b>Игры, которые я создал:</b>\n\n"
        for i, game in enumerate(user_games['created'], 1):
            players = len(game.get('players', []))
            
            response += (
                f"{i}. <b>{game.get('title')}</b>\n"
                f"   🆔 ID: {game.get('id')}\n"
                f"   🕒 {game.get('date')}\n"
                f"   👥 Участники: {players}/{game.get('max_players')}\n"
                f"   📊 Статус: {get_status_text(game.get('status'))}\n\n"
            )
    else:
        response += "👑 <b>Вы еще не создали ни одной игры</b>\n\n"
    
    # Игры где участвует
    if user_games['joined']:
        response += "✅ <b>Игры, в которых я участвую:</b>\n\n"
        for i, game in enumerate(user_games['joined'], 1):
            response += (
                f"{i}. <b>{game.get('title')}</b>\n"
                f"   🆔 ID: {game.get('id')}\n"
                f"   👤 Создатель: {game.get('creator')}\n"
                f"   🕒 {game.get('date')}\n"
                f"   📊 Статус: {get_status_text(game.get('status'))}\n\n"
            )
    else:
        response += "✅ <b>Вы еще не участвуете в играх</b>\n\n"
    
    response += "👇 Выберите игру для управления или просмотра деталей:"
    
    await update.message.reply_text(
        text=response,
        parse_mode='HTML',
        reply_markup=get_games_keyboard(user_id)
    )

async def show_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Показывает уведомления пользователя"""
    notifications = get_notifications(user_id)
    
    if not notifications:
        await update.message.reply_text(
            "📭 У вас нет новых уведомлений.",
            reply_markup=get_main_keyboard()
        )
        return
    
    response = "🔔 <b>ВАШИ УВЕДОМЛЕНИЯ:</b>\n\n"
    
    for i, notification in enumerate(notifications[:10], 1):  # Ограничиваем 10 уведомлениями
        timestamp = notification.get('timestamp', '')
        message = notification.get('message', '')
        
        response += f"{i}. <i>{timestamp}</i>\n{message}\n\n"
    
    if len(notifications) > 10:
        response += f"... и еще {len(notifications) - 10} уведомлений\n\n"
    
    response += "✅ Уведомления будут показаны при следующем заходе в 'Мои игры'"
    
    # Очищаем уведомления после показа
    clear_notifications(user_id)
    
    await update.message.reply_text(
        text=response,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

def get_status_text(status: str) -> str:
    """Возвращает текстовое описание статуса игры"""
    status_map = {
        'active': '🟡 Активна (есть места)',
        'gathering': '✅ Собралась (все на месте)',
        'completed': '🏁 Завершена'
    }
    return status_map.get(status, '❓ Неизвестен')

async def show_game_details(update: Update, context: ContextTypes.DEFAULT_TYPE, game=None, game_id: int = None):
    """Показывает детали игры с полной информацией"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Если передана игра, используем ее
    if not game and game_id:
        game = get_game_by_id(game_id)
    
    if not game:
        logger.error(f"❌ Игра не найдена для пользователя {user_id}")
        await update.message.reply_text(
            "❌ Игра не найдена.",
            reply_markup=get_main_keyboard()
        )
        return
    
    game_id = game.get('id')
    logger.info(f"ℹ️ Пользователь {user_id} запросил детали игры {game_id}")
    
    # Формируем детали
    players = game.get('players', [])
    player_ids = game.get('player_ids', [])
    
    # Полное название игры (без обрезания)
    full_title = game.get('title', 'Без названия')
    
    details = (
        f"🎮 <b>{full_title}</b>\n"
        f"🆔 <b>ID игры:</b> {game.get('id')}\n\n"
        
        f"👤 <b>Создатель:</b> {game.get('creator', 'Аноним')}\n"
        f"📅 <b>Дата и время:</b> {game.get('date', 'Не указано')}\n"
        f"📍 <b>Место:</b> {game.get('location', 'Не указано')}\n"
        f"👥 <b>Участники:</b> {len(players)}/{game.get('max_players', 0)}\n"
        f"📊 <b>Статус:</b> {get_status_text(game.get('status'))}\n\n"
    )
    
    # Показываем полное название если оно было обрезано
    if len(full_title) > 30:
        details += f"📝 <b>Полное название:</b> {full_title}\n\n"
    
    # Список участников
    if players:
        details += "<b>📋 Список участников:</b>\n"
        for i, player in enumerate(players, 1):
            details += f"{i}. {player}\n"
        details += "\n"
    
    # Статус текущего пользователя
    is_creator = game.get('creator_id') == user_id
    is_player = user_id in player_ids
    
    if is_creator:
        details += "👑 <b>Вы создатель этой игры</b>\n"
    elif is_player:
        details += "✅ <b>Вы участвуете в этой игре</b>\n"
    else:
        if len(players) < game.get('max_players', 0):
            details += "🟢 <b>Есть свободные места</b>\n"
        else:
            details += "🔴 <b>Все места заняты</b>\n"
    
    # Создаем клавиатуру действий
    keyboard = []
    
    if is_creator:
        # Для создателя: удаление игры
        keyboard.append([KeyboardButton(f"🗑️ Удалить игру {game_id}")])
    
    elif is_player:
        # Для участника: выход из игры
        keyboard.append([KeyboardButton(f"➖ Выйти из игры {game_id}")])
    
    else:
        # Для других пользователей: вход в игру
        if len(players) < game.get('max_players', 0):
            keyboard.append([KeyboardButton(f"➕ Войти в игру {game_id}")])
        else:
            details += "\n⚠️ <i>Все места заняты</i>\n"
    
    keyboard.append([KeyboardButton(BACK_TO_MENU)])
    
    await update.message.reply_text(
        text=details,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора игры из списка"""
    text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"🎲 Пользователь {user_id} выбрал: '{text}'")
    
    if text == BACK_TO_MENU:
        await update.message.reply_text(
            "📱 Возвращаю в главное меню:",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Заголовки разделов - просто показываем список заново
    if "📌 МОИ СОЗДАННЫЕ ИГРЫ 📌" in text or "🎮 ДРУГИЕ АКТИВНЫЕ ИГРЫ 🎮" in text:
        await update.message.reply_text(
            "👇 Выберите игру:",
            reply_markup=get_games_keyboard(user_id)
        )
        return
    
    # Выбор конкретной игры
    game = parse_game_button(text)
    
    if game:
        await show_game_details(update, context, game)
    else:
        logger.error(f"❌ Не удалось найти игру для текста: '{text}'")
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Не удалось найти выбранную игру.\n"
            "Пожалуйста, выберите игру из списка снова.",
            parse_mode='HTML',
            reply_markup=get_games_keyboard(user_id)
        )

async def handle_join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик входа в игру"""
    text = update.message.text
    
    if '➕ Войти в игру' in text:
        try:
            game_id = int(text.split('➕ Войти в игру ')[1])
            user_name = update.effective_user.first_name
            user_id = update.effective_user.id
            
            logger.info(f"➕ Пользователь {user_id} входит в игру {game_id}")
            
            # Получаем application из context
            application = context.application
            
            result = await join_game(game_id, user_name, user_id, application)
            
            if result['success']:
                await update.message.reply_text(
                    "✅ <b>Вы успешно вошли в игру!</b>\n\n"
                    f"Все участники игры получили уведомление о вашем входе.",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>{result['message']}</b>",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка при входе в игру: {e}")
            await update.message.reply_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_main_keyboard()
            )

async def handle_leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выхода из игры"""
    text = update.message.text
    
    if '➖ Выйти из игры' in text:
        try:
            game_id = int(text.split('➖ Выйти из игры ')[1])
            user_id = update.effective_user.id
            
            logger.info(f"➖ Пользователь {user_id} выходит из игры {game_id}")
            
            # Получаем application из context
            application = context.application
            
            result = await leave_game(game_id, user_id, application)
            
            if result['success']:
                await update.message.reply_text(
                    "➖ <b>Вы вышли из игры</b>\n\n"
                    "Все участники игры получили уведомление о вашем выходе.\n"
                    "Вы можете войти в эту игру снова позже.",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>{result['message']}</b>",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка при выходе из игры: {e}")
            await update.message.reply_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_main_keyboard()
            )

async def handle_delete_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик удаления игры"""
    text = update.message.text
    
    if '🗑️ Удалить игру' in text:
        try:
            game_id = int(text.split('🗑️ Удалить игру ')[1])
            user_id = update.effective_user.id
            
            logger.info(f"🗑️ Пользователь {user_id} удаляет игру {game_id}")
            
            # Получаем application из context
            application = context.application
            
            result = await delete_game(game_id, user_id, application)
            
            if result['success']:
                await update.message.reply_text(
                    "🗑️ <b>Игра успешно удалена!</b>\n\n"
                    "Все участники игры получили уведомление об отмене.",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>{result['message']}</b>",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка при удалении игры: {e}")
            await update.message.reply_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_main_keyboard()
            )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главный обработчик текстовых сообщений
    """
    text = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"📝 Пользователь {user_id} ({user_name}): '{text}'")
    
    # Обработка нажатий основных кнопок
    if text == CREATE_GAME:
        await update.message.reply_text(
            "🎮 Нажмите кнопку '🎮 Создать игру' в главном меню для начала создания.",
            reply_markup=get_main_keyboard()
        )
    
    elif text == GAME_LIST:
        logger.info(f"📋 Пользователь {user_id} запросил список игр")
        games_list = get_active_games()
        
        if not games_list:
            await update.message.reply_text(
                "📭 <b>Активных игр пока нет</b>\n\n"
                "Создайте первую игру! 🎮",
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
            return
        
        await update.message.reply_text(
            "📋 <b>Список всех активных игр:</b>\n"
            "👇 Выберите игру для просмотра деталей:",
            parse_mode='HTML',
            reply_markup=get_games_keyboard(user_id)
        )
    
    elif text == CONFIRMED_GAMES:
        logger.info(f"✅ Пользователь {user_id} запросил подтвержденные игры")
        confirmed = get_confirmed_games()
        
        if not confirmed:
            await update.message.reply_text(
                "✅ <b>Подтвержденных игр пока нет</b>\n\n"
                "Игра становится подтвержденной, когда все участники собрались.",
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
            return
        
        response = "✅ <b>Подтвержденные игры (все участники собрались):</b>\n\n"
        
        for i, game in enumerate(confirmed, 1):
            players = game.get('players', [])
            
            response += (
                f"{i}. <b>{game.get('title')}</b>\n"
                f"   👤 Создатель: {game.get('creator')}\n"
                f"   🕒 {game.get('date')}\n"
                f"   👥 Участники: {len(players)}/{game.get('max_players')}\n\n"
            )
        
        await update.message.reply_text(
            text=response,
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
    
    elif text == MY_GAMES:
        await handle_my_games(update, context)
    
    elif text == BACK_TO_MENU:
        logger.info(f"🏠 Пользователь {user_id} вернулся в главное меню")
        await update.message.reply_text(
            text="📱 Главное меню:",
            reply_markup=get_main_keyboard()
        )
    
    # Обработка действий с играми по ID
    elif '➕ Войти в игру' in text:
        await handle_join_game(update, context)
    
    elif '➖ Выйти из игры' in text:
        await handle_leave_game(update, context)
    
    elif '🗑️ Удалить игру' in text:
        await handle_delete_game(update, context)
    
    # Выбор игры из списка (по кнопке)
    elif '🎮' in text or '👑' in text or '✅' in text or '👥' in text:
        await handle_game_selection(update, context)
    
    # Любой другой текст
    else:
        logger.warning(f"❓ Неизвестная команда от пользователя {user_id}: '{text}'")
        await update.message.reply_text(
            text="🤔 <b>Не понял вашего сообщения</b>\n\n"
                 "Пожалуйста, используйте кнопки для навигации.",
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )