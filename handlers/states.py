from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, Application
from .keyboards import get_main_keyboard, BACK_TO_MENU, add_game
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

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
    
    # Проверяем формат даты
    try:
        datetime.strptime(game_date, "%d.%m.%Y %H:%M")
    except ValueError:
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
    
    if max_players < 2:
        await update.message.reply_text(
            "❌ Минимальное количество игроков - 2!\n"
            "Введите число больше 1:"
        )
        return GAME_PLAYERS
    
    if max_players > 20:
        await update.message.reply_text(
            "❌ Максимальное количество игроков - 20!\n"
            "Введите число до 20:"
        )
        return GAME_PLAYERS
    
    # Получаем данные игры
    game_data = context.user_data.get('game_data', {})
    
    if not game_data:
        await update.message.reply_text(
            "❌ Ошибка: данные игры потеряны!\n"
            "Начните создание заново.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Получаем application из контекста
    application = context.application
    
    # Добавляем игру
    full_game_data = add_game({
        'title': game_data.get('title'),
        'date': game_data.get('date'),
        'location': game_data.get('location'),
        'max_players': max_players,
        'creator': game_data.get('creator'),
        'creator_id': game_data.get('creator_id')
    }, application)
    
    # Очищаем временные данные
    context.user_data.pop('game_data', None)
    
    await update.message.reply_text(
        f"🎉 <b>Игра успешно создана!</b>\n\n"
        f"🎮 <b>Название:</b> {full_game_data['title']}\n"
        f"📅 <b>Дата и время:</b> {full_game_data['date']}\n"
        f"📍 <b>Место:</b> {full_game_data['location']}\n"
        f"👥 <b>Макс. игроков:</b> {full_game_data['max_players']}\n"
        f"👤 <b>Создатель:</b> {full_game_data['creator']}\n"
        f"🆔 <b>ID игры:</b> {full_game_data['id']}\n\n"
        
        f"📢 <b>Теперь другие игроки могут войти в вашу игру!</b>\n\n"
        
        f"ℹ️ <b>Правила:</b>\n"
        f"• Игроки могут входить/выходить из игры\n"
        f"• Когда все места будут заняты, все получат уведомление\n"
        f"• За час до начала, если все на месте, игра подтверждается\n"
        f"• За час до начала вход/выход/удаление становятся невозможны\n\n"
        
        f"👇 Используйте кнопки для управления игрой:",
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END

async def cancel_game_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания игры"""
    context.user_data.pop('game_data', None)
    
    await update.message.reply_text(
        "❌ Создание игры отменено.",
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END