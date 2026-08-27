"""
Конфигурация бота.

Все секретные данные (токены) берутся из переменных окружения — обычно через
файл .env — и НИКОГДА не хранятся прямо в коде. Так безопаснее: код можно
свободно показывать, выкладывать на GitHub и т.д., а секреты остаются только
у вас в .env, который в git не попадает (см. .gitignore).

Как задать переменные окружения:
1. Скопируйте .env.example в .env
2. Впишите в .env свой токен бота, токен Hugging Face и свой Telegram ID
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = {
    int(chunk.strip())
    for chunk in _admin_ids_raw.split(",")
    if chunk.strip().lstrip("-").isdigit()
}

DB_PATH = os.getenv("DB_PATH", "bot_data.db")

# Лимиты, о которых просил пользователь: длинные видео/аудио резать не будем,
# но зададим потолок в 5 минут, как указано в ТЗ.
MAX_MEDIA_DURATION_SECONDS = 5 * 60

# Обычный (не self-hosted) Telegram Bot API не позволяет боту скачивать файлы
# тяжелее 20 МБ. Это ограничение самого Telegram, а не этого кода.
MAX_TELEGRAM_DOWNLOAD_BYTES = 20 * 1024 * 1024


def validate() -> None:
    """Проверяет, что обязательные переменные окружения заданы, до запуска бота."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not HF_TOKEN:
        missing.append("HF_TOKEN")

    if missing:
        print(
            "Не заданы обязательные переменные окружения: " + ", ".join(missing) + "\n"
            "Создайте файл .env на основе .env.example и укажите там свои значения.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not ADMIN_IDS:
        print(
            "Внимание: ADMIN_IDS не задан — кнопка админ-статистики никому не "
            "будет показана. Укажите свой Telegram ID в .env, если хотите видеть статистику.",
            file=sys.stderr,
        )
