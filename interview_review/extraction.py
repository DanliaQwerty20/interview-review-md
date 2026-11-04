import re
from collections.abc import Callable

from .models import AnalysisResult, Question, QuestionBatch, Segment
from .timecodes import format_timestamp

AnalysisProgress = Callable[[float, str], None]

_QUESTION_CUES = re.compile(
    r"(?:\?|\b(?:как|какой|какая|какие|почему|зачем|где|когда|что|кто|сколько|"
    r"можешь|можете|расскажи|расскажите|представь|допустим|насколько|работал ли|"
    r"приходилось ли|понимаешь ли|давай уточним)\b)",
    re.IGNORECASE,
)

_TOPICS: list[tuple[str, tuple[str, ...]]] = [
    ("Kubernetes и диагностика", ("kubernetes", "кубер", "pod", "oom", "heap", "памят")),
    ("Java", ("java", "stream", "null", "класс", "метод", "поток", "thread")),
    ("Kafka и интеграции", ("kafka", "кавк", "consumer", "producer", "outbox")),
    ("Базы данных", ("баз", "postgres", "sql", "транзак", "миграц", "индекс")),
    ("Архитектура", ("архитект", "микросервис", "монолит", "reactive", "webflux")),
    ("Опыт и роль", ("опыт", "грейд", "middle", "senior", "команд", "нагруз")),
]


def _topic_for(text: str) -> str:
    lowered = text.lower()
    for topic, words in _TOPICS:
        if any(word in lowered for word in words):
            return topic
    return "Прочее"


def _normalize_question(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" -—")
    if cleaned and cleaned[-1] not in "?.!":
        cleaned += "?"
    return cleaned


def extract_questions_locally(
    segments: list[Segment], include_organizational: bool = False
) -> AnalysisResult:
    questions: list[Question] = []
    for index, segment in enumerate(segments):
        if not _QUESTION_CUES.search(segment.text):
            continue

        start_index = index
        while start_index > 0 and index - start_index < 3:
            previous = segments[start_index - 1]
            if segment.start - previous.end > 2.0:
                break
            if previous.text.endswith((".", "!", "?")):
                break
            start_index -= 1

        combined = " ".join(item.text for item in segments[start_index : index + 1])
        question = _normalize_question(combined)
        if len(question) < 8:
            continue
        kind = "organizational" if _is_organizational(question) else "substantive"
        if kind == "organizational" and not include_organizational:
            continue
        questions.append(
            Question(
                start_seconds=segments[start_index].start,
                end_seconds=segment.end,
                question=question,
                topic=_topic_for(question),
                kind=kind,
            )
        )

    return AnalysisResult(
        questions=_deduplicate(questions),
        analysis_mode="local",
        notes=[
            "Локальный режим ищет вопросительные конструкции без распознавания спикеров.",
            "Встречные вопросы кандидата могут попасть в результат; рекомендуется ручная проверка.",
        ],
    )


def extract_questions_with_openai(
    segments: list[Segment],
    api_key: str,
    model: str,
    include_organizational: bool = False,
    progress_callback: AnalysisProgress | None = None,
) -> AnalysisResult:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    chunks = _chunk_segments(segments, chunk_seconds=720)
    collected: list[Question] = []
    system_prompt = _analysis_prompt(include_organizational)

    for index, chunk in enumerate(chunks, start=1):
        transcript = "\n".join(
            f"[{format_timestamp(item.start)}–{format_timestamp(item.end)}] {item.text}"
            for item in chunk
        )
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            text_format=QuestionBatch,
        )
        if response.output_parsed is None:
            raise RuntimeError("OpenAI вернул ответ без структурированного результата")
        collected.extend(response.output_parsed.questions)
        if progress_callback:
            progress_callback(index / len(chunks), f"Проанализирован блок {index} из {len(chunks)}")

    return AnalysisResult(
        questions=_deduplicate(collected),
        analysis_mode=f"openai:{model}",
        notes=["В OpenAI отправлялся только текст расшифровки; исходный медиафайл не отправлялся."],
    )


def _analysis_prompt(include_organizational: bool) -> str:
    organizational = (
        "Include organizational questions addressed to the candidate."
        if include_organizational
        else "Exclude greetings, sound checks, scheduling, and other organizational questions."
    )
    return f"""
You extract interview questions from timestamped transcripts in any language.
Return only questions asked by interviewers to the candidate. Exclude questions asked by the
candidate, rhetorical questions inside answers, and the interviewers' presentation about the
company. Preserve every substantive follow-up as a separate item. Combine adjacent fragments only
when they form one continuous question. Rewrite lightly for readability without inventing facts.
Use the timestamps from the transcript and return seconds from the beginning for start_seconds and
end_seconds. Pick a short topic label in the transcript's language. Set kind to exactly
"substantive" or "organizational". {organizational}
""".strip()


def _chunk_segments(segments: list[Segment], chunk_seconds: int) -> list[list[Segment]]:
    if not segments:
        return []
    chunks: list[list[Segment]] = []
    current: list[Segment] = []
    chunk_start = segments[0].start
    for segment in segments:
        if current and segment.start - chunk_start >= chunk_seconds:
            chunks.append(current)
            current = []
            chunk_start = segment.start
        current.append(segment)
    if current:
        chunks.append(current)
    return chunks


def _deduplicate(questions: list[Question]) -> list[Question]:
    result: list[Question] = []
    seen: set[tuple[int, str]] = set()
    for question in sorted(questions, key=lambda item: item.start_seconds):
        normalized = re.sub(r"\W+", "", question.question.lower())[:80]
        key = (round(question.start_seconds / 5), normalized)
        if key in seen:
            continue
        seen.add(key)
        result.append(question)
    return result


def _is_organizational(text: str) -> bool:
    lowered = text.lower()
    markers = ("слышно", "на ты", "вопросы остались", "можете нас оставить", "перерыв")
    return any(marker in lowered for marker in markers)

