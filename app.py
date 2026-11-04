import json
import os
import tempfile
from pathlib import Path

import streamlit as st

from interview_review.extraction import (
    extract_questions_locally,
    extract_questions_with_openai,
)
from interview_review.report import render_questions_markdown, render_transcript_markdown
from interview_review.transcription import create_whisper_model, transcribe_media

st.set_page_config(page_title="Interview → Markdown", page_icon="🎙️", layout="wide")


@st.cache_resource(show_spinner=False)
def load_whisper_model(model_size: str, device: str, compute_type: str):
    return create_whisper_model(model_size, device, compute_type)


def main() -> None:
    st.title("🎙️ Interview → Markdown")
    st.caption("Загрузите запись собеседования и получите список вопросов с таймкодами.")

    with st.sidebar:
        st.header("Настройки")
        whisper_model = st.selectbox(
            "Модель распознавания",
            ["small", "medium", "large-v3"],
            index=0,
            help="Чем крупнее модель, тем выше точность и требования к памяти.",
        )
        device = st.selectbox("Устройство", ["cpu", "cuda"], index=0)
        compute_type = st.selectbox(
            "Тип вычислений",
            ["int8", "float16", "float32"],
            index=0 if device == "cpu" else 1,
        )
        language = st.text_input("Язык (пусто = определить автоматически)", value="ru")
        analysis_mode = st.radio(
            "Анализ вопросов",
            ["Точный — OpenAI", "Локальный — без API"],
            help="Точный режим лучше отличает интервьюеров от кандидата.",
        )
        api_key = ""
        openai_model = os.getenv("OPENAI_MODEL", "gpt-6-astra")
        if analysis_mode.startswith("Точный"):
            api_key = st.text_input(
                "OpenAI API key",
                value=os.getenv("OPENAI_API_KEY", ""),
                type="password",
            )
            openai_model = st.text_input("Модель OpenAI", value=openai_model)
            st.caption("В API отправляется только текст расшифровки, не MP4.")
        include_organizational = st.checkbox("Включать служебные вопросы", value=False)

    uploaded = st.file_uploader(
        "MP4, MP3, WAV, M4A или WebM",
        type=["mp4", "mp3", "wav", "m4a", "webm", "mov"],
    )

    if uploaded is not None:
        left, right = st.columns([2, 1])
        with left:
            st.info(f"Файл: **{uploaded.name}**, размер: **{uploaded.size / 1024 / 1024:.1f} МБ**")
        with right:
            start = st.button("Начать обработку", type="primary", use_container_width=True)
    else:
        start = False

    if start:
        if analysis_mode.startswith("Точный") and not api_key:
            st.error("Для точного режима укажите OpenAI API key.")
            return
        process_upload(
            uploaded=uploaded,
            whisper_model=whisper_model,
            device=device,
            compute_type=compute_type,
            language=language.strip() or None,
            analysis_mode=analysis_mode,
            api_key=api_key,
            openai_model=openai_model,
            include_organizational=include_organizational,
        )

    show_results()


def process_upload(**settings) -> None:
    uploaded = settings.pop("uploaded")
    transcription_bar = st.progress(0, text="Подготовка модели распознавания…")

    with tempfile.TemporaryDirectory(prefix="interview-review-") as temporary_directory:
        media_path = Path(temporary_directory) / uploaded.name
        media_path.write_bytes(uploaded.getbuffer())

        try:
            model = load_whisper_model(
                settings["whisper_model"], settings["device"], settings["compute_type"]
            )
            segments, detected_language, duration = transcribe_media(
                model,
                media_path,
                language=settings["language"],
                progress_callback=lambda value, text: transcription_bar.progress(
                    value, text=f"Расшифровка: {value:.0%} — {text[:70]}"
                ),
            )
            analysis_bar = st.progress(0, text="Выделение вопросов…")
            if settings["analysis_mode"].startswith("Точный"):
                result = extract_questions_with_openai(
                    segments,
                    api_key=settings["api_key"],
                    model=settings["openai_model"],
                    include_organizational=settings["include_organizational"],
                    progress_callback=lambda value, text: analysis_bar.progress(value, text=text),
                )
            else:
                result = extract_questions_locally(
                    segments, include_organizational=settings["include_organizational"]
                )
                analysis_bar.progress(1.0, text="Локальный анализ завершён")

            report = render_questions_markdown(
                uploaded.name, duration, detected_language, result
            )
            transcript = render_transcript_markdown(uploaded.name, segments)
            jsonl = "\n".join(
                json.dumps(segment.model_dump(), ensure_ascii=False) for segment in segments
            )
            st.session_state["interview_results"] = {
                "report": report,
                "transcript": transcript,
                "jsonl": jsonl,
                "source_stem": Path(uploaded.name).stem,
                "question_count": len(result.questions),
            }
            st.success(f"Готово: найдено вопросов — {len(result.questions)}")
        except Exception as error:
            st.exception(error)


def show_results() -> None:
    result = st.session_state.get("interview_results")
    if not result:
        return
    st.divider()
    st.subheader(f"Результат · {result['question_count']} вопросов")
    st.markdown(result["report"])
    first, second, third = st.columns(3)
    first.download_button(
        "Скачать вопросы (.md)",
        data=result["report"],
        file_name=f"{result['source_stem']}_questions.md",
        mime="text/markdown",
        use_container_width=True,
    )
    second.download_button(
        "Скачать расшифровку (.md)",
        data=result["transcript"],
        file_name=f"{result['source_stem']}_transcript.md",
        mime="text/markdown",
        use_container_width=True,
    )
    third.download_button(
        "Скачать JSONL",
        data=result["jsonl"],
        file_name=f"{result['source_stem']}_transcript.jsonl",
        mime="application/x-ndjson",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()

