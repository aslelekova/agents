# main.py

import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.start_handler import router as start_router
from handlers.agent_handler import router as agent_router
from handlers.support_handler import router as support_router
from services.db_service import setup_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    # Здесь можно настроить вашу сессию при необходимости
    session = AiohttpSession()

    bot = Bot(token=BOT_TOKEN,
              session=session,
              default=DefaultBotProperties(parse_mode="HTML"),
              timeout=150)
    dp = Dispatcher(storage=MemoryStorage())

    try:
        await setup_db()  # Инициализация БД (или CSV и т.п.)
    except Exception as e:
        logger.exception("Ошибка инициализации БД: %s", e)

    # Регистрируем маршруты
    dp.include_router(start_router)
    dp.include_router(agent_router)
    dp.include_router(support_router)

    # Стартуем поллинг
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Произошла ошибка во время работы бота: %s", e)
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
