"""工具注册表 —— 每个 QC 工具在这里登记一次。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class ToolMeta:
    key: str          # 唯一标识, URL 路径
    name: str         # 中文显示名
    category: str     # 分组: "新QC七大手法" / "QC七大手法" / "其他"
    description: str
    icon: str = "Connection"
    ready: bool = True


_REGISTRY: dict[str, ToolMeta] = {}


def register(meta: ToolMeta) -> None:
    _REGISTRY[meta.key] = meta


def all_tools() -> list[ToolMeta]:
    return list(_REGISTRY.values())


def get(key: str) -> ToolMeta | None:
    return _REGISTRY.get(key)
