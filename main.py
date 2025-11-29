import asyncio

from aiogram import Bot, Dispatcher

from config.config_app import BOT_TOKEN
from database.db import init_db
from handlers.graup_moders import graup_moders
from handlers.registered import registered
from handlers.admin import admin
from services.logger import send_log


# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(admin)
dp.include_router(registered)
dp.include_router(graup_moders)


# --- ЗАПУСК ---
async def main():
    
    # Инициализация БД
    await init_db()
    
    # Удаляем вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await send_log(bot, "🤖 Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")