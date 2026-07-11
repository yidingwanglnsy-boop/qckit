"""build_fishbone_pptx —— PPT 原生形状画鱼骨（PPT 里可编辑）。

几何逻辑（模仿标准 Ishikawa）:
- 16:9 幻灯, 主脊水平居中, 鱼头在右
- 4 个 4M 大骨: 上/下各 2 根, 均以约 60° 斜角落到主脊
  - 上骨向左上延伸, 下骨向左下延伸, 与主脊夹角 30°
- 中骨(层 2)与主脊平行, 从大骨上某点水平向后延伸
- 末端(层 3)与大骨平行, 短斜线挂在中骨上
- 颜色 / 字体来源 ~/.qckit/brand.yaml
"""
from __future__ import annotations

import io
import math
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

from ..brand import BrandConfig


SLIDE_W, SLIDE_H = 12192000, 6858000                 # 16:9 EMU
BONE_ANGLE_DEG   = 30                                # 大骨与主脊夹角
BONE_LEN         = 1_900_000                         # 大骨长度


def _rgb(hex6: str) -> RGBColor:
    return RGBColor.from_string(hex6)


def _no_line(shape) -> None:
    shape.line.fill.background()


def _fill(shape, hex6: str) -> None:
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(hex6)


def _tint(hex6: str, k: float) -> str:
    r, g, b = int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)
    return "{:02X}{:02X}{:02X}".format(
        int(r + (255 - r) * k), int(g + (255 - g) * k), int(b + (255 - b) * k))


def _text(slide, x, y, w, h, txt: str, *, font: str, size: int, color: str,
          bold: bool = False, anchor: str = "l") -> None:
    tb = slide.shapes.add_textbox(Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h)))
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER,
                   "r": PP_ALIGN.RIGHT}[anchor]
    run = p.add_run()
    run.text = txt
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)


def _line(slide, x1, y1, x2, y2, color: str, w_pt: float = 2.0):
    ln = slide.shapes.add_connector(
        1, Emu(int(x1)), Emu(int(y1)), Emu(int(x2)), Emu(int(y2)))
    ln.line.color.rgb = _rgb(color)
    ln.line.width = Pt(w_pt)
    return ln


def build_fishbone_pptx(payload: dict[str, Any], brand: BrandConfig) -> io.BytesIO:
    topic     = payload.get("topic", "鱼骨图")
    context   = payload.get("context", "")
    reasoning = payload.get("reasoning", "")
    layers    = int(payload.get("layers", 2))
    categories = (payload.get("categories") or [])[:4]

    prs = Presentation()
    prs.slide_width  = Emu(SLIDE_W)
    prs.slide_height = Emu(SLIDE_H)
    slide = prs.slides.add_slide(prs.slide_layouts[6])   # blank
    fz = brand.font_zh

    # ── 标题条 ─────────────────────────────────────────────
    title = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Emu(0), Emu(0), Emu(SLIDE_W), Emu(500_000))
    _fill(title, brand.primary); _no_line(title)
    p = title.text_frame.paragraphs[0]
    p.text = f"鱼骨图分析 · {topic}"
    r = p.runs[0]
    r.font.name = fz; r.font.size = Pt(20); r.font.bold = True
    r.font.color.rgb = _rgb(brand.text_on_primary)
    title.text_frame.margin_left = Emu(200_000)
    title.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    if brand.company:
        _text(slide, SLIDE_W - 3_000_000, 130_000, 2_800_000, 240_000,
              brand.company, font=fz, size=10,
              color=brand.text_on_primary, anchor="r")

    # ── 主脊 + 鱼头 ───────────────────────────────────────
    spine_y      = 3_400_000                           # 略高于纸面中线
    spine_x1     = 700_000
    head_w, head_h = 2_100_000, 900_000
    head_x       = SLIDE_W - head_w - 300_000
    head_y       = spine_y - head_h // 2
    spine_x2     = head_x                              # 主脊右端(在鱼头左缘)

    _line(slide, spine_x1, spine_y, spine_x2 - 100_000, spine_y,
          brand.text, 4.0)

    # 箭头（右向三角）
    arr_w, arr_h = 220_000, 200_000
    arr = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_TRIANGLE, Emu(spine_x2 - arr_w),
        Emu(spine_y - arr_h // 2), Emu(arr_w), Emu(arr_h))
    _fill(arr, brand.text); _no_line(arr)
    arr.rotation = 90

    # 鱼头
    head = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Emu(head_x), Emu(head_y),
        Emu(head_w), Emu(head_h))
    _fill(head, brand.primary); _no_line(head)
    hp = head.text_frame.paragraphs[0]
    hp.alignment = PP_ALIGN.CENTER
    hp.text = topic
    hr = hp.runs[0]
    hr.font.name = fz; hr.font.size = Pt(15); hr.font.bold = True
    hr.font.color.rgb = _rgb(brand.text_on_primary)
    head.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    # ── 4 根大骨 ───────────────────────────────────────────
    # 沿主脊均匀取 4 个 attach 点; up 骨 attach 靠右, down 骨 attach 靠右, 交替
    #   ord 0(上-左) < 1(下-左) < 2(上-右) < 3(下-右) 沿主脊由左至右
    spine_usable_l = spine_x1 + 900_000
    spine_usable_r = spine_x2 - 900_000
    attach_xs = [spine_usable_l + i * (spine_usable_r - spine_usable_l) / 3
                 for i in range(4)]

    ang = math.radians(BONE_ANGLE_DEG)
    dx = int(BONE_LEN * math.cos(ang))
    dy = int(BONE_LEN * math.sin(ang))
    label_w, label_h = 1_500_000, 450_000

    for idx, cat in enumerate(categories):
        up = idx % 2 == 0                              # 0/2 上, 1/3 下
        ax = int(attach_xs[idx])
        ay = spine_y
        # 大骨的外端 (向左上/左下)
        ex = ax - dx
        ey = ay - dy if up else ay + dy

        _line(slide, ax, ay, ex, ey, brand.secondary, 3.0)

        # 大骨标签 (贴在外端外侧)
        lx = ex - label_w if not up else ex - label_w   # 都放外端左侧
        ly = ey - label_h - 40_000 if up else ey + 40_000
        lbl = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Emu(lx), Emu(ly),
            Emu(label_w), Emu(label_h))
        _fill(lbl, brand.secondary); _no_line(lbl)
        lp = lbl.text_frame.paragraphs[0]
        lp.alignment = PP_ALIGN.CENTER
        lp.text = cat.get("name", "")
        lr = lp.runs[0]
        lr.font.name = fz; lr.font.size = Pt(14); lr.font.bold = True
        lr.font.color.rgb = _rgb(brand.text_on_primary)
        lbl.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

        # 中骨 / 末端
        children = cat.get("children") or []
        n = max(len(children), 1)
        sub_line_len   = 1_400_000                     # 水平中骨长度
        leaf_font_size = 10

        for si, sub in enumerate(children):
            # 沿大骨方向的比例 t (从外端到 attach 点), 避开两端
            t = 0.25 + 0.55 * (si + 0.5) / n
            bx = int(ex + (ax - ex) * t)
            by = int(ey + (ay - ey) * t)

            if layers == 1:
                # 层 1: 直接把末端文字挂在大骨点旁边
                clr = _tint(brand.warn, 0.35) if sub.get("inferred") else brand.text
                offset_y = -80_000 if up else 20_000
                _text(slide, bx + 60_000, by + offset_y,
                      1_700_000, 240_000, sub.get("name", ""),
                      font=fz, size=leaf_font_size + 1, color=clr)
                continue

            # 层 2/3: 中骨水平向左延伸
            mx1 = bx - sub_line_len
            _line(slide, mx1, by, bx, by, _tint(brand.text, 0.45), 1.75)
            mclr = _tint(brand.warn, 0.35) if sub.get("inferred") else brand.secondary
            _text(slide, mx1 - 40_000, by - 260_000, sub_line_len, 240_000,
                  sub.get("name", ""), font=fz, size=11,
                  color=mclr, bold=True, anchor="r")

            if layers == 3:
                leaves = sub.get("children") or []
                ln = max(len(leaves), 1)
                # 末端小刺: 与大骨平行(同斜率), 短线, 从中骨上等分点向斜上/斜下
                for li, leaf in enumerate(leaves):
                    tt = (li + 1) / (ln + 1)
                    lx0 = int(mx1 + (bx - mx1) * tt)
                    ly0 = by
                    lex = lx0 - 200_000
                    ley = ly0 - 240_000 if up else ly0 + 240_000
                    _line(slide, lx0, ly0, lex, ley,
                          _tint(brand.text, 0.65), 1.0)
                    lclr = (_tint(brand.warn, 0.35)
                            if leaf.get("inferred") else brand.text)
                    _text(slide, lex - 1_300_000, ley - 90_000,
                          1_200_000, 200_000, leaf.get("name", ""),
                          font=fz, size=leaf_font_size - 1,
                          color=lclr, anchor="r")

    # ── 底部信息条 ─────────────────────────────────────────
    footer_y = 6_100_000
    if context:
        _text(slide, 400_000, footer_y, SLIDE_W - 800_000, 260_000,
              f"背景: {context}", font=fz, size=10,
              color=_tint(brand.text, 0.4))
        footer_y += 280_000
    if reasoning:
        _text(slide, 400_000, footer_y, SLIDE_W - 800_000, 380_000,
              f"AI 推理: {reasoning}", font=fz, size=10,
              color=_tint(brand.text, 0.35))

    buf = io.BytesIO(); prs.save(buf); buf.seek(0); return buf
