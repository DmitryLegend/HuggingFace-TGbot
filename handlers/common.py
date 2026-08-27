import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards import cancel_keyboard, main_menu_keyboard
from states import GenStates
from tasks import TASKS

logger = logging.getLogger(__name__)
router = Router(name="common")

WELCOME_TEXT = (
    "👋 Привет! Я бот с доступом к 10 нейросетям для разных задач: "
    "текст, код, изображения, видео, музыка, озвучка, распознавание речи, "
    "пересказ и перевод текста.\n\n"
    "Выберите, что нужно сделать:"
)

MENU_TEXT = "📋 Главное меню. Выберите действие:"

HELP_TEXT = (
    "ℹ️ <b>Как пользоваться ботом</b>\n\n"
    "1. Нажмите на кнопку с нужным действием.\n"
    "2. Пришлите то, что бот попросит (текст, фото или голосовое/видео).\n"
    "3. Дождитесь ответа — во время генерации бот показывает "
    "статус «печатает…» / «отправляет фото» и т.п.\n\n"
    "Также я понимаю .zip-архивы (покажу список файлов) и .txt/.pdf/.docx "
    "документы (можно прислать вместо текста — например, для пересказа).\n\n"
    "Команды:\n"
    "/menu — главное меню\n"
    "/help — эта справка"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard(message.from_user.id))


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MENU_TEXT, reply_markup=main_menu_keyboard(message.from_user.id))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.callback_query(F.data == "nav:menu")
async def cb_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(MENU_TEXT, reply_markup=main_menu_keyboard(callback.from_user.id))
    await callback.answer()


@router.callback_query(F.data == "nav:cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Отменено. " + MENU_TEXT, reply_markup=main_menu_keyboard(callback.from_user.id))
    await callback.answer()


@router.callback_query(F.data.startswith("task:"))
async def cb_task_selected(callback: CallbackQuery, state: FSMContext) -> None:
    task_key = callback.data.split(":", 1)[1]
    task = TASKS.get(task_key)
    if not task:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    await state.set_state(GenStates.waiting_for_input)
    await state.update_data(task=task_key)
    await callback.message.edit_text(f"{task.title}\n\n{task.prompt}", reply_markup=cancel_keyboard())
    await callback.answer()
