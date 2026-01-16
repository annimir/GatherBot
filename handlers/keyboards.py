from telegram import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

# Константы для текста кнопок
CREATE_GAME = "🎮 Создать игру"
GAME_LIST = "📋 Список игр"
CONFIRMED_GAMES = "✅ Подтвержденные игры"
MY_GAMES = "👤 Мои игры"
BACK_TO_MENU = "⬅️ Назад в меню"

# Хранилище данных
games = []  # Список всех игр
game_id_counter = 1  # Счетчик для ID игр
# Словарь для хранения уведомлений: user_id -> список уведомлений
notifications = {}

def get_main_keyboard(with_back: bool = False) -> ReplyKeyboardMarkup:
    """Создает главную клавиатуру с 4 кнопками"""
    keyboard = [
        [KeyboardButton(CREATE_GAME)],
        [KeyboardButton(GAME_LIST)],
        [KeyboardButton(CONFIRMED_GAMES)],
        [KeyboardButton(MY_GAMES)]
    ]
    
    if with_back:
        keyboard.append([KeyboardButton(BACK_TO_MENU)])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def add_notification(user_id: int, message: str):
    """Добавляет уведомление пользователю"""
    if user_id not in notifications:
        notifications[user_id] = []
    notifications[user_id].append({
        'message': message,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    logger.info(f"📢 Уведомление для {user_id}: {message}")

def get_notifications(user_id: int) -> list:
    """Получает уведомления пользователя"""
    return notifications.get(user_id, [])

def clear_notifications(user_id: int):
    """Очищает уведомления пользователя"""
    if user_id in notifications:
        notifications[user_id] = []

def add_game(game_data: dict, application) -> dict:
    """Добавляет игру в список и возвращает полные данные игры"""
    global game_id_counter
    
    game_id = game_id_counter
    game_id_counter += 1
    
    full_game_data = {
        'id': game_id,
        'title': game_data.get('title', 'Без названия'),
        'date': game_data.get('date', 'Не указано'),
        'location': game_data.get('location', 'Не указано'),
        'max_players': game_data.get('max_players', 0),
        'creator': game_data.get('creator', 'Аноним'),
        'creator_id': game_data.get('creator_id'),
        'players': [game_data.get('creator', 'Аноним')],
        'player_ids': [game_data.get('creator_id')],
        'declined_users': [],    # Пользователи, отклонившие участие
        'status': 'active',  # active, gathering, completed
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'notified_gathering': False  # Было ли отправлено уведомление о сборе
    }
    
    games.append(full_game_data)
    logger.info(f"✅ Игра добавлена: ID={game_id}, Название='{full_game_data['title']}', "
                f"Длина названия={len(full_game_data['title'])}, Создатель={full_game_data['creator_id']}")
    
    return full_game_data

async def check_game_gathering(game_id: int, application):
    """Проверяет, собралась ли комната"""
    await asyncio.sleep(0.1)  # Небольшая задержка
    
    game = get_game_by_id(game_id)
    if not game:
        return
    
    current_players = len(game.get('players', []))
    max_players = game.get('max_players', 0)
    
    if current_players >= max_players and not game.get('notified_gathering'):
        game['notified_gathering'] = True
        game['status'] = 'gathering'  # Меняем статус на "собирается"
        game['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Отправляем уведомление всем участникам
        notification_msg = (
            f"🎉 <b>КОМНАТА СОБРАЛАСЬ!</b>\n\n"
            f"🎮 Игра: {game.get('title')}\n"
            f"📅 Дата: {game.get('date')}\n"
            f"📍 Место: {game.get('location')}\n"
            f"👥 Все {max_players} участников в сборе!\n\n"
            f"Приятной игры! 🎲"
        )
        
        for player_id in game.get('player_ids', []):
            add_notification(player_id, notification_msg)
            try:
                # Пытаемся отправить уведомление через бота
                await application.bot.send_message(
                    chat_id=player_id,
                    text=notification_msg,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {player_id}: {e}")
        
        logger.info(f"🎉 Комната собралась: Игра {game_id}")

def get_active_games() -> list:
    """Возвращает список активных игр"""
    return [game for game in games if game.get('status') in ['active', 'gathering']]

def get_confirmed_games() -> list:
    """Возвращает список игр где все участники собрались"""
    return [game for game in games if game.get('status') == 'gathering']

def get_user_games(user_id: int) -> dict:
    """Возвращает игры пользователя разделенные по категориям"""
    created_games = []
    joined_games = []
    
    for game in games:
        if game.get('status') not in ['active', 'gathering']:
            continue
            
        # Игры созданные пользователем
        if game.get('creator_id') == user_id:
            created_games.append(game)
        # Игры где пользователь участник
        elif user_id in game.get('player_ids', []):
            joined_games.append(game)
    
    logger.info(f"👤 Игры пользователя {user_id}: "
                f"создано={len(created_games)}, "
                f"участвует={len(joined_games)}")
    
    return {
        'created': created_games,
        'joined': joined_games
    }

def get_game_by_id(game_id: int):
    """Находит игру по ID"""
    for game in games:
        if game.get('id') == game_id:
            return game
    return None

def get_game_by_title_partial(title_part: str):
    """Находит игру по части названия"""
    logger.info(f"🔍 Поиск игры по части названия: '{title_part}'")
    
    for game in games:
        game_title = game.get('title', '')
        if title_part in game_title:
            logger.info(f"✅ Найдена игра: ID={game.get('id')}, Название='{game_title}'")
            return game
    
    logger.warning(f"❌ Игра с частью названия '{title_part}' не найдена")
    return None

def format_game_button(game: dict, user_id: int = None) -> str:
    """Форматирует текст для кнопки игры"""
    game_title = game.get('title', 'Без названия')
    players = len(game.get('players', []))
    max_players = game.get('max_players', 0)
    game_id = game.get('id')
    status = game.get('status', 'active')
    
    # Определяем иконку статуса
    if status == 'gathering':
        status_icon = '✅'
    else:
        status_icon = '🎮'
    
    # Обрезаем название если слишком длинное
    display_title = game_title[:25] + "..." if len(game_title) > 25 else game_title
    
    # Определяем префикс в зависимости от статуса пользователя
    prefix = status_icon  # По умолчанию для других игр
    
    if user_id:
        if game.get('creator_id') == user_id:
            prefix = "👑"
        elif user_id in game.get('player_ids', []):
            prefix = "✅"
    
    # Формат: префикс + обрезанное название + игроки + ID в конце
    button_text = f"{prefix} {display_title} ({players}/{max_players}) [{game_id}]"
    
    # Проверяем длину кнопки (ограничение Telegram - 64 символа)
    if len(button_text) > 64:
        # Если слишком длинно, еще больше обрезаем название
        display_title = game_title[:15] + "..."
        button_text = f"{prefix} {display_title} ({players}/{max_players}) [{game_id}]"
    
    logger.debug(f"📝 Кнопка игры: '{button_text}', длина={len(button_text)}")
    return button_text

def parse_game_button(button_text: str):
    """
    Парсит текст кнопки игры и возвращает ID игры
    """
    logger.info(f"🔍 Парсинг кнопки: '{button_text}'")
    
    try:
        # Ищем ID в квадратных скобках в конце
        if '[' in button_text and ']' in button_text:
            # Извлекаем ID из скобок
            id_part = button_text.split('[')[-1].split(']')[0]
            game_id = int(id_part)
            
            # Находим игру по ID
            game = get_game_by_id(game_id)
            
            if game:
                logger.info(f"✅ Найдена игра по ID: ID={game_id}, Название='{game.get('title')}'")
                return game
            else:
                logger.warning(f"❌ Игра с ID={game_id} не найдена в базе")
        
        # Если не нашли по ID, пытаемся по названию
        clean_text = button_text
        
        # Убираем префикс (эмодзи и пробел)
        prefixes = ["👑 ", "🎮 ", "✅ ", "👥 ", "⏳ "]
        for prefix in prefixes:
            if clean_text.startswith(prefix):
                clean_text = clean_text[len(prefix):]
                break
        
        # Убираем информацию об игроках в скобках и ID в квадратных скобках
        if ' (' in clean_text:
            clean_text = clean_text.split(' (')[0]
        
        # Убираем ID в квадратных скобках если остался
        if ' [' in clean_text:
            clean_text = clean_text.split(' [')[0]
        
        # Ищем игру по части названия
        game = get_game_by_title_partial(clean_text.strip())
        
        if game:
            logger.info(f"✅ Найдена игра по названию: '{clean_text}' -> ID={game.get('id')}")
            return game
        
        logger.error(f"❌ Не удалось распознать игру из текста: '{button_text}'")
        return None
        
    except (ValueError, IndexError) as e:
        logger.error(f"❌ Ошибка парсинга кнопки '{button_text}': {e}")
        return None

def get_games_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    """Создает клавиатуру со списком игр с разделением"""
    user_games = get_user_games(user_id) if user_id else {'created': [], 'joined': []}
    active_games = get_active_games()
    
    keyboard = []
    
    # Сначала игры созданные пользователем
    if user_games['created']:
        keyboard.append([KeyboardButton("📌 МОИ СОЗДАННЫЕ ИГРЫ 📌")])
        
        for game in user_games['created'][:5]:  # Ограничиваем 5 играми
            button_text = format_game_button(game, user_id)
            keyboard.append([KeyboardButton(button_text)])
    
    # Затем другие активные игры
    other_games = [g for g in active_games if g not in user_games['created']]
    
    if other_games:
        if user_games['created']:
            keyboard.append([])  # Пустая строка для разделения
        
        keyboard.append([KeyboardButton("🎮 ДРУГИЕ АКТИВНЫЕ ИГРЫ 🎮")])
        
        for game in other_games[:10]:  # Ограничиваем 10 играми
            button_text = format_game_button(game, user_id)
            keyboard.append([KeyboardButton(button_text)])
    
    keyboard.append([KeyboardButton(BACK_TO_MENU)])
    
    logger.info(f"⌨️ Создана клавиатура игр: "
                f"мои={len(user_games['created'])}, "
                f"другие={len(other_games)}, "
                f"всего кнопок={len(keyboard)-1}")
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def join_game(game_id: int, user_name: str, user_id: int, application) -> dict:
    """Вход пользователя в игру"""
    game = get_game_by_id(game_id)
    
    if not game:
        logger.warning(f"⚠️ Игра {game_id} не найдена для входа пользователя {user_id}")
        return {'success': False, 'message': 'Игра не найдена'}
    
    # Проверяем не создатель ли это
    if game.get('creator_id') == user_id:
        logger.info(f"ℹ️ Создатель {user_id} пытается войти в свою игру {game_id}")
        return {'success': False, 'message': 'Вы создатель этой игры'}
    
    # Проверяем уже участвует ли
    if user_id in game.get('player_ids', []):
        logger.info(f"ℹ️ Пользователь {user_id} уже участвует в игре {game_id}")
        return {'success': False, 'message': 'Вы уже участвуете в этой игре'}
    
    # Проверяем есть ли свободные места
    current_players = len(game.get('players', []))
    max_players = game.get('max_players', 0)
    
    if current_players >= max_players:
        return {'success': False, 'message': 'Все места заняты'}
    
    # Проверяем не отклонил ли уже пользователь
    if user_id in game.get('declined_users', []):
        logger.info(f"ℹ️ Пользователь {user_id} ранее отклонил игру {game_id}, разрешаем повторную попытку")
        game['declined_users'].remove(user_id)
    
    # Добавляем в участники
    game['players'].append(user_name)
    game['player_ids'].append(user_id)
    game['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"✅ Пользователь вошел в игру: Игра={game_id}, Пользователь={user_id}")
    
    # Отправляем уведомление всем участникам
    notification_msg = (
        f"👤 <b>НОВЫЙ УЧАСТНИК!</b>\n\n"
        f"🎮 Игра: {game.get('title')}\n"
        f"👤 {user_name} присоединился к игре\n"
        f"👥 Теперь участников: {current_players + 1}/{max_players}"
    )
    
    for player_id in game.get('player_ids', []):
        if player_id != user_id:  # Не отправляем уведомление самому себе
            add_notification(player_id, notification_msg)
            try:
                await application.bot.send_message(
                    chat_id=player_id,
                    text=notification_msg,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления о входе пользователю {player_id}: {e}")
    
    # Проверяем, собралась ли комната
    if current_players + 1 >= max_players:
        await check_game_gathering(game_id, application)
    
    return {
        'success': True, 
        'message': 'Вы успешно вошли в игру!',
        'game': game
    }

async def leave_game(game_id: int, user_id: int, application) -> dict:
    """Выход пользователя из игры"""
    game = get_game_by_id(game_id)
    
    if not game:
        logger.warning(f"⚠️ Игра {game_id} не найдена для выхода пользователя {user_id}")
        return {'success': False, 'message': 'Игра не найдена'}
    
    player_ids = game.get('player_ids', [])
    
    if user_id not in player_ids:
        logger.info(f"ℹ️ Пользователь {user_id} не участвует в игре {game_id}")
        return {'success': False, 'message': 'Вы не участвуете в этой игре'}
    
    # Получаем имя пользователя перед удалением
    user_idx = player_ids.index(user_id)
    user_name = game['players'][user_idx]
    
    # Удаляем из обоих списков
    game['players'].pop(user_idx)
    game['player_ids'].pop(user_idx)
    game['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Обновляем статус
    current_players = len(game.get('players', []))
    if current_players < game.get('max_players', 0):
        game['status'] = 'active'
        game['notified_gathering'] = False  # Сбрасываем флаг сбора
    
    logger.info(f"➖ Пользователь вышел из игры: Игра={game_id}, Пользователь={user_id}")
    
    # Отправляем уведомление всем участникам
    notification_msg = (
        f"🚪 <b>УЧАСТНИК ВЫШЕЛ</b>\n\n"
        f"🎮 Игра: {game.get('title')}\n"
        f"👤 {user_name} вышел из игры\n"
        f"👥 Теперь участников: {current_players}/{game.get('max_players', 0)}"
    )
    
    for player_id in game.get('player_ids', []):
        add_notification(player_id, notification_msg)
        try:
            await application.bot.send_message(
                chat_id=player_id,
                text=notification_msg,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о выходе пользователю {player_id}: {e}")
    
    # Создателю тоже отправляем уведомление
    if game.get('creator_id') != user_id:
        creator_id = game.get('creator_id')
        add_notification(creator_id, notification_msg)
        try:
            await application.bot.send_message(
                chat_id=creator_id,
                text=notification_msg,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления создателю {creator_id}: {e}")
    
    return {
        'success': True,
        'message': 'Вы вышли из игры',
        'game': game
    }

async def delete_game(game_id: int, user_id: int, application) -> dict:
    """Удаляет игру (только для создателя)"""
    game = get_game_by_id(game_id)
    
    if not game:
        return {'success': False, 'message': 'Игра не найдена'}
    
    # Проверяем права
    if game.get('creator_id') != user_id:
        logger.warning(f"⚠️ Попытка удалить чужую игру: Игра={game_id}, Пользователь={user_id}")
        return {'success': False, 'message': 'Вы не можете удалить чужую игру'}
    
    game_title = game.get('title')
    player_ids = game.get('player_ids', [])
    
    # Отправляем уведомление всем участникам об отмене
    notification_msg = (
        f"❌ <b>ИГРА ОТМЕНЕНА!</b>\n\n"
        f"🎮 Игра: {game_title}\n"
        f"📅 Дата: {game.get('date')}\n"
        f"📍 Место: {game.get('location')}\n\n"
        f"Создатель игры отменил мероприятие."
    )
    
    for player_id in player_ids:
        if player_id != user_id:  # Не отправляем уведомление создателю
            add_notification(player_id, notification_msg)
            try:
                await application.bot.send_message(
                    chat_id=player_id,
                    text=notification_msg,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления об отмене пользователю {player_id}: {e}")
    
    # Удаляем игру
    games.remove(game)
    logger.info(f"🗑️ Игра удалена: ID={game_id}, Создатель={user_id}")
    
    return {
        'success': True,
        'message': 'Игра удалена. Все участники уведомлены.'
    }