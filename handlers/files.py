import logging
import os
from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

import database as db
import hf_client
from config import MAX_MEDIA_DURATION_SECONDS, MAX_TELEGRAM_DOWNLOAD_BYTES
from handlers.generation import run_text_task
from keyboards import back_to_menu_keyboard
from states import GenStates
from tasks import TASKS, InputType
from utils import extract_audio_from_video, extract_text_from_document, list_zip_contents

logger = logging.getLogger(__name__)
router = Router(name="files")

SUPPORTED_TEXT_EXTENSIONS = (".txt", ".pdf", ".docx")


async def _download(bot, file_id: str) -> bytes:
    tg_file = await bot.get_file(file_id)
    buf = BytesIO()
    await bot.download_file(tg_file.file_path, destination=buf)
    return buf.getvalue()


@router.message(GenStates.waiting_for_input, F.photo)
async def handle_photo_input(message: Message, state: FSMContext, bot) -> None:
    data = await state.get_data()
    task_key = data.get("task")
    task = TASKS.get(task_key)

    if not task or task.input_type != InputType.PHOTO:
        await message.answer("Это действие не принимает фото. Подсказка — в сообщении выше. /menu — открыть меню.")
        return

    photo = message.photo[-1]
    if photo.file_size and photo.file_size > MAX_TELEGRAM_DOWNLOAD_BYTES:
        await message.answer("⚠️ Файл слишком большой: обычный Telegram Bot API умеет скачивать файлы только до 20 МБ.")
        return

    image_bytes = await _download(bot, photo.file_id)
    await db.log_request(message.from_user.id, task_key)

    try:
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            caption = await hf_client.caption_image(image_bytes)
        await message.answer(f"🖼 {caption}", reply_markup=back_to_menu_keyboard())
    except Exception:
        logger.exception("Ошибка при распознавании фото")
        await message.answer("😔 Не удалось обработать фото. Попробуйте ещё раз позже.", reply_markup=back_to_menu_keyboard())


@router.message(GenStates.waiting_for_input, F.voice | F.audio | F.video | F.video_note)
async def handle_audio_video_input(message: Message, state: FSMContext, bot) -> None:
    data = await state.get_data()
    task_key = data.get("task")
    task = TASKS.get(task_key)

    if not task or task.input_type != InputType.AUDIO:
        await message.answer("Это действие ожидает другой тип данных. Подсказка — в сообщении выше. /menu — открыть меню.")
        return

    media = message.voice or message.audio or message.video or message.video_note
    duration = getattr(media, "duration", 0) or 0
    if duration > MAX_MEDIA_DURATION_SECONDS:
        await message.answer("⚠️ Максимальная длительность — 5 минут. Пришлите файл покороче.")
        return
    if media.file_size and media.file_size > MAX_TELEGRAM_DOWNLOAD_BYTES:
        await message.answer("⚠️ Файл слишком большой: обычный Telegram Bot API умеет скачивать файлы только до 20 МБ.")
        return

    raw_bytes = await _download(bot, media.file_id)
    await db.log_request(message.from_user.id, task_key)

    is_video = bool(message.video or message.video_note)
    audio_bytes = raw_bytes
    if is_video:
        try:
            audio_bytes = extract_audio_from_video(raw_bytes)
        except Exception:
            logger.warning("ffmpeg недоступен или не смог обработать видео — пробую отправить как есть")
            audio_bytes = raw_bytes

    try:
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            text = await hf_client.speech_to_text(audio_bytes)
        await message.answer(f"📝 Распознанный текст:\n\n{text}", reply_markup=back_to_menu_keyboard())
    except Exception:
        logger.exception("Ошибка распознавания речи")
        await message.answer(
            "😔 Не удалось распознать речь. Убедитесь, что в файле есть звук, и попробуйте ещё раз.",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(F.document)
async def handle_document(message: Message, state: FSMContext, bot) -> None:
    """
    Универсальный обработчик документов:
    - .zip -> показываем список файлов внутри
    - .txt/.pdf/.docx, когда активна текстовая задача -> вытаскиваем текст
      и обрабатываем его так же, как если бы пользователь его напечатал
    - всё остальное -> вежливо подтверждаем получение и просим выбрать действие
    """
    doc = message.document
    filename = doc.file_name or "file"
    extension = os.path.splitext(filename)[1].lower()

    if doc.file_size and doc.file_size > MAX_TELEGRAM_DOWNLOAD_BYTES:
        await message.answer("⚠️ Файл слишком большой: обычный Telegram Bot API умеет скачивать файлы только до 20 МБ.")
        return

    file_bytes = await _download(bot, doc.file_id)

    if extension == ".zip":
        await message.answer(list_zip_contents(file_bytes))
        return

    data = await state.get_data()
    task_key = data.get("task")
    task = TASKS.get(task_key) if task_key else None

    if task and task.input_type == InputType.TEXT and extension in SUPPORTED_TEXT_EXTENSIONS:
        try:
            text = extract_text_from_document(file_bytes, extension)
        except Exception:
            logger.exception("Ошибка извлечения текста из файла %s", filename)
            await message.answer("⚠️ Не удалось прочитать файл.")
            return

        if not text.strip():
            await message.answer("⚠️ В файле не нашлось текста.")
            return

        await run_text_task(message, bot, task_key, text)
        return

    size_kb = (doc.file_size or 0) / 1024
    await message.answer(
        f"📎 Получен файл «{filename}» ({size_kb:.1f} КБ).\n\n"
        "Чтобы я его обработал, сначала выберите действие в меню: /menu\n"
        "(документы .txt/.pdf/.docx можно прислать вместо текста для задач "
        "«Пересказать текст», «Перевести текст», «Текстовый чат» и «Написать код»)"
    )
