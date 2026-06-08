from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import ConversationStore, KnowledgeAgent
from app.knowledge import chunk_documents, load_markdown_documents
from app.llm import build_llm
from app.retrieval import KeywordRetriever
from app.schemas import AskRequest, AskResponse, HealthResponse, ReindexResponse
from app.settings import Settings


def create_app(*, testing: bool = False) -> FastAPI:
    settings = Settings.from_env()
    app = FastAPI(title="Estevan Cyber Knowledge Agent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or [],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    _wire_agent(app, settings=settings, testing=testing)

    @app.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            documents=app.state.document_count,
            chunks=len(app.state.agent.retriever.chunks),
        )

    @app.post("/api/ask", response_model=AskResponse)
    async def ask(request: AskRequest) -> AskResponse:
        return await app.state.agent.answer(request)

    @app.post("/api/reindex", response_model=ReindexResponse)
    async def reindex() -> ReindexResponse:
        _wire_agent(app, settings=settings, testing=testing)
        return ReindexResponse(
            status="ok",
            documents=app.state.document_count,
            chunks=len(app.state.agent.retriever.chunks),
        )

    return app


def _wire_agent(app: FastAPI, *, settings: Settings, testing: bool) -> None:
    documents = load_markdown_documents(settings.content_dir, site_base_url=settings.site_base_url)
    chunks = chunk_documents(documents)
    conversations = getattr(app.state, "conversations", None) or ConversationStore(
        max_messages=settings.max_history_messages
    )
    app.state.document_count = len(documents)
    app.state.conversations = conversations
    app.state.agent = KnowledgeAgent(
        retriever=KeywordRetriever(chunks),
        llm=build_llm(settings, testing=testing),
        conversations=conversations,
        retriever_limit=settings.retriever_limit,
    )


app = create_app()

