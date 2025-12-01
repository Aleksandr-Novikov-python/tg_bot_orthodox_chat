import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен от @BotFather
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))    # ID канала для логов (должен начинаться с -100)
GROUP_CHAT_LINK = os.getenv("GROUP_CHAT_LINK") # Ссылка на твою группу
ADMIN_IDS = [int(os.getenv("ADMIN_IDS", "0"))] # ID администраторов (числа)
DB_NAME = os.getenv("DB_NAME")
TTS_LANGUAGE = "ru"
FFMPEG_BIN = "ffmpeg"