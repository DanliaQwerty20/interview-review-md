from collections import OrderedDict
from pathlib import Path

from .models import AnalysisResult, Segment
from .timecodes import format_range, format_timestamp


def render_questions_markdown(
    source_name: str,
    duration: float,
    language: str,
    result: AnalysisResult,
) -> str:
    groups: OrderedDict[str, list] = OrderedDict()
    for question in result.questions:
        groups.setdefault(question.topic, []).append(question)

    lines = [
        f"# Вопросы из собеседования — {Path(source_name).stem}",
        "",
        f"- Исходный файл: `{source_name}`",
        f"- Длительность аудио: **{format_timestamp(duration)}**",
        f"- Язык распознавания: **{language}**",
        f"- Режим анализа: **{result.analysis_mode}**",
        f"- Найдено вопросов: **{len(result.questions)}**",
        "",
    ]

    counter = 1
    for topic, questions in groups.items():
        lines.extend([f"## {topic}", ""])
        for question in questions:
            timecode = format_range(question.start_seconds, question.end_seconds)
            lines.append(f"{counter}. **{timecode}** — {question.question}")
            counter += 1
        lines.append("")

    if not result.questions:
        lines.extend(["Вопросы не найдены.", ""])

    if result.notes:
        lines.extend(["## Примечания", ""])
        lines.extend(f"- {note}" for note in result.notes)
        lines.append("")
    return "\n".join(lines)


def render_transcript_markdown(source_name: str, segments: list[Segment]) -> str:
    lines = [
        f"# Автоматическая расшифровка — {Path(source_name).stem}",
        "",
        "> Черновая автоматическая расшифровка без разметки спикеров.",
        "",
    ]
    lines.extend(
        f"- **{format_range(segment.start, segment.end)}** — {segment.text}"
        for segment in segments
    )
    return "\n".join(lines) + "\n"

