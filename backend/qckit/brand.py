"""品牌主题（Brand Theme）—— 一次配置，所有导出物统一视觉。

存储在 ~/.qckit/brand.yaml（跟 config.yaml 并列，与 LLM 配置解耦）。
提供 3 个内置预设（默认 / 商务蓝 / 极简黑），也支持完全自定义。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from .config import CONFIG_DIR

BRAND_FILE = CONFIG_DIR / "brand.yaml"

HEX_RE = re.compile(r"^[0-9A-Fa-f]{6}$")


def _norm_hex(v: str) -> str:
    v = (v or "").strip().lstrip("#").upper()
    if not HEX_RE.match(v):
        raise ValueError(f"颜色必须是 6 位 HEX，例如 2563EB，收到: {v!r}")
    return v


class BrandConfig(BaseModel):
    """一套主题。所有颜色是 6 位 HEX（不含 #）。"""

    name: str = "默认"
    company: str = ""                # 页眉/水印用；可选
    primary:   str = "0F172A"        # 主色 - 表头背景
    secondary: str = "1E3A8A"        # 辅色1 - 分组表头
    accent:    str = "DC2626"        # 强调 - 要因/关键
    warn:      str = "F59E0B"        # 警示 - AI 补全
    neutral:   str = "E5E7EB"        # 边框/分隔
    text:      str = "0F172A"        # 正文
    text_on_primary: str = "FFFFFF"  # 主色底上的文字
    font_zh:   str = "微软雅黑"
    font_en:   str = "Arial"
    header_style: Literal["solid", "band"] = "solid"  # 表头样式

    @field_validator("primary", "secondary", "accent", "warn",
                     "neutral", "text", "text_on_primary")
    @classmethod
    def _hex(cls, v: str) -> str:
        return _norm_hex(v)


# ─── 内置预设 ────────────────────────────────────────────────────────
PRESETS: dict[str, BrandConfig] = {
    "default": BrandConfig(
        name="QCKit 默认", primary="0F172A", secondary="1E3A8A",
        accent="DC2626", warn="F59E0B", neutral="E5E7EB",
    ),
    "business_blue": BrandConfig(
        name="商务蓝", primary="1E40AF", secondary="0369A1",
        accent="EA580C", warn="CA8A04", neutral="CBD5E1",
    ),
    "minimal_black": BrandConfig(
        name="极简黑", primary="111827", secondary="374151",
        accent="EF4444", warn="D97706", neutral="D1D5DB",
    ),
    "fresh_green": BrandConfig(
        name="清新绿", primary="065F46", secondary="0F766E",
        accent="DC2626", warn="D97706", neutral="D1FAE5",
    ),
}


class BrandFile(BaseModel):
    """磁盘存储结构：当前主题 + 用户自定义预设。"""
    current: BrandConfig = Field(default_factory=lambda: PRESETS["default"])

    @classmethod
    def load(cls) -> "BrandFile":
        if BRAND_FILE.exists():
            data = yaml.safe_load(BRAND_FILE.read_text(encoding="utf-8")) or {}
            try:
                return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        BRAND_FILE.write_text(
            yaml.safe_dump(self.model_dump(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


_cached: BrandFile | None = None


def get_brand() -> BrandConfig:
    global _cached
    if _cached is None:
        _cached = BrandFile.load()
    return _cached.current


def set_brand(cfg: BrandConfig) -> None:
    global _cached
    _cached = BrandFile(current=cfg)
    _cached.save()
