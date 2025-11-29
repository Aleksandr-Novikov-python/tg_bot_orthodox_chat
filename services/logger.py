import logging
import os
from datetime import datetime
from aiogram import Bot
from aiogram.enums import ParseMode

LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

async def send_log(bot: Bot, text: str):
    """Отправляет сообщение в спец канал и пишет в консоль"""
    logging.info(f"LOG: {text}")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await bot.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=f"📝 <b>LOG [{timestamp}]</b>\n{text}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Не удалось отправить лог: {e}", exc_info=True)
