import logging
import sys
import aiosqlite
from config.config_app import DB_NAME

# Настройка базового логгера (в консоль)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# --- Инициализация базы ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                warnings INTEGER DEFAULT 0
            )
        """)
        await db.commit()

# --- Регистрация пользователя ---
async def add_user(user_id: int, username: str) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()

# --- Проверка регистрации ---
async def is_registered(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

# --- Работа с предупреждениями ---
async def add_warning(user_id: int) -> int:
    """Добавляет варн и возвращает новое количество."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, warnings) VALUES (?, 0)", (user_id,))
        await db.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

        async with db.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def reset_warnings(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET warnings = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_warnings(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0



