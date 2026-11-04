from collections.abc import Callable
from pathlib import Path
from typing import Any

from .models import Segment

ProgressCallback = Callable[[float, str], None]


def create_whisper_model(model_size: str, device: str, compute_type: str) -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device=device, compute_type=compute_type)


def transcribe_media(
    model: Any,
    media_path: Path,
    language: str | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[list[Segment], str, float]:
    raw_segments, info = model.transcribe(
        str(media_path),
        language=language or None,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 350},
        condition_on_previous_text=True,
        word_timestamps=False,
    )

    duration = max(float(info.duration), 1.0)
    segments: list[Segment] = []
    for item in raw_segments:
        text = item.text.strip()
        if not text:
            continue
        segment = Segment(start=item.start, end=item.end, text=text)
        segments.append(segment)
        if progress_callback:
            progress_callback(min(segment.end / duration, 1.0), text)

    if progress_callback:
        progress_callback(1.0, "Расшифровка завершена")
    return segments, info.language, float(info.duration)

