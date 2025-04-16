# handlers/start_handler.py

from aiogram import Router, F
from aiogram.types import Message

from config import SUPPORT_USER_IDS
from services.role_service import set_user_role

router = Router()

@router.message(F.text == "/start")
async def start_command(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Агент"

    # Определяем роль
    if user_id in SUPPORT_USER_IDS:
        role = "support"
    else:
        role = "agent"

    set_user_role(user_id, role)

    if role == "agent":
        await message.answer(f"Добрый день, {user_name}!\n"
                             f"Если у вас есть вопрос, пожалуйста, напишите его в этом чате, и мы поможем вам 🙌")
    else:
        await message.answer(f"Здравствуйте, {user_name}!\n"
                             f"Ожидайте вопросы от агентов.")