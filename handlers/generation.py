import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message
from aiogram.utils.chat_action import ChatActionSender

import database as db
import hf_client
from keyboards import back_to_menu_keyboard
from states import GenStates
from tasks import TASKS, InputType, OutputKind

logger = logging.getLogger(__name__)
router = Router(name="generation")

# Задача -> функция в hf_client, вызываемая с одним строковым аргументом (текстом).
# Сюда попадают все задачи, для которых input_type == TEXT.
TEXT_TASK_FUNCS = {
    "chat": hf_client.chat_reply,
    "code": hf_client.generate_code,
    "image": hf_client.generate_image,
    "video": hf_client.generate_video,
    "music": hf_client.generate_music,
    "tts": hf_client.text_to_speech,
    "summarize": hf_client.summarize_text,
    "translate": hf_client.translate_text,
}

RESULT_CAPTION = "✅ Готово! Пришлите новый запрос или вернитесь в меню."

FRIENDLY_ERROR = (
    "😔 Не удалось выполнить запрос.\n\n"
    "Скорее всего модель на Hugging Face сейчас недоступна, перегружена, "
    "или закончились бесплатные кредиты аккаунта. Попробуйте ещё раз через "
    "минуту-другую или выберите другое действие."
)


async def send_result(message: Message, output_kind: OutputKind, result) -> None:
    if output_kind == OutputKind.TEXT:
        text = result if isinstance(result, str) else str(result)
        text = text.strip() or "(пустой ответ модели)"
        for i in range(0, len(text), 4000):
            await message.answer(text[i : i + 4000])
        await message.answer(RESULT_CAPTION, reply_markup=back_to_menu_keyboard())
    elif output_kind == OutputKind.PHOTO:
        await message.answer_photo(
            BufferedInputFile(result, filename="result.png"),
            caption=RESULT_CAPTION,
            reply_markup=back_to_menu_keyboard(),
        )
    elif output_kind == OutputKind.VIDEO:
        await message.answer_video(
            BufferedInputFile(result, filename="result.mp4"),
            caption=RESULT_CAPTION,
            reply_markup=back_to_menu_keyboard(),
        )
    elif output_kind == OutputKind.AUDIO:
        await message.answer_audio(
            BufferedInputFile(result, filename="result.wav"),
            caption=RESULT_CAPTION,
            reply_markup=back_to_menu_keyboard(),
        )


async def run_text_task(message: Message, bot, task_key: str, user_text: str) -> None:
    """Общая логика: показать нужный chat action, вызвать модель, отправить результат.

    Используется и из этого файла (когда пользователь просто написал текст),
    и из handlers/files.py (когда текст был извлечён из .txt/.pdf/.docx файла).
    """
    task = TASKS[task_key]
    func = TEXT_TASK_FUNCS[task_key]

    await db.log_request(message.from_user.id, task_key)

    sender_factory = getattr(ChatActionSender, task.chat_action)
    try:
        async with sender_factory(bot=bot, chat_id=message.chat.id):
            result = await func(user_text)
        await send_result(message, task.output_kind, result)
    except Exception:
        logger.exception("Ошибка Hugging Face при выполнении задачи %s", task_key)
        await message.answer(FRIENDLY_ERROR, reply_markup=back_to_menu_keyboard())


@router.message(GenStates.waiting_for_input, F.text, ~F.text.startswith("/"))
async def handle_text_input(message: Message, state: FSMContext, bot) -> None:
    data = await state.get_data()
    task_key = data.get("task")
    task = TASKS.get(task_key)

    if not task or task.input_type != InputType.TEXT:
        await message.answer("Это действие ожидает другой тип данных (см. подсказку выше). /menu — открыть меню.")
        return

    await run_text_task(message, bot, task_key, message.text)
