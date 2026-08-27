# Telegram AI Bot (Hugging Face, 10 нейросетей)

Телеграм-бот на aiogram 3, который через Hugging Face Inference обращается
к 10 разным нейросетям по кнопкам:

| Кнопка | Задача | Модель по умолчанию |
|---|---|---|
| 💬 Текстовый чат | ответ на вопрос | `Qwen/Qwen2.5-7B-Instruct` |
| 💻 Написать код | генерация кода | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| 🎨 Сгенерировать фото | текст → изображение | `black-forest-labs/FLUX.1-schnell` |
| 🖼 Распознать фото | изображение → описание | `Salesforce/blip-image-captioning-large` |
| 🎬 Сгенерировать видео | текст → видео | `tencent/HunyuanVideo-1.5` (через провайдера fal-ai) |
| 🎵 Сгенерировать музыку | текст → музыка | `facebook/musicgen-small` |
| 🗣 Озвучить текст | текст → речь (TTS) | `facebook/mms-tts-rus` |
| 🎧 Распознать речь | голос/видео → текст (ASR) | `openai/whisper-large-v3` |
| 📝 Пересказать текст | суммаризация | `facebook/bart-large-cnn` |
| 🌐 Перевести текст | перевод RU↔EN | `Helsinki-NLP/opus-mt-*` |

Дополнительно бот умеет:
- показывать статус «печатает…» / «отправляет фото» и т.п., пока ждёт ответ от нейросети;
- принимать `.zip` (покажет список файлов внутри) и `.txt`/`.pdf`/`.docx` (вытащит текст — можно прислать вместо того чтобы печатать);
- принимать голосовые, аудио и видео длиной до 5 минут для распознавания речи;
- админ-панель по кнопке (или командой `/stats`) — сколько пользователей, сколько всего запросов, что генерируют чаще всего.

## ⚠️ Важно про безопасность (прочитайте перед тем как заливать на GitHub)

Токены (`BOT_TOKEN`, `HF_TOKEN`) в коде **не хранятся** — они читаются из
файла `.env`, которого нет в этом архиве (только пример `.env.example`).
`.gitignore` уже настроен так, чтобы `.env` никогда не попал в git.

Перед публикацией репозитория на GitHub:
1. Никогда не коммитьте файл `.env` — только `.env.example`.
2. Токены, которые вы присылали мне в чате ранее, уже нужно считать
   скомпрометированными (они прошли через переписку) — **перевыпустите их**:
   - Telegram-токен: откройте диалог с **@BotFather** → `/mybots` → ваш бот →
     **API Token** → **Revoke current token**, получите новый.
   - Hugging Face-токен: **hf.co/settings/tokens** → удалите старый токен,
     создайте новый.
3. Впишите новые значения в свой локальный `.env` (см. ниже) — не в код и не в README.

## Структура проекта

```
telegram_ai_bot/
├── main.py              # точка входа
├── config.py            # чтение .env, проверка обязательных переменных
├── tasks.py             # описание всех 10 задач/кнопок в одном месте
├── states.py            # состояние FSM "жду ввод от пользователя"
├── keyboards.py         # инлайн-клавиатуры
├── hf_client.py         # обёртка над Hugging Face InferenceClient (10 функций)
├── database.py          # SQLite: пользователи + статистика запросов
├── utils.py             # zip/pdf/docx/видео → аудио (ffmpeg)
├── handlers/
│   ├── common.py        # /start, /menu, /help, выбор задачи
│   ├── generation.py    # обработка текстового ввода + отправка результата
│   ├── files.py         # фото/голос/видео/документы/zip
│   ├── admin.py         # статистика для админа
│   └── fallback.py      # "не понял, вот меню" (подключается последним!)
├── requirements.txt
├── .env.example         # шаблон переменных окружения (без реальных секретов)
└── .gitignore           # .env, bot_data.db и т.п. никогда не коммитятся
```

## Установка (Linux / macOS / Windows / VPS)

Нужен Python 3.10+ и (желательно) `ffmpeg` — он нужен только для того, чтобы
доставать звук из видео при распознавании речи; без него бот тоже запустится,
просто эта конкретная функция для видео (не для голосовых) может не сработать.

```bash
git clone <ссылка-на-ваш-репозиторий>
cd telegram_ai_bot
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
nano .env                        # впишите BOT_TOKEN, HF_TOKEN, ADMIN_IDS
python main.py
```

Где взять значения для `.env`:
- **BOT_TOKEN** — у **@BotFather** в Telegram: `/newbot` (или `/mybots` для существующего).
- **HF_TOKEN** — на https://huggingface.co/settings/tokens (достаточно токена с правом Read; для инференса он всё равно тратит ваши бесплатные месячные кредиты).
- **ADMIN_IDS** — узнать свой числовой Telegram ID можно у **@userinfobot**. Можно указать несколько через запятую: `111111,222222`.

## Установка через Termux (Android)

Работает, но есть нюансы: у некоторых зависимостей (в частности, у
`hf-xet` — вспомогательного пакета Hugging Face) есть Rust/бинарные
компоненты, которые не всегда ставятся на Android так же гладко, как на
обычном Linux. Ниже — рабочий путь и запасной вариант, если что-то не встанет.

```bash
pkg update && pkg upgrade
pkg install python git ffmpeg clang make rust libjpeg-turbo

git clone <ссылка-на-ваш-репозиторий>
cd telegram_ai_bot
pip install -r requirements.txt
```

**Если установка упадёт на пакете `hf-xet`** (Rust-компонент, нужен только
для ускоренной загрузки больших файлов моделей — этому боту он не нужен,
так как бот только дёргает Inference API, а не скачивает файлы моделей):

```bash
pip install huggingface_hub --no-deps
pip install click filelock fsspec httpx packaging pyyaml tqdm typing-extensions
pip install aiogram python-dotenv aiosqlite pypdf python-docx Pillow
```

Это проверено: без `hf-xet` `AsyncInferenceClient` создаётся и работает нормально —
он просто не нужен для вызовов Inference API.

Дальше — как обычно:

```bash
cp .env.example .env
nano .env    # впишите свои токены
python main.py
```

Чтобы бот не "засыпал" вместе с телефоном:
```bash
termux-wake-lock
```
и в настройках Android для Termux стоит отключить оптимизацию батареи.
Для по-настоящему стабильной работы 24/7 телефон всё же менее надёжен, чем
дешёвый VPS — Termux хорошо подходит, чтобы быстро всё проверить.

## Загрузка на GitHub

В этом архиве папка `.git` уже есть — git инициализирован, первый коммит
уже сделан (ветка `main`). Осталось создать пустой репозиторий на GitHub
и отправить туда:

```bash
cd telegram_ai_bot
git remote add origin https://github.com/<ваш-логин>/<репозиторий>.git
git push -u origin main
```

Если хотите начать git-историю с нуля — удалите папку `.git` и повторите:
```bash
rm -rf .git
git init && git add . && git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<ваш-логин>/<репозиторий>.git
git push -u origin main
```

В любом случае перед пушем стоит проверить глазами `git status` /
`git ls-files | grep .env` — файла `.env` в списке быть не должно (он и так
игнорируется `.gitignore`, но лишняя проверка не помешает).

## Как поменять модель

Все ID моделей собраны в одном месте — словарь `MODELS` в `hf_client.py`.
Если какая-то модель перестала отвечать (Hugging Face периодически меняет,
что доступно бесплатно через Inference Providers), замените её ID на другую
с такой же задачей (pipeline_tag) с https://huggingface.co/models.
Чаще всего "плавают" именно видео и музыка — они самые ресурсоёмкие.

## Известные ограничения

- Обычный Telegram Bot API не даёт боту скачивать файлы тяжелее **20 МБ**
  (ограничение самого Telegram, не этого кода) — для больших файлов нужен
  self-hosted Bot API сервер, это отдельная история.
- У бесплатного аккаунта Hugging Face — ограниченные **ежемесячные кредиты**
  на Inference Providers; генерация видео/музыки "стоит" больше текста.
- Перевод по умолчанию — только связка русский↔английский (детектируется
  по наличию кириллицы). Для других языков добавьте свою модель в `hf_client.py`.
- `bot_data.db` (SQLite) хранится локально рядом с ботом; для нескольких
  запущенных копий бота одновременно её лучше вынести в отдельную БД.
