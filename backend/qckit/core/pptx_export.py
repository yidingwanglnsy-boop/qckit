"""PPTX 导出 —— 用 python-pptx 生成可继续编辑的原生形状。

设计原则:
  - 一个工具 = 一个 build_*_pptx(payload) 函数, 返回 io.BytesIO
  - 使用形状(矩形/连线/文本框), 不用图片, 到 PPT 里能选中编辑
  - 幻灯片 16:9 (13.333 x 7.5 英寸), 中文用微软雅黑
  - 颜色调色板与前端保持一致
"""
from __future__ import annotations

import io
import math
from typing import Any

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# —— 通用配色（与前端 Role 一致） —— #
ROLE_COLORS = {
    "core":    {"bg": "FEE2E2", "border": "DC2626", "text": "991B1B"},
    "key":     {"bg": "FEF3C7", "border": "D97706", "text": "92400E"},
    "conduct": {"bg": "DBEAFE", "border": "2563EB", "text": "1E40AF"},
    "normal":  {"bg": "F1F5F9", "border": "94A3B8", "text": "334155"},
}
PRIO_COLORS = {1: "DC2626", 2: "F59E0B", 3: "94A3B8"}
FONT = "Microsoft YaHei"


def _rgb(hex_str: str) -> RGBColor:
    return RGBColor.from_string(hex_str)


def _set_text(tf, text: str, *, size: int = 14, bold: bool = False,
              color: str = "111827", align: PP_ALIGN = PP_ALIGN.CENTER):
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Emu(36000)
    tf.margin_top = tf.margin_bottom = Emu(18000)
    p = tf.paragraphs[0]
    p.alignment = align
    p.text = ""
    run = p.add_run()
    run.text = text
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)


def _add_footer(prs, subtitle_hint: str = "") -> None:
    """给每一页底部加统一品牌页脚 —— QCKit · <hint>。"""
    for slide in prs.slides:
        # 底部横线
        line_y = prs.slide_height - Inches(0.28)
        ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
            Inches(0.35), line_y,
            prs.slide_width - Inches(0.35), line_y)
        ln.line.color.rgb = _rgb("E5E7EB"); ln.line.width = Pt(0.5)
        # 左下: 品牌
        left = slide.shapes.add_textbox(
            Inches(0.35), prs.slide_height - Inches(0.25),
            Inches(6), Inches(0.22))
        _set_text(left.text_frame, f"QCKit · {subtitle_hint}" if subtitle_hint else "QCKit",
                  size=8, color="94A3B8", align=PP_ALIGN.LEFT)
        # 右下: 页码占位 (由 PPT 自身页码机制维护; 这里直接留一句 slogan)
        right = slide.shapes.add_textbox(
            prs.slide_width - Inches(4.35), prs.slide_height - Inches(0.25),
            Inches(4), Inches(0.22))
        _set_text(right.text_frame,
                  "AI 驱动的 QCC 质量工具箱  ·  qckit.dev",
                  size=8, color="94A3B8", align=PP_ALIGN.RIGHT)


def _new_deck(title: str, subtitle: str = "") -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白版
    # 顶部标题条
    hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(0), Inches(0),
                                 prs.slide_width, Inches(0.6))
    hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
    hdr.line.fill.background()
    _set_text(hdr.text_frame, title, size=18, bold=True,
              color="FFFFFF", align=PP_ALIGN.LEFT)
    hdr.text_frame.margin_left = Inches(0.3)

    if subtitle:
        stf = slide.shapes.add_textbox(Inches(0.3), Inches(0.65),
                                       Inches(13), Inches(0.35)).text_frame
        _set_text(stf, subtitle, size=11, color="64748B", align=PP_ALIGN.LEFT)
    return prs


# ─────────────────────────────────────────────────────────
# 关联图
# ─────────────────────────────────────────────────────────
def _relations_layout(nodes: list, edges: list) -> dict:
    """三列分层布局: normal/conduct(左) → key(中) → core(右).
    每列内部按度数降序、上下均匀分布, 避免重叠."""
    # 度统计
    indeg: dict[str, int] = {}
    outdeg: dict[str, int] = {}
    for n in nodes:
        indeg[n["id"]] = 0; outdeg[n["id"]] = 0
    for e in edges:
        s, t = e.get("source"), e.get("target")
        if s in outdeg: outdeg[s] += 1
        if t in indeg: indeg[t] += 1

    col_of = {"normal": 0, "conduct": 0, "key": 1, "core": 2}
    cols: list[list[dict]] = [[], [], []]
    for n in nodes:
        cols[col_of.get(n.get("role", "normal"), 0)].append(n)
    # 每列按总度降序 (高度数放中间视觉更平衡)
    for c in cols:
        c.sort(key=lambda x: -(indeg[x["id"]] + outdeg[x["id"]]))

    # 三列 x 坐标 (16:9 slide, 剩余画面区高 1.0 - 7.2 英寸)
    col_xs = [Inches(2.2), Inches(6.8), Inches(11.0)]
    y_top, y_bot = Inches(1.4), Inches(6.9)
    positions: dict[str, tuple] = {}
    for ci, col in enumerate(cols):
        n = len(col)
        if n == 0: continue
        # 单节点垂直居中; 多节点等距
        if n == 1:
            positions[col[0]["id"]] = (col_xs[ci], (y_top + y_bot) // 2)
        else:
            step = (y_bot - y_top) // (n - 1)
            for i, node in enumerate(col):
                positions[node["id"]] = (col_xs[ci], y_top + step * i)
    return {"positions": positions, "indeg": indeg, "outdeg": outdeg,
            "cols": cols, "col_xs": col_xs}


def build_relations_pptx(payload: dict[str, Any]) -> io.BytesIO:
    topic = payload.get("topic", "关联图")
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    summary = payload.get("summary", "")
    recs = payload.get("recommendations", [])

    prs = _new_deck(f"关联图 · {topic}", "QCKit · Relations Diagram · 左→右 因果流向")
    slide = prs.slides[0]

    layout = _relations_layout(nodes, edges)
    positions = layout["positions"]
    indeg, outdeg = layout["indeg"], layout["outdeg"]

    # 三列标题条 & 底色带
    col_titles = [("一般 / 传导原因", "94A3B8"),
                  ("关键节点 (Key)",  "F59E0B"),
                  ("核心问题 (Core)", "DC2626")]
    for ci, (title, color) in enumerate(col_titles):
        x = layout["col_xs"][ci] - Inches(1.6)
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      x, Inches(1.0), Inches(3.2), Inches(0.32))
        band.fill.solid(); band.fill.fore_color.rgb = _rgb(color)
        band.line.fill.background()
        _set_text(band.text_frame, title, size=11, bold=True, color="FFFFFF")

    # 画节点
    node_shapes: dict[str, Any] = {}
    for node in nodes:
        role = node.get("role", "normal")
        c = ROLE_COLORS.get(role, ROLE_COLORS["normal"])
        raw = node.get("label", "")
        label = raw if len(raw) <= 14 else raw[:13] + "…"
        w = Inches(2.6 if role == "core" else 2.4)
        h = Inches(0.75 if role == "core" else 0.6)
        x0, y0 = positions.get(node["id"], (Inches(6.7), Inches(4.2)))
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                     x0 - w // 2, y0 - h // 2, w, h)
        shp.fill.solid(); shp.fill.fore_color.rgb = _rgb(c["bg"])
        shp.line.color.rgb = _rgb(c["border"])
        shp.line.width = Pt(2.5 if role == "core" else (1.75 if role == "key" else 1.0))
        _set_text(shp.text_frame, label,
                  size=13 if role == "core" else 11,
                  bold=(role in ("core", "key")),
                  color=c["text"])
        node_shapes[node["id"]] = shp
        # 度数小徽章 (in↓ / out↑)
        deg_txt = f"↓{indeg[node['id']]}  ↑{outdeg[node['id']]}"
        badge = slide.shapes.add_textbox(
            x0 - w // 2, y0 + h // 2 + Inches(0.02), w, Inches(0.22))
        _set_text(badge.text_frame, deg_txt, size=8, color="64748B")

    # 画边 —— 起点从形状右缘、终点从形状左缘, 更像流向
    for e in edges:
        s = node_shapes.get(e["source"]); t = node_shapes.get(e["target"])
        if not s or not t:
            continue
        sx = s.left + s.width           # 右缘
        sy = s.top + s.height // 2
        tx = t.left                     # 左缘
        ty = t.top + t.height // 2
        # 反向连接 (右列指左列) 时改用中心, 避免穿透
        if tx < sx:
            sx = s.left + s.width // 2
            tx = t.left + t.width // 2
        conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx, sy, tx, ty)
        strength = int(e.get("strength", 1) or 1)
        conn.line.color.rgb = _rgb("DC2626" if strength >= 3
                                   else "F59E0B" if strength == 2 else "94A3B8")
        conn.line.width = Pt(0.75 + 0.6 * strength)
        line = conn.line._get_or_add_ln()
        from pptx.oxml.ns import qn
        from lxml import etree
        tail = etree.SubElement(line, qn("a:tailEnd"))
        tail.set("type", "triangle")
        lbl = e.get("label", "")
        if lbl:
            tb = slide.shapes.add_textbox(
                (sx + tx) // 2 - Inches(0.55), (sy + ty) // 2 - Inches(0.14),
                Inches(1.1), Inches(0.28))
            tb.fill.solid(); tb.fill.fore_color.rgb = _rgb("FFFFFF")
            tb.line.color.rgb = _rgb("E2E8F0")
            _set_text(tb.text_frame, lbl if len(lbl) <= 10 else lbl[:9] + "…",
                      size=9, color="475569")

    # ============= 第二页: 出度/入度分析 =============
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    hdr = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  Inches(0), Inches(0),
                                  prs.slide_width, Inches(0.6))
    hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
    hdr.line.fill.background()
    _set_text(hdr.text_frame, f"出度 / 入度分析 · {topic}",
              size=18, bold=True, color="FFFFFF", align=PP_ALIGN.LEFT)
    hdr.text_frame.margin_left = Inches(0.3)
    stf = slide2.shapes.add_textbox(Inches(0.3), Inches(0.65),
                                    Inches(13), Inches(0.35)).text_frame
    _set_text(stf,
              "出度=该节点向外传导的因果条数 (驱动力) · 入度=被指向的条数 (被影响程度)",
              size=11, color="64748B", align=PP_ALIGN.LEFT)

    # 排序: 按 总度 降序取 Top 8
    ranked = sorted(nodes,
                    key=lambda x: -(indeg[x["id"]] + outdeg[x["id"]]))[:8]
    driver = max(nodes, key=lambda x: outdeg[x["id"]], default=None)
    outcome = max(nodes, key=lambda x: indeg[x["id"]], default=None)

    # 左: 结论卡片
    left = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Inches(0.4), Inches(1.15),
                                   Inches(4.4), Inches(5.9))
    left.fill.solid(); left.fill.fore_color.rgb = _rgb("F8FAFC")
    left.line.color.rgb = _rgb("2563EB"); left.line.width = Pt(2)
    tf = left.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.25)
    _set_text(tf, "🎯 关键节点识别", size=15, bold=True,
              color="1E40AF", align=PP_ALIGN.LEFT)

    def _add_conclusion(label, node, color, tip):
        if not node: return
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT; p.space_before = Pt(14)
        r = p.add_run(); r.text = label
        r.font.name = FONT; r.font.size = Pt(12); r.font.bold = True
        r.font.color.rgb = _rgb(color)
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        r2 = p2.add_run()
        r2.text = f"  {node.get('label','')} (出{outdeg[node['id']]} / 入{indeg[node['id']]})"
        r2.font.name = FONT; r2.font.size = Pt(13); r2.font.bold = True
        r2.font.color.rgb = _rgb("0F172A")
        p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.LEFT
        r3 = p3.add_run(); r3.text = f"  {tip}"
        r3.font.name = FONT; r3.font.size = Pt(11); r3.font.color.rgb = _rgb("475569")

    _add_conclusion("🚀 驱动节点 (最大出度)", driver, "059669",
                    "推动力最强 → 优先改善此处能同时缓解多个下游问题")
    _add_conclusion("🎯 结果节点 (最大入度)", outcome, "DC2626",
                    "汇聚多条因果链 → 通常是需要监控的核心 KPI")
    _add_conclusion("📊 全局统计", None, "1E40AF", "")
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = f"  节点 {len(nodes)} 个 · 因果边 {len(edges)} 条 · 平均度 {round(2 * len(edges) / max(1, len(nodes)), 1)}"
    r.font.name = FONT; r.font.size = Pt(11); r.font.color.rgb = _rgb("334155")

    # 右: 度数条形图 (Top 8, 出度绿+入度蓝 堆叠)
    box_x, box_y = Inches(5.05), Inches(1.15)
    box_w, box_h = Inches(7.9), Inches(5.9)
    box = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  box_x, box_y, box_w, box_h)
    box.fill.solid(); box.fill.fore_color.rgb = _rgb("FFFFFF")
    box.line.color.rgb = _rgb("E5E7EB")
    _set_text(box.text_frame, "🏆 度数 Top 8 (出度 + 入度)",
              size=13, bold=True, color="0F172A", align=PP_ALIGN.LEFT)
    box.text_frame.margin_left = Inches(0.25)
    box.text_frame.margin_top = Inches(0.2)

    max_deg = max((outdeg[n["id"]] + indeg[n["id"]] for n in ranked), default=1) or 1
    row_h = Inches(0.55)
    bar_area_x = box_x + Inches(2.6)
    bar_area_w = Inches(4.6)
    for i, node in enumerate(ranked):
        row_y = box_y + Inches(0.75) + i * row_h
        # 节点标签
        nl = slide2.shapes.add_textbox(box_x + Inches(0.15), row_y,
                                       Inches(2.4), Inches(0.4))
        label = node.get("label", "")
        _set_text(nl.text_frame, label if len(label) <= 12 else label[:11] + "…",
                  size=11, bold=True, color="1E293B", align=PP_ALIGN.LEFT)

        out_v = outdeg[node["id"]]; in_v = indeg[node["id"]]
        out_w = int(bar_area_w * out_v / max_deg) if max_deg else 0
        in_w  = int(bar_area_w * in_v  / max_deg) if max_deg else 0
        # 出度条 (绿, 左)
        if out_w > 0:
            b1 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                          bar_area_x, row_y + Inches(0.08),
                                          out_w, Inches(0.32))
            b1.fill.solid(); b1.fill.fore_color.rgb = _rgb("10B981")
            b1.line.fill.background()
        # 入度条 (蓝, 紧接右)
        if in_w > 0:
            b2 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                          bar_area_x + out_w, row_y + Inches(0.08),
                                          in_w, Inches(0.32))
            b2.fill.solid(); b2.fill.fore_color.rgb = _rgb("3B82F6")
            b2.line.fill.background()
        # 数值标签
        vtxt = slide2.shapes.add_textbox(
            bar_area_x + out_w + in_w + Inches(0.05),
            row_y + Inches(0.05), Inches(1.2), Inches(0.35))
        _set_text(vtxt.text_frame, f"↑{out_v}  ↓{in_v}",
                  size=10, color="334155", align=PP_ALIGN.LEFT)

    # 图例
    lg_y = box_y + box_h - Inches(0.4)
    lg1 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  box_x + Inches(0.25), lg_y,
                                  Inches(0.2), Inches(0.2))
    lg1.fill.solid(); lg1.fill.fore_color.rgb = _rgb("10B981"); lg1.line.fill.background()
    t1 = slide2.shapes.add_textbox(box_x + Inches(0.5), lg_y - Inches(0.02),
                                   Inches(1.5), Inches(0.25))
    _set_text(t1.text_frame, "↑ 出度 (驱动)", size=10, color="065F46", align=PP_ALIGN.LEFT)
    lg2 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  box_x + Inches(2.0), lg_y,
                                  Inches(0.2), Inches(0.2))
    lg2.fill.solid(); lg2.fill.fore_color.rgb = _rgb("3B82F6"); lg2.line.fill.background()
    t2 = slide2.shapes.add_textbox(box_x + Inches(2.25), lg_y - Inches(0.02),
                                   Inches(1.5), Inches(0.25))
    _set_text(t2.text_frame, "↓ 入度 (被影响)", size=10, color="1E40AF", align=PP_ALIGN.LEFT)

    # ============= 第三页: 解读 & 建议 (原来的第二页) =============
    if summary or recs:
        slide3 = prs.slides.add_slide(prs.slide_layouts[6])
        hdr = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(0), Inches(0),
                                      prs.slide_width, Inches(0.6))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
        hdr.line.fill.background()
        _set_text(hdr.text_frame, f"分析结论 · {topic}", size=18, bold=True,
                  color="FFFFFF", align=PP_ALIGN.LEFT)
        hdr.text_frame.margin_left = Inches(0.3)

        left = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(0.4), Inches(1.0),
                                       Inches(6.2), Inches(5.8))
        left.fill.solid(); left.fill.fore_color.rgb = _rgb("F8FAFC")
        left.line.color.rgb = _rgb("2563EB"); left.line.width = Pt(2)
        tf = left.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.25)
        _set_text(tf, "📌 整体解读", size=15, bold=True, color="1E40AF",
                  align=PP_ALIGN.LEFT)
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        r = p2.add_run(); r.text = summary
        r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = _rgb("334155")

        right = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                        Inches(6.8), Inches(1.0),
                                        Inches(6.1), Inches(5.8))
        right.fill.solid(); right.fill.fore_color.rgb = _rgb("FFFFFF")
        right.line.color.rgb = _rgb("E5E7EB"); right.line.width = Pt(1)
        tf2 = right.text_frame
        tf2.word_wrap = True
        tf2.margin_left = tf2.margin_right = Inches(0.25)
        tf2.margin_top = Inches(0.25)
        _set_text(tf2, "🎯 改善建议", size=15, bold=True, color="065F46",
                  align=PP_ALIGN.LEFT)
        for i, rec in enumerate(recs, 1):
            pr = tf2.add_paragraph()
            pr.alignment = PP_ALIGN.LEFT
            pr.space_before = Pt(8)
            run = pr.add_run(); run.text = f"{i}. {rec}"
            run.font.name = FONT; run.font.size = Pt(12)
            run.font.color.rgb = _rgb("1F2937")

    buf = io.BytesIO()
    _add_footer(prs)
    prs.save(buf); buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────
# 亲和图 (KJ 法) - 看板式布局
# ─────────────────────────────────────────────────────────
def build_affinity_pptx(payload: dict[str, Any]) -> io.BytesIO:
    topic = payload.get("topic", "亲和图")
    groups = payload.get("groups", [])
    pool = payload.get("pool", [])
    insights = payload.get("insights", "")
    recs = payload.get("recommendations", [])

    prs = _new_deck(f"亲和图 · {topic}", "QCKit · Affinity Diagram (KJ)")
    slide = prs.slides[0]

    # 看板列
    n = max(1, len(groups))
    col_w = Inches(min(3.0, 12.6 / n))
    gap = Inches(0.15)
    start_x = Inches(0.4) + (Inches(12.6) - (col_w * n + gap * (n - 1))) // 2
    y_top = Inches(1.05)
    col_h = Inches(6.1)

    for i, g in enumerate(groups):
        x = start_x + i * (col_w + gap)
        prio = int(g.get("priority", 2) or 2)
        # 列背景
        col = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y_top, col_w, col_h)
        col.fill.solid(); col.fill.fore_color.rgb = _rgb("F8FAFC")
        col.line.color.rgb = _rgb("E5E7EB"); col.line.width = Pt(1)
        # 优先级色带
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y_top, col_w, Inches(0.08))
        band.fill.solid(); band.fill.fore_color.rgb = _rgb(PRIO_COLORS.get(prio, "94A3B8"))
        band.line.fill.background()
        # 标题
        hd = slide.shapes.add_textbox(x, y_top + Inches(0.12), col_w, Inches(0.4))
        _set_text(hd.text_frame, f"P{prio} · {g.get('name','')}",
                  size=13, bold=True, color="0F172A", align=PP_ALIGN.LEFT)
        hd.text_frame.margin_left = Inches(0.12)
        # 摘要
        if g.get("summary"):
            sm = slide.shapes.add_textbox(x, y_top + Inches(0.5), col_w, Inches(0.5))
            _set_text(sm.text_frame, g["summary"],
                      size=10, color="64748B", align=PP_ALIGN.LEFT)
            sm.text_frame.margin_left = Inches(0.12)
        # 条目
        y_item = y_top + Inches(1.05)
        item_h = Inches(0.4)
        for it in g.get("items", []):
            if y_item + item_h > y_top + col_h - Inches(0.1):
                break
            chip = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                         x + Inches(0.1), y_item,
                                         col_w - Inches(0.2), item_h)
            chip.fill.solid(); chip.fill.fore_color.rgb = _rgb("FFFFFF")
            chip.line.color.rgb = _rgb("E2E8F0"); chip.line.width = Pt(0.75)
            _set_text(chip.text_frame, it, size=10, color="1E293B",
                      align=PP_ALIGN.LEFT)
            y_item += item_h + Inches(0.06)
        # 条目计数
        cnt = slide.shapes.add_textbox(x, y_top + col_h - Inches(0.3),
                                        col_w, Inches(0.25))
        _set_text(cnt.text_frame, f"{len(g.get('items', []))} 条",
                  size=9, color="94A3B8", align=PP_ALIGN.RIGHT)
        cnt.text_frame.margin_right = Inches(0.15)

    # 未分类池 (若有)
    if pool:
        pool_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                            Inches(0.4), Inches(7.2),
                                            Inches(12.6), Inches(0.25))
        pool_shape.fill.solid()
        pool_shape.fill.fore_color.rgb = _rgb("FEF3C7")
        pool_shape.line.color.rgb = _rgb("FDE68A")
        _set_text(pool_shape.text_frame,
                  f"未分类池: {' · '.join(pool[:8])}" + (f"（+{len(pool)-8}）" if len(pool) > 8 else ""),
                  size=9, color="92400E", align=PP_ALIGN.LEFT)
        pool_shape.text_frame.margin_left = Inches(0.15)

    # 第二页: 洞察 & 建议
    if insights or recs:
        slide2 = prs.slides.add_slide(prs.slide_layouts[6])
        hdr = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(0), Inches(0),
                                      prs.slide_width, Inches(0.6))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
        hdr.line.fill.background()
        _set_text(hdr.text_frame, f"分析结论 · {topic}", size=18, bold=True,
                  color="FFFFFF", align=PP_ALIGN.LEFT)
        hdr.text_frame.margin_left = Inches(0.3)

        left = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(0.4), Inches(1.0),
                                       Inches(6.2), Inches(5.8))
        left.fill.solid(); left.fill.fore_color.rgb = _rgb("F8FAFC")
        left.line.color.rgb = _rgb("059669"); left.line.width = Pt(2)
        tf = left.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.25)
        _set_text(tf, "💡 整体洞察", size=15, bold=True, color="065F46",
                  align=PP_ALIGN.LEFT)
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        r = p2.add_run(); r.text = insights
        r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = _rgb("334155")

        right = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                        Inches(6.8), Inches(1.0),
                                        Inches(6.1), Inches(5.8))
        right.fill.solid(); right.fill.fore_color.rgb = _rgb("FFFFFF")
        right.line.color.rgb = _rgb("E5E7EB")
        tf2 = right.text_frame
        tf2.word_wrap = True
        tf2.margin_left = tf2.margin_right = Inches(0.25)
        tf2.margin_top = Inches(0.25)
        _set_text(tf2, "🎯 改善建议", size=15, bold=True, color="065F46",
                  align=PP_ALIGN.LEFT)
        for i, rec in enumerate(recs, 1):
            pr = tf2.add_paragraph()
            pr.alignment = PP_ALIGN.LEFT
            pr.space_before = Pt(8)
            run = pr.add_run(); run.text = f"{i}. {rec}"
            run.font.name = FONT; run.font.size = Pt(12)
            run.font.color.rgb = _rgb("1F2937")

    buf = io.BytesIO()
    _add_footer(prs)
    prs.save(buf); buf.seek(0)
    return buf



# ─────────────────────────────────────────────────────────
# 柏拉图 (Pareto) - 原生柱状 chart + 手绘累积折线
# ─────────────────────────────────────────────────────────
def build_pareto_pptx(payload: dict[str, Any]) -> io.BytesIO:
    topic = payload.get("topic", "柏拉图")
    metric = payload.get("metric", "频次")
    items = payload.get("items", [])
    vital = set(payload.get("vital_few", []))
    insights = payload.get("insights", "")
    recs = payload.get("recommendations", [])
    total = payload.get("total") or sum(i.get("value", 0) for i in items) or 1
    threshold = float(payload.get("threshold", 80))

    prs = _new_deck(f"柏拉图 · {topic}",
                    f"QCKit · Pareto Diagram · 度量: {metric} · 合计: {total}")
    slide = prs.slides[0]
    if not items:
        _add_footer(prs)
        buf = io.BytesIO(); prs.save(buf); buf.seek(0); return buf

    cats = [i["name"] for i in items]
    values = [round(float(i.get("value", 0)), 2) for i in items]
    cum = [round(float(i.get("cumulative_percent", 0)), 2) for i in items]

    # 原生柱状图
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series(metric, values)
    chart_x, chart_y = Inches(0.4), Inches(1.0)
    chart_w, chart_h = Inches(9.0), Inches(6.0)
    graphic = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,
                                     chart_x, chart_y, chart_w, chart_h, cd)
    chart = graphic.chart
    chart.has_title = True
    chart.chart_title.text_frame.text = f"{topic} · {metric}分布"
    for p in chart.chart_title.text_frame.paragraphs:
        for r in p.runs:
            r.font.name = FONT; r.font.size = Pt(14); r.font.bold = True
    chart.has_legend = False

    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    plot.data_labels.font.size = Pt(9)
    plot.data_labels.font.name = FONT
    for i, pt in enumerate(plot.series[0].points):
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = _rgb("DC2626" if cats[i] in vital else "94A3B8")
        pt.format.line.color.rgb = _rgb("FFFFFF")

    # 累积折线覆盖 (python-pptx 无双轴, 用形状叠加)
    px, py = chart_x + Inches(0.7), chart_y + Inches(0.7)
    pw, ph = chart_w - Inches(1.4), chart_h - Inches(1.5)
    n = len(items)
    pts = [(px + int(pw * (i + 0.5) / n),
            py + int(ph * (1 - c / 100.0))) for i, c in enumerate(cum)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
        seg.line.color.rgb = _rgb("F59E0B"); seg.line.width = Pt(2.25)
    for (x, y), c in zip(pts, cum):
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                     x - Inches(0.08), y - Inches(0.08),
                                     Inches(0.16), Inches(0.16))
        dot.fill.solid(); dot.fill.fore_color.rgb = _rgb("F59E0B")
        dot.line.color.rgb = _rgb("FFFFFF")
        tb = slide.shapes.add_textbox(x - Inches(0.4), y - Inches(0.42),
                                       Inches(0.8), Inches(0.25))
        _set_text(tb.text_frame, f"{c:.0f}%", size=9, bold=True, color="B45309")

    # 阈值参考线 (虚线)
    y_th = py + int(ph * (1 - threshold / 100.0))
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px, y_th, px + pw, y_th)
    ln.line.color.rgb = _rgb("EF4444"); ln.line.width = Pt(1.0)
    try:
        from pptx.enum.dml import MSO_LINE_DASH_STYLE
        ln.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    except Exception:
        pass
    tb_th = slide.shapes.add_textbox(px + pw - Inches(0.7), y_th - Inches(0.32),
                                     Inches(0.7), Inches(0.25))
    _set_text(tb_th.text_frame, f"{threshold:g}%", size=9, bold=True, color="B91C1C",
              align=PP_ALIGN.RIGHT)

    # 右侧关键少数卡片
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Inches(9.55), Inches(1.0),
                                   Inches(3.45), Inches(6.0))
    card.fill.solid(); card.fill.fore_color.rgb = _rgb("FEF2F2")
    card.line.color.rgb = _rgb("DC2626"); card.line.width = Pt(2)
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.2)
    _set_text(tf, "🎯 关键少数 (Vital Few)", size=13, bold=True,
              color="991B1B", align=PP_ALIGN.LEFT)
    for name in [x for x in cats if x in vital]:
        idx = cats.index(name)
        pct = values[idx] / total * 100 if total else 0
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT; p.space_before = Pt(6)
        r1 = p.add_run(); r1.text = f"• {name}"
        r1.font.name = FONT; r1.font.size = Pt(11); r1.font.bold = True
        r1.font.color.rgb = _rgb("7F1D1D")
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        r2 = p2.add_run()
        r2.text = f"   {values[idx]} · 占 {pct:.1f}% · 累计 {cum[idx]:.1f}%"
        r2.font.name = FONT; r2.font.size = Pt(10)
        r2.font.color.rgb = _rgb("991B1B")

    # 第二页: 洞察 & 建议
    if insights or recs:
        slide2 = prs.slides.add_slide(prs.slide_layouts[6])
        hdr = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(0), Inches(0),
                                      prs.slide_width, Inches(0.6))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
        hdr.line.fill.background()
        _set_text(hdr.text_frame, f"分析结论 · {topic}", size=18, bold=True,
                  color="FFFFFF", align=PP_ALIGN.LEFT)
        hdr.text_frame.margin_left = Inches(0.3)

        left = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(0.4), Inches(1.0),
                                       Inches(6.2), Inches(5.8))
        left.fill.solid(); left.fill.fore_color.rgb = _rgb("F8FAFC")
        left.line.color.rgb = _rgb("DC2626"); left.line.width = Pt(2)
        tf = left.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.25)
        _set_text(tf, "💡 洞察", size=15, bold=True, color="991B1B",
                  align=PP_ALIGN.LEFT)
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        r = p2.add_run(); r.text = insights
        r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = _rgb("334155")

        right = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                        Inches(6.8), Inches(1.0),
                                        Inches(6.1), Inches(5.8))
        right.fill.solid(); right.fill.fore_color.rgb = _rgb("FFFFFF")
        right.line.color.rgb = _rgb("E5E7EB")
        tf2 = right.text_frame
        tf2.word_wrap = True
        tf2.margin_left = tf2.margin_right = Inches(0.25)
        tf2.margin_top = Inches(0.25)
        _set_text(tf2, "🎯 改善建议 (优先针对关键少数)",
                  size=14, bold=True, color="065F46", align=PP_ALIGN.LEFT)
        for i, rec in enumerate(recs, 1):
            pr = tf2.add_paragraph()
            pr.alignment = PP_ALIGN.LEFT; pr.space_before = Pt(8)
            run = pr.add_run(); run.text = f"{i}. {rec}"
            run.font.name = FONT; run.font.size = Pt(12)
            run.font.color.rgb = _rgb("1F2937")

    _add_footer(prs)
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf



# ─────────────────────────────────────────────────────────
# 雷达图 (Radar) - 原生 RADAR chart + 洞察页
# ─────────────────────────────────────────────────────────
def build_radar_pptx(payload: dict[str, Any]) -> io.BytesIO:
    topic = payload.get("topic", "雷达图")
    dims = payload.get("dimensions", [])
    entities = payload.get("entities", [])
    max_s = float(payload.get("max_score", 10))
    weak_th = float(payload.get("weak_threshold", 0.6))
    best = payload.get("best_entity", "")
    leaders = payload.get("dim_leaders", {}) or {}
    insights = payload.get("insights", "")
    recs = payload.get("recommendations", [])

    prs = _new_deck(f"雷达图 · {topic}",
                    f"QCKit · Radar · 维度 {len(dims)} · 对象 {len(entities)} · 满分 {max_s:g}")
    slide = prs.slides[0]
    if not dims or not entities:
        _add_footer(prs)
        buf = io.BytesIO(); prs.save(buf); buf.seek(0); return buf

    # 原生雷达图
    cd = CategoryChartData()
    cd.categories = dims
    for e in entities:
        cd.add_series(e["name"], e["scores"])

    chart_x, chart_y = Inches(0.4), Inches(1.0)
    chart_w, chart_h = Inches(8.5), Inches(6.0)
    graphic = slide.shapes.add_chart(XL_CHART_TYPE.RADAR,
                                     chart_x, chart_y, chart_w, chart_h, cd)
    chart = graphic.chart
    chart.has_title = True
    chart.chart_title.text_frame.text = f"{topic}"
    for p in chart.chart_title.text_frame.paragraphs:
        for r in p.runs:
            r.font.name = FONT; r.font.size = Pt(14); r.font.bold = True
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.name = FONT; chart.legend.font.size = Pt(10)

    # 右侧: 冠军卡 + 短板汇总
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Inches(9.05), Inches(1.0),
                                   Inches(3.95), Inches(2.6))
    card.fill.solid(); card.fill.fore_color.rgb = _rgb("ECFDF5")
    card.line.color.rgb = _rgb("059669"); card.line.width = Pt(2)
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.2)
    _set_text(tf, "🏆 综合最强", size=13, bold=True, color="065F46", align=PP_ALIGN.LEFT)
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = best
    r.font.name = FONT; r.font.size = Pt(20); r.font.bold = True
    r.font.color.rgb = _rgb("047857")
    if leaders:
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        p2.space_before = Pt(8)
        r2 = p2.add_run()
        r2.text = "各维度冠军:"
        r2.font.name = FONT; r2.font.size = Pt(11); r2.font.bold = True
        r2.font.color.rgb = _rgb("065F46")
        for dim, who in leaders.items():
            p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.LEFT
            r3 = p3.add_run()
            r3.text = f"• {dim}: {who}"
            r3.font.name = FONT; r3.font.size = Pt(10)
            r3.font.color.rgb = _rgb("064E3B")

    # 短板汇总卡
    weak_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                        Inches(9.05), Inches(3.75),
                                        Inches(3.95), Inches(3.25))
    weak_card.fill.solid(); weak_card.fill.fore_color.rgb = _rgb("FEF2F2")
    weak_card.line.color.rgb = _rgb("DC2626"); weak_card.line.width = Pt(2)
    tf2 = weak_card.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = Inches(0.2)
    tf2.margin_top = Inches(0.2)
    _set_text(tf2, f"⚠️ 短板 (< {weak_th*100:.0f}% 满分)",
              size=13, bold=True, color="991B1B", align=PP_ALIGN.LEFT)
    for e in entities:
        if not e.get("weak_dims"): continue
        p = tf2.add_paragraph(); p.alignment = PP_ALIGN.LEFT
        p.space_before = Pt(6)
        r = p.add_run(); r.text = f"• {e['name']} (均值 {e['average']})"
        r.font.name = FONT; r.font.size = Pt(11); r.font.bold = True
        r.font.color.rgb = _rgb("7F1D1D")
        p2 = tf2.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        r2 = p2.add_run(); r2.text = "   " + ", ".join(e["weak_dims"])
        r2.font.name = FONT; r2.font.size = Pt(10)
        r2.font.color.rgb = _rgb("991B1B")

    # 第二页: 洞察 + 建议
    if insights or recs:
        slide2 = prs.slides.add_slide(prs.slide_layouts[6])
        hdr = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(0), Inches(0),
                                      prs.slide_width, Inches(0.6))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
        hdr.line.fill.background()
        _set_text(hdr.text_frame, f"分析结论 · {topic}", size=18, bold=True,
                  color="FFFFFF", align=PP_ALIGN.LEFT)
        hdr.text_frame.margin_left = Inches(0.3)

        left = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(0.4), Inches(1.0),
                                       Inches(6.2), Inches(5.8))
        left.fill.solid(); left.fill.fore_color.rgb = _rgb("F8FAFC")
        left.line.color.rgb = _rgb("0284C7"); left.line.width = Pt(2)
        tf = left.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.25)
        _set_text(tf, "💡 对比洞察", size=15, bold=True, color="075985",
                  align=PP_ALIGN.LEFT)
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
        r = p2.add_run(); r.text = insights
        r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = _rgb("334155")

        right = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                        Inches(6.8), Inches(1.0),
                                        Inches(6.1), Inches(5.8))
        right.fill.solid(); right.fill.fore_color.rgb = _rgb("FFFFFF")
        right.line.color.rgb = _rgb("E5E7EB")
        tf2 = right.text_frame
        tf2.word_wrap = True
        tf2.margin_left = tf2.margin_right = Inches(0.25)
        tf2.margin_top = Inches(0.25)
        _set_text(tf2, "🎯 改善建议 (针对短板)",
                  size=14, bold=True, color="065F46", align=PP_ALIGN.LEFT)
        for i, rec in enumerate(recs, 1):
            pr = tf2.add_paragraph()
            pr.alignment = PP_ALIGN.LEFT; pr.space_before = Pt(8)
            run = pr.add_run(); run.text = f"{i}. {rec}"
            run.font.name = FONT; run.font.size = Pt(12)
            run.font.color.rgb = _rgb("1F2937")

    _add_footer(prs)
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf





# ─────────────────────────────────────────────────────────
# 5W2H 表格 - 多根因批量, 每行一条 + AI 补全字段黄底
# ─────────────────────────────────────────────────────────
def build_w5h2_pptx(payload: dict[str, Any]) -> io.BytesIO:
    topic = payload.get("topic", "5W2H")
    rows = payload.get("rows", [])
    reasoning = payload.get("reasoning", "")

    prs = _new_deck(f"5W2H · {topic}", f"QCKit · 5W2H 分析 · {len(rows)} 条根因")
    slide = prs.slides[0]

    if not rows:
        _add_footer(prs)
        buf = io.BytesIO(); prs.save(buf); buf.seek(0); return buf

    headers = ["#", "Why 根因", "What", "Where", "When", "Who", "How", "How Much"]
    keys = ["_idx", "why", "what", "where", "when", "who", "how", "how_much"]
    col_widths = [0.4, 2.6, 1.8, 1.4, 1.2, 1.2, 2.2, 1.5]  # inches, 合计 12.3

    n_rows = len(rows) + 1  # +header
    tx, ty = Inches(0.4), Inches(1.0)
    tw = Inches(sum(col_widths))
    # 行高：内容行随 rows 数量收缩
    body_h = 5.5 / max(len(rows), 1)   # 内容区总高 5.5"
    body_h = max(0.5, min(0.9, body_h))
    header_h = 0.4
    th = Inches(header_h + body_h * len(rows))

    table_shape = slide.shapes.add_table(n_rows, len(headers), tx, ty, tw, th)
    table = table_shape.table

    # 列宽
    for i, w in enumerate(col_widths):
        table.columns[i].width = Inches(w)
    table.rows[0].height = Inches(header_h)
    for i in range(1, n_rows):
        table.rows[i].height = Inches(body_h)

    # 表头
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.fill.solid(); cell.fill.fore_color.rgb = _rgb("0F172A")
        cell.margin_left = cell.margin_right = Inches(0.05)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        tf = cell.text_frame; tf.clear()
        _set_text(tf, h, size=10, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)

    # 数据行
    for r_idx, row in enumerate(rows, 1):
        inferred = set(row.get("inferred", []))
        for c_idx, key in enumerate(keys):
            cell = table.cell(r_idx, c_idx)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.03)

            if key == "_idx":
                val = str(r_idx)
                color, bg = "334155", "F1F5F9"
                bold = True
            elif key == "why":
                val = row.get("why", "")
                color, bg = "991B1B", "FEF2F2"
                bold = True
            elif key in inferred:
                val = row.get(key, "")
                color, bg = "B45309", "FFFBEB"   # AI 补全: 黄底
                bold = False
            else:
                val = row.get(key, "") or "—"
                color, bg = "1F2937", "FFFFFF"
                bold = False

            cell.fill.solid(); cell.fill.fore_color.rgb = _rgb(bg)
            tf = cell.text_frame; tf.clear(); tf.word_wrap = True
            _set_text(tf, val, size=9, bold=bold, color=color,
                      align=PP_ALIGN.LEFT if key != "_idx" else PP_ALIGN.CENTER)
            # AI 标记
            if key in inferred and val:
                p = tf.add_paragraph()
                r = p.add_run(); r.text = "🤖"
                r.font.name = FONT; r.font.size = Pt(7)
                r.font.color.rgb = _rgb("B45309")

    # 图例
    lg_y = ty + th + Inches(0.2)
    _mk_legend_swatch(slide, Inches(0.4), lg_y, "FEF2F2", "Why 根因（必填）", "991B1B")
    _mk_legend_swatch(slide, Inches(3.5), lg_y, "FFFBEB", "🤖 AI 联想补全", "B45309")

    # 第二页: 推理逻辑
    if reasoning:
        slide2 = prs.slides.add_slide(prs.slide_layouts[6])
        hdr = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(0), Inches(0),
                                      prs.slide_width, Inches(0.6))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
        hdr.line.fill.background()
        _set_text(hdr.text_frame, f"AI 推理逻辑 · {topic}", size=18, bold=True,
                  color="FFFFFF", align=PP_ALIGN.LEFT)
        hdr.text_frame.margin_left = Inches(0.3)

        box = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(0.5), Inches(1.0),
                                       prs.slide_width - Inches(1.0), Inches(5.8))
        box.fill.solid(); box.fill.fore_color.rgb = _rgb("FFFBEB")
        box.line.color.rgb = _rgb("F59E0B"); box.line.width = Pt(2)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.3)
        tf.margin_top = Inches(0.25)
        _set_text(tf, "🤖 推理", size=14, bold=True, color="B45309",
                  align=PP_ALIGN.LEFT)
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT
        p.space_before = Pt(8)
        r = p.add_run(); r.text = reasoning
        r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = _rgb("451A03")

    _add_footer(prs)
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf


def _mk_legend_swatch(slide, x, y, bg, label, color):
    sw = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.25), Inches(0.2))
    sw.fill.solid(); sw.fill.fore_color.rgb = _rgb(bg)
    sw.line.color.rgb = _rgb(color); sw.line.width = Pt(0.75)
    tb = slide.shapes.add_textbox(x + Inches(0.3), y - Inches(0.02),
                                   Inches(3.0), Inches(0.3))
    _set_text(tb.text_frame, label, size=10, color=color, align=PP_ALIGN.LEFT)


# ─────────────────────────────────────────────────────────
# 根因确认 (要因确认) - 症结 → 末端原因 (1:N) 表格
# ─────────────────────────────────────────────────────────
def build_rca_pptx(payload: dict[str, Any]) -> io.BytesIO:
    topic = payload.get("topic", "根因确认")
    rows = payload.get("rows", [])
    reasoning = payload.get("reasoning", "")

    prs = _new_deck(f"根因确认 · {topic}",
                    f"QCKit · 要因确认 · {len(rows)} 条末端原因")
    slide = prs.slides[0]
    if not rows:
        _add_footer(prs)
        buf = io.BytesIO(); prs.save(buf); buf.seek(0); return buf

    headers = ["#", "症结", "末端原因", "确认内容", "确认方法",
               "确认结果", "责任人", "完成时间", "是否要因"]
    keys = ["_idx", "symptom", "cause", "content", "method",
            "result", "owner", "due", "is_key"]
    col_widths = [0.35, 1.8, 1.9, 2.0, 1.5, 2.0, 0.9, 1.0, 0.85]  # ≈12.3

    n_rows = len(rows) + 1
    tx, ty = Inches(0.4), Inches(1.0)
    tw = Inches(sum(col_widths))
    body_h = max(0.45, min(0.85, 5.5 / max(len(rows), 1)))
    header_h = 0.4
    th = Inches(header_h + body_h * len(rows))

    table = slide.shapes.add_table(n_rows, len(headers), tx, ty, tw, th).table
    for i, w in enumerate(col_widths):
        table.columns[i].width = Inches(w)
    table.rows[0].height = Inches(header_h)
    for i in range(1, n_rows):
        table.rows[i].height = Inches(body_h)

    # 表头
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.fill.solid(); cell.fill.fore_color.rgb = _rgb("0F172A")
        cell.margin_left = cell.margin_right = Inches(0.05)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        tf = cell.text_frame; tf.clear()
        _set_text(tf, h, size=10, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)

    # 数据行 —— 同一症结连续行浅色底交替，视觉上分组
    prev_sym = None
    band_toggle = False
    for r_idx, row in enumerate(rows, 1):
        inferred = set(row.get("inferred", []))
        sym = row.get("symptom", "")
        if sym != prev_sym:
            band_toggle = not band_toggle
            prev_sym = sym
        sym_bg = "EFF6FF" if band_toggle else "F8FAFC"

        is_key_val = (row.get("is_key") or "").strip()
        key_is_yes = is_key_val in ("是", "Y", "yes", "Yes", "YES")

        for c_idx, key in enumerate(keys):
            cell = table.cell(r_idx, c_idx)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.03)

            if key == "_idx":
                val = str(r_idx); color, bg, bold = "334155", "F1F5F9", True
                align = PP_ALIGN.CENTER
            elif key == "symptom":
                val = sym; color, bg, bold = "1E3A8A", sym_bg, True
                align = PP_ALIGN.LEFT
            elif key == "cause":
                val = row.get("cause", ""); color, bg, bold = "7C2D12", "FEF3C7", True
                align = PP_ALIGN.LEFT
            elif key == "is_key":
                val = is_key_val or "—"
                if key_is_yes:
                    color, bg, bold = "FFFFFF", "DC2626", True
                elif is_key_val in ("否", "N", "no", "No", "NO"):
                    color, bg, bold = "334155", "F1F5F9", False
                else:
                    color, bg, bold = "B45309", "FEF3C7", True
                align = PP_ALIGN.CENTER
            elif key in inferred:
                val = row.get(key, ""); color, bg, bold = "B45309", "FFFBEB", False
                align = PP_ALIGN.LEFT
            else:
                val = row.get(key, "") or "—"
                color, bg, bold = "1F2937", "FFFFFF", False
                align = PP_ALIGN.LEFT

            cell.fill.solid(); cell.fill.fore_color.rgb = _rgb(bg)
            tf = cell.text_frame; tf.clear(); tf.word_wrap = True
            _set_text(tf, val, size=9, bold=bold, color=color, align=align)
            if key in inferred and val and key != "is_key":
                p = tf.add_paragraph()
                r = p.add_run(); r.text = "🤖"
                r.font.name = FONT; r.font.size = Pt(7)
                r.font.color.rgb = _rgb("B45309")

    # 图例
    lg_y = ty + th + Inches(0.2)
    _mk_legend_swatch(slide, Inches(0.4), lg_y, "FEF3C7", "症结/末端原因（必填）", "7C2D12")
    _mk_legend_swatch(slide, Inches(3.8), lg_y, "FFFBEB", "🤖 AI 联想补全", "B45309")
    _mk_legend_swatch(slide, Inches(6.6), lg_y, "DC2626", "要因", "FFFFFF")

    # 第二页：推理逻辑
    if reasoning:
        slide2 = prs.slides.add_slide(prs.slide_layouts[6])
        hdr = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(0), Inches(0),
                                      prs.slide_width, Inches(0.6))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
        hdr.line.fill.background()
        _set_text(hdr.text_frame, f"AI 推理逻辑 · {topic}", size=18, bold=True,
                  color="FFFFFF", align=PP_ALIGN.LEFT)
        hdr.text_frame.margin_left = Inches(0.3)

        box = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                     Inches(0.5), Inches(1.0),
                                     prs.slide_width - Inches(1.0), Inches(5.8))
        box.fill.solid(); box.fill.fore_color.rgb = _rgb("FFFBEB")
        box.line.color.rgb = _rgb("F59E0B"); box.line.width = Pt(2)
        tf = box.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.3); tf.margin_top = Inches(0.25)
        _set_text(tf, "🤖 推理", size=14, bold=True, color="B45309", align=PP_ALIGN.LEFT)
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT; p.space_before = Pt(8)
        r = p.add_run(); r.text = reasoning
        r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = _rgb("451A03")

    _add_footer(prs)
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf
