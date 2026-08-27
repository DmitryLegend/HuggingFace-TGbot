import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ErrorEvent

import config
import database as db
from handlers import admin, common, files, fallback, generation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота / открыть меню"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="help", description="Как пользоваться ботом"),
        BotCommand(command="stats", description="Статистика (только для админа)"),
    ])


async def main() -> None:
    config.validate()
    await db.init_db()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок подключения важен: специфичные обработчики — раньше,
    # "ловушки на всё" (fallback) — обязательно последними.
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(generation.router)
    dp.include_router(files.router)
    dp.include_router(fallback.router)

    @dp.error()
    async def global_error_handler(event: ErrorEvent) -> bool:
        logger.exception("Необработанная ошибка при обработке апдейта: %s", event.exception)
        return True

    await _set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Бот запущен, жду сообщений…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
