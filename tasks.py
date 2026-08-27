"""
Единое описание всех 10 "нейронок"/задач бота.

Здесь и только здесь описаны кнопки, подписи и тип ожидаемого ввода для
каждой задачи. keyboards.py, handlers/* и hf_client.py используют этот
словарь, чтобы не дублировать одно и то же в разных местах.

Чтобы добавить/изменить задачу — правьте только этот файл и hf_client.py
(там, где указаны конкретные модели Hugging Face).
"""

from dataclasses import dataclass
from enum import Enum


class InputType(Enum):
    TEXT = "text"    # ждём текстовое сообщение
    PHOTO = "photo"  # ждём фотографию
    AUDIO = "audio"  # ждём голосовое/аудио/видео (до 5 минут)


class OutputKind(Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"


@dataclass(frozen=True)
class TaskInfo:
    key: str
    title: str          # текст на кнопке
    prompt: str         # что попросить у пользователя после выбора кнопки
    input_type: InputType
    output_kind: OutputKind
    chat_action: str    # имя classmethod у aiogram ChatActionSender (typing/upload_photo/...)


TASKS: dict[str, TaskInfo] = {
    "chat": TaskInfo(
        key="chat",
        title="💬 Текстовый чат",
        prompt="✍️ Напишите вопрос или сообщение — отвечу текстом.",
        input_type=InputType.TEXT,
        output_kind=OutputKind.TEXT,
        chat_action="typing",
    ),
    "code": TaskInfo(
        key="code",
        title="💻 Написать код",
        prompt="✍️ Опишите задачу: на каком языке и что должен делать код.",
        input_type=InputType.TEXT,
        output_kind=OutputKind.TEXT,
        chat_action="typing",
    ),
    "image": TaskInfo(
        key="image",
        title="🎨 Сгенерировать фото",
        prompt="🖌 Опишите изображение, которое нужно нарисовать.",
        input_type=InputType.TEXT,
        output_kind=OutputKind.PHOTO,
        chat_action="upload_photo",
    ),
    "image_caption": TaskInfo(
        key="image_caption",
        title="🖼 Распознать фото",
        prompt="📷 Пришлите фотографию — опишу, что на ней изображено.",
        input_type=InputType.PHOTO,
        output_kind=OutputKind.TEXT,
        chat_action="typing",
    ),
    "video": TaskInfo(
        key="video",
        title="🎬 Сгенерировать видео",
        prompt="🎬 Опишите сюжет видео. Генерация видео — самая долгая операция, наберитесь терпения (может занять пару минут).",
        input_type=InputType.TEXT,
        output_kind=OutputKind.VIDEO,
        chat_action="upload_video",
    ),
    "music": TaskInfo(
        key="music",
        title="🎵 Сгенерировать музыку",
        prompt="🎧 Опишите музыку: жанр, настроение, инструменты (например: «спокойный лоу-фай с пианино»).",
        input_type=InputType.TEXT,
        output_kind=OutputKind.AUDIO,
        chat_action="upload_voice",
    ),
    "tts": TaskInfo(
        key="tts",
        title="🗣 Озвучить текст",
        prompt="⌨️ Введите текст, который нужно превратить в речь.",
        input_type=InputType.TEXT,
        output_kind=OutputKind.AUDIO,
        chat_action="upload_voice",
    ),
    "stt": TaskInfo(
        key="stt",
        title="🎧 Распознать речь",
        prompt="🎤 Пришлите голосовое сообщение, аудиофайл или видео (до 5 минут) — переведу речь в текст.",
        input_type=InputType.AUDIO,
        output_kind=OutputKind.TEXT,
        chat_action="typing",
    ),
    "summarize": TaskInfo(
        key="summarize",
        title="📝 Пересказать текст",
        prompt="📄 Пришлите текст сообщением или файлом (.txt / .pdf / .docx) — сделаю краткое содержание.",
        input_type=InputType.TEXT,
        output_kind=OutputKind.TEXT,
        chat_action="typing",
    ),
    "translate": TaskInfo(
        key="translate",
        title="🌐 Перевести текст",
        prompt="🔤 Пришлите текст на русском или английском языке — переведу на другой.",
        input_type=InputType.TEXT,
        output_kind=OutputKind.TEXT,
        chat_action="typing",
    ),
}

TASK_ORDER = list(TASKS.keys())
