"""qckit configuration — 读取环境变量 / ~/.qckit/config.yaml。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel


CONFIG_DIR = Path(os.environ.get("QCKIT_CONFIG_DIR", Path.home() / ".qckit"))
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class LLMConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    timeout: int = 300


class AppConfig(BaseModel):
    llm: LLMConfig = LLMConfig()

    @classmethod
    def load(cls) -> "AppConfig":
        # 1. 文件
        data: dict = {}
        if CONFIG_FILE.exists():
            data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
        cfg = cls(**data)
        # 2. 环境变量覆盖（部署友好）
        env_map = {
            "QCKIT_LLM_BASE_URL": ("llm", "base_url"),
            "QCKIT_LLM_API_KEY": ("llm", "api_key"),
            "QCKIT_LLM_MODEL": ("llm", "model"),
            "OPENAI_BASE_URL": ("llm", "base_url"),
            "OPENAI_API_KEY": ("llm", "api_key"),
        }
        for env, (section, field) in env_map.items():
            v = os.environ.get(env)
            if v:
                setattr(getattr(cfg, section), field, v)
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            yaml.safe_dump(self.model_dump(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        # 保护 API Key: 强制 0600
        try:
            os.chmod(CONFIG_FILE, 0o600)
            os.chmod(CONFIG_DIR, 0o700)
        except OSError:
            pass  # Windows / 不支持 chmod

    def masked(self) -> dict:
        """返回脱敏后的配置字典 —— API Key 只保留前 4 + 后 4 位。"""
        d = self.model_dump()
        key = d.get("llm", {}).get("api_key", "") or ""
        if len(key) > 8:
            d["llm"]["api_key"] = key[:4] + "…" + key[-4:]
        elif key:
            d["llm"]["api_key"] = "…"
        return d


_cached: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _cached
    if _cached is None:
        _cached = AppConfig.load()
    return _cached


def set_config(cfg: AppConfig) -> None:
    global _cached
    _cached = cfg
    cfg.save()
