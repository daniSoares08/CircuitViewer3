# CircuitViewer3 - github.com/daniSoares08
# Open source (MIT License): free to use, copy, modify and redistribute.

NAME = CIRCVIE3
DESCRIPTION = "Circuit viewer 3"
COMPRESSED = YES
ARCHIVED = YES

SRC = src/main.c src/ui.c src/formulas.c src/exercises.c src/search_overlay.c src/appvar.c

CFLAGS = -Wall -Wextra -Oz
LDFLAGS = -lgraphx -lkeypadc -lfileioc -ltice

include $(shell cedev-config --makefile)
