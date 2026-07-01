/* CircuitViewer3 - github.com/daniSoares08
 * Open source (MIT License): free to use, copy, modify and redistribute. */

#include "cv3.h"
#include <fileioc.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <limits.h>

#define CALC_EXPR_MAX 22
#define CALC_OUT_MAX  16
#define CALC_HIST_LEN (CALC_EXPR_MAX + CALC_OUT_MAX + 2)
#define CALC_HIST     5
#define CALC_APPVAR   "CV3CALC"

typedef struct {
    bool dec;
    int32_t n;
    int32_t d;
    double x;
} CalcVal;

typedef struct {
    const char *p;
    bool ok;
} CalcParser;

/* Parse cases fixed: (2^3)+1, ((2)^3)*4, (2^(1+1))+3. */
static char calc_expr[CALC_EXPR_MAX + 1];
static uint8_t calc_len = 0;
static uint8_t calc_cursor = 0;
static char calc_result[CALC_OUT_MAX + 1];
static char calc_num[CALC_OUT_MAX + 1];
static char calc_den[CALC_OUT_MAX + 1];
static bool calc_has_result = false;
static bool calc_error = false;
static bool calc_result_fraction = false;
static char calc_hist[CALC_HIST][CALC_HIST_LEN];
static CalcVal calc_value;

static CalcVal parse_expr(CalcParser *ps);

static int64_t iabs64(int64_t v) {
    return v < 0 ? -v : v;
}

static int64_t gcd64(int64_t a, int64_t b) {
    a = iabs64(a);
    b = iabs64(b);
    while (b) {
        int64_t t = a % b;
        a = b;
        b = t;
    }
    return a ? a : 1;
}

static bool fits_i32(int64_t v) {
    return v >= INT32_MIN && v <= INT32_MAX;
}

static double val_double(CalcVal v) {
    if (v.dec) return v.x;
    return (double)v.n / (double)v.d;
}

static CalcVal val_dec(double x) {
    CalcVal v;
    v.dec = true;
    v.n = 0;
    v.d = 1;
    v.x = x;
    return v;
}

static CalcVal val_rat_raw(int64_t n, int64_t d) {
    CalcVal v;
    int64_t g;

    if (d < 0) {
        n = -n;
        d = -d;
    }
    if (d == 0 || !fits_i32(n) || !fits_i32(d)) {
        return val_dec((double)n / (double)d);
    }
    g = gcd64(n, d);
    n /= g;
    d /= g;
    if (!fits_i32(n) || !fits_i32(d)) {
        return val_dec((double)n / (double)d);
    }

    v.dec = false;
    v.n = (int32_t)n;
    v.d = (int32_t)d;
    v.x = (double)v.n / (double)v.d;
    return v;
}

static CalcVal val_rat(int32_t n, int32_t d) {
    return val_rat_raw(n, d);
}

static bool finite_double(double x) {
    return x == x && x < 1.0e12 && x > -1.0e12;
}

static CalcVal val_add(CalcVal a, CalcVal b, int sign) {
    int64_t n, d;
    if (a.dec || b.dec) return val_dec(val_double(a) + sign * val_double(b));
    n = (int64_t)a.n * b.d + sign * (int64_t)b.n * a.d;
    d = (int64_t)a.d * b.d;
    if (!fits_i32(n) || !fits_i32(d)) {
        return val_dec(val_double(a) + sign * val_double(b));
    }
    return val_rat_raw(n, d);
}

static CalcVal val_mul(CalcVal a, CalcVal b) {
    int64_t n, d;
    if (a.dec || b.dec) return val_dec(val_double(a) * val_double(b));
    n = (int64_t)a.n * b.n;
    d = (int64_t)a.d * b.d;
    if (!fits_i32(n) || !fits_i32(d)) {
        return val_dec(val_double(a) * val_double(b));
    }
    return val_rat_raw(n, d);
}

static CalcVal val_div(CalcParser *ps, CalcVal a, CalcVal b) {
    int64_t n, d;
    if ((b.dec && val_double(b) == 0.0) || (!b.dec && b.n == 0)) {
        ps->ok = false;
        return val_rat(0, 1);
    }
    if (a.dec || b.dec) return val_dec(val_double(a) / val_double(b));
    n = (int64_t)a.n * b.d;
    d = (int64_t)a.d * b.n;
    if (!fits_i32(n) || !fits_i32(d)) {
        return val_dec(val_double(a) / val_double(b));
    }
    return val_rat_raw(n, d);
}

static CalcVal val_neg(CalcVal v) {
    if (v.dec) return val_dec(-v.x);
    if (v.n == INT32_MIN) return val_dec(-val_double(v));
    v.n = -v.n;
    v.x = -v.x;
    return v;
}

static bool mul_i32_checked(int32_t a, int32_t b, int32_t *out) {
    int64_t r = (int64_t)a * b;
    if (!fits_i32(r)) return false;
    *out = (int32_t)r;
    return true;
}

static CalcVal val_pow(CalcParser *ps, CalcVal base, CalcVal exp) {
    int32_t rn = 1;
    int32_t rd = 1;
    int32_t bn, bd;
    int32_t e;
    uint8_t i, count;
    double x;

    if (!exp.dec && exp.d == 1 && !base.dec) {
        e = exp.n;
        bn = base.n;
        bd = base.d;
        if (e < 0) {
            if (bn == 0) {
                ps->ok = false;
                return val_rat(0, 1);
            }
            if (e == INT32_MIN) return val_dec(pow(val_double(base), val_double(exp)));
            e = -e;
            {
                int32_t t = bn;
                bn = bd;
                bd = t;
            }
        }
        if (e > 31) return val_dec(pow(val_double(base), val_double(exp)));
        count = (uint8_t)e;
        for (i = 0; i < count; i++) {
            if (!mul_i32_checked(rn, bn, &rn) ||
                !mul_i32_checked(rd, bd, &rd)) {
                return val_dec(pow(val_double(base), val_double(exp)));
            }
        }
        return val_rat(rn, rd);
    }

    x = pow(val_double(base), val_double(exp));
    if (!finite_double(x)) ps->ok = false;
    return val_dec(x);
}

static CalcVal parse_number(CalcParser *ps) {
    const char *s = ps->p;
    bool any = false;
    bool exact = true;
    int64_t n = 0;
    int64_t d = 1;
    double x = 0.0;
    double place = 0.1;

    while (*ps->p >= '0' && *ps->p <= '9') {
        uint8_t digit = (uint8_t)(*ps->p - '0');
        any = true;
        x = x * 10.0 + digit;
        if (exact) {
            n = n * 10 + digit;
            if (!fits_i32(n)) exact = false;
        }
        ps->p++;
    }

    if (*ps->p == '.') {
        ps->p++;
        while (*ps->p >= '0' && *ps->p <= '9') {
            uint8_t digit = (uint8_t)(*ps->p - '0');
            any = true;
            x += digit * place;
            place *= 0.1;
            if (exact) {
                n = n * 10 + digit;
                d *= 10;
                if (!fits_i32(n) || !fits_i32(d)) exact = false;
            }
            ps->p++;
        }
    }

    if (!any || ps->p == s) {
        ps->ok = false;
        return val_rat(0, 1);
    }
    if (exact) return val_rat_raw(n, d);
    return val_dec(x);
}

static CalcVal parse_primary(CalcParser *ps) {
    CalcVal v;
    if (*ps->p == '(') {
        ps->p++;
        v = parse_expr(ps);
        if (*ps->p == ')') {
            ps->p++;
        } else {
            ps->ok = false;
        }
        return v;
    }
    return parse_number(ps);
}

static CalcVal parse_unary(CalcParser *ps) {
    if (*ps->p == '+') {
        ps->p++;
        return parse_unary(ps);
    }
    if (*ps->p == '-') {
        ps->p++;
        return val_neg(parse_unary(ps));
    }
    return parse_primary(ps);
}

static CalcVal parse_power(CalcParser *ps) {
    CalcVal v = parse_unary(ps);
    if (*ps->p == '^') {
        ps->p++;
        v = val_pow(ps, v, parse_power(ps));
    }
    return v;
}

static CalcVal parse_term(CalcParser *ps) {
    CalcVal v = parse_power(ps);
    for (;;) {
        char c = *ps->p;
        if (c == '*') {
            ps->p++;
            v = val_mul(v, parse_power(ps));
        } else if (c == '/') {
            ps->p++;
            v = val_div(ps, v, parse_power(ps));
        } else {
            break;
        }
    }
    return v;
}

static CalcVal parse_expr(CalcParser *ps) {
    CalcVal v = parse_term(ps);
    for (;;) {
        char c = *ps->p;
        if (c == '+') {
            ps->p++;
            v = val_add(v, parse_term(ps), 1);
        } else if (c == '-') {
            ps->p++;
            v = val_add(v, parse_term(ps), -1);
        } else {
            break;
        }
    }
    return v;
}

static uint8_t append_char(char *dst, uint8_t pos, uint8_t max, char c) {
    if (pos < max) dst[pos++] = c;
    dst[pos] = '\0';
    return pos;
}

static uint8_t append_u32(char *dst, uint8_t pos, uint8_t max, uint32_t v) {
    char tmp[10];
    uint8_t n = 0;
    if (v == 0) return append_char(dst, pos, max, '0');
    while (v && n < sizeof(tmp)) {
        tmp[n++] = (char)('0' + v % 10);
        v /= 10;
    }
    while (n) pos = append_char(dst, pos, max, tmp[--n]);
    return pos;
}

static void format_i32(int32_t v, char *dst, uint8_t max) {
    uint8_t pos = 0;
    uint32_t u;
    if (v < 0) {
        pos = append_char(dst, pos, max, '-');
        u = (uint32_t)(-(int64_t)v);
    } else {
        u = (uint32_t)v;
    }
    append_u32(dst, pos, max, u);
}

static void format_rat_inline(CalcVal v, char *dst, uint8_t max) {
    char den[CALC_OUT_MAX + 1];
    uint8_t pos;

    format_i32(v.n, dst, max);
    if (v.d == 1) return;
    pos = (uint8_t)strlen(dst);
    pos = append_char(dst, pos, max, '/');
    format_i32(v.d, den, sizeof(den) - 1);
    {
        uint8_t i;
        for (i = 0; den[i]; i++) pos = append_char(dst, pos, max, den[i]);
    }
}

static void format_dec(double x, char *dst, uint8_t max) {
    uint8_t pos = 0;
    uint32_t whole;
    uint32_t frac;
    uint8_t i;
    char digits[6];

    if (!finite_double(x)) {
        strcpy(dst, "Erro");
        return;
    }
    if (x < 0) {
        pos = append_char(dst, pos, max, '-');
        x = -x;
    }
    if (x > 999999999.0) {
        strcpy(dst, "Grande");
        return;
    }
    whole = (uint32_t)x;
    frac = (uint32_t)((x - whole) * 1000000.0 + 0.5);
    if (frac >= 1000000) {
        whole++;
        frac -= 1000000;
    }
    pos = append_u32(dst, pos, max, whole);
    if (frac == 0) return;

    for (i = 0; i < 6; i++) {
        digits[5 - i] = (char)('0' + frac % 10);
        frac /= 10;
    }
    i = 6;
    while (i > 0 && digits[i - 1] == '0') i--;
    pos = append_char(dst, pos, max, '.');
    {
        uint8_t j;
        for (j = 0; j < i; j++) pos = append_char(dst, pos, max, digits[j]);
    }
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
    calc_cursor = 0;
    calc_has_result = false;
    calc_error = false;
    calc_result_fraction = false;
}

void calc_clear(void) {
    calc_expr[0] = '\0';
    calc_len = 0;
    calc_cursor = 0;
    calc_has_result = false;
    calc_error = false;
    calc_result_fraction = false;
}

bool calc_is_empty(void) {
    return calc_len == 0;
}

static void calc_insert_char(char c) {
    if (calc_len < CALC_EXPR_MAX) {
        memmove(&calc_expr[calc_cursor + 1], &calc_expr[calc_cursor],
                calc_len - calc_cursor + 1);
        calc_expr[calc_cursor++] = c;
        calc_len++;
        calc_has_result = false;
    }
}

static bool calc_insert_str(const char *s) {
    if (calc_len + strlen(s) > CALC_EXPR_MAX) return false;
    while (*s) calc_insert_char(*s++);
    return true;
}

static void calc_backspace(void) {
    if (calc_cursor > 0) {
        memmove(&calc_expr[calc_cursor - 1], &calc_expr[calc_cursor],
                calc_len - calc_cursor + 1);
        calc_cursor--;
        calc_len--;
        calc_has_result = false;
    }
}

static void calc_eval(void) {
    CalcParser ps;

    if (calc_len == 0) return;
    ps.p = calc_expr;
    ps.ok = true;
    calc_value = parse_expr(&ps);
    if (!ps.ok || *ps.p != '\0' ||
        (calc_value.dec && !finite_double(calc_value.x))) {
        calc_error = true;
        calc_result_fraction = false;
        strcpy(calc_result, "Erro");
    } else {
        calc_error = false;
        if (!calc_value.dec) {
            format_i32(calc_value.n, calc_num, CALC_OUT_MAX);
            format_i32(calc_value.d, calc_den, CALC_OUT_MAX);
            calc_result_fraction = calc_value.d != 1;
            format_rat_inline(calc_value, calc_result, CALC_OUT_MAX);
        } else {
            calc_result_fraction = false;
            format_dec(calc_value.x, calc_result, CALC_OUT_MAX);
        }
    }
    calc_has_result = true;
    calc_cursor = calc_len;
    if (!calc_error) {
        uint8_t i, a = 0, n = 0;
        for (i = CALC_HIST - 1; i > 0; i--) strcpy(calc_hist[i], calc_hist[i - 1]);
        /* build "expr=result" manually (avoids linking the printf core) */
        while (calc_expr[a] && n < CALC_HIST_LEN - 1) calc_hist[0][n++] = calc_expr[a++];
        if (n < CALC_HIST_LEN - 1) calc_hist[0][n++] = '=';
        a = 0;
        while (calc_result[a] && n < CALC_HIST_LEN - 1) calc_hist[0][n++] = calc_result[a++];
        calc_hist[0][n] = '\0';
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
        if (pressed_once(keymap[i].k)) {
            calc_insert_char(keymap[i].c);
            changed = true;
        }
    }
    if (pressed_once(kb_KeySquare)) {
        if (calc_insert_str("^2")) changed = true;
    }
    if (pressed_once(kb_KeyLeft)) {
        if (calc_cursor > 0) calc_cursor--;
        changed = true;
    }
    if (pressed_once(kb_KeyRight)) {
        if (calc_cursor < calc_len) calc_cursor++;
        changed = true;
    }
    if (pressed_once(kb_KeyDel)) {
        calc_backspace();
        changed = true;
    }
    if (pressed_once(kb_KeySto)) {
        calc_eval();
        changed = true;
    }
    return changed;
}

static bool split_top_fraction(const char *src, char *num, char *den) {
    uint8_t i;
    uint8_t slash = 255;
    int8_t depth = 0;

    for (i = 0; src[i]; i++) {
        if (src[i] == '(') depth++;
        else if (src[i] == ')' && depth > 0) depth--;
        else if (src[i] == '/' && depth == 0) {
            if (slash != 255) return false;
            slash = i;
        }
    }
    if (slash == 255 || slash == 0 || src[slash + 1] == '\0') return false;
    if (slash > CALC_EXPR_MAX || strlen(src + slash + 1) > CALC_EXPR_MAX) {
        return false;
    }
    memcpy(num, src, slash);
    num[slash] = '\0';
    strcpy(den, src + slash + 1);
    return true;
}

static void draw_fraction(const char *num, const char *den,
                          int center_x, int bar_y, uint8_t color) {
    int nw = (int)gfx_GetStringWidth(num);
    int dw = (int)gfx_GetStringWidth(den);
    int bw = (nw > dw ? nw : dw) + 10;
    int x;

    if (bw > 272) bw = 272;
    x = center_x - bw / 2;
    if (x < 28) x = 28;
    if (x + bw > 312) x = 312 - bw;

    gfx_SetTextFGColor(color);
    prn(num, center_x - nw / 2, bar_y - 13);
    gfx_SetColor(color);
    gfx_HorizLine(x, bar_y, bw);
    prn(den, center_x - dw / 2, bar_y + 6);
    gfx_SetTextFGColor(COL_BLACK);
}

static void draw_expr_with_caret(void) {
    char left[CALC_EXPR_MAX + 1];
    int caret_x;

    if (calc_len == 0) {
        prn("_", 12, 130);
        caret_x = 12;
    } else {
        prn(calc_expr, 12, 130);
        memcpy(left, calc_expr, calc_cursor);
        left[calc_cursor] = '\0';
        caret_x = 12 + (int)gfx_GetStringWidth(left);
    }
    gfx_SetColor(COL_BLACK);
    gfx_VertLine(caret_x, 128, 12);
}

void search_overlay_draw(void) {
    uint8_t i;

    /* history: newest at top, oldest at bottom */
    gfx_SetTextFGColor(COL_GRAY);
    for (i = 0; i < CALC_HIST; i++) {
        if (calc_hist[i][0]) prn(calc_hist[i], 12, 22 + i * 17);
    }

    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(8, 116, 304);

    gfx_SetTextFGColor(COL_BLACK);
    draw_expr_with_caret();

    if (calc_has_result) {
        gfx_SetTextFGColor(calc_error ? COL_RED : COL_BLUE);
        prn("=", 12, 158);
        if (calc_result_fraction) {
            draw_fraction(calc_num, calc_den, 92, 166, COL_BLUE);
        } else {
            prn(calc_result, 28, 158);
        }
        gfx_SetTextFGColor(COL_BLACK);
    } else {
        char num[CALC_EXPR_MAX + 1];
        char den[CALC_EXPR_MAX + 1];
        if (split_top_fraction(calc_expr, num, den)) {
            draw_fraction(num, den, 160, 174, COL_GRAY);
        }
    }
}
