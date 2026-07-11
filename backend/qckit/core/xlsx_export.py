"""XLSX 导出 —— 由 BrandConfig 驱动颜色/字体。

一个工具 = 一个 build_*_xlsx(payload, brand) -> io.BytesIO
表头背景 / 强调色 / 字体全部走品牌主题。
"""
from __future__ import annotations

import io
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from ..brand import BrandConfig


# ─── 样式工厂（缓存到本次导出） ──────────────────────────────────
def _styler(brand: BrandConfig):
    fz = brand.font_zh
    thin = Side(style="thin", color=brand.neutral)
    border = Border(top=thin, left=thin, right=thin, bottom=thin)

    def _fill(hex6: str) -> PatternFill:
        return PatternFill("solid", fgColor=hex6)

    def _font(*, color: str, bold: bool = False, size: int = 11) -> Font:
        return Font(name=fz, color=color, bold=bold, size=size)

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left   = Alignment(horizontal="left",   vertical="center", wrap_text=True)

    return {
        "header": {
            "fill": _fill(brand.primary),
            "font": _font(color=brand.text_on_primary, bold=True, size=11),
            "align": center, "border": border,
        },
        "header_alt": {
            "fill": _fill(brand.secondary),
            "font": _font(color=brand.text_on_primary, bold=True, size=11),
            "align": center, "border": border,
        },
        "key_required": {   # 必填 key 列（症结/Why 等）
            "fill": _fill(_tint(brand.secondary, 0.85)),
            "font": _font(color=brand.secondary, bold=True),
            "align": left, "border": border,
        },
        "key_required_alt": {  # 第 2 个必填列（末端原因/What 等）
            "fill": _fill(_tint(brand.warn, 0.85)),
            "font": _font(color=_darken(brand.warn), bold=True),
            "align": left, "border": border,
        },
        "ai": {              # AI 补全
            "fill": _fill(_tint(brand.warn, 0.90)),
            "font": _font(color=_darken(brand.warn)),
            "align": left, "border": border,
        },
        "plain": {
            "fill": PatternFill(fill_type=None),
            "font": _font(color=brand.text),
            "align": left, "border": border,
        },
        "idx": {
            "fill": _fill(_tint(brand.neutral, 0.5)),
            "font": _font(color=brand.text, bold=True),
            "align": center, "border": border,
        },
        "accent_solid": {    # 要因=是
            "fill": _fill(brand.accent),
            "font": _font(color="FFFFFF", bold=True),
            "align": center, "border": border,
        },
        "accent_muted": {    # 要因=否
            "fill": _fill(_tint(brand.neutral, 0.4)),
            "font": _font(color=brand.text),
            "align": center, "border": border,
        },
    }


def _apply(cell, style: dict) -> None:
    cell.fill = style["fill"]
    cell.font = style["font"]
    cell.alignment = style["align"]
    cell.border = style["border"]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "".join(f"{max(0, min(255, int(c))):02X}" for c in rgb)


def _tint(hex6: str, amount: float) -> str:
    """向白色混合：amount=0 原色，1 纯白。"""
    r, g, b = _hex_to_rgb(hex6)
    return _rgb_to_hex((r + (255 - r) * amount,
                        g + (255 - g) * amount,
                        b + (255 - b) * amount))


def _darken(hex6: str, amount: float = 0.35) -> str:
    r, g, b = _hex_to_rgb(hex6)
    return _rgb_to_hex((r * (1 - amount), g * (1 - amount), b * (1 - amount)))


def _title_row(ws, text: str, brand: BrandConfig, ncols: int) -> None:
    """第 1 行标题横幅，第 2 行公司名（可选），第 3 行留空。"""
    ws.cell(1, 1).value = text
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(1, 1)
    c.fill = PatternFill("solid", fgColor=brand.primary)
    c.font = Font(name=brand.font_zh, color=brand.text_on_primary,
                  bold=True, size=16)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 32
    if brand.company:
        c2 = ws.cell(2, 1)
        c2.value = brand.company
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
        c2.font = Font(name=brand.font_zh, color="64748B", italic=True, size=10)
        c2.alignment = Alignment(horizontal="right", indent=1)
        ws.row_dimensions[2].height = 18


# ─── 5W2H ────────────────────────────────────────────────────────
W5H2_HEADERS = [
    ("#", 5), ("根因 (Why)", 32), ("对象 (What)", 20), ("地点 (Where)", 16),
    ("时间 (When)", 14), ("责任人 (Who)", 12), ("方法 (How)", 26),
    ("程度 (How Much)", 16),
]
W5H2_KEYS = ["_idx", "why", "what", "where", "when", "who", "how", "how_much"]


def build_w5h2_xlsx(payload: dict[str, Any], brand: BrandConfig) -> io.BytesIO:
    topic = payload.get("topic", "5W2H")
    rows = payload.get("rows", [])
    reasoning = payload.get("reasoning", "")

    wb = Workbook()
    ws = wb.active
    ws.title = "5W2H"
    S = _styler(brand)
    ncols = len(W5H2_HEADERS)

    _title_row(ws, f"5W2H 分析 · {topic}", brand, ncols)
    header_row = 3 if brand.company else 2

    # 表头
    for i, (h, w) in enumerate(W5H2_HEADERS, 1):
        c = ws.cell(header_row, i, h)
        _apply(c, S["header"] if i != 2 else S["header_alt"])
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[header_row].height = 26

    # 数据
    for r_idx, row in enumerate(rows, header_row + 1):
        inferred = set(row.get("inferred", []))
        for c_idx, key in enumerate(W5H2_KEYS, 1):
            cell = ws.cell(r_idx, c_idx)
            if key == "_idx":
                cell.value = r_idx - header_row
                _apply(cell, S["idx"])
            elif key == "why":
                cell.value = row.get("why", "")
                _apply(cell, S["key_required"])
            elif key in inferred:
                cell.value = f"🤖 {row.get(key, '')}"
                _apply(cell, S["ai"])
            else:
                cell.value = row.get(key, "") or "—"
                _apply(cell, S["plain"])
        ws.row_dimensions[r_idx].height = 42

    # 推理逻辑
    if reasoning:
        r = header_row + len(rows) + 2
        ws.cell(r, 1, "🤖 AI 推理逻辑").font = Font(
            name=brand.font_zh, bold=True, color=brand.secondary, size=12)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
        ws.cell(r + 1, 1, reasoning)
        ws.merge_cells(start_row=r + 1, start_column=1,
                       end_row=r + 1, end_column=ncols)
        rc = ws.cell(r + 1, 1)
        rc.font = Font(name=brand.font_zh, color=brand.text, size=10)
        rc.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r + 1].height = 80

    buf = io.BytesIO(); wb.save(buf); buf.seek(0); return buf


# ─── RCA 根因确认 ─────────────────────────────────────────────────
RCA_HEADERS = [
    ("#", 5), ("症结 (Symptom)", 22), ("末端原因 (Root Cause)", 26),
    ("确认内容 (Content)", 28), ("确认方法 (Method)", 20),
    ("确认结果 (Result)", 26), ("责任人 (Owner)", 12),
    ("完成时间 (Due)", 14), ("是否要因 (Key?)", 12),
]
RCA_KEYS = ["_idx", "symptom", "cause", "content", "method",
            "result", "owner", "due", "is_key"]


def build_rca_xlsx(payload: dict[str, Any], brand: BrandConfig) -> io.BytesIO:
    topic = payload.get("topic", "根因确认")
    rows = payload.get("rows", [])
    reasoning = payload.get("reasoning", "")

    wb = Workbook()
    ws = wb.active
    ws.title = "根因确认"
    S = _styler(brand)
    ncols = len(RCA_HEADERS)

    _title_row(ws, f"根因确认 · {topic}", brand, ncols)
    header_row = 3 if brand.company else 2

    for i, (h, w) in enumerate(RCA_HEADERS, 1):
        c = ws.cell(header_row, i, h)
        _apply(c, S["header_alt"] if i in (2, 3) else S["header"])
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[header_row].height = 26

    for r_idx, row in enumerate(rows, header_row + 1):
        inferred = set(row.get("inferred", []))
        is_key_val = (row.get("is_key") or "").strip()
        for c_idx, key in enumerate(RCA_KEYS, 1):
            cell = ws.cell(r_idx, c_idx)
            if key == "_idx":
                cell.value = r_idx - header_row
                _apply(cell, S["idx"])
            elif key == "symptom":
                cell.value = row.get("symptom", "")
                _apply(cell, S["key_required"])
            elif key == "cause":
                cell.value = row.get("cause", "")
                _apply(cell, S["key_required_alt"])
            elif key == "is_key":
                cell.value = is_key_val or "—"
                if is_key_val == "是":
                    _apply(cell, S["accent_solid"])
                elif is_key_val == "否":
                    _apply(cell, S["accent_muted"])
                elif key in inferred:
                    _apply(cell, S["ai"])
                else:
                    _apply(cell, S["plain"])
            elif key in inferred:
                cell.value = f"🤖 {row.get(key, '')}"
                _apply(cell, S["ai"])
            else:
                cell.value = row.get(key, "") or "—"
                _apply(cell, S["plain"])
        ws.row_dimensions[r_idx].height = 42

    if reasoning:
        r = header_row + len(rows) + 2
        ws.cell(r, 1, "🤖 AI 推理逻辑").font = Font(
            name=brand.font_zh, bold=True, color=brand.secondary, size=12)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
        ws.cell(r + 1, 1, reasoning)
        ws.merge_cells(start_row=r + 1, start_column=1,
                       end_row=r + 1, end_column=ncols)
        rc = ws.cell(r + 1, 1)
        rc.font = Font(name=brand.font_zh, color=brand.text, size=10)
        rc.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r + 1].height = 80

    buf = io.BytesIO(); wb.save(buf); buf.seek(0); return buf
