/* CircuitViewer3 - github.com/daniSoares08
 * Open source (MIT License): free to use, copy, modify and redistribute. */

#include "cv3.h"

static void appvar_missing_loop(void);

static void draw_empty_state(void) {
    gfx_FillScreen(COL_WHITE);
    gfx_SetTextFGColor(COL_BLACK);
    print_center("CIRCVIE3", 8);
    gfx_SetColor(COL_BLACK);
    gfx_HorizLine(0, 24, SCREEN_W);
    print_center("Sem exercicios carregados.", 82);
    print_center("Adicione itens em src/exercises.c", 104);
    print_center("e formulas em src/formulas.c.", 122);
    draw_footer_menu();
}

static void draw_main_menu(uint8_t selected) {
    uint8_t i;
    uint8_t first = 0;
    uint8_t visible = 10;

    gfx_FillScreen(COL_WHITE);
    gfx_SetTextFGColor(COL_BLACK);
    print_center("CIRCVIE3", 8);
    gfx_SetColor(COL_BLACK);
    gfx_HorizLine(0, 24, SCREEN_W);
    gfx_SetTextFGColor(COL_GRAY);
    prn("Assunto:", 10, 30);

    if (selected >= visible) first = (uint8_t)(selected - visible + 1);

    for (i = 0; i < visible && first + i < menu_count; i++) {
        uint8_t item = (uint8_t)(first + i);
        int y = 46 + i * 17;
        if (item == selected) {
            gfx_SetColor(COL_LIGHT);
            gfx_FillRectangle(12, y - 3, 296, 15);
            gfx_SetColor(COL_BLUE);
            gfx_Rectangle(12, y - 3, 296, 15);
            gfx_SetTextFGColor(COL_BLUE);
        } else {
            gfx_SetTextFGColor(COL_BLACK);
        }
        prn(menu_items[item].title, 22, y);
    }

    if (first > 0) prn("^", 300, 32);
    if (first + visible < menu_count) prn("v", 300, 212);

    draw_footer_menu();
}

static void draw_antigos_menu(uint8_t selected) {
    uint8_t i;
    uint8_t first = 0;
    uint8_t visible = 10;

    gfx_FillScreen(COL_WHITE);
    gfx_SetTextFGColor(COL_BLACK);
    print_center("ANTIGOS", 8);
    gfx_SetColor(COL_BLACK);
    gfx_HorizLine(0, 24, SCREEN_W);
    gfx_SetTextFGColor(COL_GRAY);
    prn("Versoes anteriores:", 10, 30);

    if (selected >= visible) first = (uint8_t)(selected - visible + 1);
    for (i = 0; i < visible && first + i < antigos_topic_count; i++) {
        uint8_t item = (uint8_t)(first + i);
        int y = 46 + i * 17;
        if (item == selected) {
            gfx_SetColor(COL_LIGHT);
            gfx_FillRectangle(12, y - 3, 296, 15);
            gfx_SetColor(COL_BLUE);
            gfx_Rectangle(12, y - 3, 296, 15);
            gfx_SetTextFGColor(COL_BLUE);
        } else {
            gfx_SetTextFGColor(COL_BLACK);
        }
        prn(antigos_topics[item].title, 22, y);
    }
    if (first > 0) prn("^", 300, 32);
    if (first + visible < antigos_topic_count) prn("v", 300, 212);
    draw_footer_menu();
}

static void draw_formula_menu(uint8_t selected) {
    uint8_t i;

    gfx_FillScreen(COL_WHITE);
    gfx_SetTextFGColor(COL_BLACK);
    print_center("FORMULARIO", 8);
    gfx_SetColor(COL_BLACK);
    gfx_HorizLine(0, 24, SCREEN_W);
    gfx_SetTextFGColor(COL_GRAY);
    prn("Escolha o bloco:", 10, 30);

    for (i = 0; i < formula_count; i++) {
        int y = 46 + i * 17;
        if (i == selected) {
            gfx_SetColor(COL_LIGHT);
            gfx_FillRectangle(12, y - 3, 296, 15);
            gfx_SetColor(COL_BLUE);
            gfx_Rectangle(12, y - 3, 296, 15);
            gfx_SetTextFGColor(COL_BLUE);
        } else {
            gfx_SetTextFGColor(COL_BLACK);
        }
        prn(formula_topics[i].title, 22, y);
    }

    draw_footer_menu();
}

static int main_menu_loop(void) {
    uint8_t selected = 0;
    bool redraw = true;

    wait_key_release();
    if (menu_count == 0) {
        draw_empty_state();
        gfx_SwapDraw();
        while (1) {
            check_on_exit();
            kb_Scan();
            delay(15);
        }
    }

    while (1) {
        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_main_menu(selected);
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyDown) && selected + 1 < menu_count) {
            selected++;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && selected > 0) {
            selected--;
            redraw = true;
        }
        if (pressed_once(kb_KeyEnter)) {
            wait_key_release();
            return selected;
        }
        delay(15);
    }
}

static int formula_menu_loop(void) {
    uint8_t selected = 0;
    bool redraw = true;

    wait_key_release();
    if (formula_count == 0) {
        return -1;
    }

    while (1) {
        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_formula_menu(selected);
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return -1;
        }
        if (pressed_once(kb_KeyDown) && selected + 1 < formula_count) {
            selected++;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && selected > 0) {
            selected--;
            redraw = true;
        }
        if (pressed_once(kb_KeyEnter)) {
            wait_key_release();
            return selected;
        }
        delay(15);
    }
}

static void formula_topic_loop(uint8_t index) {
    const FormulaTopic *topic = &formula_topics[index];
    uint8_t page = 0;
    bool redraw = true;

    wait_key_release();
    while (1) {
        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_header(topic->title, page, topic->page_count);
            draw_page_template(&topic->pages[page]);
            draw_footer_formula();
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return;
        }
        if ((pressed_once(kb_KeyRight) || pressed_once(kb_KeyEnter)) &&
            page + 1 < topic->page_count) {
            page++;
            redraw = true;
        }
        if (pressed_once(kb_KeyLeft) && page > 0) {
            page--;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) || pressed_once(kb_KeyDown)) {
            wait_key_release();
            return;
        }
        delay(15);
    }
}

static void formulas_loop(void) {
    while (1) {
        int choice = formula_menu_loop();
        if (choice < 0) return;
        formula_topic_loop((uint8_t)choice);
    }
}

static void subject_loop(uint8_t subject_index) {
    const SubRange *subject = &subjects[subject_index];
    uint16_t ex_index = 0;
    uint8_t page = 0;
    bool redraw = true;

    if (!appvar_available()) {
        appvar_missing_loop();
        return;
    }

    wait_key_release();
    while (1) {
        uint16_t gidx = (uint16_t)(subject->start + ex_index);
        const Exercise *ex = exercise_load(gidx);
        uint16_t total = subject->count;
        if (!ex) {
            appvar_missing_loop();
            return;
        }

        check_on_exit();
        kb_Scan();

        if (redraw && ex) {
            exercise_set_page(page);
            draw_ex_header(subject->title, ex->title, ex_index,
                           total, page, ex->page_count);
            draw_page_template(&ex->pages[page]);
            draw_footer_ex();
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return;
        }
        if ((pressed_once(kb_KeyRight) || pressed_once(kb_KeyEnter)) &&
            page + 1 < ex->page_count) {
            page++;
            redraw = true;
        }
        if (pressed_once(kb_KeyLeft) && page > 0) {
            page--;
            redraw = true;
        }
        if (pressed_once(kb_KeyDown) && ex_index + 1 < total) {
            ex_index++;
            page = 0;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && ex_index > 0) {
            ex_index--;
            page = 0;
            redraw = true;
        }
        delay(15);
    }
}

static void appvar_missing_loop(void) {
    bool redraw = true;

    wait_key_release();
    while (1) {
        check_on_exit();
        kb_Scan();
        if (redraw) {
            gfx_FillScreen(COL_WHITE);
            gfx_SetTextFGColor(COL_BLACK);
            print_center("CIRCVIE3", 8);
            gfx_SetColor(COL_BLACK);
            gfx_HorizLine(0, 24, SCREEN_W);
            print_center("Dados ausentes", 92);
            print_center("Envie CV3DAT0..N", 114);
            print_center("CLEAR volta", 140);
            draw_footer_ex();
            gfx_SwapDraw();
            redraw = false;
        }
        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return;
        }
        delay(15);
    }
}

static void antigos_view_loop(uint8_t topic) {
    uint16_t start = antigos_topics[topic].start;
    uint16_t total = antigos_topics[topic].count;
    uint16_t pos = 0;
    uint8_t page = 0;
    bool redraw = true;

    wait_key_release();
    while (1) {
        uint16_t gidx = (uint16_t)(start + pos);
        const Exercise *ex = exercise_load(gidx);
        if (!ex) {
            appvar_missing_loop();
            return;
        }
        check_on_exit();
        kb_Scan();
        if (redraw && ex) {
            exercise_set_page(page);
            draw_ex_header(antigos_topics[topic].title, ex->title, pos, total,
                           page, ex->page_count);
            draw_page_template(&ex->pages[page]);
            draw_footer_ex();
            gfx_SwapDraw();
            redraw = false;
        }
        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return;
        }
        if ((pressed_once(kb_KeyRight) || pressed_once(kb_KeyEnter)) &&
            ex && page + 1 < ex->page_count) {
            page++;
            redraw = true;
        }
        if (pressed_once(kb_KeyLeft) && page > 0) {
            page--;
            redraw = true;
        }
        if (pressed_once(kb_KeyDown) && pos + 1 < total) {
            pos++;
            page = 0;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && pos > 0) {
            pos--;
            page = 0;
            redraw = true;
        }
        delay(15);
    }
}

static void antigos_loop(void) {
    uint8_t selected = 0;
    bool redraw = true;

    if (!appvar_available()) {
        appvar_missing_loop();
        return;
    }

    wait_key_release();
    while (1) {
        check_on_exit();
        kb_Scan();
        if (redraw) {
            draw_antigos_menu(selected);
            gfx_SwapDraw();
            redraw = false;
        }
        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return;
        }
        if (pressed_once(kb_KeyDown) && selected + 1 < antigos_topic_count) {
            selected++;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && selected > 0) {
            selected--;
            redraw = true;
        }
        if (pressed_once(kb_KeyEnter)) {
            wait_key_release();
            antigos_view_loop(selected);
            redraw = true;
        }
        delay(15);
    }
}

/* ---- Component search -------------------------------------------------- */

enum { SEARCH_BACK = 0, SEARCH_RUN = 1, SEARCH_SIN = 2, SEARCH_COS = 3 };

static void draw_search_select(const uint8_t counts[5], bool show_labels,
                               bool show_counts) {
    gfx_FillScreen(COL_WHITE);
    /* the blank body now hosts the calculator overlay */
    search_overlay_draw();
    draw_search_footer(counts, show_labels, show_counts);
}

static uint8_t search_select_loop(uint8_t counts[5]) {
    bool redraw = true;
    bool second = false;       /* armed by 2nd: subtract on next component key */
    bool prev_alpha = false;
    bool prev_math = false;

    wait_key_release();
    while (1) {
        bool alpha_held, math_held;
        uint8_t hy, hw, hz, ht, hg;
        int comp;

        check_on_exit();
        kb_Scan();
        /* alpha peeks the component labels, math peeks the live counts */
        alpha_held = kb_IsDown(kb_KeyAlpha) ? true : false;
        math_held = kb_IsDown(kb_KeyMath) ? true : false;
        if (alpha_held != prev_alpha) { prev_alpha = alpha_held; redraw = true; }
        if (math_held != prev_math) { prev_math = math_held; redraw = true; }

        if (redraw) {
            draw_search_select(counts, alpha_held, math_held && !alpha_held);
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_Key2nd)) second = !second;

        /* evaluate every component key each frame (no short-circuit, so the
           edge state of each key stays correct) */
        hy = pressed_once(kb_KeyYequ);
        hw = pressed_once(kb_KeyWindow);
        hz = pressed_once(kb_KeyZoom);
        ht = pressed_once(kb_KeyTrace);
        hg = pressed_once(kb_KeyGraph);
        comp = hy ? 0 : hw ? 1 : hz ? 2 : ht ? 3 : hg ? 4 : -1;
        if (comp >= 0) {
            if (second) {
                if (counts[comp] > 0) counts[comp]--;
                second = false;
            } else if (counts[comp] < 99) {
                counts[comp]++;
            }
            redraw = true;
        }

        if (pressed_once(kb_KeySin)) { wait_key_release(); return SEARCH_SIN; }
        if (pressed_once(kb_KeyCos)) { wait_key_release(); return SEARCH_COS; }

        if (calc_handle_key()) redraw = true;

        if (pressed_once(kb_KeyEnter)) { wait_key_release(); return SEARCH_RUN; }
        if (pressed_once(kb_KeyClear)) {
            if (!calc_is_empty()) {
                calc_clear();
                redraw = true;
            } else {
                wait_key_release();
                return SEARCH_BACK;
            }
        }
        delay(15);
    }
}

static void search_no_match_loop(void) {
    bool redraw = true;
    wait_key_release();
    while (1) {
        check_on_exit();
        kb_Scan();
        if (redraw) {
            gfx_FillScreen(COL_WHITE);
            gfx_SetTextFGColor(COL_BLACK);
            print_center("Nenhum exercicio encontrado", 100);
            print_center("CLEAR volta", 120);
            draw_footer_ex();
            gfx_SwapDraw();
            redraw = false;
        }
        if (pressed_once(kb_KeyClear)) { wait_key_release(); return; }
        delay(15);
    }
}

static void search_results_loop(const uint16_t *filtered, uint16_t fcount) {
    uint16_t idx = 0;
    uint8_t page = 0;
    bool redraw = true;
    bool big = fcount > 10;   /* >10 results: wrap-around + 2nd jumps 10 */
    bool jump = false;        /* armed by 2nd: next up/down moves 10 */

    if (fcount == 0) { search_no_match_loop(); return; }

    wait_key_release();
    while (1) {
        uint16_t gidx = filtered[idx];
        const ExMeta *meta = &ex_meta[gidx];
        const Exercise *ex;
        const char *subject = meta->subject;

        ex = exercise_load(gidx);
        if (!ex) {
            appvar_missing_loop();
            return;
        }

        check_on_exit();
        kb_Scan();

        if (redraw && ex) {
            exercise_set_page(page);
            draw_ex_header(subject, ex->title, idx, fcount,
                           page, ex->page_count);
            draw_page_template(&ex->pages[page]);
            draw_footer_ex();
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) { wait_key_release(); return; }
        if ((pressed_once(kb_KeyRight) || pressed_once(kb_KeyEnter)) &&
            page + 1 < ex->page_count) { page++; redraw = true; }
        if (pressed_once(kb_KeyLeft) && page > 0) { page--; redraw = true; }

        if (big && pressed_once(kb_Key2nd)) jump = !jump;
        {
            bool dn = pressed_once(kb_KeyDown);
            bool up = pressed_once(kb_KeyUp);
            if (dn || up) {
                uint16_t old = idx;
                uint16_t step = (big && jump) ? 10 : 1;
                if (big) {
                    /* infinite scroll: wrap modulo fcount */
                    if (dn) idx = (uint16_t)((idx + step) % fcount);
                    else    idx = (uint16_t)((idx + fcount - (step % fcount)) % fcount);
                } else {
                    if (dn && idx + 1 < fcount) idx++;
                    else if (up && idx > 0) idx--;
                }
                jump = false;
                if (idx != old) { page = 0; redraw = true; }
            }
        }
        delay(15);
    }
}

static void search_flow(void) {
    static uint8_t counts[5] = { 0, 0, 0, 0, 0 };  /* persists across entries */
    static uint16_t filtered[256];
    const uint16_t cap = (uint16_t)(sizeof(filtered) / sizeof(filtered[0]));

    if (!appvar_available()) {
        appvar_missing_loop();
        return;
    }

    while (1) {
        uint8_t action = search_select_loop(counts);
        uint16_t i, fcount = 0;

        if (action == SEARCH_BACK) return;

        if (action == SEARCH_SIN || action == SEARCH_COS) {
            /* sin = sem grafico, cos = com grafico (generated lists). */
            const uint16_t *src = (action == SEARCH_SIN) ? nofig_items : withfig_items;
            uint16_t n = (action == SEARCH_SIN) ? nofig_count : withfig_count;
            for (i = 0; i < n; i++) {
                if (fcount < cap) filtered[fcount++] = src[i];
            }
            search_results_loop(filtered, fcount);
            continue;
        }

        /* SEARCH_RUN: filter by component minimums over all exercises. */
        for (i = 0; i < ex_count; i++) {
            const ExMeta *m = &ex_meta[i];
            if (m->comp[0] >= counts[0] && m->comp[1] >= counts[1] &&
                m->comp[2] >= counts[2] && m->comp[3] >= counts[3] &&
                m->comp[4] >= counts[4]) {
                if (fcount < cap) {
                    filtered[fcount++] = i;
                }
            }
        }
        search_results_loop(filtered, fcount);
        /* loop back to the select screen with counts preserved */
    }
}

int main(void) {
    kb_DisableOnLatch();
    kb_Scan();
    screen_init();
    calc_init();
    appvar_init();

    /* open straight into the search/calculator screen */
    search_flow();

    while (1) {
        int choice = main_menu_loop();
        const MenuItem *item;

        if (choice < 0) continue;
        item = &menu_items[choice];

        if (item->kind == MENU_FORMULA) {
            formulas_loop();
        } else if (item->kind == MENU_SEARCH) {
            search_flow();
        } else if (item->kind == MENU_ANTIGOS) {
            antigos_loop();
        } else {
            subject_loop(item->index);
        }
    }

    gfx_End();
    return 0;
}
