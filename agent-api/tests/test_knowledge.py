from __future__ import annotations

from pathlib import Path

from app.knowledge import chunk_documents, load_markdown_documents


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_markdown_documents_extracts_metadata_and_ignores_drafts(tmp_path: Path) -> None:
    content = tmp_path / "content"
    write_text(
        content / "about.md",
        """---
title: "关于"
draft: false
---

你好，我是 Estevan。
""",
    )
    write_text(
        content / "posts" / "hermes-agent-wechat" / "index.md",
        """---
title: "VPS 上部署 Hermes-agent"
date: 2026-06-05
draft: false
tags: ["AI Agent", "Docker"]
summary: "Hermes-agent 微信部署记录"
---

Hermes-agent 可以用 Docker Compose 部署。
""",
    )
    write_text(
        content / "posts" / "draft-note" / "index.md",
        """---
title: "草稿"
draft: true
---

不要进入知识库。
""",
    )

    documents = load_markdown_documents(content, site_base_url="https://blog.estevancyber.net")

    assert [doc.title for doc in documents] == ["关于", "VPS 上部署 Hermes-agent"]
    assert documents[0].url == "https://blog.estevancyber.net/about/"
    assert documents[1].url == "https://blog.estevancyber.net/posts/hermes-agent-wechat/"
    assert documents[1].tags == ["AI Agent", "Docker"]
    assert "不要进入知识库" not in "\n".join(doc.content for doc in documents)


def test_chunk_documents_keeps_source_metadata() -> None:
    documents = load_markdown_documents(
        Path(__file__).resolve().parents[2] / "content",
        site_base_url="https://blog.estevancyber.net",
    )

    chunks = chunk_documents(documents, chunk_size=180, overlap=30)

    assert chunks
    first = chunks[0]
    assert first.title
    assert first.url.startswith("https://blog.estevancyber.net/")
    assert first.chunk_id.endswith(":0")
    assert len(first.content) <= 240

