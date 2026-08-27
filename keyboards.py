from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from tasks import TASK_ORDER, TASKS


def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Главное меню: по 2 кнопки в ряд на 10 задач + отдельная кнопка админ-статистики."""
    builder = InlineKeyboardBuilder()
    for key in TASK_ORDER:
        builder.button(text=TASKS[key].title, callback_data=f"task:{key}")
    builder.adjust(2)

    if user_id in ADMIN_IDS:
        builder.row(InlineKeyboardButton(text="📊 Статистика (админ)", callback_data="admin:stats"))

    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="nav:cancel")
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Главное меню", callback_data="nav:menu")
    return builder.as_markup()
