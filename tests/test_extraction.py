from interview_review.extraction import extract_questions_locally
from interview_review.models import Segment


def test_local_extraction_finds_questions_and_skips_plain_answers() -> None:
    segments = [
        Segment(start=1, end=2, text="Расскажи про свой опыт с Kafka?"),
        Segment(start=3, end=5, text="Я использовал Spring Kafka."),
        Segment(start=6, end=8, text="Как обеспечить согласованность двух баз?"),
    ]

    result = extract_questions_locally(segments)

    assert [question.question for question in result.questions] == [
        "Расскажи про свой опыт с Kafka?",
        "Как обеспечить согласованность двух баз?",
    ]
    assert result.questions[0].topic == "Kafka и интеграции"


def test_local_extraction_can_skip_organizational_questions() -> None:
    segments = [Segment(start=1, end=2, text="Меня слышно?")]

    assert extract_questions_locally(segments).questions == []
    assert len(extract_questions_locally(segments, include_organizational=True).questions) == 1

