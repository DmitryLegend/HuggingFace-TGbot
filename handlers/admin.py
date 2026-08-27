import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import database as db
from config import ADMIN_IDS
from keyboards import back_to_menu_keyboard
from tasks import TASKS

logger = logging.getLogger(__name__)
router = Router(name="admin")


def format_stats(stats: dict) -> str:
    lines = [
        "📊 <b>Статистика бота</b>",
        "",
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>",
        f"📨 Всего запросов: <b>{stats['total_requests']}</b>",
        f"📅 Запросов сегодня: <b>{stats['today_count']}</b> "
        f"(активных пользователей сегодня: {stats['active_today']})",
        "",
        "<b>Что чаще всего делают:</b>",
    ]

    total = stats["total_requests"] or 1
    if not stats["by_task"]:
        lines.append("Пока нет данных — бот ещё не использовали.")
    for task_key, count in stats["by_task"]:
        title = TASKS[task_key].title if task_key in TASKS else task_key
        pct = count / total * 100
        filled = round(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        lines.append(f"{title} — {count} ({pct:.1f}%) {bar}")

    return "\n".join(lines)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Эта команда доступна только администратору бота.")
        return
    stats = await db.get_stats()
    await message.answer(format_stats(stats), reply_markup=back_to_menu_keyboard())


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Недоступно", show_alert=True)
        return
    stats = await db.get_stats()
    await callback.message.edit_text(format_stats(stats), reply_markup=back_to_menu_keyboard())
    await callback.answer()
