import asyncio
import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from services.role_service import get_user_role
from handlers.agent_handler import questions_data, current_question_by_support_id, schedule_reminder
from keyboards.support_keyboards import get_support_dialog_keyboard, get_new_question_keyboard
from services.csv_logger import log_answer, log_resolution
from config import SUPPORT_CHAT_ID, CSV_FILE_PATH

router = Router()

@router.message(F.text == "/export", F.chat.type == "private", F.from_user.id.func(lambda uid: get_user_role(uid) == "support"))
async def export_log(message: Message):
    if os.path.exists(CSV_FILE_PATH):
        await message.answer_document(FSInputFile(CSV_FILE_PATH))
    else:
        await message.answer("Файл логов не найден.")

@router.message(F.text == "/end", F.chat.type == "private", F.from_user.id.func(lambda uid: get_user_role(uid) == "support"))
async def end_dialog_command(message: Message):
    user_id = message.from_user.id
    question_id = current_question_by_support_id.get(user_id)

    if not question_id:
        await message.answer("❌ У вас нет активного диалога.")
        return

    question_info = questions_data.get(question_id)
    if not question_info:
        await message.answer("❌ Вопрос не найден.")
        return

    # Завершаем
    question_info["status"] = "done"
    question_info["assigned_to"] = None
    question_info["is_followup_active"] = False
    current_question_by_support_id.pop(user_id, None)

    agent_id = question_info["agent_id"]

    await message.answer(f"Диалог по вопросу #{question_id} завершён.")
    for q in questions_data.values():
        if q["agent_id"] == agent_id:
            q["is_followup_active"] = False
    await message.bot.send_message(
        chat_id=agent_id,
        text="Мы рады были помочь! Удалось ли нам решить Вашу проблему?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="resolved"),
                InlineKeyboardButton(text="Нет", callback_data="not_resolved")
            ]
        ])
    )


@router.callback_query(F.data.startswith("accept_question"))
async def accept_question_callback(call: CallbackQuery):
    user_id = call.from_user.id
    role = get_user_role(user_id)

    if role != "support":
        await call.answer("Только специалист может принять вопрос.", show_alert=True)
        return

    _, question_id_str = call.data.split(":")
    question_id = int(question_id_str)

    question_info = questions_data.get(question_id)
    if not question_info:
        await call.answer("Вопрос не найден!", show_alert=True)
        return

    if question_info["assigned_to"] is not None and question_info["assigned_to"] != user_id:
        await call.answer("Вопрос уже принят другим специалистом!", show_alert=True)
        return

    question_info["assigned_to"] = user_id
    question_info["status"] = "in_progress"
    question_info["is_followup_active"] = True
    current_question_by_support_id[user_id] = question_id  # 🔗 Привязываем вопрос к специалисту
    agent_name = question_info.get("agent_name")
    await call.message.edit_text(
        text=f"Вопрос #{question_id} от {agent_name} принят специалистом {call.from_user.first_name}.",
    )
    await call.answer("Вопрос принят!")

    await call.bot.send_message(
        chat_id=user_id,
        text=(f"Вы приняли вопрос #{question_id} от {agent_name}.\n"
              f"Вопрос: {question_info['question_text']}\n\n"
              f"Напишите ответ в этот чат, и он будет отправлен агенту."),
        reply_markup=get_support_dialog_keyboard(question_id)
    )


@router.callback_query(F.data.startswith("reassign_question"))
async def reassign_question_callback(call: CallbackQuery):
    user_id = call.from_user.id
    role = get_user_role(user_id)
    if role != "support":
        await call.answer("Только специалист может передавать вопрос.", show_alert=True)
        return

    _, question_id_str = call.data.split(":")
    question_id = int(question_id_str)

    question_info = questions_data.get(question_id)
    if not question_info:
        await call.answer("Вопрос не найден!", show_alert=True)
        return

    if question_info.get("answered"):
        await call.answer("❌ На этот вопрос уже был дан ответ. Его нельзя передать повторно.", show_alert=True)
        return

    question_info["assigned_to"] = None
    question_info["status"] = "new"
    current_question_by_support_id.pop(user_id, None)

    try:
        await call.message.delete()
    except Exception as e:
        print(f"[WARNING] Не удалось удалить сообщение у специалиста: {e}")
    agent_name = question_info.get("agent_name")
    if SUPPORT_CHAT_ID:
        sent = await call.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=(
                f"Вопрос #{question_id} от {agent_name} \"{question_info['question_text']}\" снова доступен. Кто примет?"),
            reply_markup=get_new_question_keyboard(question_id)
        )

        question_info["support_message_id"] = sent.message_id

        asyncio.create_task(schedule_reminder(question_id, call.bot))

    await call.answer("Вопрос возвращён в общий пул.")


@router.callback_query(F.data.startswith("done_question"))
async def done_question_callback(call: CallbackQuery):
    user_id = call.from_user.id
    role = get_user_role(user_id)
    if role != "support":
        await call.answer("Только специалист может завершить вопрос.", show_alert=True)
        return

    _, question_id_str = call.data.split(":")
    question_id = int(question_id_str)
    question_info = questions_data.get(question_id)
    if not question_info:
        await call.answer("Вопрос не найден!", show_alert=True)
        return

    question_info["status"] = "done"
    question_info["assigned_to"] = None
    current_question_by_support_id.pop(user_id, None)

    await call.answer("Диалог завершён.")
    await call.message.edit_text(f"Вопрос #{question_id} завершён.")


@router.message(F.chat.type == "private", F.text, F.from_user.id.func(lambda uid: get_user_role(uid) == "support"))
async def support_answer_message(message: Message):
    user_id = message.from_user.id
    role = get_user_role(user_id)

    print(f"[DEBUG] Сообщение от {user_id}, роль: {role}, текст: {message.text}, чат: {message.chat.type}")

    if role != "support":
        return

    text = message.text.strip()
    if not text:
        await message.answer("Сообщение пустое.")
        return

    question_id = current_question_by_support_id.get(user_id)
    if not question_id:
        await message.answer("❌ У вас нет активного вопроса.")
        return

    question_info = questions_data.get(question_id)
    if not question_info:
        await message.answer("❌ Вопрос не найден.")
        return

    agent_id = question_info.get("agent_id")
    agent_name = question_info.get("agent_name")

    if not agent_id:
        await message.answer("❌ Не удалось определить агенту, кому отправить ответ.")
        return

    try:
        # Отправляем агенту ответ
        await message.bot.send_message(
            chat_id=agent_id,
            text=f"{text}"
        )

        question_info["answered"] = True
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки агенту: {e}")
        print(f"[ERROR] Не удалось отправить ответ агенту {agent_id}: {e}")
        return

    # Сохраняем в CSV
    log_answer(question_id, message.from_user.first_name, text)

    await message.answer(f"✅ Ответ отправлен агенту ({agent_name}) по вопросу #{question_id}")


@router.callback_query(F.data.in_({"resolved", "not_resolved"}))
async def resolution_feedback(call: CallbackQuery):
    user_id = call.from_user.id

    # найдём последний вопрос пользователя
    latest_qid = None
    for qid in sorted(questions_data.keys(), reverse=True):
        q = questions_data[qid]
        if q["agent_id"] == user_id:
            latest_qid = qid
            break

    if not latest_qid:
        await call.answer("Не найден соответствующий вопрос.")
        return

    if call.data == "resolved":
        log_resolution(latest_qid, "yes")
        await call.message.edit_text("Спасибо за ваше обращение! Мы рады, что смогли помочь")
    else:
        log_resolution(latest_qid, "no")
        await call.message.edit_text("Сожалеем, что не удалось помочь. Мы будем стараться лучше!")

    await call.answer()
