# keyboards/agent_keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_agent_menu_keyboard():
    kb = [
        [InlineKeyboardButton(text="Задать вопрос", callback_data="ask_question")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
