from __future__ import annotations

import asyncio
import logging
import textwrap
import uuid
from collections import defaultdict
from typing import Protocol

from app.retrieval import KeywordRetriever, RetrievalResult
from app.schemas import AskRequest, AskResponse, SourceSnippet
from app.search import WebSearchClient, WebSearchResult

logger = logging.getLogger(__name__)


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
        web_search: WebSearchClient | None = None,
        local_score_threshold: float = 2.0,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.conversations = conversations or ConversationStore()
        self.retriever_limit = retriever_limit
        self.web_search = web_search
        self.local_score_threshold = local_score_threshold

    async def answer(self, request: AskRequest) -> AskResponse:
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        trace_id = uuid.uuid4().hex
        logger.info("trace=%s session=%s question=%r", trace_id, session_id, request.question)
        results = self.retriever.search(request.question, limit=self.retriever_limit)

        max_score = max((r.score for r in results), default=0.0)
        needs_web = self.web_search is not None and max_score < self.local_score_threshold

        web_results: list[WebSearchResult] = []
        if needs_web:
            logger.info("trace=%s local_score=%.2f below threshold, triggering web search", trace_id, max_score)
            loop = asyncio.get_running_loop()
            web_results = await loop.run_in_executor(None, self.web_search.search, request.question)
        else:
            logger.info("trace=%s local_score=%.2f sufficient, skipping web search", trace_id, max_score)

        local_sources = [_source_from_result(r) for r in results]
        web_snippets = [_source_from_result_web(wr) for wr in web_results]
        all_sources = local_sources + web_snippets
        all_sources.sort(key=lambda s: s.score, reverse=True)
        all_sources = all_sources[:6]

        if not results and not web_results:
            answer = "在当前知识库和联网搜索结果中都没有找到足够相关的内容。换个问法试试。"
            self.conversations.add_turn(session_id, question=request.question, answer=answer)
            return AskResponse(answer=answer, sources=[], session_id=session_id, trace_id=trace_id)

        history = self.conversations.get(session_id)
        context = _format_context(results, web_results)
        try:
            answer = self.llm.generate(question=request.question, context=context, history=history)
        except LLMError:
            answer = "暂时无法生成回答，但我已经检索到相关资料。你可以先查看下方来源。"
        except Exception:
            answer = "暂时无法生成回答，但我已经检索到相关资料。你可以先查看下方来源。"

        answer = answer.strip() or "模型没有返回有效内容。你可以换个问题再试。"
        self.conversations.add_turn(session_id, question=request.question, answer=answer)
        logger.info(
            "trace=%s answered sources=%d web_sources=%d",
            trace_id,
            len(local_sources),
            len(web_snippets),
        )
        return AskResponse(answer=answer, sources=all_sources, session_id=session_id, trace_id=trace_id)


def _source_from_result(result: RetrievalResult) -> SourceSnippet:
    snippet = textwrap.shorten(result.chunk.content, width=180, placeholder="...")
    return SourceSnippet(
        title=result.chunk.title,
        url=result.chunk.url,
        snippet=snippet,
        score=result.score,
    )


def _source_from_result_web(result: WebSearchResult) -> SourceSnippet:
    snippet = textwrap.shorten(result.content, width=180, placeholder="...")
    return SourceSnippet(
        title=result.title,
        url=result.url,
        snippet=snippet,
        score=result.score,
        source_type="web",
    )


def _format_context(results: list[RetrievalResult], web_results: list[WebSearchResult] | None = None) -> str:
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
    if web_results:
        offset = len(results)
        for index, wr in enumerate(web_results, start=offset + 1):
            blocks.append(
                "\n".join(
                    [
                        f"[{index}] {wr.title}",
                        f"URL: {wr.url}",
                        f"内容: {wr.content}",
                    ]
                )
            )
    return "\n\n".join(blocks)

