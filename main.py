# main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import ADMIN_ID
from database import init_db
from handlers import register_handlers
from admin import register_admin_handlers

# Токен берётся из переменной окружения BOT_TOKEN
BOT_TOKEN = os.getenv('BOT_TOKEN', '8665227013:AAE8UMjSfkKW8MSVgPdVbNzKmB5TiE7uoV0')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрируем все обработчики
register_handlers(dp, bot)
register_admin_handlers(dp, ADMIN_ID)

async def main():
    # Инициализируем базу данных
    await init_db()
    
    print("=" * 50)
    print("🚀 N-G SOURCE БОТ ЗАПУЩЕН НА ХОСТИНГЕ")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print("📋 Команды: /admin - админ-панель")
    print("=" * 50)
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    me = await bot.get_me()
    print(f"✅ Бот: @{me.username}")
    print("✅ Бот успешно запущен и работает 24/7!")
    
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        print("\n⏹️ Бот остановлен")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Завершено")