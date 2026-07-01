/* CircuitViewer3 - github.com/daniSoares08
 * Open source (MIT License): free to use, copy, modify and redistribute. */

#include "cv3.h"
#include <fileioc.h>
#include <string.h>

#define AV_MAXC 8
#define AV_MAXP 12
#define AV_MAXL 8

static const uint8_t *chunk_base[AV_MAXC];
static uint16_t chunk_items[AV_MAXC];
static bool av_ok = false;

static Exercise m_ex;
static PageTemplate m_pages[AV_MAXP];
static TextLine m_lines[AV_MAXP][AV_MAXL];
static const uint8_t *m_ops[AV_MAXP];
static uint8_t m_opn[AV_MAXP];
static uint8_t m_cur;

static uint16_t ru16(const uint8_t *p) {
    return (uint16_t)(p[0] | (p[1] << 8));
}

static int16_t ri16(const uint8_t *p) {
    return (int16_t)(p[0] | (p[1] << 8));
}

static const char *rcstr(const uint8_t **pp) {
    const char *s = (const char *)*pp;
    *pp += strlen(s) + 1;
    return s;
}

void appvar_init(void) {
    uint8_t i;
    av_ok = false;
    for (i = 0; i < AV_MAXC; i++) {
        chunk_base[i] = NULL;
        chunk_items[i] = 0;
    }
    if (chunk_count > AV_MAXC) return;
    for (i = 0; i < chunk_count; i++) {
        char name[8] = "CV3DAT0";
        uint8_t f;
        const uint8_t *base;
        name[6] = (char)('0' + i);
        f = ti_Open(name, "r");
        if (!f) return;
        base = (const uint8_t *)ti_GetDataPtr(f);
        ti_Close(f);
        if (!base || base[0] != 'C' || base[1] != 'V' ||
            base[2] != '3' || base[3] != 'A' ||
            base[4] != 1 || base[5] != 0) {
            return;
        }
        chunk_base[i] = base;
        chunk_items[i] = ru16(base + 6);
    }
    av_ok = true;
}

bool appvar_available(void) {
    return av_ok;
}

void exercise_set_page(uint8_t page) {
    m_cur = page;
}

static void av_draw_circuit(void) {
    const uint8_t *p = m_ops[m_cur];
    uint8_t n = m_opn[m_cur];
    uint8_t i;
    if (!p) return;
    for (i = 0; i < n; i++) {
        uint8_t op = *p++;
        int16_t a = ri16(p); p += 2;
        int16_t b = ri16(p); p += 2;
        int16_t c = ri16(p); p += 2;
        int16_t d = ri16(p); p += 2;
        uint8_t fl = *p++;
        const char *lab = rcstr(&p);
        switch (op) {
            case 0:  draw_wire(a, b, c, d); break;
            case 1:  draw_node(a, b); break;
            case 2:  draw_terminal(a, b, lab); break;
            case 3:  draw_res_h(a, b, c, lab); break;
            case 4:  draw_res_v(a, b, c, lab); break;
            case 5:  draw_cap_h(a, b, c, lab); break;
            case 6:  draw_cap_v(a, b, c, lab); break;
            case 7:  draw_ind_h(a, b, c, lab); break;
            case 8:  draw_ind_v(a, b, c, lab); break;
            case 9:  draw_voltage_source(a, b, c, lab); break;
            case 10: draw_voltage_source_h(a, b, c, lab); break;
            case 11: draw_current_source_v_dir(a, b, c, lab, fl); break;
            case 12: draw_current_source_h_dir(a, b, c, lab, fl); break;
            case 13: draw_ground(a, b); break;
            case 14: draw_switch_open_h(a, b, c, lab); break;
            case 15: draw_opamp(a, b, fl); break;
            case 16: draw_dep_vsource_v(a, b, c, lab); break;
            case 17: draw_dep_vsource_h(a, b, c, lab); break;
            case 18: draw_dep_isource_v(a, b, c, lab, fl); break;
            case 19: ui_label(lab, a, b); break;
            case 20: ui_arrow_h(a, b, c, lab, fl); break;
            case 21: ui_arrow_v(a, b, c, lab, fl); break;
            case 22: ui_vo(a, b, c, lab); break;
            case 23: ui_pm(a, b, c); break;
            default: break;
        }
    }
}

const Exercise *exercise_load(uint16_t idx) {
    const ExMeta *meta;
    const uint8_t *base;
    const uint8_t *p;
    uint8_t pc;
    uint8_t pg;
    if (!av_ok || idx >= ex_count) return NULL;
    meta = &ex_meta[idx];
    if (meta->chunk >= chunk_count) return NULL;
    base = chunk_base[meta->chunk];
    if (!base || meta->local >= chunk_items[meta->chunk]) return NULL;
    p = base + ru16(base + 8 + 2 * meta->local);
    pc = *p++;
    if (pc > AV_MAXP) pc = AV_MAXP;
    for (pg = 0; pg < pc; pg++) {
        const char *title = rcstr(&p);
        const char *sub = rcstr(&p);
        const char *res = rcstr(&p);
        uint8_t ry = *p++;
        uint8_t lc = *p++;
        uint8_t li;
        for (li = 0; li < lc; li++) {
            int16_t x = ri16(p); p += 2;
            int16_t y = ri16(p); p += 2;
            uint8_t col = *p++;
            const char *t = rcstr(&p);
            if (li < AV_MAXL) {
                m_lines[pg][li].text = t;
                m_lines[pg][li].x = x;
                m_lines[pg][li].y = y;
                m_lines[pg][li].color = col;
            }
        }
        {
            uint8_t oc = *p++;
            uint8_t oi;
            m_ops[pg] = oc ? p : NULL;
            m_opn[pg] = oc;
            for (oi = 0; oi < oc; oi++) {
                p += 10;   /* opcode(1) + a,b,c,d (4*i16=8) + flag(1) */
                p += strlen((const char *)p) + 1;   /* label cstr */
            }
            m_pages[pg].title = title;
            m_pages[pg].subtitle = sub;
            m_pages[pg].lines = m_lines[pg];
            m_pages[pg].line_count = (lc > AV_MAXL) ? AV_MAXL : lc;
            m_pages[pg].result = res[0] ? res : 0;
            m_pages[pg].result_y = ry;
            m_pages[pg].body = oc ? av_draw_circuit : 0;
        }
    }
    m_ex.title = meta->title;
    m_ex.pages = m_pages;
    m_ex.page_count = pc;
    return &m_ex;
}
