#include "cv3.h"
#include <fileioc.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define CALC_EXPR_MAX 22
#define CALC_OUT_MAX  16
#define CALC_HIST_LEN (CALC_EXPR_MAX + CALC_OUT_MAX + 2)
#define CALC_HIST     5
#define CALC_APPVAR   "CV3CALC"

static char calc_expr[CALC_EXPR_MAX + 1];
static uint8_t calc_len = 0;
static char calc_result[CALC_OUT_MAX + 1];
static bool calc_has_result = false;
static bool calc_error = false;
static char calc_hist[CALC_HIST][CALC_HIST_LEN];

/* ---- recursive-descent evaluator over double ---- */
static const char *ep;
static bool eval_ok;

static double parse_expr(void);

static double parse_number(void) {
    char *end;
    double v = strtod(ep, &end);
    if (end == ep) { eval_ok = false; return 0; }
    ep = end;
    return v;
}

static double parse_base(void) {
    if (*ep == '-') { ep++; return -parse_base(); }
    if (*ep == '+') { ep++; return parse_base(); }
    if (*ep == '(') {
        double v;
        ep++;
        v = parse_expr();
        if (*ep == ')') ep++; else eval_ok = false;
        return v;
    }
    return parse_number();
}

static double parse_factor(void) {
    double b = parse_base();
    if (*ep == '^') {
        double e;
        ep++;
        e = parse_factor();
        return pow(b, e);
    }
    return b;
}

static double parse_term(void) {
    double v = parse_factor();
    for (;;) {
        char c = *ep;
        if (c == '*') { ep++; v *= parse_factor(); }
        else if (c == '/') {
            double d;
            ep++;
            d = parse_factor();
            if (d == 0) { eval_ok = false; return 0; }
            v /= d;
        } else break;
    }
    return v;
}

static double parse_expr(void) {
    double v = parse_term();
    for (;;) {
        char c = *ep;
        if (c == '+') { ep++; v += parse_term(); }
        else if (c == '-') { ep++; v -= parse_term(); }
        else break;
    }
    return v;
}

static void calc_save(void) {
    ti_var_t f = ti_Open(CALC_APPVAR, "w");
    if (f) {
        ti_Write(calc_hist, sizeof(calc_hist), 1, f);
        ti_SetArchiveStatus(true, f);
        ti_Close(f);
    }
}

void calc_init(void) {
    ti_var_t f;
    uint8_t i;
    for (i = 0; i < CALC_HIST; i++) calc_hist[i][0] = '\0';
    f = ti_Open(CALC_APPVAR, "r");
    if (f) {
        ti_Read(calc_hist, sizeof(calc_hist), 1, f);
        ti_Close(f);
    }
    calc_expr[0] = '\0';
    calc_len = 0;
    calc_has_result = false;
    calc_error = false;
}

void calc_clear(void) {
    calc_expr[0] = '\0';
    calc_len = 0;
    calc_has_result = false;
    calc_error = false;
}

bool calc_is_empty(void) {
    return calc_len == 0;
}

static void calc_push(char c) {
    if (calc_len < CALC_EXPR_MAX) {
        calc_expr[calc_len++] = c;
        calc_expr[calc_len] = '\0';
        calc_has_result = false;
    }
}

static void calc_backspace(void) {
    if (calc_len > 0) {
        calc_expr[--calc_len] = '\0';
        calc_has_result = false;
    }
}

static void calc_eval(void) {
    double v;
    if (calc_len == 0) return;
    ep = calc_expr;
    eval_ok = true;
    v = parse_expr();
    if (!eval_ok || *ep != '\0') {
        calc_error = true;
        strcpy(calc_result, "Erro");
    } else {
        calc_error = false;
        sprintf(calc_result, "%.6g", v);
    }
    calc_has_result = true;
    if (!calc_error) {
        uint8_t i;
        for (i = CALC_HIST - 1; i > 0; i--) strcpy(calc_hist[i], calc_hist[i - 1]);
        snprintf(calc_hist[0], CALC_HIST_LEN, "%s=%s", calc_expr, calc_result);
        calc_save();
    }
}

bool calc_handle_key(void) {
    static const struct { kb_lkey_t k; char c; } keymap[] = {
        { kb_Key0, '0' }, { kb_Key1, '1' }, { kb_Key2, '2' }, { kb_Key3, '3' },
        { kb_Key4, '4' }, { kb_Key5, '5' }, { kb_Key6, '6' }, { kb_Key7, '7' },
        { kb_Key8, '8' }, { kb_Key9, '9' }, { kb_KeyDecPnt, '.' },
        { kb_KeyAdd, '+' }, { kb_KeySub, '-' }, { kb_KeyMul, '*' },
        { kb_KeyDiv, '/' }, { kb_KeyPower, '^' },
        { kb_KeyLParen, '(' }, { kb_KeyRParen, ')' }, { kb_KeyChs, '-' },
    };
    bool changed = false;
    uint8_t i;
    for (i = 0; i < (uint8_t)(sizeof(keymap) / sizeof(keymap[0])); i++) {
        if (pressed_once(keymap[i].k)) { calc_push(keymap[i].c); changed = true; }
    }
    if (pressed_once(kb_KeyDel)) { calc_backspace(); changed = true; }
    if (pressed_once(kb_KeySto)) { calc_eval(); changed = true; }
    return changed;
}

void search_overlay_draw(void) {
    uint8_t i;

    /* history: newest at top, oldest at bottom */
    gfx_SetTextFGColor(COL_GRAY);
    for (i = 0; i < CALC_HIST; i++) {
        if (calc_hist[i][0]) prn(calc_hist[i], 12, 28 + i * 18);
    }

    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(8, 124, 304);

    gfx_SetTextFGColor(COL_BLACK);
    prn(calc_len ? calc_expr : "_", 12, 134);

    if (calc_has_result) {
        gfx_SetTextFGColor(calc_error ? COL_RED : COL_BLUE);
        prn("=", 12, 162);
        prn(calc_result, 28, 162);
        gfx_SetTextFGColor(COL_BLACK);
    }
}
