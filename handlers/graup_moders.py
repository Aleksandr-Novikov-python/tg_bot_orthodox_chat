from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from services.logger import send_log
from database.db import add_warning, reset_warnings, get_warnings

graup_moders = Router()

def load_bad_words(file_path: str = "bad_words.txt") -> list[str]:
    """Загружает список запрещённых слов из файла"""
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return [line.strip().lower() for line in f if line.strip()]

BAD_WORDS = load_bad_words()

async def is_bad_word(message: Message, text: str) -> bool:
    """Проверяет текст на наличие запрещённых слов"""
    if not text:
        return False
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            await send_log(message.bot, f"⚠️ Найдено запрещённое слово: {word} в сообщении {text}")
            return True
    return False

# --- Модерация сообщений ---
@graup_moders.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}) & ~F.text.startswith("/")
)
async def group_moderation(message: types.Message):
    if await is_bad_word(message, message.text) or await is_bad_word(message, message.caption):
        user_id = message.from_user.id
        username = message.from_user.full_name

        member = await message.chat.get_member(user_id)
        if member.status in ("creator", "administrator"):
            try:
                await message.delete()
                await send_log(message.bot, f"🛡 Админ {username} ({user_id}) написал запрещённое слово. Сообщение удалено.")
            except Exception as e:
                await send_log(message.bot, f"Не удалось удалить сообщение админа: {e}")
            return

        try:
            await message.delete()
        except Exception as e:
            await send_log(message.bot, f"Не удалось удалить сообщение: {e}")

        warnings = await add_warning(user_id)

        if warnings >= 3:
            try:
                await message.bot.ban_chat_member(message.chat.id, user_id)
                await send_log(message.bot, f"🚫 {username} ({user_id}) забанен за 3 нарушения")
            except Exception as e:
                await send_log(message.bot, f"Не удалось забанить {username}: {e}")
            await reset_warnings(user_id)
        else:
            await message.answer(f"⚠️ {username}, предупреждение {warnings}/3.")
            await send_log(message.bot, f"⚠️ {username} ({user_id}) получил предупреждение {warnings}/3")

# --- Команда /warns ---
@graup_moders.message(Command("warns", ignore_case=True))
async def check_warnings(message: types.Message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ("creator", "administrator"):
        await message.answer("⛔ Только админы могут использовать эту команду.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.full_name
    else:
        user_id = message.from_user.id
        username = message.from_user.full_name

    warnings = await get_warnings(user_id)
    if not warnings:
        await message.answer(f"ℹ️ У пользователя {username} ({user_id}) нет предупреждений.")
    else:
        await message.answer(f"ℹ️ У пользователя {username} ({user_id}) {warnings}/3 предупреждений.")

# --- Команда /resetwarns ---
@graup_moders.message(Command("resetwarns", ignore_case=True))
async def reset_user_warnings(message: types.Message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ("creator", "administrator"):
        await message.answer("⛔ Только админы могут использовать эту команду.")
        return

    if not message.reply_to_message:
        await message.answer("Использование: /resetwarns (ответом на сообщение пользователя)")
        return

    user_id = message.reply_to_message.from_user.id
    username = message.reply_to_message.from_user.full_name

    await reset_warnings(user_id)
    await message.answer(f"✅ Предупреждения пользователя {username} ({user_id}) сброшены.")
    await send_log(message.bot, f"♻️ Админ {message.from_user.full_name} сбросил предупреждения у {username} ({user_id})")


# from aiogram import F, Router, types
# from aiogram.enums import ChatType
# from aiogram.types import Message
# from aiogram.filters import Command

# from services.logger import send_log
# from database.db import add_warning, reset_warnings, get_warnings

# graup_moders = Router()

# def load_bad_words(file_path: str = "bad_words.txt") -> list[str]:
#     """Загружает список запрещённых слов из файла"""
#     with open(file_path, "r", encoding="utf-8-sig") as f:
#         return [line.strip().lower() for line in f if line.strip()]

# BAD_WORDS = load_bad_words()

# async def is_bad_word(message: Message, text: str) -> bool:
#     """Проверяет текст на наличие запрещённых слов"""
#     if not text:
#         return False
#     text_lower = text.lower()
#     for word in BAD_WORDS:
#         if word in text_lower:
#             await send_log(message.bot, f"⚠️ Найдено запрещённое слово: {word} в сообщении {text}")
#             return True
#     return False

# @graup_moders.message(
#     F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}) & ~F.text.startswith("/")
# )
# async def group_moderation(message: types.Message):
#     if await is_bad_word(message, message.text) or await is_bad_word(message, message.caption):
#         user_id = message.from_user.id
#         username = message.from_user.full_name

#         # Проверяем права пользователя
#         member = await message.chat.get_member(user_id)
#         if member.status in ("creator", "administrator"):
#             try:
#                 await message.delete()
#                 await send_log(message.bot, f"🛡 Админ/владелец {username} ({user_id}) написал запрещённое слово. Сообщение удалено.")
#             except Exception as e:
#                 await send_log(message.bot, f"Не удалось удалить сообщение админа: {e}")
#             return

#         # Обычный пользователь → варны и бан
#         try:
#             await message.delete()
#         except Exception as e:
#             await send_log(message.bot, f"Не удалось удалить сообщение: {e}")

#         warnings = await add_warning(user_id)

#         if warnings >= 3:
#             try:
#                 await message.bot.ban_chat_member(message.chat.id, user_id)
#                 await send_log(message.bot, f"🚫 {username} ({user_id}) забанен за 3 нарушения")
#             except Exception as e:
#                 await send_log(message.bot, f"Не удалось забанить {username}: {e}")
#             await reset_warnings(user_id)
#         else:
#             await message.answer(f"⚠️ {username}, предупреждение {warnings}/3.")
#             await send_log(message.bot, f"⚠️ {username} ({user_id}) получил предупреждение {warnings}/3")

# # --- Команда /warns для админов ---
# @graup_moders.message(Command("warns", ignore_case=True))
# async def check_warnings(message: types.Message):
#     """Позволяет админам проверять количество предупреждений у пользователя"""
#     member = await message.chat.get_member(message.from_user.id)
#     if member.status not in ("creator", "administrator"):
#         await message.answer("⛔ Только админы могут использовать эту команду.")
#         return

#     # Если есть реплай → проверяем того пользователя
#     if message.reply_to_message:
#         user_id = message.reply_to_message.from_user.id
#         username = message.reply_to_message.from_user.full_name
#     else:
#         # Если нет реплая → проверяем самого себя
#         user_id = message.from_user.id
#         username = message.from_user.full_name

#     warnings = await get_warnings(user_id)

#     if warnings is None or warnings == 0:
#         await message.answer(f"ℹ️ У пользователя {username} ({user_id}) нет предупреждений.")
#     else:
#         await message.answer(f"ℹ️ У пользователя {username} ({user_id}) {warnings}/3 предупреждений.")



