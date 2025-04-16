import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CSV_FILE_PATH=os.getenv('CSV_FILE_PATH')
SUPPORT_CHAT_ID=os.getenv('SUPPORT_CHAT_ID')
SUPPORT_USER_IDS = [5995089891, 276475080, 524763432, 345350730]
