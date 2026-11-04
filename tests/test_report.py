from interview_review.models import AnalysisResult, Question
from interview_review.report import render_questions_markdown


def test_report_groups_questions_and_renders_timecodes() -> None:
    result = AnalysisResult(
        questions=[
            Question(
                start_seconds=390,
                end_seconds=397,
                question="В чём разница между middle и senior?",
                topic="Опыт и роль",
                kind="substantive",
            )
        ],
        analysis_mode="test",
    )

    report = render_questions_markdown("interview.mp4", 4280, "ru", result)

    assert "## Опыт и роль" in report
    assert "**00:06:30–00:06:37**" in report
    assert "Найдено вопросов: **1**" in report

