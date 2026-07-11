"""导入所有工具，触发注册。新增工具时在这里加一行 import 即可。"""
from . import relations, affinity, pareto, radar  # noqa: F401

__all__ = ["relations", "affinity", "pareto", "radar"]
