from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from .keyboards import get_main_keyboard, BACK_TO_MENU, add_game

# Состояния для создания игры
GAME_TITLE, GAME_DATE, GAME_LOCATION, GAME_PLAYERS = range(4)

async def start_game_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания игры - запрос названия"""
    await update.message.reply_text(
        "🎮 <b>Создание новой игры</b>\n\n"
        "Введите <b>название игры</b> (например: Мафия, Монополия, Шахматы):",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(BACK_TO_MENU)]],
            resize_keyboard=True
        )
    )
    
    # Очищаем предыдущие данные
    context.user_data.pop('game_data', None)
    return GAME_TITLE

async def process_game_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия игры"""
    game_title = update.message.text.strip()
    
    if game_title == BACK_TO_MENU:
        await update.message.reply_text(
            "Возвращаю в главное меню...",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Сохраняем название
    context.user_data['game_data'] = {
        'title': game_title,
        'creator': update.effective_user.first_name,
        'creator_id': update.effective_user.id
    }
    
    await update.message.reply_text(
        f"✅ Название: <b>{game_title}</b>\n\n"
        "Теперь введите <b>дату и время</b> игры:\n"
        "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Пример: 15.01.2024 19:00",
        parse_mode='HTML'
    )
    
    return GAME_DATE

async def process_game_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка даты и времени игры"""
    game_date = update.message.text.strip()
    
    if game_date == BACK_TO_MENU:
        await update.message.reply_text(
            "Возвращаю в главное меню...",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Простая валидация формата даты
    if not any(char in game_date for char in ['.', '-', ':']):
        await update.message.reply_text(
            "❌ Неверный формат даты!\n"
            "Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Пример: 15.01.2024 19:00\n\n"
            "Попробуйте еще раз:"
        )
        return GAME_DATE
    
    # Сохраняем дату
    context.user_data['game_data']['date'] = game_date
    
    await update.message.reply_text(
        f"✅ Дата и время: <b>{game_date}</b>\n\n"
        "Теперь введите <b>место проведения</b> игры:\n"
        "Пример: Кафе 'Игротека', Дом у Максима, Парк Горького",
        parse_mode='HTML'
    )
    
    return GAME_LOCATION

async def process_game_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка места проведения"""
    location = update.message.text.strip()
    
    if location == BACK_TO_MENU:
        await update.message.reply_text(
            "Возвращаю в главное меню...",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Сохраняем место
    context.user_data['game_data']['location'] = location
    
    await update.message.reply_text(
        f"✅ Место: <b>{location}</b>\n\n"
        "Теперь введите <b>максимальное количество игроков</b>:\n"
        "Только цифра (например: 4, 6, 10)",
        parse_mode='HTML'
    )
    
    return GAME_PLAYERS

async def process_game_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка количества игроков и завершение создания"""
    players_input = update.message.text.strip()
    
    if players_input == BACK_TO_MENU:
        await update.message.reply_text(
            "Возвращаю в главное меню...",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Проверяем, что введено число
    if not players_input.isdigit():
        await update.message.reply_text(
            "❌ Введите только цифру!\n"
            "Пример: 4, 6, 10\n\n"
            "Попробуйте еще раз:"
        )
        return GAME_PLAYERS
    
    max_players = int(players_input)
    
    # Получаем данные игры
    game_data = context.user_data.get('game_data', {})
    
    if not game_data:
        await update.message.reply_text(
            "❌ Ошибка: данные игры потеряны!\n"
            "Начните создание заново.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Формируем полные данные игры
    full_game_data = {
        'title': game_data.get('title', 'Без названия'),
        'date': game_data.get('date', 'Не указано'),
        'location': game_data.get('location', 'Не указано'),
        'max_players': max_players,
        'creator': game_data.get('creator', 'Аноним'),
        'creator_id': game_data.get('creator_id'),
        'players': [game_data.get('creator', 'Аноним')],  # Создатель сразу участник
        'player_ids': [game_data.get('creator_id')],
        'confirmed': False
    }
    
    # Сохраняем игру
    add_game(full_game_data)
    
    # Формируем сообщение об успешном создании
    success_message = (
        "🎉 <b>Игра успешно создана!</b>\n\n"
        f"🎮 <b>Название:</b> {full_game_data['title']}\n"
        f"📅 <b>Дата и время:</b> {full_game_data['date']}\n"
        f"📍 <b>Место:</b> {full_game_data['location']}\n"
        f"👥 <b>Макс. игроков:</b> {full_game_data['max_players']}\n"
        f"👤 <b>Создатель:</b> {full_game_data['creator']}\n\n"
        
        "📢 <b>Теперь вы можете:</b>\n"
        "1. Поделиться этой игрой с друзьями\n"
        "2. Следить за набором участников\n"
        "3. Когда наберется достаточно игроков, игра станет 'Подтвержденной'\n\n"
        
        "👇 Используйте кнопки для дальнейших действий:"
    )
    
    await update.message.reply_text(
        success_message,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )
    
    # Очищаем временные данные
    context.user_data.pop('game_data', None)
    
    return ConversationHandler.END

async def cancel_game_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания игры"""
    context.user_data.pop('game_data', None)
    
    await update.message.reply_text(
        "❌ Создание игры отменено.",
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END