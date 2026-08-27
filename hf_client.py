"""
Обёртка над Hugging Face Inference (huggingface_hub.AsyncInferenceClient) —
10 функций, по одной на каждую из 10 задач бота.

ВАЖНО про модели:
Hugging Face периодически меняет, какие модели доступны бесплатно через
Inference Providers (это не капризы, а особенность их инфраструктуры —
провайдеры-партнёры сами решают, какие модели держать "прогретыми").
Если какая-то модель перестанет отвечать — просто замените её ID в словаре
MODELS ниже на другую модель с такой же задачей (pipeline_tag) на
https://huggingface.co/models.

Бесплатный аккаунт Hugging Face даёт ограниченные ежемесячные кредиты на
Inference Providers. Генерация видео и музыки обычно "стоит" больше, чем
текст, так что именно на них кредиты закончатся быстрее всего.
"""

import re
from io import BytesIO

from huggingface_hub import AsyncInferenceClient

from config import HF_TOKEN

# Основной клиент — сам подбирает провайдера ("auto"), подходит для
# текста, картинок, распознавания и синтеза речи.
client = AsyncInferenceClient(api_key=HF_TOKEN)

# HF Inference (hf-inference) не хостит видео-модели — для text_to_video
# нужен провайдер, который их поддерживает (fal-ai — один из немногих,
# входит в бесплатные кредиты HF). Поэтому для видео — отдельный клиент.
video_client = AsyncInferenceClient(provider="fal-ai", api_key=HF_TOKEN)

MODELS = {
    "chat": "Qwen/Qwen2.5-7B-Instruct",
    "code": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "image": "black-forest-labs/FLUX.1-schnell",
    "image_caption": "Salesforce/blip-image-captioning-large",
    "video": "tencent/HunyuanVideo-1.5",
    "music": "facebook/musicgen-small",
    "tts": "facebook/mms-tts-rus",
    "stt": "openai/whisper-large-v3",
    "summarize": "facebook/bart-large-cnn",
    "translate_ru_en": "Helsinki-NLP/opus-mt-ru-en",
    "translate_en_ru": "Helsinki-NLP/opus-mt-en-ru",
}

_CYRILLIC_RE = re.compile(r"[а-яА-ЯёЁ]")


async def chat_reply(prompt: str) -> str:
    result = await client.chat_completion(
        model=MODELS["chat"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return result.choices[0].message.content or "(пустой ответ модели)"


async def generate_code(prompt: str) -> str:
    result = await client.chat_completion(
        model=MODELS["code"],
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — опытный программист. Пиши рабочий, аккуратно "
                    "оформленный код в markdown-блоках, с короткими пояснениями на русском."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
    )
    return result.choices[0].message.content or "(пустой ответ модели)"


async def generate_image(prompt: str) -> bytes:
    image = await client.text_to_image(prompt, model=MODELS["image"])
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


async def caption_image(image_bytes: bytes) -> str:
    result = await client.image_to_text(image_bytes, model=MODELS["image_caption"])
    return getattr(result, "generated_text", None) or str(result)


async def generate_video(prompt: str) -> bytes:
    return await video_client.text_to_video(prompt, model=MODELS["video"])


async def generate_music(prompt: str) -> bytes:
    # У MusicGen нет отдельного клиентского метода — но text_to_speech
    # просто отправляет текст и получает аудио-байты обратно, что
    # прекрасно подходит и для музыкальных моделей.
    return await client.text_to_speech(prompt, model=MODELS["music"])


async def text_to_speech(text: str) -> bytes:
    return await client.text_to_speech(text, model=MODELS["tts"])


async def speech_to_text(audio_bytes: bytes) -> str:
    result = await client.automatic_speech_recognition(audio_bytes, model=MODELS["stt"])
    return result.text or "(речь не распознана)"


async def summarize_text(text: str) -> str:
    result = await client.summarization(text, model=MODELS["summarize"])
    return result.summary_text


async def translate_text(text: str) -> str:
    model = MODELS["translate_ru_en"] if _CYRILLIC_RE.search(text) else MODELS["translate_en_ru"]
    result = await client.translation(text, model=model)
    return result.translation_text
