# Knowledge Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a DeepSeek-backed FastAPI RAG service and Hugo ask page for natural-language Q&A over the site's Markdown knowledge base.

**Architecture:** The Hugo site stays static and exposes an `/ask/` page. A separate `agent-api/` FastAPI service loads Markdown from `content/`, builds retrievable chunks, calls a configurable DeepSeek-compatible chat model, and returns answers with source citations and session-aware context.

**Tech Stack:** Python 3.10, FastAPI, LangChain, DeepSeek OpenAI-compatible chat API, pytest, Hugo/PaperMod.

---

### Task 1: Backend Contract And Settings

**Files:**
- Create: `agent-api/app/settings.py`
- Create: `agent-api/app/schemas.py`
- Test: `agent-api/tests/test_settings_and_schemas.py`

- [ ] Write failing tests for default settings, DeepSeek environment overrides, request validation, and response source shape.
- [ ] Run `python -m pytest agent-api/tests/test_settings_and_schemas.py -q`; expected failure before implementation.
- [ ] Implement settings and Pydantic schemas.
- [ ] Re-run the test; expected pass.

### Task 2: Markdown Knowledge Loader

**Files:**
- Create: `agent-api/app/knowledge.py`
- Test: `agent-api/tests/test_knowledge.py`

- [ ] Write failing tests that load page-bundle Markdown, extract front matter, build canonical URLs, ignore drafts, and produce stable chunks.
- [ ] Run `python -m pytest agent-api/tests/test_knowledge.py -q`; expected failure before implementation.
- [ ] Implement Markdown loading and deterministic chunking without requiring model calls.
- [ ] Re-run the test; expected pass.

### Task 3: Retriever And Agent Orchestration

**Files:**
- Create: `agent-api/app/retrieval.py`
- Create: `agent-api/app/agent.py`
- Test: `agent-api/tests/test_agent.py`

- [ ] Write failing tests for relevant source retrieval, source citation formatting, session history trimming, and provider-error fallback.
- [ ] Run `python -m pytest agent-api/tests/test_agent.py -q`; expected failure before implementation.
- [ ] Implement a LangChain-compatible keyword retriever for the first version and a pluggable LLM client interface.
- [ ] Re-run the test; expected pass.

### Task 4: FastAPI Application

**Files:**
- Create: `agent-api/app/main.py`
- Create: `agent-api/tests/test_api.py`

- [ ] Write failing API tests for `/api/health`, `/api/ask`, `/api/reindex`, CORS headers, empty question validation, and no-secret error responses.
- [ ] Run `python -m pytest agent-api/tests/test_api.py -q`; expected failure before implementation.
- [ ] Implement the FastAPI app, dependency wiring, and API error handling.
- [ ] Re-run the test; expected pass.

### Task 5: Packaging And Deployment Files

**Files:**
- Create: `agent-api/requirements.txt`
- Create: `agent-api/Dockerfile`
- Create: `agent-api/.env.example`
- Create: `agent-api/README.md`

- [ ] Add runtime dependencies and documented DeepSeek env vars.
- [ ] Add Docker image build instructions with `/app/content` mounted or copied.
- [ ] Add API examples for curl and frontend integration.

### Task 6: Hugo Ask Page

**Files:**
- Modify: `config.yaml`
- Create: `content/ask.md`
- Create: `layouts/_default/ask.html`
- Create: `assets/js/ask-agent.js`
- Modify: `assets/css/extended/custom.css`

- [ ] Add a new menu/profile button named `问答`.
- [ ] Create a usable ask page with message history, source cards, loading state, and error state.
- [ ] Keep API base configurable through page params and default to `https://api.estevancyber.net`.
- [ ] Add responsive CSS without changing article content.

### Task 7: Verification

**Files:**
- No new files unless verification reveals a defect.

- [ ] Run backend unit/API tests.
- [ ] Run a local import smoke test for the FastAPI app.
- [ ] Initialize PaperMod submodule if needed and run Hugo build if Hugo is available.
- [ ] If Docker is available, build the backend image.
- [ ] Report exact commands and outcomes.
