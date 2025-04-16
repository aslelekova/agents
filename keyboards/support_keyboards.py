# keyboards/support_keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_new_question_keyboard(question_id: int):
    kb = [
        [
            InlineKeyboardButton(
                text="Принять",
                callback_data=f"accept_question:{question_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_support_dialog_keyboard(question_id: int):
    kb = [
        [
            InlineKeyboardButton(
                text="Передать другому специалисту",
                callback_data=f"reassign_question:{question_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
