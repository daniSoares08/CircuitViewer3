#!/usr/bin/env python3
# CircuitViewer3 - github.com/daniSoares08
# Open source (MIT License): free to use, copy, modify and redistribute.
"""Shared circuit primitives for CIRCVIE3.

A circuit is a list of "ops" (tuples). Each op maps 1:1 to a primitive in
src/ui.c (or a helper emitted into src/exercises.c). The SAME op list is used
to (a) emit C draw functions and (b) render a faithful 320x240 PNG preview, so
every page can be checked for off-screen / overlap problems before building.

Geometry here mirrors src/ui.c exactly. If ui.c changes, update this too.
"""

from PIL import Image, ImageDraw, ImageFont

SCREEN_W = 320
SCREEN_H = 240

# Palette matches screen_init() in src/ui.c.
COLORS = {
    "COL_WHITE": (255, 255, 255),
    "COL_BLACK": (0, 0, 0),
    "COL_GRAY": (145, 145, 145),
    "COL_LIGHT": (228, 236, 244),
    "COL_BLUE": (35, 76, 150),
    "COL_RED": (190, 36, 36),
    "COL_GREEN": (34, 128, 82),
}

CHAR_W = 8   # default graphx font advance
CHAR_H = 8


def _load_font():
    for name in ("consola.ttf", "cour.ttf", "lucon.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, 11)
        except OSError:
            continue
    return ImageFont.load_default()


_FONT = _load_font()


def text_w(s):
    """gfx_GetStringWidth for the default fixed 8px font."""
    return CHAR_W * len(s)


# --------------------------------------------------------------------------
# C emission
# --------------------------------------------------------------------------

def _b(v):
    return "true" if v else "false"


def _s(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


_C_EMIT = {
    "node": lambda a: "draw_node(%d, %d);" % a,
    "wire": lambda a: "draw_wire(%d, %d, %d, %d);" % a,
    "line": lambda a: "draw_wire(%d, %d, %d, %d);" % a,
    "term": lambda a: "draw_terminal(%d, %d, %s);" % (a[0], a[1], _s(a[2])),
    "res_h": lambda a: "draw_res_h(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "res_v": lambda a: "draw_res_v(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "cap_h": lambda a: "draw_cap_h(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "cap_v": lambda a: "draw_cap_v(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "ind_h": lambda a: "draw_ind_h(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "ind_v": lambda a: "draw_ind_v(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "vsrc_v": lambda a: "draw_voltage_source(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "vsrc_h": lambda a: "draw_voltage_source_h(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "isrc_v": lambda a: "draw_current_source_v_dir(%d, %d, %d, %s, %s);" % (a[0], a[1], a[2], _s(a[3]), _b(a[4])),
    "isrc_h": lambda a: "draw_current_source_h_dir(%d, %d, %d, %s, %s);" % (a[0], a[1], a[2], _s(a[3]), _b(a[4])),
    "gnd": lambda a: "draw_ground(%d, %d);" % a,
    "sw_h": lambda a: "draw_switch_open_h(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "opamp": lambda a: "draw_opamp(%d, %d, %s);" % (a[0], a[1], _b(a[2])),
    "dvs_v": lambda a: "draw_dep_vsource_v(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "dvs_h": lambda a: "draw_dep_vsource_h(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "dis_v": lambda a: "draw_dep_isource_v(%d, %d, %d, %s, %s);" % (a[0], a[1], a[2], _s(a[3]), _b(a[4])),
    "lbl": lambda a: "label(%s, %d, %d);" % (_s(a[0]), a[1], a[2]),
    "arr_h": lambda a: "draw_arrow_h(%d, %d, %d, %s, %s);" % (a[0], a[1], a[2], _s(a[3]), _b(a[4])),
    "arr_v": lambda a: "draw_arrow_v(%d, %d, %d, %s, %s);" % (a[0], a[1], a[2], _s(a[3]), _b(a[4])),
    "vo": lambda a: "draw_vo_marks(%d, %d, %d, %s);" % (a[0], a[1], a[2], _s(a[3])),
    "pm": lambda a: "plus_minus_v(%d, %d, %d);" % a,
}


def emit_circuit_c(name, ops):
    body = ["static void %s(void) {" % name]
    for op in ops:
        kind = op[0]
        args = op[1:]
        body.append("    " + _C_EMIT[kind](args))
    body.append("}")
    return "\n".join(body)


# --------------------------------------------------------------------------
# PIL rendering (mirror of src/ui.c geometry)
# --------------------------------------------------------------------------

class _R:
    def __init__(self, draw):
        self.d = draw

    def text(self, s, x, y, color="COL_BLACK"):
        col = COLORS[color]
        for i, ch in enumerate(str(s)):
            self.d.text((x + i * CHAR_W, y - 1), ch, font=_FONT, fill=col)

    def line(self, x1, y1, x2, y2, color="COL_BLACK"):
        self.d.line((x1, y1, x2, y2), fill=COLORS[color], width=1)

    def hline(self, x, y, ln, color="COL_BLACK"):
        self.d.line((x, y, x + ln - 1, y), fill=COLORS[color], width=1)

    def vline(self, x, y, ln, color="COL_BLACK"):
        self.d.line((x, y, x, y + ln - 1), fill=COLORS[color], width=1)

    def rect(self, x, y, w, h, color="COL_BLACK"):
        self.d.rectangle((x, y, x + w, y + h), outline=COLORS[color])

    def fillrect(self, x, y, w, h, color):
        self.d.rectangle((x, y, x + w, y + h), fill=COLORS[color])

    def circle(self, x, y, r, color="COL_BLACK"):
        self.d.ellipse((x - r, y - r, x + r, y + r), outline=COLORS[color])

    def fillcircle(self, x, y, r, color):
        self.d.ellipse((x - r, y - r, x + r, y + r), fill=COLORS[color])


def _text_in_rect(r, s, x, y, w, h):
    tw = text_w(s)
    tx = x + (w - tw) // 2
    ty = y + (h - 8) // 2
    if tx < x + 1:
        tx = x + 1
    r.text(s, tx, ty)


def _draw_op(r, op):
    k = op[0]
    a = op[1:]
    if k == "node":
        r.fillcircle(a[0], a[1], 2, "COL_BLACK")
    elif k in ("wire", "line"):
        r.line(a[0], a[1], a[2], a[3])
    elif k == "term":
        r.circle(a[0], a[1], 4)
        r.text(a[2], a[0] + 8, a[1] - 4)
    elif k == "res_h":
        x1, y, x2, s = a
        bw, bh = 32, 16
        cx = (x1 + x2) // 2
        bx, by = cx - bw // 2, y - bh // 2
        r.line(x1, y, bx, y)
        r.line(bx + bw, y, x2, y)
        r.fillrect(bx, by, bw, bh, "COL_LIGHT")
        r.rect(bx, by, bw, bh)
        _text_in_rect(r, s, bx, by, bw, bh)
    elif k == "res_v":
        x, y1, y2, s = a
        bw, bh = 28, 32
        cy = (y1 + y2) // 2
        bx, by = x - bw // 2, cy - bh // 2
        r.line(x, y1, x, by)
        r.line(x, by + bh, x, y2)
        r.fillrect(bx, by, bw, bh, "COL_LIGHT")
        r.rect(bx, by, bw, bh)
        _text_in_rect(r, s, bx, by, bw, bh)
    elif k == "cap_h":
        x1, y, x2, s = a
        cx = (x1 + x2) // 2
        lw = text_w(s)
        lx = max(0, cx - lw // 2)
        r.line(x1, y, cx - 5, y)
        r.line(cx + 5, y, x2, y)
        r.vline(cx - 5, y - 14, 28, "COL_GREEN")
        r.vline(cx + 5, y - 14, 28, "COL_GREEN")
        r.text(s, lx, y - 28)
    elif k == "cap_v":
        x, y1, y2, s = a
        cy = (y1 + y2) // 2
        r.line(x, y1, x, cy - 5)
        r.line(x, cy + 5, x, y2)
        r.hline(x - 14, cy - 5, 28, "COL_GREEN")
        r.hline(x - 14, cy + 5, 28, "COL_GREEN")
        r.text(s, x + 16, cy - 4)
    elif k == "ind_h":
        x1, y, x2, s = a
        cx = (x1 + x2) // 2
        sx = cx - 22
        lw = text_w(s)
        lx = max(0, cx - lw // 2)
        r.line(x1, y, sx, y)
        pts = [(sx, y), (sx + 8, y - 8), (sx + 16, y + 8), (sx + 24, y - 8),
               (sx + 32, y + 8), (sx + 44, y)]
        for p, q in zip(pts, pts[1:]):
            r.line(p[0], p[1], q[0], q[1], "COL_GREEN")
        r.line(sx + 44, y, x2, y)
        r.text(s, lx, y - 26)
    elif k == "ind_v":
        x, y1, y2, s = a
        cy = (y1 + y2) // 2
        sy = cy - 22
        r.line(x, y1, x, sy)
        pts = [(x, sy), (x - 8, sy + 8), (x + 8, sy + 16), (x - 8, sy + 24),
               (x + 8, sy + 32), (x, sy + 44)]
        for p, q in zip(pts, pts[1:]):
            r.line(p[0], p[1], q[0], q[1], "COL_GREEN")
        r.line(x, sy + 44, x, y2)
        r.text(s, x + 12, cy - 4)
    elif k == "vsrc_v":
        x, y1, y2, s = a
        cy = (y1 + y2) // 2
        rr = 14
        r.line(x, y1, x, cy - rr)
        r.line(x, cy + rr, x, y2)
        r.fillcircle(x, cy, rr, "COL_WHITE")
        r.circle(x, cy, rr)
        r.text("+", x - 3, cy - 10)
        r.text("-", x - 3, cy + 4)
        r.text(s, x - 34, cy - 4)
    elif k == "vsrc_h":
        x1, y, x2, s = a
        cx = (x1 + x2) // 2
        rr = 14
        r.line(x1, y, cx - rr, y)
        r.line(cx + rr, y, x2, y)
        r.fillcircle(cx, y, rr, "COL_WHITE")
        r.circle(cx, y, rr)
        r.text("-", cx - 9, y - 4)
        r.text("+", cx + 5, y - 4)
        r.text(s, cx - 10, y - 28)
    elif k == "isrc_v":
        x, y1, y2, s, up = a
        cy = (y1 + y2) // 2
        rr = 14
        r.line(x, y1, x, cy - rr)
        r.line(x, cy + rr, x, y2)
        r.fillcircle(x, cy, rr, "COL_WHITE")
        r.circle(x, cy, rr)
        if up:
            r.line(x, cy + 8, x, cy - 8)
            r.line(x, cy - 8, x - 4, cy - 2)
            r.line(x, cy - 8, x + 4, cy - 2)
        else:
            r.line(x, cy - 8, x, cy + 8)
            r.line(x, cy + 8, x - 4, cy + 2)
            r.line(x, cy + 8, x + 4, cy + 2)
        r.text(s, x + 16, cy - 4)
    elif k == "isrc_h":
        x1, y, x2, s, right = a
        cx = (x1 + x2) // 2
        rr = 14
        ax1 = cx - 8 if right else cx + 8
        ax2 = cx + 8 if right else cx - 8
        ah = -1 if right else 1
        r.line(x1, y, cx - rr, y)
        r.line(cx + rr, y, x2, y)
        r.fillcircle(cx, y, rr, "COL_WHITE")
        r.circle(cx, y, rr)
        r.line(ax1, y, ax2, y)
        r.line(ax2, y, ax2 + ah * 6, y - 4)
        r.line(ax2, y, ax2 + ah * 6, y + 4)
        r.text(s, cx - 8, y - 27)
    elif k == "gnd":
        x, y = a
        r.vline(x, y, 7)
        r.hline(x - 12, y + 7, 24)
        r.hline(x - 8, y + 12, 16)
        r.hline(x - 4, y + 17, 8)
    elif k == "sw_h":
        x1, y, x2, s = a
        xm = (x1 + x2) // 2
        r.line(x1, y, xm - 12, y)
        r.line(xm + 14, y, x2, y)
        r.circle(xm - 12, y, 2)
        r.circle(xm + 14, y, 2)
        r.line(xm - 10, y - 2, xm + 8, y - 16)
        r.text(s, xm - 18, y - 32, "COL_BLUE")
    elif k == "opamp":
        x, y, top = a
        r.line(x, y, x, y + 58)
        r.line(x, y, x + 62, y + 29)
        r.line(x, y + 58, x + 62, y + 29)
        r.text("+" if top else "-", x + 8, y + 13)
        r.text("-" if top else "+", x + 8, y + 37)
    elif k == "dvs_v":
        x, y1, y2, s = a
        cy = (y1 + y2) // 2
        rr = 14
        r.line(x, y1, x, cy - rr)
        r.line(x, cy + rr, x, y2)
        r.fillcircle(x, cy, rr, "COL_WHITE")
        r.line(x, cy - rr, x + rr, cy)
        r.line(x + rr, cy, x, cy + rr)
        r.line(x, cy + rr, x - rr, cy)
        r.line(x - rr, cy, x, cy - rr)
        r.text("+", x - 3, cy - 10)
        r.text("-", x - 3, cy + 4)
        r.text(s, x + 16, cy - 4)
    elif k == "dvs_h":
        x1, y, x2, s = a
        cx = (x1 + x2) // 2
        rr = 14
        r.line(x1, y, cx - rr, y)
        r.line(cx + rr, y, x2, y)
        r.fillcircle(cx, y, rr, "COL_WHITE")
        r.line(cx, y - rr, cx + rr, y)
        r.line(cx + rr, y, cx, y + rr)
        r.line(cx, y + rr, cx - rr, y)
        r.line(cx - rr, y, cx, y - rr)
        r.text("-", cx - 9, y - 4)
        r.text("+", cx + 5, y - 4)
        r.text(s, cx - 10, y - 28)
    elif k == "dis_v":
        x, y1, y2, s, up = a
        cy = (y1 + y2) // 2
        rr = 14
        r.line(x, y1, x, cy - rr)
        r.line(x, cy + rr, x, y2)
        r.fillcircle(x, cy, rr, "COL_WHITE")
        r.line(x, cy - rr, x + rr, cy)
        r.line(x + rr, cy, x, cy + rr)
        r.line(x, cy + rr, x - rr, cy)
        r.line(x - rr, cy, x, cy - rr)
        if up:
            r.line(x, cy + 7, x, cy - 7)
            r.line(x, cy - 7, x - 4, cy - 1)
            r.line(x, cy - 7, x + 4, cy - 1)
        else:
            r.line(x, cy - 7, x, cy + 7)
            r.line(x, cy + 7, x - 4, cy + 1)
            r.line(x, cy + 7, x + 4, cy + 1)
        r.text(s, x + 16, cy - 4)
    elif k == "lbl":
        r.text(a[0], a[1], a[2])
    elif k == "arr_h":
        x1, y, x2, s, right = a
        ah = -1 if right else 1
        head = x2 if right else x1
        r.line(x1, y, x2, y)
        r.line(head, y, head + ah * 7, y - 4)
        r.line(head, y, head + ah * 7, y + 4)
        r.text(s, (x1 + x2) // 2 - 8, y - 16)
    elif k == "arr_v":
        x, y1, y2, s, up = a
        ah = 1 if up else -1
        head = y1 if up else y2
        r.line(x, y1, x, y2)
        r.line(x, head, x - 4, head + ah * 7)
        r.line(x, head, x + 4, head + ah * 7)
        r.text(s, x + 6, (y1 + y2) // 2 - 4)
    elif k == "vo":
        x, yt, yb, s = a
        r.text("+", x, yt)
        r.text("-", x, yb)
        r.text(s, x - 8, (yt + yb) // 2 - 4)
    elif k == "pm":
        x, y1, y2 = a
        r.text("+", x, y1)
        r.text("-", x, y2)
    else:
        raise ValueError("unknown op %r" % (op,))


def render_ops(draw, ops):
    r = _R(draw)
    for op in ops:
        _draw_op(r, op)


def render_page(page, subject="", ex_meta="", ex_title=""):
    """Render one PageTemplate-like dict to a 320x240 image for QA."""
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), COLORS["COL_WHITE"])
    d = ImageDraw.Draw(img)
    r = _R(d)
    # header (mirror draw_ex_header)
    if subject:
        r.text(subject, 2, 2)
        if ex_meta:
            r.text(ex_meta, 190, 2)
        r.hline(0, 14, SCREEN_W)
        if ex_title:
            r.text(ex_title, 8, 18, "COL_GRAY")
    # title block (mirror draw_title)
    if page.get("title"):
        t = page["title"]
        r.text(t, (SCREEN_W - text_w(t)) // 2, 30)
    if page.get("subtitle"):
        s = page["subtitle"]
        r.text(s, (SCREEN_W - text_w(s)) // 2, 44, "COL_GRAY")
    # body
    if page.get("body"):
        render_ops(d, page["body"])
    # text lines
    for (text, x, y, color) in page.get("lines", []):
        r.text(text, x, y, color)
    # result box (mirror result_box)
    if page.get("result"):
        y = page.get("result_y", 186)
        d.rectangle((24, y, 24 + 272, y + 30), outline=COLORS["COL_BLUE"])
        d.rectangle((25, y + 1, 25 + 270, y + 1 + 28), outline=COLORS["COL_BLUE"])
        t = page["result"]
        r.text(t, (SCREEN_W - text_w(t)) // 2, y + 10, "COL_BLUE")
    # footer
    r.hline(0, 224, SCREEN_W, "COL_GRAY")
    r.text("UP/DOWN ex  </> pg  CLEAR volta ON sair", 2, 229)
    return img
