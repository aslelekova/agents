import os

ID_FILE_PATH = "last_id.txt"

def load_last_id():
    if os.path.exists(ID_FILE_PATH):
        with open(ID_FILE_PATH, "r") as f:
            return int(f.read().strip())
    return 0

def save_last_id(new_id: int):
    with open(ID_FILE_PATH, "w") as f:
        f.write(str(new_id))

def get_next_question_id():
    last_id = load_last_id()
    next_id = last_id + 1
    save_last_id(next_id)
    return next_id
