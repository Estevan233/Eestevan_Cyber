from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    url: str
    content: str
    score: float


class WebSearchClient:
    def __init__(self, api_key: str | None, max_results: int = 3) -> None:
        self._api_key = api_key
        self._max_results = max_results
        self._client: Any = None
        if api_key:
            try:
                from tavily import TavilyClient

                self._client = TavilyClient(api_key=api_key)
            except ImportError:
                logger.warning("tavily-python not installed, web search disabled")

    def search(self, question: str) -> list[WebSearchResult]:
        if not self._client or not question.strip():
            return []
        try:
            response = self._client.search(
                query=question,
                search_depth="advanced",
                max_results=self._max_results,
                include_raw_content=True,
            )
            results: list[WebSearchResult] = []
            for r in response.get("results", []):
                content = r.get("raw_content") or r.get("content") or ""
                results.append(
                    WebSearchResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        content=content[:3000],
                        score=r.get("score", 0.0),
                    )
                )
            logger.info("web search returned %d results for %r", len(results), question)
            return results
        except Exception:
            logger.warning("web search failed for %r", question, exc_info=True)
            return []
