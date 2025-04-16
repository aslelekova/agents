import csv
import os
from datetime import datetime
from config import CSV_FILE_PATH

CSV_HEADERS = [
    "timestamp",
    "question_id",
    "agent_name",
    "question",
    "answer_time",
    "support_name",
    "answer",
    "resolved"
]

def read_all_rows():
    if not os.path.exists(CSV_FILE_PATH):
        return []
    with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # ❗ Удаляем лишние ключи, чтобы не падало
            cleaned_row = {k: row.get(k, "") for k in CSV_HEADERS}
            rows.append(cleaned_row)
        return rows


def write_all_rows(rows: list[dict]):
    with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def log_question(question_id: int, agent_name: str, question: str):
    rows = read_all_rows()

    found = False
    for row in rows:
        if str(row["question_id"]) == str(question_id):
            row["timestamp"] = datetime.now().isoformat()
            row["question"] = question
            row["agent_name"] = agent_name
            found = True
            break

    if not found:
        rows.append({
            "timestamp": datetime.now().isoformat(),
            "question_id": question_id,
            "agent_name": agent_name,
            "question": question,
            "answer_time": "",
            "support_name": "",
            "answer": "",
            "resolved": ""
        })

    write_all_rows(rows)


def log_answer(question_id: int, support_name: str, answer_text: str):
    rows = read_all_rows()
    found = False

    for row in rows:
        if str(row["question_id"]) == str(question_id):
            row["answer_time"] = datetime.now().isoformat()
            row["support_name"] = support_name
            row["answer"] = answer_text
            found = True
            break

    if found:
        write_all_rows(rows)
    else:
        print(f"[WARNING] Вопрос #{question_id} не найден при попытке логировать ответ.")


def get_average_response_time_seconds() -> int:
    rows = read_all_rows()
    time_deltas = []

    for row in rows:
        ts_str = row.get("timestamp")
        ans_str = row.get("answer_time")
        if ts_str and ans_str:
            try:
                created_at = datetime.fromisoformat(ts_str)
                answered_at = datetime.fromisoformat(ans_str)
                delta = (answered_at - created_at).total_seconds()
                if delta > 0:
                    time_deltas.append(delta)
            except Exception:
                continue

    if not time_deltas:
        return 60 * 3

    return int(sum(time_deltas) / len(time_deltas))

def log_resolution(question_id: int, resolved: str):
    rows = read_all_rows()
    for row in rows:
        if str(row["question_id"]) == str(question_id):
            row["resolved"] = resolved
            break
    write_all_rows(rows)
