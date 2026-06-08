from __future__ import annotations

from dataclasses import dataclass


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

    def search(self, question: str) -> list[WebSearchResult]:
        if not self._api_key or not question.strip():
            return []
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self._api_key)
            response = client.search(
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
            return results
        except Exception:
            return []
