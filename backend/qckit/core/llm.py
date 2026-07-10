"""统一 LLM 客户端 —— OpenAI 兼容协议。"""
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from ..config import get_config


def get_client() -> OpenAI:
    cfg = get_config().llm
    return OpenAI(
        base_url=cfg.base_url or None,
        api_key=cfg.api_key or "sk-placeholder",
        timeout=cfg.timeout,
    )


def chat_json(system: str, user: str, *, model: str | None = None) -> dict[str, Any]:
    """调 LLM 并强制返回 JSON dict。"""
    cfg = get_config().llm
    client = get_client()
    resp = client.chat.completions.create(
        model=model or cfg.model,
        temperature=cfg.temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content or "{}"
    return _safe_json(text)


def _safe_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 抠出第一个 { ... } 块
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise ValueError(f"LLM 未返回合法 JSON:\n{text[:500]}")
