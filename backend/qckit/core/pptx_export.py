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
def build_relations_pptx(payload: dict[str, Any]) -> io.BytesIO:
    topic = payload.get("topic", "关联图")
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    summary = payload.get("summary", "")
    recs = payload.get("recommendations", [])

    prs = _new_deck(f"关联图 · {topic}", "QCKit · Relations Diagram")
    slide = prs.slides[0]

    # 布局: 力导圆环 —— 简易环形位置计算
    cx, cy = Inches(6.8), Inches(4.2)
    radius_x, radius_y = Inches(4.2), Inches(2.5)
    n = max(1, len(nodes))
    positions: dict[str, tuple[Emu, Emu]] = {}

    # core 放中心, 其他环绕
    core_ids = [x["id"] for x in nodes if x.get("role") == "core"]
    others = [x for x in nodes if x.get("role") != "core"]

    if core_ids:
        # 多个 core 时垂直排列在中心
        for i, cid in enumerate(core_ids):
            offset = (i - (len(core_ids) - 1) / 2) * Inches(1.0)
            positions[cid] = (cx, cy + offset)
    ring_n = max(1, len(others))
    for i, node in enumerate(others):
        ang = 2 * math.pi * i / ring_n - math.pi / 2
        positions[node["id"]] = (cx + int(radius_x * math.cos(ang)),
                                 cy + int(radius_y * math.sin(ang)))

    # 画节点
    node_shapes: dict[str, Any] = {}
    for node in nodes:
        role = node.get("role", "normal")
        c = ROLE_COLORS.get(role, ROLE_COLORS["normal"])
        label = node.get("label", "")
        w = Inches(max(1.4, min(2.6, 0.28 * len(label) + 0.6)))
        h = Inches(0.55 if role != "core" else 0.65)
        x0, y0 = positions[node["id"]]
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                     x0 - w // 2, y0 - h // 2, w, h)
        shp.fill.solid(); shp.fill.fore_color.rgb = _rgb(c["bg"])
        shp.line.color.rgb = _rgb(c["border"])
        shp.line.width = Pt(1.5 if role != "core" else 2.5)
        _set_text(shp.text_frame, label,
                  size=13 if role != "core" else 14,
                  bold=(role in ("core", "key")),
                  color=c["text"])
        node_shapes[node["id"]] = shp

    # 画边 (直线连接) - python-pptx 的 connector 需要重新算 begin/end,
    # 更稳妥直接用 LINE 形状
    for e in edges:
        s, t = node_shapes.get(e["source"]), node_shapes.get(e["target"])
        if not s or not t:
            continue
        sx = s.left + s.width // 2
        sy = s.top + s.height // 2
        tx = t.left + t.width // 2
        ty = t.top + t.height // 2
        conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx, sy, tx, ty)
        strength = int(e.get("strength", 1) or 1)
        conn.line.color.rgb = _rgb("64748B" if strength >= 3 else "94A3B8")
        conn.line.width = Pt(1.0 + 0.7 * strength)
        # 箭头
        line = conn.line._get_or_add_ln()
        from pptx.oxml.ns import qn
        from lxml import etree
        tail = etree.SubElement(line, qn("a:tailEnd"))
        tail.set("type", "triangle")
        # 边标签 (小文本框在中点)
        lbl = e.get("label", "")
        if lbl:
            tb = slide.shapes.add_textbox(
                (sx + tx) // 2 - Inches(0.5), (sy + ty) // 2 - Inches(0.15),
                Inches(1.0), Inches(0.3))
            tb.fill.solid(); tb.fill.fore_color.rgb = _rgb("FFFFFF")
            tb.line.color.rgb = _rgb("E2E8F0")
            _set_text(tb.text_frame, lbl, size=9, color="475569")

    # ============= 第二页: 解读 & 建议 =============
    if summary or recs:
        slide2 = prs.slides.add_slide(prs.slide_layouts[6])
        hdr = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(0), Inches(0),
                                      prs.slide_width, Inches(0.6))
        hdr.fill.solid(); hdr.fill.fore_color.rgb = _rgb("0F172A")
        hdr.line.fill.background()
        _set_text(hdr.text_frame, f"分析结论 · {topic}", size=18, bold=True,
                  color="FFFFFF", align=PP_ALIGN.LEFT)
        hdr.text_frame.margin_left = Inches(0.3)

        # 左: 整体解读
        left = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
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
        p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run(); run.text = ""
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.LEFT
        r = p2.add_run(); r.text = summary
        r.font.name = FONT; r.font.size = Pt(13); r.font.color.rgb = _rgb("334155")

        # 右: 改善建议
        right = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
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

    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf
