from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_reports_ready() -> None:
    client = TestClient(create_app(testing=True))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_endpoint_validates_question_and_returns_sources() -> None:
    client = TestClient(create_app(testing=True))

    empty = client.post("/api/ask", json={"question": " "})
    ok = client.post("/api/ask", json={"question": "Hermes Agent 怎么部署？", "session_id": "web"})

    assert empty.status_code == 422
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["answer"]
    assert payload["sources"]
    assert payload["session_id"] == "web"
    assert "DEEPSEEK_API_KEY" not in ok.text


def test_reindex_endpoint_reloads_knowledge_base() -> None:
    client = TestClient(create_app(testing=True))

    response = client.post("/api/reindex")

    assert response.status_code == 200
    assert response.json()["chunks"] > 0


def test_cors_allows_configured_origin() -> None:
    client = TestClient(create_app(testing=True))

    response = client.options(
        "/api/ask",
        headers={
            "Origin": "https://blog.estevancyber.net",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://blog.estevancyber.net"


def test_ask_endpoint_returns_source_type() -> None:
    client = TestClient(create_app(testing=True))

    response = client.post("/api/ask", json={"question": "Hermes Agent 怎么部署？", "session_id": "web"})

    assert response.status_code == 200
    payload = response.json()
    for source in payload["sources"]:
        assert "source_type" in source
