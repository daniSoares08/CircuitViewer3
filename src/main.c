#include "cv3.h"

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
    for (i = 0; i < visible && first + i < antigos_count; i++) {
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
        prn(antigos_items[item].title, 22, y);
    }
    if (first > 0) prn("^", 300, 32);
    if (first + visible < antigos_count) prn("v", 300, 212);
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

static uint8_t subject_ex_count(const Subject *subject) {
    return (uint8_t)(subject->count + subject->extra_count);
}

static const Exercise *subject_ex_at(const Subject *subject, uint8_t index) {
    if (index < subject->count) return &subject->items[index];
    return &subject->extra_items[index - subject->count];
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
    const Subject *subject = &subjects[subject_index];
    uint8_t ex_index = 0;
    uint8_t page = 0;
    bool redraw = true;

    wait_key_release();
    while (1) {
        const Exercise *ex = subject_ex_at(subject, ex_index);
        uint8_t total = subject_ex_count(subject);

        check_on_exit();
        kb_Scan();

        if (redraw) {
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

static void antigos_loop(void) {
    uint8_t selected = 0;
    bool redraw = true;

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
        if (pressed_once(kb_KeyDown) && selected + 1 < antigos_count) {
            selected++;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && selected > 0) {
            selected--;
            redraw = true;
        }
        if (pressed_once(kb_KeyEnter)) {
            wait_key_release();
            subject_loop(antigos_items[selected].index);
            redraw = true;
        }
        delay(15);
    }
}

/* ---- Component search -------------------------------------------------- */

enum { SEARCH_BACK = 0, SEARCH_RUN = 1 };

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

static void search_results_loop(const uint8_t *filtered, uint16_t fcount) {
    uint16_t idx = 0;
    uint8_t page = 0;
    bool redraw = true;

    if (fcount == 0) { search_no_match_loop(); return; }

    wait_key_release();
    while (1) {
        const ExEntry *e = &all_exercises[filtered[idx]];
        const Exercise *ex = e->ex;

        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_ex_header(e->subject, ex->title, (uint8_t)idx,
                           (uint8_t)fcount, page, ex->page_count);
            draw_page_template(&ex->pages[page]);
            draw_footer_ex();
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) { wait_key_release(); return; }
        if ((pressed_once(kb_KeyRight) || pressed_once(kb_KeyEnter)) &&
            page + 1 < ex->page_count) { page++; redraw = true; }
        if (pressed_once(kb_KeyLeft) && page > 0) { page--; redraw = true; }
        if (pressed_once(kb_KeyDown) && idx + 1 < fcount) { idx++; page = 0; redraw = true; }
        if (pressed_once(kb_KeyUp) && idx > 0) { idx--; page = 0; redraw = true; }
        delay(15);
    }
}

static void search_flow(void) {
    static uint8_t counts[5] = { 0, 0, 0, 0, 0 };  /* persists across entries */
    static uint8_t filtered[256];

    while (1) {
        uint8_t action = search_select_loop(counts);
        uint16_t i, fcount = 0;

        if (action == SEARCH_BACK) return;

        for (i = 0; i < all_exercises_count; i++) {
            const ExEntry *e = &all_exercises[i];
            if (e->comp[0] >= counts[0] && e->comp[1] >= counts[1] &&
                e->comp[2] >= counts[2] && e->comp[3] >= counts[3] &&
                e->comp[4] >= counts[4]) {
                if (fcount < (uint16_t)sizeof(filtered))
                    filtered[fcount++] = (uint8_t)i;
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
