from telegram import Update
from telegram.ext import ContextTypes
from .keyboards import (
    get_main_keyboard, 
    CREATE_GAME, 
    GAME_LIST, 
    CONFIRMED_GAMES, 
    BACK_TO_MENU,
    get_active_games,
    get_confirmed_games,
    get_games_keyboard,
    get_game_by_id,
    join_game,
    leave_game
)

async def handle_create_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Создать игру'"""
    # Этот обработчик теперь вызывается из ConversationHandler
    # Вместо этого показываем сообщение с инструкцией
    await update.message.reply_text(
        "🎮 Чтобы создать игру, нажмите кнопку '🎮 Создать игру' в главном меню\n"
        "и следуйте инструкциям бота.",
        reply_markup=get_main_keyboard()
    )

async def handle_game_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Список игр'"""
    games = get_active_games()
    
    if not games:
        await update.message.reply_text(
            "📭 <b>Активных игр пока нет</b>\n\n"
            "Создайте первую игру! 🎮",
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем клавиатуру со списком игр
    user_id = update.effective_user.id
    await update.message.reply_text(
        "📋 <b>Выберите игру для просмотра или присоединения:</b>",
        parse_mode='HTML',
        reply_markup=get_games_keyboard(user_id)
    )

async def handle_confirmed_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Подтвержденные игры'"""
    games = get_confirmed_games()
    
    if not games:
        await update.message.reply_text(
            "✅ <b>Подтвержденных игр пока нет</b>\n\n"
            "Игра становится подтвержденной, когда набирается "
            "более 50% от максимального количества игроков.\n\n"
            "Создайте игру и пригласите друзей! 👥",
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        return
    
    response = "✅ <b>Подтвержденные игры (готовы к запуску):</b>\n\n"
    
    for i, game in enumerate(games, 1):
        players = game.get('players', [])
        players_list = ', '.join(players) if players else "пока нет участников"
        
        response += (
            f"{i}. <b>{game.get('title', 'Без названия')}</b>\n"
            f"   👤 Создатель: {game.get('creator', 'Аноним')}\n"
            f"   🕒 {game.get('date', 'Не указано')}\n"
            f"   📍 {game.get('location', 'Не указано')}\n"
            f"   👥 Участники: {players_list}\n"
            f"   🆔 ID игры: {game.get('id')}\n\n"
        )
    
    await update.message.reply_text(
        text=response,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора конкретной игры из списка"""
    text = update.message.text
    
    if text == BACK_TO_MENU:
        await update.message.reply_text(
            "📱 Возвращаю в главное меню:",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Извлекаем ID игры из текста кнопки (если есть)
    # Формат кнопки: "🎮 Название (3/6)"
    if '🎮' in text:
        # Показываем детали выбранной игры
        await show_game_details(update, context)
    else:
        # Любой другой текст - возвращаем в меню
        await update.message.reply_text(
            "Используйте кнопки для навигации:",
            reply_markup=get_main_keyboard()
        )

async def show_game_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает детали выбранной игры"""
    text = update.message.text
    
    # Находим игру по названию (упрощенная логика)
    active_games = get_active_games()
    
    # Извлекаем название из текста кнопки
    if '🎮' in text:
        game_title = text.split('🎮 ')[1].split(' (')[0]
        
        for game in active_games:
            if game.get('title') == game_title:
                # Формируем детали игры
                players = game.get('players', [])
                player_ids = game.get('player_ids', [])
                current_user_id = update.effective_user.id
                
                is_joined = current_user_id in player_ids
                
                details = (
                    f"🎮 <b>{game.get('title', 'Без названия')}</b>\n\n"
                    f"👤 <b>Создатель:</b> {game.get('creator', 'Аноним')}\n"
                    f"📅 <b>Дата и время:</b> {game.get('date', 'Не указано')}\n"
                    f"📍 <b>Место:</b> {game.get('location', 'Не указано')}\n"
                    f"👥 <b>Участники:</b> {len(players)}/{game.get('max_players', 0)}\n"
                    f"🆔 <b>ID игры:</b> {game.get('id')}\n\n"
                )
                
                if players:
                    details += "<b>Список участников:</b>\n"
                    for i, player in enumerate(players, 1):
                        details += f"{i}. {player}\n"
                    details += "\n"
                
                # Добавляем статус
                if is_joined:
                    details += "✅ <b>Вы участвуете в этой игре</b>\n"
                else:
                    if len(players) < game.get('max_players', 0):
                        details += "🟡 <b>Есть свободные места</b>\n"
                    else:
                        details += "🔴 <b>Мест нет</b>\n"
                
                # Создаем клавиатуру действий
                from telegram import ReplyKeyboardMarkup, KeyboardButton
                keyboard = []
                
                if is_joined:
                    keyboard.append([KeyboardButton(f"➖ Покинуть игру {game.get('id')}")])
                else:
                    if len(players) < game.get('max_players', 0):
                        keyboard.append([KeyboardButton(f"➕ Присоединиться к игре {game.get('id')}")])
                
                keyboard.append([KeyboardButton(BACK_TO_MENU)])
                
                await update.message.reply_text(
                    text=details,
                    parse_mode='HTML',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
    
    # Если игра не найдена
    await update.message.reply_text(
        "❌ Игра не найдена.",
        reply_markup=get_main_keyboard()
    )

async def handle_join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик присоединения к игре"""
    text = update.message.text
    
    # Извлекаем ID игры из текста
    if '➕ Присоединиться к игре' in text:
        try:
            game_id = int(text.split('➕ Присоединиться к игре ')[1])
            user_name = update.effective_user.first_name
            user_id = update.effective_user.id
            
            success = join_game(game_id, user_name, user_id)
            
            if success:
                await update.message.reply_text(
                    "✅ <b>Вы успешно присоединились к игре!</b>\n\n"
                    "Теперь вы будете получать уведомления об обновлениях.",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ <b>Не удалось присоединиться к игре.</b>\n"
                    "Возможно, все места уже заняты или вы уже участвуете.",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_main_keyboard()
            )

async def handle_leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выхода из игры"""
    text = update.message.text
    
    if '➖ Покинуть игру' in text:
        try:
            game_id = int(text.split('➖ Покинуть игру ')[1])
            user_id = update.effective_user.id
            
            success = leave_game(game_id, user_id)
            
            if success:
                await update.message.reply_text(
                    "✅ <b>Вы вышли из игры.</b>",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ <b>Не удалось выйти из игры.</b>\n"
                    "Возможно, вы не участвуете в этой игре.",
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_main_keyboard()
            )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главный обработчик текстовых сообщений
    """
    text = update.message.text
    
    # Обработка нажатий основных кнопок
    if text == CREATE_GAME:
        await handle_create_game(update, context)
    
    elif text == GAME_LIST:
        await handle_game_list(update, context)
    
    elif text == CONFIRMED_GAMES:
        await handle_confirmed_games(update, context)
    
    elif text == BACK_TO_MENU:
        await update.message.reply_text(
            text="📱 Возвращаю в главное меню:",
            reply_markup=get_main_keyboard()
        )
    
    # Обработка присоединения к игре
    elif '➕ Присоединиться к игре' in text:
        await handle_join_game(update, context)
    
    # Обработка выхода из игры
    elif '➖ Покинуть игру' in text:
        await handle_leave_game(update, context)
    
    # Обработка выбора игры из списка
    elif '🎮' in text:
        await handle_game_selection(update, context)
    
    # Любой другой текст
    else:
        await update.message.reply_text(
            text="🤔 <b>Не понял вашего сообщения</b>\n\n"
                 "Пожалуйста, используйте кнопки для навигации.",
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )