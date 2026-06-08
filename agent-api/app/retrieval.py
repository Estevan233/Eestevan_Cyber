from __future__ import annotations

import math
import re
from dataclasses import dataclass

from app.knowledge import KnowledgeChunk


TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]", re.IGNORECASE)


@dataclass(frozen=True)
class RetrievalResult:
    chunk: KnowledgeChunk
    score: float


class KeywordRetriever:
    def __init__(self, chunks: list[KnowledgeChunk]) -> None:
        self._chunks = chunks

    @property
    def chunks(self) -> list[KnowledgeChunk]:
        return self._chunks

    def search(self, question: str, *, limit: int = 4) -> list[RetrievalResult]:
        query_tokens = _tokens(question)
        if not query_tokens:
            return []

        scored: list[RetrievalResult] = []
        for chunk in self._chunks:
            haystack = f"{chunk.title} {chunk.summary} {' '.join(chunk.tags)} {chunk.content}"
            score = _score(query_tokens, haystack)
            if score > 0:
                scored.append(RetrievalResult(chunk=chunk, score=score))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]


def _tokens(text: str) -> list[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    joined = "".join(token for token in tokens if len(token) == 1)
    bigrams = [joined[i : i + 2] for i in range(max(0, len(joined) - 1))]
    return tokens + bigrams


def _score(tokens: list[str], text: str) -> float:
    lowered = text.lower()
    score = 0.0
    for token in tokens:
        if not token:
            continue
        count = lowered.count(token)
        if count:
            score += math.log1p(count) * (2.0 if len(token) > 1 else 0.65)
    return round(score, 4)

