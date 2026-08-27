from aiogram import F, Router
from aiogram.types import Message

from keyboards import main_menu_keyboard

router = Router(name="fallback")

# ВАЖНО: этот роутер должен подключаться в main.py ПОСЛЕДНИМ.
# Он ловит любое сообщение, которое не подошло ни одному из обработчиков
# выше (например, пользователь написал текст, не выбрав действие в меню).


@router.message(F.text, ~F.text.startswith("/"))
async def fallback_text(message: Message) -> None:
    await message.answer(
        "Не совсем понял 🙂 Выберите действие из меню:",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message()
async def fallback_any(message: Message) -> None:
    """Ловит всё остальное: стикеры, геолокацию, контакты и т.п."""
    await message.answer(
        "Такой тип сообщений пока не обрабатываю без выбранного действия. Выберите пункт меню:",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
