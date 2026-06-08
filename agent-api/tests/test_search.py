from __future__ import annotations

from app.search import WebSearchClient, WebSearchResult


def test_client_returns_empty_without_api_key() -> None:
    client = WebSearchClient(api_key=None)
    assert client.search("test question") == []


def test_client_returns_empty_on_empty_question() -> None:
    client = WebSearchClient(api_key="tvly-test")
    assert client.search("") == []
