from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ExplanationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=1000)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Topic cannot be blank.")
        return value


class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=30000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text cannot be blank.")
        return value


class QuizRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=15000)
    question_count: int = Field(default=3, ge=1, le=10)

    @field_validator("text")
    @classmethod
    def validate_quiz_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Study text cannot be blank.")
        return value


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer: str
    explanation: str


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]


class LearningStep(BaseModel):
    level: str
    estimated_time: str
    key_topics: list[str]
    resources: list[str]


class LearningRecommendationResponse(BaseModel):
    topic: str
    overview: str
    steps: list[LearningStep]
    adaptive_tips: list[str]
