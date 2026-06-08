from __future__ import annotations

import pytest

from app.agent import ConversationStore, KnowledgeAgent, LLMError
from app.knowledge import KnowledgeChunk
from app.retrieval import KeywordRetriever
from app.schemas import AskRequest
from app.search import WebSearchResult


class FakeLLM:
    def __init__(self, answer: str = "根据资料，可以使用 Docker 部署。") -> None:
        self.answer = answer
        self.calls: list[dict[str, object]] = []

    def generate(self, *, question: str, context: str, history: list[dict[str, str]]) -> str:
        self.calls.append({"question": question, "context": context, "history": history})
        return self.answer


class FailingLLM:
    def generate(self, *, question: str, context: str, history: list[dict[str, str]]) -> str:
        raise LLMError("provider unavailable")


def sample_chunks() -> list[KnowledgeChunk]:
    return [
        KnowledgeChunk(
            chunk_id="hermes:0",
            title="VPS 上部署 Hermes-agent",
            url="https://blog.estevancyber.net/posts/hermes-agent-wechat/",
            content="Hermes-agent 支持 Docker Compose 部署，并可以接入微信。",
            summary="Hermes-agent 微信部署记录",
        ),
        KnowledgeChunk(
            chunk_id="vps:0",
            title="如何从0开始部署海外 VPS",
            url="https://blog.estevancyber.net/posts/vps-deployment-first-blog/",
            content="VPS 上可以安装 Docker、Nginx，并通过 Cloudflare 暴露网站。",
            summary="VPS 基础环境搭建记录",
        ),
    ]


def test_keyword_retriever_returns_relevant_sources() -> None:
    retriever = KeywordRetriever(sample_chunks())

    results = retriever.search("Hermes Agent 微信 Docker 怎么部署", limit=2)

    assert results[0].chunk.title == "VPS 上部署 Hermes-agent"
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_agent_answers_with_sources_and_history() -> None:
    llm = FakeLLM()
    store = ConversationStore(max_messages=2)
    agent = KnowledgeAgent(retriever=KeywordRetriever(sample_chunks()), llm=llm, conversations=store)

    response = await agent.answer(AskRequest(question="Hermes Agent 怎么部署？", session_id="s1"))
    await agent.answer(AskRequest(question="它能接入微信吗？", session_id="s1"))

    assert response.answer == "根据资料，可以使用 Docker 部署。"
    assert response.sources[0].title == "VPS 上部署 Hermes-agent"
    assert response.session_id == "s1"
    assert llm.calls[0]["history"] == []
    assert len(store.get("s1")) == 2


@pytest.mark.asyncio
async def test_agent_returns_controlled_error_when_llm_fails() -> None:
    agent = KnowledgeAgent(retriever=KeywordRetriever(sample_chunks()), llm=FailingLLM())

    response = await agent.answer(AskRequest(question="Hermes Agent 怎么部署？", session_id="s1"))

    assert "暂时无法生成回答" in response.answer
    assert response.sources
    assert response.trace_id


class FakeWebSearch:
    def __init__(self, results: list[WebSearchResult] | None = None) -> None:
        self.results = results or []
        self.calls: list[str] = []

    def search(self, question: str) -> list[WebSearchResult]:
        self.calls.append(question)
        return self.results


WEB_FIXTURES = [
    WebSearchResult(
        title="Docker Compose 快速搭建 Hermes Agent",
        url="https://example.com/hermes-docker",
        content="Hermes Agent 支持通过 Docker Compose 一键部署，需要配置 .env 文件并运行 docker-compose up -d。",
        score=0.92,
    ),
]


@pytest.mark.asyncio
async def test_agent_uses_web_search_when_local_score_low() -> None:
    fake_web = FakeWebSearch(results=WEB_FIXTURES)
    low_score_chunks = [
        KnowledgeChunk(
            chunk_id="misc:0",
            title="一些笔记",
            url="https://blog.estevancyber.net/notes/misc/",
            content="一些日常笔记片段。",
            summary="日常",
        ),
    ]
    agent = KnowledgeAgent(
        retriever=KeywordRetriever(low_score_chunks),
        llm=FakeLLM(),
        web_search=fake_web,
        local_score_threshold=2.0,
    )

    response = await agent.answer(AskRequest(question="Hermes Agent 怎么部署 Docker？", session_id="s1"))

    assert len(fake_web.calls) == 1
    web_sources = [s for s in response.sources if s.source_type == "web"]
    assert len(web_sources) >= 1
    assert "Hermes Agent" in web_sources[0].title


@pytest.mark.asyncio
async def test_agent_skips_web_search_when_local_score_high() -> None:
    fake_web = FakeWebSearch(results=WEB_FIXTURES)
    agent = KnowledgeAgent(
        retriever=KeywordRetriever(sample_chunks()),
        llm=FakeLLM(),
        web_search=fake_web,
        local_score_threshold=2.0,
    )

    response = await agent.answer(AskRequest(question="VPS 上部署 Hermes-agent Docker", session_id="s1"))

    assert len(fake_web.calls) == 0
    assert all(s.source_type == "local" for s in response.sources)


@pytest.mark.asyncio
async def test_agent_handles_web_search_failure_gracefully() -> None:
    class FailingWebSearch:
        def search(self, question: str) -> list[WebSearchResult]:
            return []

    agent = KnowledgeAgent(
        retriever=KeywordRetriever(sample_chunks()),
        llm=FakeLLM(),
        web_search=FailingWebSearch(),
        local_score_threshold=5.0,
    )

    response = await agent.answer(AskRequest(question="Hermes Agent 怎么部署？", session_id="s1"))

    assert response.answer
    assert response.sources

