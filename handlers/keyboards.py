from telegram import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# Константы для текста кнопок
CREATE_GAME = "🎮 Создать игру"
GAME_LIST = "📋 Список игр"
CONFIRMED_GAMES = "✅ Подтвержденные игры"
BACK_TO_MENU = "⬅️ Назад в меню"
JOIN_GAME = "➕ Присоединиться"
LEAVE_GAME = "➖ Покинуть игру"

# Хранилище данных (в реальном проекте используйте БД)
games = []  # Список всех игр
game_id_counter = 1  # Счетчик для ID игр

def get_main_keyboard(with_back: bool = False) -> ReplyKeyboardMarkup:
    """Создает главную клавиатуру"""
    keyboard = [
        [KeyboardButton(CREATE_GAME)],
        [KeyboardButton(GAME_LIST)],
        [KeyboardButton(CONFIRMED_GAMES)]
    ]
    
    if with_back:
        keyboard.append([KeyboardButton(BACK_TO_MENU)])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def add_game(game_data: dict) -> int:
    """Добавляет игру в список и возвращает её ID"""
    global game_id_counter
    
    game_data['id'] = game_id_counter
    game_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    game_data['status'] = 'active'  # active, confirmed, cancelled, completed
    
    games.append(game_data)
    game_id_counter += 1
    
    return game_data['id']

def get_active_games() -> list:
    """Возвращает список активных игр"""
    return [game for game in games if game.get('status') == 'active']

def get_confirmed_games() -> list:
    """Возвращает список подтвержденных игр"""
    confirmed_games = []
    
    for game in games:
        if game.get('status') == 'active':
            current_players = len(game.get('players', []))
            max_players = game.get('max_players', 0)
            
            # Игра подтверждена если набрано более 50% игроков
            if current_players >= 2 and current_players >= max_players * 0.5:
                confirmed_games.append(game)
    
    return confirmed_games

def get_game_by_id(game_id: int):
    """Находит игру по ID"""
    for game in games:
        if game.get('id') == game_id:
            return game
    return None

def join_game(game_id: int, user_name: str, user_id: int) -> bool:
    """Добавляет пользователя в игру"""
    game = get_game_by_id(game_id)
    
    if not game:
        return False
    
    current_players = len(game.get('players', []))
    max_players = game.get('max_players', 0)
    
    # Проверяем есть ли место
    if current_players >= max_players:
        return False
    
    # Проверяем не участвует ли уже
    if user_id in game.get('player_ids', []):
        return False
    
    # Добавляем пользователя
    game['players'].append(user_name)
    game['player_ids'].append(user_id)
    
    # Проверяем нужно ли обновить статус
    if current_players + 1 >= max_players * 0.5:
        game['status'] = 'confirmed'
    
    return True

def leave_game(game_id: int, user_id: int) -> bool:
    """Удаляет пользователя из игры"""
    game = get_game_by_id(game_id)
    
    if not game:
        return False
    
    player_ids = game.get('player_ids', [])
    
    if user_id not in player_ids:
        return False
    
    # Находим индекс пользователя
    idx = player_ids.index(user_id)
    
    # Удаляем из обоих списков
    game['players'].pop(idx)
    game['player_ids'].pop(idx)
    
    # Если создатель ушел, удаляем игру
    if user_id == game.get('creator_id'):
        games.remove(game)
        return True
    
    # Проверяем статус после ухода
    current_players = len(game.get('players', []))
    if current_players < game.get('max_players', 0) * 0.5:
        game['status'] = 'active'
    
    return True

def get_games_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    """Создает клавиатуру со списком игр"""
    active_games = get_active_games()
    
    if not active_games:
        return get_main_keyboard()
    
    keyboard = []
    
    for game in active_games[:10]:  # Ограничиваем 10 играми
        game_title = game.get('title', 'Без названия')[:20]
        players = len(game.get('players', []))
        max_players = game.get('max_players', 0)
        
        # Проверяем участвует ли уже пользователь
        is_joined = user_id in game.get('player_ids', []) if user_id else False
        
        if is_joined:
            button_text = f"🎮 {game_title} ({players}/{max_players}) ✅"
        else:
            button_text = f"🎮 {game_title} ({players}/{max_players})"
        
        keyboard.append([KeyboardButton(button_text)])
    
    keyboard.append([KeyboardButton(BACK_TO_MENU)])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)