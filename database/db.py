import logging
import sys
import aiosqlite
from config.config_app import DB_NAME

# Настройка базового логгера (в консоль)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей: ID, никнейм, количество предупреждений
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                warnings INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def register_user_db(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()

async def is_registered(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

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


# import logging
# import sys

# import aiosqlite

# from config.config_app import DB_NAME

# # Настройка базового логгера (в консоль)
# logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# # --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
# async def init_db():
#     async with aiosqlite.connect(DB_NAME) as db:
#         # Таблица пользователей: ID, никнейм, количество предупреждений
#         await db.execute("""
#             CREATE TABLE IF NOT EXISTS users (
#                 user_id INTEGER PRIMARY KEY,
#                 username TEXT,
#                 warnings INTEGER DEFAULT 0
#             )
#         """)
#         await db.commit()

# async def register_user_db(user_id: int, username: str):
#     async with aiosqlite.connect(DB_NAME) as db:
#         await db.execute(
#             "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
#             (user_id, username)
#         )
#         await db.commit()

# async def is_registered(user_id: int) -> bool:
#     async with aiosqlite.connect(DB_NAME) as db:
#         async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
#             return await cursor.fetchone() is not None

# async def add_warning(user_id: int) -> int:
#     """Добавляет варн и возвращает новое количество."""
#     async with aiosqlite.connect(DB_NAME) as db:
#         # Убедимся, что юзер есть в БД (если он зашел сразу в группу без /start)
#         await db.execute("INSERT OR IGNORE INTO users (user_id, warnings) VALUES (?, 0)", (user_id,))
        
#         await db.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (user_id,))
#         await db.commit()
        
#         async with db.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,)) as cursor:
#             row = await cursor.fetchone()
#             return row[0] if row else 0

# async def reset_warnings(user_id: int):
#     async with aiosqlite.connect(DB_NAME) as db:
#         await db.execute("UPDATE users SET warnings = 0 WHERE user_id = ?", (user_id,))
#         await db.commit()

# async def get_warnings(user_id: int) -> int:
#     async with aiosqlite.connect(DB_NAME) as db:
#         async with db.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,)) as cursor:
#             row = await cursor.fetchone()
#             return row[0] if row else 0
