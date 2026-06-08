from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str | None
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    site_base_url: str = "https://blog.estevancyber.net"
    content_dir: Path = REPO_ROOT / "content"
    cors_origins: list[str] | None = None
    retriever_limit: int = 4
    max_history_messages: int = 8
    temperature: float = 0.2

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv_files()
        return cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY") or None,
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            site_base_url=os.getenv("SITE_BASE_URL", "https://blog.estevancyber.net").rstrip("/"),
            content_dir=Path(os.getenv("KNOWLEDGE_CONTENT_DIR", str(REPO_ROOT / "content"))),
            cors_origins=_split_csv(
                os.getenv(
                    "ASK_AGENT_CORS_ORIGINS",
                    "https://blog.estevancyber.net,https://estevancyber.net,http://localhost:1313",
                )
            ),
            retriever_limit=int(os.getenv("ASK_AGENT_RETRIEVER_LIMIT", "4")),
            max_history_messages=int(os.getenv("ASK_AGENT_MAX_HISTORY_MESSAGES", "8")),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.2")),
        )

    def __repr__(self) -> str:
        safe = "set" if self.deepseek_api_key else "missing"
        return (
            "Settings("
            f"deepseek_api_key={safe}, "
            f"deepseek_model={self.deepseek_model!r}, "
            f"deepseek_base_url={self.deepseek_base_url!r}, "
            f"site_base_url={self.site_base_url!r}, "
            f"content_dir={str(self.content_dir)!r})"
        )


def _load_dotenv_files() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    for path in (
        REPO_ROOT / "agent-api" / ".env.local",
        REPO_ROOT / ".env.local",
        REPO_ROOT / "agent-api" / ".env",
        REPO_ROOT / ".env",
    ):
        if path.exists():
            load_dotenv(path, override=False)
