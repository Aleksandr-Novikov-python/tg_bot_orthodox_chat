from aiogram import Router, types
from aiogram.filters import Command, CommandObject

from config.config_app import ADMIN_IDS
from database.db import reset_warnings
from services.logger import send_log

admin = Router()

@admin.message(Command("myid"))
async def myid_handler(message: types.Message):
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")

# --- ХЕНДЛЕРЫ: АДМИН КОМАНДЫ ---

@admin .message(Command("ban"))
async def admin_ban(message: types.Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        return

    # Логика: /ban (реплай) или /ban ID
    target_id = None
    reason = "Администратор решил так."
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif command.args:
        try:
            target_id = int(command.args.split()[0])
        except ValueError:
            await message.reply("Неверный ID.")
            return
    
    if target_id:
        try:
            await message.bot.ban_chat_member(message.chat.id, target_id)
            await message.reply(f"Пользователь {target_id} забанен.")
            await send_log(f"👮‍♂️ Админ {message.from_user.first_name} забанил {target_id} вручную.")
        except Exception as e:
            await message.reply(f"Ошибка бана: {e}")
    else:
        await message.reply("Используйте команду в ответ на сообщение или укажите ID: /ban 12345")

@admin .message(Command("unban"))
async def admin_unban(message: types.Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        return

    if not command.args:
        await message.reply("Укажите ID пользователя: /unban 12345")
        return

    try:
        target_id = int(command.args.split()[0])
        await message.bot.unban_chat_member(message.chat.id, target_id, only_if_banned=True)
        await reset_warnings(target_id) # Сброс варнов при разбане
        await message.reply(f"Пользователь {target_id} разбанен.")
        await send_log(f"🕊 Админ {message.from_user.first_name} разбанил {target_id}.")
    except Exception as e:
        await message.reply(f"Ошибка разбана: {e}")
