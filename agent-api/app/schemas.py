from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    session_id: str | None = Field(default=None, max_length=120)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be empty")
        return value


class SourceSnippet(BaseModel):
    title: str
    url: str
    snippet: str
    score: float = Field(ge=0)


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceSnippet]
    session_id: str
    trace_id: str


class HealthResponse(BaseModel):
    status: str
    documents: int
    chunks: int


class ReindexResponse(BaseModel):
    status: str
    documents: int
    chunks: int

