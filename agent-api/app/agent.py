from __future__ import annotations

import textwrap
import uuid
from collections import defaultdict
from typing import Protocol

from app.retrieval import KeywordRetriever, RetrievalResult
from app.schemas import AskRequest, AskResponse, SourceSnippet


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    def generate(self, *, question: str, context: str, history: list[dict[str, str]]) -> str:
        ...


class ConversationStore:
    def __init__(self, *, max_messages: int = 8) -> None:
        self.max_messages = max_messages
        self._messages: dict[str, list[dict[str, str]]] = defaultdict(list)

    def get(self, session_id: str) -> list[dict[str, str]]:
        return list(self._messages.get(session_id, []))

    def add_turn(self, session_id: str, *, question: str, answer: str) -> None:
        messages = self._messages[session_id]
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})
        if len(messages) > self.max_messages:
            self._messages[session_id] = messages[-self.max_messages :]


class KnowledgeAgent:
    def __init__(
        self,
        *,
        retriever: KeywordRetriever,
        llm: LLMClient,
        conversations: ConversationStore | None = None,
        retriever_limit: int = 4,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.conversations = conversations or ConversationStore()
        self.retriever_limit = retriever_limit

    async def answer(self, request: AskRequest) -> AskResponse:
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        trace_id = uuid.uuid4().hex
        results = self.retriever.search(request.question, limit=self.retriever_limit)
        sources = [_source_from_result(result) for result in results]

        if not results:
            answer = "我在当前知识库里没有找到足够相关的内容。换个问法，或者先把相关笔记补进 content 目录。"
            self.conversations.add_turn(session_id, question=request.question, answer=answer)
            return AskResponse(answer=answer, sources=[], session_id=session_id, trace_id=trace_id)

        history = self.conversations.get(session_id)
        context = _format_context(results)
        try:
            answer = self.llm.generate(question=request.question, context=context, history=history)
        except LLMError:
            answer = "暂时无法生成回答，但我已经检索到相关资料。你可以先查看下方来源。"
        except Exception:
            answer = "暂时无法生成回答，但我已经检索到相关资料。你可以先查看下方来源。"

        answer = answer.strip() or "模型没有返回有效内容。你可以换个问题再试。"
        self.conversations.add_turn(session_id, question=request.question, answer=answer)
        return AskResponse(answer=answer, sources=sources, session_id=session_id, trace_id=trace_id)


def _source_from_result(result: RetrievalResult) -> SourceSnippet:
    snippet = textwrap.shorten(result.chunk.content, width=180, placeholder="...")
    return SourceSnippet(
        title=result.chunk.title,
        url=result.chunk.url,
        snippet=snippet,
        score=result.score,
    )


def _format_context(results: list[RetrievalResult]) -> str:
    blocks = []
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        blocks.append(
            "\n".join(
                [
                    f"[{index}] {chunk.title}",
                    f"URL: {chunk.url}",
                    f"摘要: {chunk.summary}",
                    f"内容: {chunk.content}",
                ]
            )
        )
    return "\n\n".join(blocks)

