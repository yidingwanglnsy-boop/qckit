"""合成完整 QCC 项目 PPTX —— 封面 + 各阶段分隔页 + 每附件复用工具的 build_ 函数.

结构:
  slide 1  项目封面 (圈名/圈长/主题/日期/成员)
  slide 2  QC-STORY 目录
  for each stage in [select, current, target, cause, root,
                     measure, schedule, execute, evaluate, standard]:
    if any attachment:
      分隔页 (阶段标题 + 附件列表)
      逐附件 → 调该工具的 build_<tool>_pptx() 把 slides 复制过来
  末尾  完整报告完.
"""
from __future__ import annotations

import copy
import io
from datetime import datetime
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# 复用已有的 build_ 函数
from ..brand import get_brand
from . import fishbone_pptx as _fb
from . import pptx_export as _px

FONT = _px.FONT

_BRAND = None
def _brand():
    global _BRAND
    if _BRAND is None:
        _BRAND = get_brand()
    return _BRAND

BUILDERS = {
    "relations":  lambda p: _px.build_relations_pptx(p),
    "affinity":   lambda p: _px.build_affinity_pptx(p),
    "pareto":     lambda p: _px.build_pareto_pptx(p),
    "radar":      lambda p: _px.build_radar_pptx(p),
    "w5h2":       lambda p: _px.build_w5h2_pptx(p),
    "rca":        lambda p: _px.build_rca_pptx(p),
    "fishbone":   lambda p: _fb.build_fishbone_pptx(p, _brand()),
    "tree":       lambda p: _px.build_tree_pptx(p),
    "matrix":     lambda p: _px.build_matrix_pptx(p),
    "mda":        lambda p: _px.build_mda_pptx(p),
    "pdpc":       lambda p: _px.build_pdpc_pptx(p),
    "arrow":      lambda p: _px.build_arrow_pptx(p),
}

STAGE_LABELS = {
    "select": "① 选题理由",  "current": "② 现状调查",
    "target": "③ 目标设定",  "cause":   "④ 要因分析",
    "root":   "⑤ 根因确认",  "measure": "⑥ 对策制定",
    "schedule":"⑦ 实施排期", "execute": "⑧ 实施记录",
    "evaluate":"⑨ 效果确认", "standard":"⑩ 标准化",
}
STAGES = list(STAGE_LABELS.keys())


def build_project_pptx(project: dict) -> io.BytesIO:
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    _cover(prs, blank, project)
    _toc(prs, blank, project)

    stages = project.get("stages", {})
    for stage in STAGES:
        atts = stages.get(stage, []) or []
        if not atts:
            continue
        _stage_divider(prs, blank, stage, atts)
        for att in atts:
            _merge_attachment(prs, att)

    _closing(prs, blank, project)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# ── 封面 ──────────────────────────────────────────────
def _cover(prs, layout, project):
    s = prs.slides.add_slide(layout)
    # 顶部渐变条
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
        prs.slide_width, Inches(1.6))
    bar.fill.solid(); bar.fill.fore_color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    bar.line.fill.background()

    tb = s.shapes.add_textbox(Inches(0.6), Inches(0.4),
        prs.slide_width - Inches(1.2), Inches(1.0))
    _px._set_text(tb.text_frame, "QCC 品管圈项目报告",
                   size=32, bold=True, color="FFFFFF", align=PP_ALIGN.LEFT)

    tb = s.shapes.add_textbox(Inches(0.6), Inches(1.05),
        prs.slide_width - Inches(1.2), Inches(0.5))
    _px._set_text(tb.text_frame, project.get("name", "(未命名项目)"),
                   size=18, color="DBEAFE", align=PP_ALIGN.LEFT)

    # 元信息卡
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1.5), Inches(2.5), Inches(10.3), Inches(3.5))
    box.fill.solid(); box.fill.fore_color.rgb = RGBColor(0xF8, 0xFA, 0xFC)
    box.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0); box.line.width = Pt(1)

    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.3); tf.margin_top = Inches(0.25)
    lines = [
        ("主题", project.get("topic", "—")),
        ("圈名", project.get("circle", "—")),
        ("圈长", project.get("leader", "—")),
        ("成员", "、".join(project.get("members", []) or ["—"])),
        ("创建时间", project.get("created_at", "")[:10]),
        ("更新时间", project.get("updated_at", "")[:10]),
    ]
    tf.text = ""
    for i, (k, v) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(10)
        r = p.add_run()
        r.text = f"◆ {k}："
        r.font.name = FONT; r.font.size = Pt(15); r.font.bold = True
        r.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
        r2 = p.add_run()
        r2.text = str(v)
        r2.font.name = FONT; r2.font.size = Pt(15)
        r2.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)


# ── 目录 ──────────────────────────────────────────────
def _toc(prs, layout, project):
    s = prs.slides.add_slide(layout)
    hdr = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
        prs.slide_width, Inches(0.7))
    hdr.fill.solid(); hdr.fill.fore_color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    hdr.line.fill.background()
    _px._set_text(hdr.text_frame, "目录 · QC-STORY 十步法",
                   size=20, bold=True, color="FFFFFF", align=PP_ALIGN.LEFT)
    hdr.text_frame.margin_left = Inches(0.4)

    stages = project.get("stages", {})
    x = 0.8; y = 1.2
    for i, stage in enumerate(STAGES):
        atts = stages.get(stage, []) or []
        col = i % 2
        row = i // 2
        px = 0.8 + col * 6.2
        py = 1.2 + row * 1.15
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(px), Inches(py), Inches(5.8), Inches(1.0))
        has = bool(atts)
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(0xDB, 0xEA, 0xFE) if has else RGBColor(0xF1, 0xF5, 0xF9)
        box.line.color.rgb = RGBColor(0x60, 0xA5, 0xFA) if has else RGBColor(0xCB, 0xD5, 0xE1)
        box.line.width = Pt(1)
        tf = box.text_frame; tf.word_wrap = True
        tf.margin_left = Inches(0.2); tf.margin_top = Inches(0.15)
        _px._set_text(tf, STAGE_LABELS[stage],
                       size=14, bold=True,
                       color="1E40AF" if has else "94A3B8",
                       align=PP_ALIGN.LEFT)
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = f"  {len(atts)} 份产出" if has else "  (未挂产出)"
        r.font.name = FONT; r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)


# ── 阶段分隔页 ─────────────────────────────────────────
def _stage_divider(prs, layout, stage, atts):
    s = prs.slides.add_slide(layout)
    # 大标题
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(2.5),
        prs.slide_width, Inches(2.5))
    bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    bg.line.fill.background()
    tf = bg.text_frame
    tf.margin_left = Inches(0.6)
    _px._set_text(tf, STAGE_LABELS.get(stage, stage),
                   size=44, bold=True, color="FFFFFF", align=PP_ALIGN.LEFT)
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = "  ".join(f"· {a.get('title','')} ({a.get('tool','')})" for a in atts)
    r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = RGBColor(0xDB, 0xEA, 0xFE)


# ── 附件合并: 复用工具的 build_ 函数 ────────────────────
def _merge_attachment(prs, att):
    tool = att.get("tool")
    builder = BUILDERS.get(tool)
    if not builder:
        return
    # 组装 payload (兼容各工具 build_ 函数的入参形状)
    payload = dict(att.get("result") or {})
    snap = att.get("snapshot") or {}
    # 缺 topic 时补
    payload.setdefault("topic", snap.get("topic") or att.get("title") or tool)
    try:
        buf = builder(payload)
    except Exception:
        # 单个工具失败不影响整包
        return

    # 把子 pptx 的所有 slide 复制过来
    child = Presentation(buf)
    for cs in child.slides:
        _copy_slide(prs, cs)


def _copy_slide(dst_prs, src_slide):
    """把 src_slide 的形状拷贝到目标 prs 的新 slide。

    python-pptx 没有直接 clone_slide, 我们采用形状 XML 拷贝。
    """
    blank = dst_prs.slide_layouts[6]
    ns = dst_prs.slides.add_slide(blank)
    # 复制 spTree 下的 shape XML
    src_tree = src_slide.shapes._spTree
    dst_tree = ns.shapes._spTree
    for elem in list(src_tree):
        tag = elem.tag.split("}")[-1]
        if tag in ("nvGrpSpPr", "grpSpPr"):
            continue  # 跳过组容器属性 (会与已存在的冲突)
        dst_tree.append(copy.deepcopy(elem))


# ── 尾页 ──────────────────────────────────────────────
def _closing(prs, layout, project):
    s = prs.slides.add_slide(layout)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
        prs.slide_width, prs.slide_height)
    bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    bg.line.fill.background()

    tb = s.shapes.add_textbox(Inches(0.6), Inches(2.8),
        prs.slide_width - Inches(1.2), Inches(1.5))
    _px._set_text(tb.text_frame, "感谢聆听 · 持续改进",
                   size=40, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)

    tb = s.shapes.add_textbox(Inches(0.6), Inches(4.5),
        prs.slide_width - Inches(1.2), Inches(0.5))
    _px._set_text(tb.text_frame,
                   f"{project.get('circle') or ''}  ·  " +
                   datetime.now().strftime("%Y-%m-%d"),
                   size=16, color="DBEAFE", align=PP_ALIGN.CENTER)
