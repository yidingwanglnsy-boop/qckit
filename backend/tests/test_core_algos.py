"""关键算法单测: CPM 关键路径 + PCA 降维 + safe_json 解析。

运行: cd backend && .venv/bin/python -m pytest tests/ -v
"""
from __future__ import annotations

import math

import pytest


# ══════════════════════════════════════════════════════════════
# 1. CPM (箭线图关键路径)
# ══════════════════════════════════════════════════════════════
from qckit.tools.arrow.service import TaskOut, _cpm


def test_cpm_diamond_topology():
    """经典 A→B→D, A→C→D, D→E 菱形拓扑."""
    tasks = [
        TaskOut(name="A", duration=3, predecessors=[]),
        TaskOut(name="B", duration=5, predecessors=["A"]),
        TaskOut(name="C", duration=2, predecessors=["A"]),
        TaskOut(name="D", duration=4, predecessors=["B", "C"]),
        TaskOut(name="E", duration=1, predecessors=["D"]),
    ]
    critical, dur = _cpm(tasks)
    assert dur == 13
    assert critical == ["A", "B", "D", "E"]
    idx = {t.name: t for t in tasks}
    assert idx["C"].slack == 3
    assert idx["A"].slack == 0
    assert idx["B"].is_critical
    assert not idx["C"].is_critical


def test_cpm_linear_chain():
    """线性依赖 A→B→C, 所有任务都是关键路径."""
    tasks = [
        TaskOut(name="A", duration=2, predecessors=[]),
        TaskOut(name="B", duration=3, predecessors=["A"]),
        TaskOut(name="C", duration=1, predecessors=["B"]),
    ]
    critical, dur = _cpm(tasks)
    assert dur == 6
    assert critical == ["A", "B", "C"]
    assert all(t.is_critical for t in tasks)


def test_cpm_parallel_branches():
    """并行两条 A→B, A→C, 慢的那条是关键路径."""
    tasks = [
        TaskOut(name="A", duration=1, predecessors=[]),
        TaskOut(name="B", duration=5, predecessors=["A"]),
        TaskOut(name="C", duration=2, predecessors=["A"]),
    ]
    critical, dur = _cpm(tasks)
    assert dur == 6
    assert critical == ["A", "B"]
    idx = {t.name: t for t in tasks}
    assert idx["C"].slack == 3


def test_cpm_cycle_returns_empty():
    """循环依赖时返回空列表 (不 panic)."""
    tasks = [
        TaskOut(name="A", duration=1, predecessors=["B"]),
        TaskOut(name="B", duration=1, predecessors=["A"]),
    ]
    critical, dur = _cpm(tasks)
    assert critical == []
    assert dur == 0


# ══════════════════════════════════════════════════════════════
# 2. PCA (矩阵数据解析 · 纯 Python 实现)
# ══════════════════════════════════════════════════════════════
from qckit.tools.mda.service import _pca_2d, _z_score


def test_z_score_basics():
    result = _z_score([1, 2, 3, 4, 5])
    # 均值应为 0
    assert abs(sum(result) / len(result)) < 1e-9
    # 标准差应为 1 (人口 std, N 除法)
    var = sum(x * x for x in result) / len(result)
    assert abs(var - 1) < 1e-9


def test_z_score_constant_column():
    """所有值相同时应返回全 0, 不能除零 panic."""
    result = _z_score([5, 5, 5])
    assert result == [0, 0, 0]


def test_pca_2d_captures_main_variance():
    """沿一条主轴分散的数据 → PC1 应吃掉绝大多数方差."""
    # 沿 (1,1,1,1) 方向分散
    matrix = [
        [2.0, 2.0, 2.0, 2.0],
        [0.5, 0.5, 0.5, 0.5],
        [-1.0, -1.0, -1.0, -1.0],
        [-1.5, -1.5, -1.5, -1.5],
        [1.0, 1.0, 1.0, 1.0],
    ]
    proj, var_ratio = _pca_2d(matrix)
    assert len(proj) == 5
    assert len(var_ratio) == 2
    # PC1 应吃 >95% 方差
    assert var_ratio[0] > 0.95
    # PC1 上的排序应与原始综合得分一致
    order = sorted(range(5), key=lambda i: proj[i][0])
    expected = sorted(range(5), key=lambda i: matrix[i][0])
    assert order == expected


def test_pca_2d_orthogonal_data():
    """4 象限点应能被 PC1/PC2 各自捕获."""
    matrix = [
        [1.0, 0.0], [-1.0, 0.0],
        [0.0, 1.0], [0.0, -1.0],
    ]
    proj, var = _pca_2d(matrix)
    # PC1 + PC2 应几乎解释 100%
    assert var[0] + var[1] > 0.99


# ══════════════════════════════════════════════════════════════
# 3. LLM JSON 兜底解析
# ══════════════════════════════════════════════════════════════
from qckit.core.llm import _safe_json


def test_safe_json_direct():
    assert _safe_json('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_safe_json_with_markdown_fence():
    """LLM 有时会包 ```json ... ``` 包裹, 应能抠出."""
    text = """好的, 结果如下:
```json
{"nodes": [1,2,3], "ok": true}
```
希望有帮助!"""
    assert _safe_json(text) == {"nodes": [1, 2, 3], "ok": True}


def test_safe_json_with_prefix_suffix():
    """LLM 前后加了说明文字."""
    text = 'Result: {"score": 0.9, "label": "high"} — that\'s all.'
    assert _safe_json(text) == {"score": 0.9, "label": "high"}


def test_safe_json_invalid_raises():
    with pytest.raises(ValueError):
        _safe_json("this is not json at all")
