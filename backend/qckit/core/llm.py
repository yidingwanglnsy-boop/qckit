"""统一 LLM 客户端 —— OpenAI 兼容协议。"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from ..config import get_config

DEBUG_LOG = Path.home() / ".qckit" / "last_llm_debug.txt"


def get_client() -> OpenAI:
    cfg = get_config().llm
    return OpenAI(
        base_url=cfg.base_url or None,
        api_key=cfg.api_key or "***",
        timeout=cfg.timeout,
    )


def chat_json(system: str, user: str, *, model: str | None = None) -> dict[str, Any]:
    """调 LLM 并强制返回 JSON dict。失败时把最近一次原始响应落盘到 ~/.qckit/last_llm_debug.txt."""
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
    try:
        return _safe_json(text)
    except ValueError:
        _dump_debug(system, user, text)
        raise


def _safe_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 抠出第一个 { ... } 块
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"LLM 未返回合法 JSON:\n{text[:500]}")


def _dump_debug(system: str, user: str, raw: str) -> None:
    """保存最近一次失败的 LLM 交互到 ~/.qckit/last_llm_debug.txt, 方便排查."""
    try:
        DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_LOG.write_text(
            f"[{datetime.now().isoformat(timespec='seconds')}]\n"
            f"=== SYSTEM ===\n{system}\n\n"
            f"=== USER ===\n{user}\n\n"
            f"=== RAW RESPONSE ===\n{raw}\n",
            encoding="utf-8",
        )
    except Exception:
        pass  # 诊断能力优雅降级
