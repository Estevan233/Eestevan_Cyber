from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_hugo_config_exposes_ask_entry() -> None:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

    profile_buttons = config["params"]["profileMode"]["buttons"]
    menu_items = config["menu"]["main"]

    assert {"name": "问答", "url": "/ask/"} in profile_buttons
    assert any(item["identifier"] == "ask" and item["url"] == "/ask/" for item in menu_items)


def test_hugo_ask_page_assets_exist() -> None:
    ask_page = ROOT / "content" / "ask.md"
    ask_layout = ROOT / "layouts" / "_default" / "ask.html"
    ask_js = ROOT / "assets" / "js" / "ask-agent.js"
    custom_css = ROOT / "assets" / "css" / "extended" / "custom.css"

    assert 'layout: "ask"' in ask_page.read_text(encoding="utf-8")
    assert "data-agent-endpoint" in ask_layout.read_text(encoding="utf-8")
    assert "/api/ask" in ask_js.read_text(encoding="utf-8")
    assert ".ask-agent" in custom_css.read_text(encoding="utf-8")
