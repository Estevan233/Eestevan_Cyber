from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str
    title: str
    url: str
    content: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    source_path: Path | None = None


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    title: str
    url: str
    content: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)


def load_markdown_documents(content_dir: Path, *, site_base_url: str) -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    if not content_dir.exists():
        return documents

    for path in sorted(content_dir.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, body = _split_front_matter(raw)
        if bool(metadata.get("draft", False)):
            continue

        body = _clean_markdown(body)
        if not body:
            continue

        rel = path.relative_to(content_dir)
        doc_id = _doc_id_from_path(rel)
        documents.append(
            KnowledgeDocument(
                doc_id=doc_id,
                title=str(metadata.get("title") or _title_from_path(rel)),
                url=_url_from_path(rel, site_base_url),
                content=body,
                summary=str(metadata.get("summary") or ""),
                tags=_as_string_list(metadata.get("tags")),
                source_path=path,
            )
        )
    return documents


def chunk_documents(
    documents: list[KnowledgeDocument],
    *,
    chunk_size: int = 900,
    overlap: int = 120,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    safe_overlap = max(0, min(overlap, chunk_size // 2))

    for document in documents:
        text = re.sub(r"\s+", " ", document.content).strip()
        if not text:
            continue

        start = 0
        index = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{document.doc_id}:{index}",
                        title=document.title,
                        url=document.url,
                        content=chunk_text,
                        summary=document.summary,
                        tags=document.tags,
                    )
                )
            if end == len(text):
                break
            start = max(0, end - safe_overlap)
            index += 1
    return chunks


def _split_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    match = FRONT_MATTER_RE.match(raw)
    if not match:
        return {}, raw.strip()

    parsed = yaml.safe_load(match.group(1)) or {}
    if not isinstance(parsed, dict):
        parsed = {}
    return parsed, raw[match.end() :].strip()


def _clean_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"^\s*[-*_]{3,}\s*$", " ", text, flags=re.MULTILINE)
    return text.strip()


def _doc_id_from_path(path: Path) -> str:
    if path.name == "index.md":
        return "/".join(path.parent.parts)
    return "/".join(path.with_suffix("").parts)


def _title_from_path(path: Path) -> str:
    if path.name == "index.md":
        return path.parent.name.replace("-", " ").title()
    return path.stem.replace("-", " ").title()


def _url_from_path(path: Path, site_base_url: str) -> str:
    base = site_base_url.rstrip("/")
    if path.name == "index.md":
        slug = "/".join(path.parent.parts)
    else:
        slug = "/".join(path.with_suffix("").parts)
    return f"{base}/{slug.strip('/')}/"


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []

