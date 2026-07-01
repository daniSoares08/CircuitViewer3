/* CircuitViewer3 - github.com/daniSoares08
 * Open source (MIT License): free to use, copy, modify and redistribute. */

#ifndef CV3_H
#define CV3_H

#include <tice.h>
#include <graphx.h>
#include <keypadc.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

#define SCREEN_W 320
#define SCREEN_H 240
#define COUNT_OF(a) (sizeof(a) / sizeof((a)[0]))

enum {
    COL_WHITE = 0,
    COL_BLACK = 1,
    COL_GRAY = 2,
    COL_LIGHT = 3,
    COL_BLUE = 4,
    COL_RED = 5,
    COL_GREEN = 6
};

enum {
    MENU_FORMULA = 0,
    MENU_SUBJECT = 1,
    MENU_SEARCH = 2,
    MENU_ANTIGOS = 3
};

typedef void (*body_draw_fn)(void);

typedef struct {
    const char *text;
    int x;
    int y;
    uint8_t color;
} TextLine;

typedef struct {
    const char *title;
    const char *subtitle;
    const TextLine *lines;
    uint8_t line_count;
    const char *result;
    uint8_t result_y;
    body_draw_fn body;
} PageTemplate;

typedef struct {
    const char *title;
    const PageTemplate *pages;
    uint8_t page_count;
} FormulaTopic;

typedef struct {
    const char *title;
    const PageTemplate *pages;
    uint8_t page_count;
} Exercise;

typedef struct {
    const char *title;
    const char *subject;
    uint8_t chunk;
    uint16_t local;
    uint8_t page_count;
    uint8_t comp[5];
} ExMeta;

typedef struct {
    const char *title;
    uint16_t start;
    uint16_t count;
} SubRange;

typedef struct {
    const char *title;
    uint8_t kind;
    uint8_t index;
} MenuItem;

extern const FormulaTopic formula_topics[];
extern const uint8_t formula_count;
extern const ExMeta ex_meta[];
extern const uint16_t ex_count;
extern const uint8_t chunk_count;
extern const SubRange subjects[];
extern const uint8_t subject_count;
extern const SubRange antigos_topics[];
extern const uint8_t antigos_topic_count;
extern const MenuItem menu_items[];
extern const uint8_t menu_count;

extern const uint16_t nofig_items[];     /* sin: sem grafico */
extern const uint16_t nofig_count;
extern const uint16_t withfig_items[];   /* cos: com grafico */
extern const uint16_t withfig_count;

void appvar_init(void);
bool appvar_available(void);
const Exercise *exercise_load(uint16_t global_idx);
void exercise_set_page(uint8_t page);

void check_on_exit(void);
uint8_t pressed_once(kb_lkey_t key);
void wait_key_release(void);
void screen_init(void);

void print_center(const char *text, int y);
void prn(const char *text, int x, int y);
void draw_header(const char *title, uint8_t page, uint8_t total);
void draw_ex_header(const char *subject, const char *ex_title,
                    uint16_t ex, uint16_t ex_total,
                    uint8_t page, uint8_t page_total);
void draw_footer_menu(void);
void draw_footer_formula(void);
void draw_footer_ex(void);
void draw_search_footer(const uint8_t counts[5], bool show_labels, bool show_counts);
void calc_init(void);
bool calc_handle_key(void);
bool calc_is_empty(void);
void calc_clear(void);
void search_overlay_draw(void);
void draw_title(const char *title, const char *subtitle);
void result_box(const char *text, int y);
void step_box(int y, const char *l1, const char *l2);
void draw_page_template(const PageTemplate *page);

void draw_node(int x, int y);
void draw_wire(int x1, int y1, int x2, int y2);
void draw_terminal(int x, int y, const char *label);
void draw_res_h(int x1, int y, int x2, const char *label);
void draw_res_v(int x, int y1, int y2, const char *label);
void draw_cap_h(int x1, int y, int x2, const char *label);
void draw_cap_v(int x, int y1, int y2, const char *label);
void draw_ind_h(int x1, int y, int x2, const char *label);
void draw_ind_v(int x, int y1, int y2, const char *label);
void draw_voltage_source(int x, int y1, int y2, const char *label);
void draw_voltage_source_h(int x1, int y, int x2, const char *label);
void draw_current_source_v_dir(int x, int y1, int y2,
                               const char *label, bool upward);
void draw_current_source_h_dir(int x1, int y, int x2,
                               const char *label, bool right);
void draw_ground(int x, int y);
void draw_switch_open_h(int x1, int y, int x2, const char *label);
void draw_opamp(int x, int y, bool noninv_input_top);
void draw_dep_vsource_v(int x, int y1, int y2, const char *label);
void draw_dep_vsource_h(int x1, int y, int x2, const char *label);
void draw_dep_isource_v(int x, int y1, int y2, const char *label, bool upward);

void ui_label(const char *text, int x, int y);
void ui_arrow_h(int x1, int y, int x2, const char *label, bool right);
void ui_arrow_v(int x, int y1, int y2, const char *label, bool up);
void ui_pm(int x, int y1, int y2);
void ui_vo(int x, int y_top, int y_bottom, const char *label);

#endif
