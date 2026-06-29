NAME = CIRCVIE3
DESCRIPTION = "Circuit viewer 3"
COMPRESSED = YES
ARCHIVED = YES

SRC = src/main.c src/ui.c src/formulas.c src/exercises.c

CFLAGS = -Wall -Wextra -Oz
LDFLAGS = -lgraphx -lkeypadc -ltice

include $(shell cedev-config --makefile)
