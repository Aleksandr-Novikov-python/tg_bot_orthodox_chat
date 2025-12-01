import asyncio, tempfile, os

from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import FSInputFile

from config.config_app import FFMPEG_BIN, TTS_LANGUAGE
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

# --- Модерация сообщений ---
@graup_moders.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}) & ~F.text.startswith("/")
)
async def group_moderation(message: types.Message):
    if await is_bad_word(message, message.text) or await is_bad_word(message, message.caption):
        user_id = message.from_user.id
        username = message.from_user.full_name

        try:
            await message.delete()
        except Exception as e:
            await send_log(message.bot, f"Не удалось удалить сообщение: {e}")

        member = await message.chat.get_member(user_id)

        # --- Если админ ---
        if member.status in ("creator", "administrator"):
            remind_text = f"{username}, даже админам стоит следить за языком."
            ok = await send_voice(message, remind_text)
            if not ok:
                await message.answer(remind_text)
            await send_log(message.bot, f"🛡 Админ {username} ({user_id}) получил голосовое напоминание.")
            return

        # --- Если обычный пользователь ---
        warnings = await add_warning(user_id)

        if warnings >= 3:
            try:
                await message.bot.ban_chat_member(message.chat.id, user_id)
                await send_log(message.bot, f"🚫 {username} ({user_id}) забанен за 3 нарушения")
            except Exception as e:
                await send_log(message.bot, f"Не удалось забанить {username}: {e}")
            await reset_warnings(user_id)
        else:
            warn_text = (
                f"{username}, это предупреждение номер {warnings} из трёх. "
                "Пожалуйста, давай общаться уважительно и следить за языком."
            )
            ok = await send_voice(message, warn_text)
            if not ok:
                await message.answer(f"⚠️ {warn_text}")
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





