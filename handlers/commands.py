from telegram import Update
from telegram.ext import ContextTypes
from config.bot import user_chat_ids, users_language, users

from messages.messagePath import start_message

from messages.message import message, default_language

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_chat_ids.add(chat_id)
    if not (chat_id in users_language):
        users_language[chat_id] = default_language
    await update.message.reply_text(
        message(users_language[chat_id], start_message, 'start', update.effective_user.first_name), 
        parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
    Доступные команды:
    /start - Начать работу
    /help - Получить справку
    /echo [текст] - Эхо-ответ
    """
    await update.message.reply_text(help_text)

async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /echo"""
    if context.args:
        text = ' '.join(context.args)
        await update.message.reply_text(f"Вы сказали: {text}")
    else:
        await update.message.reply_text("Напишите: /echo [ваш текст]")