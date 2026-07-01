# CIRCVIE3

_github.com/daniSoares08 - Open source (MIT License): free to use, copy, modify and redistribute._

CIRCVIE3 is a personal solutions app for Sadiku & Alexander's **"Fundamentals
of Electric Circuits"** ("Fundamentos de Circuitos Eletricos"), built for the
**TI-84 Plus CE** graphing calculator. It ships 211 fully worked circuit
exercises (statement, redrawn circuit diagram, step-by-step solution and
final answer) plus a component-search screen and a built-in exact-fraction
scientific calculator, all running natively on-calculator via `graphx` +
`keypadc` (CE C toolchain / CEdev).

No copyrighted book pages, scans or images ship inside the `.8xp`/`.8xv` -
every circuit is redrawn from scratch with `graphx` primitives.

## Navigation

- App boots straight into **Buscar** (search + calculator overlay).
- `UP/DOWN`: choose a menu item / previous-next exercise inside a subject.
- `ENTER`: open a menu entry, or advance a page.
- `LEFT/RIGHT`: previous/next page inside an exercise.
- `CLEAR`: back to the previous menu (from the search screen, back to the
  main menu; from the main menu, exits toward the search screen again).
- `ON`: quits immediately from anywhere.

Each exercise follows the page order: **Circuito -> Enunciado -> Resolucao
(step by step) -> Resultado**. The circuit page is skipped for exercises with
no diagram (pure formula/charge/energy/cost calculations).

## Content

211 exercises across 9 main subjects plus an "Antigos" (legacy) section with
6 more topics ported from earlier CircuitViewer versions:

- Tensao/Potencia, Leis de Kirchhoff, Serie/Paralelo, Estrela-Triangulo,
  Analise Nodal, Analise de Malhas, Superposicao, Transformacao de Fontes,
  Revisao (40 chapter-end conceptual questions).
- Antigos: Thevenin/Norton, Amplificadores Operacionais, Capacitancia,
  Indutancia, Resposta RC/RL, and 2 legacy CircuitViewer v1 problems.

Sources: the Sadiku textbook ("Problemas" sections, chapters 1-4 mostly),
practice exams in `PROVAS/`, and the CircuitViewer2 "Ivan" catalog. All
answers were re-derived by hand - generated manifests/`.md` notes from
earlier automated passes contained errors (see `EXERCISE_MANIFEST.md`).

## Component search

The first screen (`Buscar`) doubles as a basic exact-fraction calculator
(digits, `+ - * / ^ ( )`, `STO->` = evaluate) and a filter: hold `alpha` to
peek the footer's component-key labels, hold `math` to peek the live counts,
then use `Y=`/`WINDOW`/`ZOOM`/`TRACE`/`GRAPH` to bump minimum counts for
resistors/voltage sources/current sources/capacitors/inductors (`2nd` arms a
"subtract one" on the next key). `ENTER` filters; `sin`/`cos` on the select
screen instead browse every exercise without/with a figure.

## Code layout

- `src/main.c` - menus and navigation loops (app logic).
- `src/ui.c` - keyboard/screen init and every circuit-drawing primitive
  (`draw_res_h`, `draw_voltage_source`, controlled sources
  `draw_dep_vsource_*`/`draw_dep_isource_v`, etc.).
- `src/search_overlay.c` - the exact-rational calculator + search overlay.
- `src/appvar.c` - runtime AppVar loader/decoder (see below).
- `src/exercises.c` - **GENERATED** by `tools/generate_exercises.py`. Never
  hand-edit.
- `src/cv3.h` - shared types/prototypes.
- `tools/generate_exercises.py` - source of truth: exercise data (statement,
  circuit as an "ops" list, solution), C codegen, manifest, and AppVar
  packing.
- `tools/cv_render.py` - mirrors `ui.c` geometry in Python; renders every
  page to a 320x240 PNG (`--preview DIR`) so layout can be checked without a
  calculator.
- `tools/audit_strings.py` - checks ASCII-only + string length <= 39 chars.
- `tools/render_pdf.py` - renders book/exam PDF pages to PNG for intake.
- `ADDING_EXERCISES.md` - guide for adding new exercises to the generator.

## Memory architecture (important)

The compiled `.8xp` only holds lightweight **metadata** (`ExMeta[211]`:
title/subject/chunk/local index/page count/component counts) plus the menu
tables. The actual page content (text, circuit "ops") for **every**
exercise lives in three archived AppVars, `CV3DAT0.8xv` / `CV3DAT1.8xv` /
`CV3DAT2.8xv` (each < 58 KB), read straight from Flash at runtime by
`src/appvar.c`. This keeps the running program under the CE's real RAM
budget (~150 KB usable; a fully-compiled build hit "ERRO: MEMORIA" well
before the size the TI tools report as free).

**You must send all 4 files to the calculator: `CIRCVIE3.8xp` +
`CV3DAT0.8xv` + `CV3DAT1.8xv` + `CV3DAT2.8xv`.** Missing AppVars show a
"dados ausentes" screen instead of crashing.

## Changing exercises

```bash
# 1) edit tools/generate_exercises.py (data/ops)
# 2) regenerate src/exercises.c + EXERCISE_MANIFEST.md + AppVar chunks + PNG previews
python tools/generate_exercises.py --preview /tmp/preview
# 3) audit strings, then build
python tools/audit_strings.py
```

Open the PNGs in `/tmp/preview` and check nothing is off-screen, overlapping
or covering text **before** sending anything to the calculator.

## Building

CEdev toolchain (Windows build, `C:\CEdev`):

```bash
export PATH="/c/CEdev/bin:$PATH"
python tools/generate_exercises.py   # (re)writes src/exercises.c + the .8xv chunks
/c/CEdev/bin/make.exe clean && /c/CEdev/bin/make.exe
```

Output: `bin/CIRCVIE3.8xp` (~16 KB) plus the three `CV3DAT*.8xv` chunks
written next to it by the generator. Send all four.

## License

MIT License - see `LICENSE`. Do whatever you want with this: use it, copy
it, modify it, redistribute it, sell it. Author: Daniel Soares
(github.com/daniSoares08).
