#include "cv3.h"

void check_on_exit(void) {
    kb_Scan();
    if (kb_On) {
        gfx_End();
        exit(0);
    }
}

uint8_t pressed_once(kb_lkey_t key) {
    static uint8_t prev[8];
    uint8_t group = (uint8_t)(key >> 8);
    uint8_t mask = (uint8_t)(key & 0xFF);
    uint8_t down;
    uint8_t edge;

    if (group >= 8) return 0;

    down = kb_IsDown(key) ? 1 : 0;
    edge = (down && !(prev[group] & mask)) ? 1 : 0;

    if (down) prev[group] |= mask;
    else prev[group] &= (uint8_t)~mask;

    return edge;
}

void wait_key_release(void) {
    do {
        check_on_exit();
        kb_Scan();
    } while (kb_Data[1] | kb_Data[2] | kb_Data[3] |
             kb_Data[4] | kb_Data[5] | kb_Data[6] | kb_Data[7]);
    delay(20);
}

void screen_init(void) {
    gfx_Begin();
    gfx_SetDrawBuffer();

    gfx_palette[COL_WHITE] = gfx_RGBTo1555(255, 255, 255);
    gfx_palette[COL_BLACK] = gfx_RGBTo1555(0, 0, 0);
    gfx_palette[COL_GRAY] = gfx_RGBTo1555(145, 145, 145);
    gfx_palette[COL_LIGHT] = gfx_RGBTo1555(228, 236, 244);
    gfx_palette[COL_BLUE] = gfx_RGBTo1555(35, 76, 150);
    gfx_palette[COL_RED] = gfx_RGBTo1555(190, 36, 36);
    gfx_palette[COL_GREEN] = gfx_RGBTo1555(34, 128, 82);

    gfx_FillScreen(COL_WHITE);
    gfx_SwapDraw();
    gfx_FillScreen(COL_WHITE);
    gfx_SwapDraw();
    gfx_SetDrawBuffer();
    gfx_FillScreen(COL_WHITE);

    gfx_SetTextFGColor(COL_BLACK);
    gfx_SetTextBGColor(COL_WHITE);
    gfx_SetTextTransparentColor(COL_WHITE);
    gfx_SetTextScale(1, 1);
}

void print_center(const char *text, int y) {
    unsigned int w = gfx_GetStringWidth(text);
    int x = (SCREEN_W - (int)w) / 2;
    if (x < 0) x = 0;
    gfx_PrintStringXY(text, x, y);
}

void prn(const char *text, int x, int y) {
    gfx_PrintStringXY(text, x, y);
}

void draw_header(const char *title, uint8_t page, uint8_t total) {
    char pg[] = "Pg 1/1";

    gfx_FillScreen(COL_WHITE);
    gfx_SetColor(COL_BLACK);
    gfx_SetTextFGColor(COL_BLACK);
    prn(title, 2, 2);

    pg[3] = (char)('1' + page);
    pg[5] = (char)('0' + total);
    prn(pg, 264, 2);

    gfx_HorizLine(0, 14, SCREEN_W);
}

void draw_ex_header(const char *subject, const char *ex_title,
                    uint8_t ex, uint8_t ex_total,
                    uint8_t page, uint8_t page_total) {
    char meta[21];
    uint8_t pos = 0;
    uint8_t n;

    gfx_FillScreen(COL_WHITE);
    gfx_SetColor(COL_BLACK);
    gfx_SetTextFGColor(COL_BLACK);
    prn(subject, 2, 2);
    meta[pos++] = 'E';
    meta[pos++] = 'x';
    meta[pos++] = ' ';
    n = (uint8_t)(ex + 1);
    if (n >= 10) meta[pos++] = (char)('0' + n / 10);
    meta[pos++] = (char)('0' + n % 10);
    meta[pos++] = '/';
    if (ex_total >= 10) meta[pos++] = (char)('0' + ex_total / 10);
    meta[pos++] = (char)('0' + ex_total % 10);
    meta[pos++] = ' ';
    meta[pos++] = 'P';
    meta[pos++] = 'g';
    meta[pos++] = ' ';
    n = (uint8_t)(page + 1);
    if (n >= 10) meta[pos++] = (char)('0' + n / 10);
    meta[pos++] = (char)('0' + n % 10);
    meta[pos++] = '/';
    if (page_total >= 10) meta[pos++] = (char)('0' + page_total / 10);
    meta[pos++] = (char)('0' + page_total % 10);
    meta[pos] = '\0';
    prn(meta, 190, 2);
    gfx_HorizLine(0, 14, SCREEN_W);

    gfx_SetTextFGColor(COL_GRAY);
    prn(ex_title, 8, 18);
    gfx_SetTextFGColor(COL_BLACK);
}

void draw_footer_menu(void) {
    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(0, 224, SCREEN_W);
    gfx_SetTextFGColor(COL_BLACK);
    prn("UP/DOWN escolhe ENTER abre ON sair", 2, 229);
}

void draw_footer_formula(void) {
    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(0, 224, SCREEN_W);
    gfx_SetTextFGColor(COL_BLACK);
    prn("UP/DOWN lista  </> pg  CLEAR volta ON", 2, 229);
}

void draw_footer_ex(void) {
    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(0, 224, SCREEN_W);
    gfx_SetTextFGColor(COL_BLACK);
    prn("UP/DOWN ex  </> pg  CLEAR volta ON sair", 2, 229);
}

void draw_title(const char *title, const char *subtitle) {
    if (title) print_center(title, 30);
    if (subtitle) {
        gfx_SetTextFGColor(COL_GRAY);
        print_center(subtitle, 44);
        gfx_SetTextFGColor(COL_BLACK);
    }
}

void result_box(const char *text, int y) {
    gfx_SetColor(COL_BLUE);
    gfx_Rectangle(24, y, 272, 30);
    gfx_Rectangle(25, y + 1, 270, 28);
    gfx_SetTextFGColor(COL_BLUE);
    print_center(text, y + 10);
    gfx_SetTextFGColor(COL_BLACK);
}

void step_box(int y, const char *l1, const char *l2) {
    gfx_SetColor(COL_LIGHT);
    gfx_FillRectangle(10, y, 300, 36);
    gfx_SetColor(COL_BLACK);
    gfx_Rectangle(10, y, 300, 36);
    gfx_SetTextFGColor(COL_BLACK);
    prn(l1, 18, y + 7);
    prn(l2, 18, y + 21);
}

void draw_page_template(const PageTemplate *page) {
    uint8_t i;

    draw_title(page->title, page->subtitle);
    if (page->body) page->body();

    for (i = 0; i < page->line_count; i++) {
        gfx_SetTextFGColor(page->lines[i].color);
        prn(page->lines[i].text, page->lines[i].x, page->lines[i].y);
    }

    if (page->result) {
        result_box(page->result, page->result_y);
    }
    gfx_SetTextFGColor(COL_BLACK);
}

void draw_node(int x, int y) {
    gfx_SetColor(COL_BLACK);
    gfx_FillCircle(x, y, 2);
}

void draw_wire(int x1, int y1, int x2, int y2) {
    gfx_SetColor(COL_BLACK);
    gfx_Line(x1, y1, x2, y2);
}

void draw_terminal(int x, int y, const char *label) {
    gfx_SetColor(COL_BLACK);
    gfx_Circle(x, y, 4);
    gfx_SetTextFGColor(COL_BLACK);
    prn(label, x + 8, y - 4);
}

static void draw_text_in_rect(const char *text, int x, int y, int w, int h) {
    unsigned int tw = gfx_GetStringWidth(text);
    int tx = x + (w - (int)tw) / 2;
    int ty = y + (h - 8) / 2;
    if (tx < x + 1) tx = x + 1;
    gfx_SetTextFGColor(COL_BLACK);
    prn(text, tx, ty);
}

void draw_res_h(int x1, int y, int x2, const char *label) {
    int body_w = 32;
    int body_h = 16;
    int cx = (x1 + x2) / 2;
    int bx = cx - body_w / 2;
    int by = y - body_h / 2;

    draw_wire(x1, y, bx, y);
    draw_wire(bx + body_w, y, x2, y);
    gfx_SetColor(COL_LIGHT);
    gfx_FillRectangle(bx, by, body_w, body_h);
    gfx_SetColor(COL_BLACK);
    gfx_Rectangle(bx, by, body_w, body_h);
    draw_text_in_rect(label, bx, by, body_w, body_h);
}

void draw_res_v(int x, int y1, int y2, const char *label) {
    int body_w = 28;
    int body_h = 32;
    int cy = (y1 + y2) / 2;
    int bx = x - body_w / 2;
    int by = cy - body_h / 2;

    draw_wire(x, y1, x, by);
    draw_wire(x, by + body_h, x, y2);
    gfx_SetColor(COL_LIGHT);
    gfx_FillRectangle(bx, by, body_w, body_h);
    gfx_SetColor(COL_BLACK);
    gfx_Rectangle(bx, by, body_w, body_h);
    draw_text_in_rect(label, bx, by, body_w, body_h);
}

void draw_cap_h(int x1, int y, int x2, const char *label) {
    int cx = (x1 + x2) / 2;
    int lw = (int)gfx_GetStringWidth(label);
    int lx = cx - lw / 2;
    draw_wire(x1, y, cx - 5, y);
    draw_wire(cx + 5, y, x2, y);
    gfx_SetColor(COL_GREEN);
    gfx_VertLine(cx - 5, y - 14, 28);
    gfx_VertLine(cx + 5, y - 14, 28);
    gfx_SetTextFGColor(COL_BLACK);
    if (lx < 0) lx = 0;
    prn(label, lx, y - 28);
}

void draw_cap_v(int x, int y1, int y2, const char *label) {
    int cy = (y1 + y2) / 2;
    draw_wire(x, y1, x, cy - 5);
    draw_wire(x, cy + 5, x, y2);
    gfx_SetColor(COL_GREEN);
    gfx_HorizLine(x - 14, cy - 5, 28);
    gfx_HorizLine(x - 14, cy + 5, 28);
    gfx_SetTextFGColor(COL_BLACK);
    prn(label, x + 16, cy - 4);
}

void draw_ind_h(int x1, int y, int x2, const char *label) {
    int cx = (x1 + x2) / 2;
    int sx = cx - 22;
    int lw = (int)gfx_GetStringWidth(label);
    int lx = cx - lw / 2;
    draw_wire(x1, y, sx, y);
    gfx_SetColor(COL_GREEN);
    gfx_Line(sx, y, sx + 8, y - 8);
    gfx_Line(sx + 8, y - 8, sx + 16, y + 8);
    gfx_Line(sx + 16, y + 8, sx + 24, y - 8);
    gfx_Line(sx + 24, y - 8, sx + 32, y + 8);
    gfx_Line(sx + 32, y + 8, sx + 44, y);
    draw_wire(sx + 44, y, x2, y);
    gfx_SetTextFGColor(COL_BLACK);
    if (lx < 0) lx = 0;
    prn(label, lx, y - 26);
}

void draw_ind_v(int x, int y1, int y2, const char *label) {
    int cy = (y1 + y2) / 2;
    int sy = cy - 22;
    draw_wire(x, y1, x, sy);
    gfx_SetColor(COL_GREEN);
    gfx_Line(x, sy, x - 8, sy + 8);
    gfx_Line(x - 8, sy + 8, x + 8, sy + 16);
    gfx_Line(x + 8, sy + 16, x - 8, sy + 24);
    gfx_Line(x - 8, sy + 24, x + 8, sy + 32);
    gfx_Line(x + 8, sy + 32, x, sy + 44);
    draw_wire(x, sy + 44, x, y2);
    gfx_SetTextFGColor(COL_BLACK);
    prn(label, x + 12, cy - 4);
}

void draw_voltage_source(int x, int y1, int y2, const char *label) {
    int cy = (y1 + y2) / 2;
    int r = 14;
    draw_wire(x, y1, x, cy - r);
    draw_wire(x, cy + r, x, y2);
    gfx_SetColor(COL_WHITE);
    gfx_FillCircle(x, cy, r);
    gfx_SetColor(COL_BLACK);
    gfx_Circle(x, cy, r);
    prn("+", x - 3, cy - 10);
    prn("-", x - 3, cy + 4);
    prn(label, x - 34, cy - 4);
}

void draw_voltage_source_h(int x1, int y, int x2, const char *label) {
    int cx = (x1 + x2) / 2;
    int r = 14;
    draw_wire(x1, y, cx - r, y);
    draw_wire(cx + r, y, x2, y);
    gfx_SetColor(COL_WHITE);
    gfx_FillCircle(cx, y, r);
    gfx_SetColor(COL_BLACK);
    gfx_Circle(cx, y, r);
    prn("-", cx - 9, y - 4);
    prn("+", cx + 5, y - 4);
    prn(label, cx - 10, y - 28);
}

void draw_current_source_v_dir(int x, int y1, int y2,
                               const char *label, bool upward) {
    int cy = (y1 + y2) / 2;
    int r = 14;
    draw_wire(x, y1, x, cy - r);
    draw_wire(x, cy + r, x, y2);
    gfx_SetColor(COL_WHITE);
    gfx_FillCircle(x, cy, r);
    gfx_SetColor(COL_BLACK);
    gfx_Circle(x, cy, r);
    if (upward) {
        gfx_Line(x, cy + 8, x, cy - 8);
        gfx_Line(x, cy - 8, x - 4, cy - 2);
        gfx_Line(x, cy - 8, x + 4, cy - 2);
    } else {
        gfx_Line(x, cy - 8, x, cy + 8);
        gfx_Line(x, cy + 8, x - 4, cy + 2);
        gfx_Line(x, cy + 8, x + 4, cy + 2);
    }
    prn(label, x + 16, cy - 4);
}

void draw_current_source_h_dir(int x1, int y, int x2,
                               const char *label, bool right) {
    int cx = (x1 + x2) / 2;
    int r = 14;
    int ax1 = right ? cx - 8 : cx + 8;
    int ax2 = right ? cx + 8 : cx - 8;
    int ah = right ? -1 : 1;
    draw_wire(x1, y, cx - r, y);
    draw_wire(cx + r, y, x2, y);
    gfx_SetColor(COL_WHITE);
    gfx_FillCircle(cx, y, r);
    gfx_SetColor(COL_BLACK);
    gfx_Circle(cx, y, r);
    gfx_Line(ax1, y, ax2, y);
    gfx_Line(ax2, y, ax2 + ah * 6, y - 4);
    gfx_Line(ax2, y, ax2 + ah * 6, y + 4);
    prn(label, cx - 8, y - 27);
}

void draw_ground(int x, int y) {
    gfx_SetColor(COL_BLACK);
    gfx_VertLine(x, y, 7);
    gfx_HorizLine(x - 12, y + 7, 24);
    gfx_HorizLine(x - 8, y + 12, 16);
    gfx_HorizLine(x - 4, y + 17, 8);
}

void draw_switch_open_h(int x1, int y, int x2, const char *label) {
    int xm = (x1 + x2) / 2;
    draw_wire(x1, y, xm - 12, y);
    draw_wire(xm + 14, y, x2, y);
    gfx_SetColor(COL_BLACK);
    gfx_Circle(xm - 12, y, 2);
    gfx_Circle(xm + 14, y, 2);
    gfx_Line(xm - 10, y - 2, xm + 8, y - 16);
    gfx_SetTextFGColor(COL_BLUE);
    prn(label, xm - 18, y - 32);
    gfx_SetTextFGColor(COL_BLACK);
}

void draw_opamp(int x, int y, bool noninv_input_top) {
    gfx_SetColor(COL_BLACK);
    gfx_Line(x, y, x, y + 58);
    gfx_Line(x, y, x + 62, y + 29);
    gfx_Line(x, y + 58, x + 62, y + 29);
    prn(noninv_input_top ? "+" : "-", x + 8, y + 13);
    prn(noninv_input_top ? "-" : "+", x + 8, y + 37);
}

void draw_dep_vsource_v(int x, int y1, int y2, const char *label) {
    int cy = (y1 + y2) / 2;
    int r = 14;
    draw_wire(x, y1, x, cy - r);
    draw_wire(x, cy + r, x, y2);
    gfx_SetColor(COL_WHITE);
    gfx_FillCircle(x, cy, r);
    gfx_SetColor(COL_BLACK);
    gfx_Line(x, cy - r, x + r, cy);
    gfx_Line(x + r, cy, x, cy + r);
    gfx_Line(x, cy + r, x - r, cy);
    gfx_Line(x - r, cy, x, cy - r);
    prn("+", x - 3, cy - 10);
    prn("-", x - 3, cy + 4);
    prn(label, x + 16, cy - 4);
}

void draw_dep_vsource_h(int x1, int y, int x2, const char *label) {
    int cx = (x1 + x2) / 2;
    int r = 14;
    draw_wire(x1, y, cx - r, y);
    draw_wire(cx + r, y, x2, y);
    gfx_SetColor(COL_WHITE);
    gfx_FillCircle(cx, y, r);
    gfx_SetColor(COL_BLACK);
    gfx_Line(cx, y - r, cx + r, y);
    gfx_Line(cx + r, y, cx, y + r);
    gfx_Line(cx, y + r, cx - r, y);
    gfx_Line(cx - r, y, cx, y - r);
    prn("-", cx - 9, y - 4);
    prn("+", cx + 5, y - 4);
    prn(label, cx - 10, y - 28);
}

void draw_dep_isource_v(int x, int y1, int y2, const char *label, bool upward) {
    int cy = (y1 + y2) / 2;
    int r = 14;
    draw_wire(x, y1, x, cy - r);
    draw_wire(x, cy + r, x, y2);
    gfx_SetColor(COL_WHITE);
    gfx_FillCircle(x, cy, r);
    gfx_SetColor(COL_BLACK);
    gfx_Line(x, cy - r, x + r, cy);
    gfx_Line(x + r, cy, x, cy + r);
    gfx_Line(x, cy + r, x - r, cy);
    gfx_Line(x - r, cy, x, cy - r);
    if (upward) {
        gfx_Line(x, cy + 7, x, cy - 7);
        gfx_Line(x, cy - 7, x - 4, cy - 1);
        gfx_Line(x, cy - 7, x + 4, cy - 1);
    } else {
        gfx_Line(x, cy - 7, x, cy + 7);
        gfx_Line(x, cy + 7, x - 4, cy + 1);
        gfx_Line(x, cy + 7, x + 4, cy + 1);
    }
    prn(label, x + 16, cy - 4);
}
