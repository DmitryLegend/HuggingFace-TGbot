"""
Вспомогательные функции для работы с файлами, которые присылают пользователи:
- .zip — показываем содержимое архива
- .txt / .pdf / .docx — вытаскиваем текст (чтобы можно было, например,
  прислать документ на "Пересказать текст" вместо того чтобы копипастить)
- видео -> звуковая дорожка (для распознавания речи через ffmpeg)
"""

import logging
import os
import subprocess
import tempfile
import zipfile
from io import BytesIO

from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_EXTRACTED_TEXT_CHARS = 8000  # защита от огромных документов


def list_zip_contents(file_bytes: bytes, max_items: int = 30) -> str:
    """Возвращает текстовое описание содержимого zip-архива."""
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile:
        return "⚠️ Не удалось открыть архив — возможно, он повреждён или это не zip-файл."

    if not infos:
        return "📦 Архив пустой."

    lines = [f"📦 В архиве {len(infos)} файл(ов):", ""]
    for info in infos[:max_items]:
        if info.is_dir():
            continue
        size_kb = info.file_size / 1024
        lines.append(f"• {info.filename} ({size_kb:.1f} КБ)")
    if len(infos) > max_items:
        lines.append(f"… и ещё {len(infos) - max_items} файл(ов)")
    return "\n".join(lines)


def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")[:MAX_EXTRACTED_TEXT_CHARS]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text_parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(text_parts)[:MAX_EXTRACTED_TEXT_CHARS]


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    text_parts = [p.text for p in document.paragraphs]
    return "\n".join(text_parts)[:MAX_EXTRACTED_TEXT_CHARS]


def extract_text_from_document(file_bytes: bytes, extension: str) -> str:
    extension = extension.lower()
    if extension == ".txt":
        return extract_text_from_txt(file_bytes)
    if extension == ".pdf":
        return extract_text_from_pdf(file_bytes)
    if extension == ".docx":
        return extract_text_from_docx(file_bytes)
    raise ValueError(f"Неподдерживаемое расширение: {extension}")


def extract_audio_from_video(video_bytes: bytes) -> bytes:
    """
    Достаёт звуковую дорожку из видео в WAV с помощью ffmpeg (должен быть
    установлен в системе: `sudo apt install ffmpeg`).

    Если ffmpeg недоступен — выбрасывает исключение, и вызывающий код должен
    сам решить, что делать (например, отправить видео как есть — часть
    ASR-моделей на стороне Hugging Face тоже умеют декодировать видео).
    """
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
        video_file.write(video_bytes)
        video_path = video_file.name

    audio_path = video_path + ".wav"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                audio_path,
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        with open(audio_path, "rb") as f:
            return f.read()
    finally:
        for path in (video_path, audio_path):
            if os.path.exists(path):
                os.remove(path)
