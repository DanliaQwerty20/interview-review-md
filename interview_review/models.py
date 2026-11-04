from pydantic import BaseModel, ConfigDict, Field


class Segment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: float
    end: float
    text: str


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_seconds: float
    end_seconds: float
    question: str
    topic: str
    kind: str = Field(description="substantive or organizational")


class QuestionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[Question]


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[Question]
    analysis_mode: str
    notes: list[str] = Field(default_factory=list)

