import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from config import TELEGRAM_BOT_TOKEN
from handlers import router
from middlewares import DialogHistoryMiddleware

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

TOKEN = os.getenv("BOT_TOKEN")  # Укажите токен через переменную окружения


async def main():
    """
    Main entry point for the bot.
    """
    logging.info("Starting Telegram bot...")
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        dp = Dispatcher()

        # Подключаем middleware для хранения историй диалогов
        dp.message.middleware(DialogHistoryMiddleware())

        dp.include_router(router)
        await dp.start_polling(bot)
    except (asyncio.CancelledError, RuntimeError) as e:
        logging.error("Bot encountered a runtime error: %s", e)
    except Exception as e:
        logging.error("Unexpected error: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
