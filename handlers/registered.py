from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


from config.config_app import GROUP_CHAT_LINK
from database.db import is_registered, register_user_db
from services.logger import send_log

registered = Router()

# --- ХЕНДЛЕРЫ: ЛИЧНЫЕ СООБЩЕНИЯ (РЕГИСТРАЦИЯ) ---

@registered.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    if await is_registered(user_id):
        # Если уже зарегистрирован -> показываем ссылку
        await send_log(message.bot, f"Пользователь {username} ({user_id}) авторизовался (повторно).")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Перейти в чат группы", url=GROUP_CHAT_LINK)]
        ])
        await message.answer(f"С возвращением, {message.from_user.first_name}! Вы уже авторизованы.", reply_markup=kb)
    else:
        # Если нет -> кнопка регистрации
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="register_me")]
        ])
        await message.answer("Добро пожаловать! Для доступа к группе необходимо пройти регистрацию.", reply_markup=kb)

@registered.callback_query(F.data == "register_me")
async def process_registration(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Unknown"
    
    await register_user_db(user_id, username)
    await send_log(callback.bot, f"🆕 Новый пользователь зарегистрирован: {username} ({user_id})")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Вступить в группу", url=GROUP_CHAT_LINK)]
    ])
    
    await callback.message.edit_text(
        "✅ Регистрация прошла успешно! Теперь вы можете вступить в наш чат.",
        reply_markup=kb
    )
