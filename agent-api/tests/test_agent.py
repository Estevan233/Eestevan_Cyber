from __future__ import annotations

import pytest

from app.agent import ConversationStore, KnowledgeAgent, LLMError
from app.knowledge import KnowledgeChunk
from app.retrieval import KeywordRetriever
from app.schemas import AskRequest


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

