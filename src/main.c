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

int main(void) {
    kb_DisableOnLatch();
    kb_Scan();
    screen_init();

    while (1) {
        int choice = main_menu_loop();
        const MenuItem *item;

        if (choice < 0) continue;
        item = &menu_items[choice];

        if (item->kind == MENU_FORMULA) {
            formulas_loop();
        } else {
            subject_loop(item->index);
        }
    }

    gfx_End();
    return 0;
}
