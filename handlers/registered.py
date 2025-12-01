from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatType
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

import asyncio
import tempfile
import os

from config.config_app import FFMPEG_BIN, GROUP_CHAT_LINK, TTS_LANGUAGE
from database.db import is_registered
from services.logger import send_log

registered = Router()



WELCOME_TEXT = "Рад тебя видеть снова, {name}! Добро пожаловать в православный чат знакомств."
REGISTER_PROMPT = (
    "Привет! Похоже, ты ещё не зарегистрирован. "
    "Чтобы присоединиться к нашему православному сообществу, нажми /register."
)

# GROUP_LINK = "https://t.me/your_group_link"  # <-- сюда вставь ссылку на группу

# --- Вспомогательные функции ---
async def synthesize_voice(text: str, lang: str = "ru") -> str | None:
    try:
        from gtts import gTTS
        fd, mp3_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        gTTS(text=text, lang=lang).save(mp3_path)
        return mp3_path
    except Exception as e:
        await send_log(None, f"TTS error: {e}")
        return None

async def convert_to_ogg(mp3_path: str) -> str | None:
    if not mp3_path or not os.path.exists(mp3_path):
        return None
    fd, ogg_path = tempfile.mkstemp(suffix=".ogg")
    os.close(fd)
    cmd = [FFMPEG_BIN, "-y", "-i", mp3_path, "-ac", "1", "-ar", "48000", "-c:a", "libopus", ogg_path]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
                                                    stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if os.path.getsize(ogg_path) < 1024:
            return None
        return ogg_path
    except Exception as e:
        await send_log(None, f"FFmpeg error: {e}")
        return None

async def send_voice(message: types.Message, text: str) -> bool:
    mp3 = await synthesize_voice(text, TTS_LANGUAGE)
    ogg = await convert_to_ogg(mp3) if mp3 else None
    try:
        if ogg and os.path.exists(ogg):
            await message.answer_voice(FSInputFile(ogg))
            return True
        return False
    finally:
        for f in (mp3, ogg):
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

# --- Хендлер /start ---
@registered.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type != ChatType.PRIVATE:
        return

    user_id = message.from_user.id
    name = message.from_user.full_name

    try:
        is_reg = await is_registered(user_id)
    except Exception as e:
        await send_log(message.bot, f"Ошибка проверки регистрации: {e}")
        is_reg = False

    if is_reg:
        text = WELCOME_TEXT.format(name=name)
        ok = await send_voice(message, text)
        if not ok:
            await message.answer(text)

        # Добавляем inline‑кнопку для перехода в группу
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Перейти в группу", url=GROUP_CHAT_LINK)]
            ]
        )
        await message.answer("👉 Нажми, чтобы войти в группу:", reply_markup=kb)

    else:
        ok = await send_voice(message, REGISTER_PROMPT)
        if not ok:
            await message.answer(REGISTER_PROMPT)




# from aiogram import F, Router, types
# from aiogram.filters import CommandStart
# from aiogram.enums import ChatType
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# from config.config_app import GROUP_CHAT_LINK
# from database.db import is_registered, register_user_db
# from services.logger import send_log

# registered = Router()

# #--- ХЕНДЛЕРЫ: ЛИЧНЫЕ СООБЩЕНИЯ (РЕГИСТРАЦИЯ) ---

# @registered.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
# async def cmd_start(message: types.Message):
#     user_id = message.from_user.id
#     username = message.from_user.username or "Unknown"

#     if await is_registered(user_id):
#         # Если уже зарегистрирован -> показываем ссылку
#         await send_log(message.bot, f"Пользователь {username} ({user_id}) авторизовался (повторно).")
#         kb = InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="💬 Перейти в чат группы", url=GROUP_CHAT_LINK)]
#         ])
#         await message.answer(f"С возвращением, {message.from_user.first_name}! Вы уже авторизованы.", reply_markup=kb)
#     else:
#         # Если нет -> кнопка регистрации
#         kb = InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="register_me")]
#         ])
#         await message.answer("Добро пожаловать! Для доступа к группе необходимо пройти регистрацию.", reply_markup=kb)

# @registered.callback_query(F.data == "register_me")
# async def process_registration(callback: types.CallbackQuery):
#     user_id = callback.from_user.id
#     username = callback.from_user.username or "Unknown"
    
#     await register_user_db(user_id, username)
#     await send_log(callback.bot, f"🆕 Новый пользователь зарегистрирован: {username} ({user_id})")
    
#     kb = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="💬 Вступить в группу", url=GROUP_CHAT_LINK)]
#     ])
    
#     await callback.message.edit_text(
#         "✅ Регистрация прошла успешно! Теперь вы можете вступить в наш чат.",
#         reply_markup=kb
#     )
