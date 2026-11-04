# Interview → Markdown

Веб-интерфейс для разбора записей собеседований. Загружает MP4/MP3/WAV/M4A/WebM,
локально расшифровывает аудио через `faster-whisper`, извлекает вопросы интервьюеров и
создаёт Markdown-файл с таймкодами.

## Возможности

- локальная расшифровка — исходный медиафайл никуда не отправляется;
- точный анализ вопросов через OpenAI Responses API и Structured Outputs;
- полностью локальный fallback без API-ключа;
- выбор модели Whisper, CPU или CUDA;
- скачивание списка вопросов, полной расшифровки и JSONL;
- поддержка длинных записей и файлов до 2 ГБ.

> В точном режиме в OpenAI API отправляется только текст расшифровки, а не видео или аудио.

## Быстрый старт на Windows

Требуется Python 3.10–3.13.

```powershell
git clone https://github.com/DanliaQwerty20/interview-review-md.git
cd interview-review-md
.\run.ps1
```

После запуска откройте `http://localhost:8501`.

## Ручная установка

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e .
streamlit run app.py
```

При первом запуске выбранная модель Whisper будет скачана в локальный кэш.

## Точный режим с OpenAI

Укажите ключ в боковой панели либо создайте переменную окружения:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_MODEL = "gpt-6-astra"
streamlit run app.py
```

Приложение использует `client.responses.parse(...)` и Pydantic-схему, поэтому результат
возвращается в предсказуемом структурированном формате. Реализация следует
[официальной документации OpenAI по Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

## Локальный режим

Локальный анализ не требует ключа и ищет вопросительные конструкции эвристически. Поскольку
Whisper не размечает спикеров, встречные вопросы кандидата иногда могут попасть в список. Для
важного ревью лучше использовать точный режим или вручную проверить результат по таймкодам.

## Docker

```bash
docker build -t interview-review-md .
docker run --rm -p 8501:8501 -e OPENAI_API_KEY=sk-... interview-review-md
```

## Приватность

- Видеофайл сохраняется только во временную директорию и удаляется после обработки.
- В локальном режиме сеть для анализа не используется (кроме первоначальной загрузки модели).
- В точном режиме в OpenAI отправляются фрагменты текстовой расшифровки.
- API-ключ не сохраняется приложением.

## Ограничения

- Точность зависит от качества звука и выбранной модели Whisper.
- Diarization спикеров пока не выполняется.
- Первая обработка медленнее из-за скачивания и загрузки модели.

## Разработка

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Лицензия

MIT
