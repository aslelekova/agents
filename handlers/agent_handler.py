# handlers/agent_handler.py
import asyncio

from aiogram import Router, F
from aiogram.types import Message

from services.id_service import get_next_question_id
from services.role_service import get_user_role
from services.csv_logger import log_question, get_average_response_time_seconds
from config import SUPPORT_CHAT_ID
import time

from keyboards.support_keyboards import get_new_question_keyboard

router = Router()

questions_data = {}
current_question_by_support_id = {}

@router.message(F.chat.type == "private", F.text, F.from_user.id.func(lambda uid: get_user_role(uid) == "agent"))
async def handle_agent_question(message: Message):
    user_id = message.from_user.id
    role = get_user_role(user_id)
    if role != "agent":
        return

    agent_name = message.from_user.first_name or "Агент"

    # Сначала проверим: это уточнение?
    for q_id, q in questions_data.items():
        if q.get("agent_id") == user_id and q.get("is_followup_active") and q.get("status") != "done":
            support_id = q.get("assigned_to")
            if support_id:
                new_question_id = get_next_question_id()
                questions_data[new_question_id] = {
                    "agent_id": user_id,
                    "agent_name": agent_name,
                    "question_text": message.text,
                    "status": "in_progress",
                    "created_at": time.time(),
                    "assigned_to": support_id,
                    "answered": False,
                    "follow_up": True,
                    "is_followup_active": True
                }
                current_question_by_support_id[support_id] = new_question_id
                log_question(new_question_id, agent_name, message.text)

                await message.bot.send_message(
                    chat_id=support_id,
                    text=(f"📨 Уточнение от агента по вопросу #{q_id}:\n"
                          f"{message.text}")
                )
                return  # ⬅️ ВАЖНО: иначе пойдёт дальше в общий чат!
    # Считаем, что уже задавался главный вопрос, если у агента есть хотя бы один не-завершённый основной вопрос
    already_asked = any(
        q["agent_id"] == user_id and not q.get("follow_up", False) and q.get("status") in {"new", "in_progress"}
        for q in questions_data.values()
    )

    # Если не уточнение — создаём обычный вопрос
    question_id = get_next_question_id()
    question_text = message.text

    questions_data[question_id] = {
        "agent_id": user_id,
        "agent_name": agent_name,
        "question_text": question_text,
        "status": "new",
        "created_at": time.time(),
        "assigned_to": None,
        "answered": False,
        "follow_up": False,
        "is_followup_active": False
    }

    log_question(question_id, agent_name, question_text)

    avg_time = get_average_response_time_seconds()
    avg_minutes = max(1, avg_time // 60)



    if not already_asked:
        await message.answer(
            f"Спасибо за Ваше обращение\n"
            f"Мы занимаемся вашим вопросом и скоро ответим на Ваш вопрос.\n"
            # f"Среднее время ожидания ответа: ~{avg_minutes} мин."
        )

    if SUPPORT_CHAT_ID:
        sent_message = await message.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=(f"Новый вопрос #{question_id} от {agent_name} (ID: {user_id}):\n"
                  f"\"{question_text}\""),
            reply_markup=get_new_question_keyboard(question_id)
        )

        questions_data[question_id]["support_message_id"] = sent_message.message_id
        asyncio.create_task(schedule_reminder(question_id, message.bot))


async def schedule_reminder(question_id: int, bot):
    REMINDER_INTERVAL_SECONDS = 120

    while True:
        await asyncio.sleep(REMINDER_INTERVAL_SECONDS)

        question_info = questions_data.get(question_id)
        if not question_info:
            return

        # Если вопрос уже принят или завершён — выходим
        if question_info.get("assigned_to") or question_info.get("status") != "new":
            return

        message_id = question_info.get("support_message_id")

        if SUPPORT_CHAT_ID:
            try:
                await bot.send_message(
                    chat_id=SUPPORT_CHAT_ID,
                    text=(f"⏰ Напоминание: Вопрос #{question_id} от {question_info['agent_name']} "
                          f"всё ещё не принят. Кто может помочь?"),
                    reply_to_message_id=message_id if message_id else None
                )
            except Exception as e:
                print(f"[WARNING] Не удалось отправить напоминание: {e}")
