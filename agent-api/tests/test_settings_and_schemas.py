from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import AskRequest, AskResponse, SourceSnippet
from app.settings import Settings


def test_settings_default_to_deepseek_without_exposing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("SITE_BASE_URL", raising=False)

    settings = Settings.from_env()

    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.deepseek_model == "deepseek-chat"
    assert settings.site_base_url == "https://blog.estevancyber.net"
    assert settings.deepseek_api_key is None
    assert "DEEPSEEK_API_KEY" not in repr(settings)


def test_settings_read_deepseek_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "redacted-test-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("SITE_BASE_URL", "https://notes.example.test")
    monkeypatch.setenv("ASK_AGENT_CORS_ORIGINS", "https://a.test, https://b.test")

    settings = Settings.from_env()

    assert settings.deepseek_api_key == "redacted-test-key"
    assert settings.deepseek_model == "deepseek-reasoner"
    assert settings.deepseek_base_url == "https://example.test/v1"
    assert settings.site_base_url == "https://notes.example.test"
    assert settings.cors_origins == ["https://a.test", "https://b.test"]


def test_ask_request_strips_question_and_rejects_empty() -> None:
    request = AskRequest(question="  Hermes Agent 如何部署？  ", session_id="abc")

    assert request.question == "Hermes Agent 如何部署？"
    assert request.session_id == "abc"

    with pytest.raises(ValidationError):
        AskRequest(question="  ")


def test_answer_response_serializes_sources() -> None:
    response = AskResponse(
        answer="可以先用 Docker 部署 Hermes-agent。",
        sources=[
            SourceSnippet(
                title="VPS 上部署 Hermes-agent",
                url="https://blog.estevancyber.net/posts/hermes-agent-wechat/",
                snippet="Docker Compose 启动 gateway 后再接入微信。",
                score=0.87,
            )
        ],
        session_id="session-1",
        trace_id="trace-1",
    )

    payload = response.model_dump()

    assert payload["sources"][0]["title"] == "VPS 上部署 Hermes-agent"
    assert payload["sources"][0]["score"] == 0.87
    assert payload["trace_id"] == "trace-1"
