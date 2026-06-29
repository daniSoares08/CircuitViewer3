#!/usr/bin/env python3
"""Generate CIRCVIE3 exercise catalog, manifest and page previews.

Each exercise can define:
  - statement : list[str]  -> "Enunciado" page(s)
  - circuit   : list[op]   -> dedicated "Circuito" page (None = no circuit)
  - solution  : list[str]  -> paginated "Resolucao" page(s)
  - answer    : list[str]  -> "Resultado" page
  - final     : str        -> short text shown in the result box

Lines support light markup: "# " = blue heading, "= " = red result line.

Run:
  python tools/generate_exercises.py            # write src + manifest
  python tools/generate_exercises.py --preview DIR  # also render page PNGs
"""

import argparse
from pathlib import Path

import cv_render


# Fallback solution outlines (used only when an exercise has no "solution").
METHODS = {
    "Tensao Pot": [
        "1) Identifique v, i, p ou energia.",
        "2) Use p=v*i e w=p*t.",
        "3) Use carga q=i*t quando pedido.",
        "4) Confira sinal pela convencao passiva.",
    ],
    "Kirchhoff": [
        "1) Marque sentidos de corrente.",
        "2) Aplique KCL nos nos.",
        "3) Aplique KVL nas malhas.",
        "4) Resolva o sistema e confira sinais.",
    ],
    "Serie/Paralelo": [
        "1) Reduza blocos serie/paralelo.",
        "2) Use divisor V ou divisor I.",
        "3) Recalcule grandezas no circuito.",
        "4) Confira Req e unidades.",
    ],
    "Estrela Triang": [
        "1) Escolha a rede Y ou delta.",
        "2) Transforme para simplificar.",
        "3) Reduza serie/paralelo restante.",
        "4) Volte para a grandeza pedida.",
    ],
    "Nodal": [
        "1) Escolha o terra.",
        "2) Escreva KCL em cada no.",
        "3) Trate fonte dependente se houver.",
        "4) Resolva tensoes nodais.",
    ],
    "Malhas": [
        "1) Defina correntes de malha.",
        "2) Escreva KVL em cada malha.",
        "3) Monte e resolva o sistema.",
        "4) Combine correntes compartilhadas.",
    ],
    "Superposicao": [
        "1) Ative uma fonte por vez.",
        "2) Fonte V vira curto quando desligada.",
        "3) Fonte I vira aberto quando desligada.",
        "4) Some contribuicoes com sinal.",
    ],
    "Transf Fontes": [
        "1) Troque V serie R por I paralelo R.",
        "2) Troque I paralelo R por V serie R.",
        "3) Combine fontes/resistores.",
        "4) Calcule a grandeza pedida.",
    ],
}

GENERIC_DRAW = {
    "Tensao Pot": "draw_generic_tensao_pot",
    "Kirchhoff": "draw_generic_kirchhoff",
    "Serie/Paralelo": "draw_generic_serie_paralelo",
    "Estrela Triang": "draw_generic_estrela_triang",
    "Nodal": "draw_generic_nodal",
    "Malhas": "draw_generic_malhas",
    "Superposicao": "draw_generic_superposicao",
    "Transf Fontes": "draw_generic_transf_fontes",
}


# ----------------------------------------------------------------------------
# Circuit op lists (single source: emitted to C and rendered for preview)
# ----------------------------------------------------------------------------

CIRCUITS = {
    # --- Exam questions (ported from the original dedicated draws) ---
    "p1_q1": [
        ("isrc_v", 42, 82, 174, "20A", True),
        ("res_h", 42, 82, 96, "2"), ("res_h", 96, 82, 150, "1"),
        ("res_v", 150, 82, 174, "3"), ("res_h", 150, 82, 208, "4"),
        ("res_v", 208, 82, 174, "6"), ("res_h", 208, 82, 262, "8"),
        ("res_v", 262, 82, 174, "12"), ("wire", 42, 174, 262, 174),
        ("res_h", 150, 174, 208, "1.2"), ("vo", 280, 98, 150, "Vx"),
    ],
    "p1_q2": [
        ("isrc_v", 54, 82, 178, "8A", True), ("res_v", 150, 82, 178, "R1"),
        ("res_v", 248, 82, 126, "R2"), ("vsrc_v", 248, 126, 178, "6V"),
        ("wire", 54, 82, 248, 82), ("wire", 54, 178, 248, 178),
        ("arr_v", 170, 92, 132, "2A", False), ("arr_v", 270, 92, 154, "I", False),
        ("vo", 130, 100, 150, "9V"), ("vo", 226, 96, 122, "3V"),
    ],
    "p1_q3": [
        ("vsrc_v", 48, 94, 170, "12V"), ("res_h", 48, 94, 118, "10"),
        ("res_h", 48, 122, 118, "10"), ("wire", 48, 94, 48, 122),
        ("wire", 118, 94, 118, 122), ("res_v", 118, 94, 170, "10"),
        ("res_h", 118, 94, 208, "4"), ("vsrc_v", 208, 94, 170, "20V"),
        ("wire", 48, 170, 208, 170), ("node", 118, 94), ("lbl", "V1", 108, 72),
    ],
    "p1_q4": [
        ("vsrc_v", 44, 88, 170, "8V"), ("res_h", 44, 88, 108, "10"),
        ("res_v", 108, 88, 170, "2"), ("res_h", 108, 88, 174, "4"),
        ("vsrc_v", 174, 88, 170, "6V"), ("res_h", 174, 88, 238, "1"),
        ("vsrc_v", 238, 88, 170, "2V"), ("res_v", 238, 88, 170, "5"),
        ("wire", 44, 170, 238, 170), ("arr_h", 68, 132, 96, "i1", True),
        ("arr_h", 130, 132, 160, "i2", True), ("arr_h", 196, 132, 226, "i3", True),
    ],
    "p1_q5": [
        ("vsrc_v", 42, 92, 170, "20V"), ("res_h", 42, 92, 104, "2"),
        ("res_v", 104, 92, 170, "1"), ("isrc_h", 104, 72, 174, "2A", True),
        ("res_h", 104, 92, 174, "3"), ("res_v", 174, 92, 170, "4"),
        ("res_h", 174, 92, 238, "5"), ("vsrc_v", 238, 92, 170, "16V"),
        ("wire", 42, 170, 238, 170), ("wire", 104, 92, 104, 72),
        ("wire", 174, 72, 174, 92), ("arr_v", 188, 110, 152, "i", False),
    ],
    "rec_q1": [
        ("term", 36, 86, "a"), ("res_h", 40, 86, 88, "10"),
        ("res_h", 88, 86, 138, "1"), ("res_v", 138, 86, 168, "6"),
        ("res_h", 138, 86, 194, "3"), ("res_v", 194, 86, 168, "12"),
        ("res_h", 194, 86, 248, "4"), ("res_v", 248, 86, 168, "5"),
        ("wire", 40, 168, 248, 168), ("term", 256, 168, "b"),
        ("res_h", 88, 168, 138, "1.2"),
    ],
    "rec_q2": [
        ("vsrc_v", 42, 100, 166, "12V"), ("res_h", 42, 100, 104, "6"),
        ("res_v", 104, 100, 166, "3"), ("res_h", 104, 100, 168, "5"),
        ("res_v", 168, 100, 166, "12"), ("res_h", 168, 100, 230, "4"),
        ("vsrc_v", 230, 100, 166, "19V"), ("wire", 42, 166, 230, 166),
        ("wire", 104, 100, 104, 74), ("wire", 168, 100, 168, 74),
        ("isrc_h", 104, 74, 168, "2A", False), ("vo", 134, 108, 130, "vo"),
    ],
    "rec_q3": [
        ("vsrc_v", 48, 90, 170, "12V"), ("res_h", 48, 90, 124, "4"),
        ("res_v", 124, 90, 170, "6"), ("vsrc_h", 124, 90, 204, "10V"),
        ("res_v", 204, 90, 170, "2"), ("wire", 48, 170, 204, 170),
        ("arr_v", 142, 104, 150, "I", False),
    ],
    "rec_q4": [
        ("vsrc_v", 48, 88, 170, "60V"), ("res_h", 48, 88, 126, "12"),
        ("res_v", 126, 88, 170, "12"), ("res_h", 126, 88, 216, "6"),
        ("vsrc_v", 216, 88, 170, "24V"), ("wire", 48, 170, 216, 170),
        ("node", 126, 88), ("lbl", "V0", 116, 68),
    ],
    "rec_q5": [
        ("isrc_v", 42, 86, 170, "2A", True), ("res_v", 84, 86, 170, "5"),
        ("res_h", 84, 86, 150, "5"), ("res_v", 150, 86, 170, "4"),
        ("res_h", 150, 86, 226, "10"), ("vsrc_v", 226, 86, 170, "20V"),
        ("wire", 42, 86, 84, 86), ("wire", 42, 170, 226, 170),
        ("arr_v", 166, 104, 150, "i", False),
    ],

    # --- Chapter 1 ---
    "e_1_7": [
        ("wire", 70, 72, 70, 178), ("wire", 60, 130, 256, 130),
        ("lbl", "q(C)", 44, 60), ("lbl", "t(s)", 248, 118),
        ("lbl", "50", 48, 86), ("lbl", "-50", 30, 166),
        ("wire", 70, 130, 115, 90), ("wire", 115, 90, 205, 170),
        ("wire", 205, 170, 250, 130),
        ("wire", 115, 128, 115, 132), ("wire", 160, 128, 160, 132),
        ("wire", 205, 128, 205, 132), ("wire", 250, 128, 250, 132),
        ("lbl", "2", 111, 134), ("lbl", "4", 156, 116),
        ("lbl", "6", 201, 134), ("lbl", "8", 252, 134),
    ],
    "e_1_17": [
        ("res_v", 55, 90, 170, "1"), ("res_h", 55, 90, 160, "2"),
        ("res_v", 160, 90, 170, "3"), ("res_h", 160, 90, 265, "4"),
        ("res_v", 265, 90, 170, "5"), ("wire", 55, 170, 265, 170),
        ("node", 55, 90), ("node", 160, 90), ("node", 265, 90),
        ("node", 55, 170), ("node", 160, 170), ("node", 265, 170),
    ],

    # --- Chapter 2: Kirchhoff ---
    "e_2_7": [
        ("vsrc_v", 55, 86, 170, "12V"),
        ("res_h", 55, 86, 135, "1"), ("res_h", 135, 86, 215, "4"),
        ("res_v", 135, 86, 170, "8"), ("res_v", 215, 86, 170, "5"),
        ("wire", 215, 86, 270, 86), ("isrc_v", 270, 86, 170, "2A", False),
        ("wire", 55, 170, 270, 170), ("node", 135, 86), ("node", 215, 86),
    ],
    "e_2_9": [
        ("wire", 60, 80, 118, 80), ("arr_h", 118, 80, 202, "4A", False),
        ("wire", 200, 80, 260, 80), ("wire", 60, 180, 260, 180),
        ("arr_v", 60, 80, 180, "5A", False), ("arr_v", 260, 80, 180, "i3", True),
        ("arr_v", 120, 80, 130, "1A", True), ("arr_v", 120, 130, 180, "i1", True),
        ("arr_h", 120, 130, 200, "6A", True),
        ("arr_v", 200, 80, 130, "i2", True), ("arr_v", 200, 130, 180, "7A", False),
        ("node", 120, 130), ("node", 200, 130),
        ("lbl", "A", 104, 134), ("lbl", "B", 186, 134),
    ],
    "e_2_11": [
        ("res_v", 60, 90, 170, "V1"), ("res_h", 60, 90, 160, "1V"),
        ("vsrc_v", 160, 90, 170, "5V"), ("res_h", 160, 90, 260, "2V"),
        ("res_v", 260, 90, 170, "V2"), ("wire", 60, 170, 260, 170),
        ("node", 160, 90),
    ],
    "e_2_13": [
        ("wire", 50, 110, 50, 80), ("arr_h", 50, 80, 260, "2A", True),
        ("wire", 260, 80, 260, 110),
        ("arr_h", 50, 110, 120, "I2", False),
        ("arr_h", 120, 110, 190, "7A", True),
        ("arr_h", 190, 110, 260, "I4", False),
        ("arr_v", 50, 110, 180, "I1", True), ("arr_v", 120, 110, 180, "3A", False),
        ("arr_v", 190, 110, 180, "I3", False), ("arr_v", 260, 110, 180, "4A", False),
        ("wire", 50, 180, 260, 180),
        ("node", 50, 110), ("node", 120, 110), ("node", 190, 110), ("node", 260, 110),
    ],
    "e_2_15": [
        ("vsrc_v", 55, 90, 170, "10V"), ("res_h", 55, 90, 150, "12"),
        ("vsrc_h", 150, 90, 245, "16V"), ("vsrc_v", 150, 90, 170, "4V"),
        ("dvs_v", 245, 90, 170, "3ix"), ("wire", 55, 170, 245, 170),
        ("node", 150, 90), ("arr_v", 172, 100, 150, "ix", False),
        ("lbl", "+v-", 90, 74),
    ],
    "e_2_17": [
        ("vsrc_v", 55, 90, 170, "24V"), ("res_h", 55, 90, 235, "v1"),
        ("res_v", 235, 90, 170, "v3"), ("vsrc_v", 285, 90, 170, "10V"),
        ("wire", 235, 90, 285, 90), ("wire", 235, 170, 285, 170),
        ("vsrc_h", 55, 170, 235, "12V"),
        ("wire", 235, 96, 150, 128), ("wire", 150, 134, 62, 166),
        ("lbl", "v2", 150, 118),
        ("node", 235, 90), ("node", 235, 170),
    ],
    "e_2_19": [
        ("vsrc_v", 60, 90, 170, "12V"), ("vsrc_h", 60, 90, 200, "10V"),
        ("res_v", 200, 90, 170, "3"), ("vsrc_h", 60, 170, 200, "-8V"),
        ("arr_v", 224, 104, 150, "I", False),
    ],
    "e_2_21": [
        ("vsrc_v", 55, 90, 170, "15V"), ("res_h", 55, 90, 150, "1"),
        ("dvs_h", 150, 90, 250, "2Vx"), ("res_v", 250, 90, 170, "5"),
        ("res_h", 55, 170, 250, "2"), ("vo", 272, 100, 150, "Vx"),
        ("node", 150, 90),
    ],
    "e_2_23": [
        ("isrc_v", 36, 90, 183, "20A", True), ("wire", 36, 90, 92, 90),
        ("res_v", 92, 90, 183, "2"), ("res_h", 92, 90, 165, "1"),
        ("res_h", 165, 90, 242, "1.2"), ("res_v", 165, 90, 133, "4"),
        ("wire", 165, 133, 145, 133), ("res_v", 145, 133, 183, "3"),
        ("wire", 165, 133, 185, 133), ("res_v", 185, 133, 183, "6"),
        ("wire", 242, 90, 288, 90),
        ("res_v", 242, 90, 183, "8"), ("res_v", 288, 90, 183, "12"),
        ("wire", 36, 183, 288, 183),
        ("node", 92, 90), ("node", 165, 90), ("node", 242, 90), ("node", 165, 133),
        ("lbl", "+vx-", 112, 74),
    ],

    # --- Chapter 2: Serie/Paralelo ---
    "e_2_27": [
        ("vsrc_v", 55, 90, 170, "10V"), ("res_h", 55, 90, 150, "8"),
        ("res_v", 150, 90, 170, "3"), ("wire", 150, 90, 210, 90),
        ("res_v", 210, 90, 170, "6"), ("wire", 55, 170, 210, 170),
        ("node", 150, 90), ("arr_h", 80, 78, 128, "Io", True),
    ],
    "e_2_29": [
        ("term", 32, 90, ""), ("term", 32, 170, ""),
        ("wire", 32, 90, 50, 90), ("wire", 32, 170, 50, 170),
        ("res_h", 50, 90, 120, "5"), ("res_h", 120, 90, 190, "5"),
        ("res_h", 190, 90, 260, "5"),
        ("res_v", 120, 90, 170, "5"), ("res_v", 190, 90, 170, "5"),
        ("res_v", 260, 90, 170, "5"), ("wire", 50, 170, 260, 170),
        ("lbl", "Req", 4, 124), ("node", 120, 90), ("node", 190, 90),
    ],
    "e_2_31": [
        ("vsrc_v", 48, 88, 178, "200V"), ("res_h", 48, 88, 118, "3"),
        ("res_v", 118, 88, 178, "4"), ("wire", 118, 88, 248, 88),
        ("res_v", 183, 88, 178, "1"), ("res_v", 248, 88, 178, "2"),
        ("wire", 48, 178, 248, 178), ("node", 118, 88), ("node", 183, 88),
        ("arr_h", 70, 76, 104, "i1", True), ("arr_v", 138, 98, 152, "i2", False),
        ("arr_h", 150, 76, 176, "i3", True), ("arr_v", 203, 98, 152, "i4", False),
        ("arr_v", 263, 98, 152, "i5", False),
    ],
    "e_2_33": [
        ("isrc_v", 45, 90, 170, "9A", True), ("res_v", 85, 90, 170, "1S"),
        ("res_h", 85, 90, 160, "4S"), ("res_v", 160, 90, 170, "2S"),
        ("res_h", 160, 90, 235, "6S"), ("res_v", 235, 90, 170, "3S"),
        ("wire", 45, 90, 85, 90), ("wire", 45, 170, 235, 170),
        ("node", 85, 90), ("node", 160, 90), ("vo", 66, 100, 160, "v"),
        ("arr_h", 95, 78, 150, "i", True),
    ],
    "e_2_35": [
        ("vsrc_v", 48, 80, 185, "200V"), ("wire", 48, 80, 230, 80),
        ("res_v", 130, 80, 130, "70"), ("res_v", 130, 130, 185, "20"),
        ("res_v", 230, 80, 130, "30"), ("res_v", 230, 130, 185, "5"),
        ("wire", 48, 185, 230, 185), ("arr_h", 130, 130, 230, "Io", True),
        ("node", 130, 130), ("node", 230, 130), ("vo", 255, 140, 178, "Vo"),
    ],
    "e_2_37": [
        ("vsrc_v", 55, 90, 170, "20V"), ("res_h", 55, 90, 150, "R"),
        ("res_h", 150, 90, 245, "10"), ("vsrc_v", 245, 90, 170, "30V"),
        ("wire", 55, 170, 245, 170), ("node", 150, 90),
        ("lbl", "+10V-", 82, 74),
    ],
    "e_2_41": [
        ("term", 30, 100, ""), ("term", 30, 180, ""), ("lbl", "Req", 2, 134),
        ("wire", 30, 100, 45, 100), ("wire", 30, 180, 45, 180),
        ("res_h", 45, 100, 110, "30"), ("res_v", 110, 100, 180, "60"),
        ("res_h", 110, 100, 175, "10"), ("res_h", 175, 100, 235, "R"),
        ("wire", 235, 100, 300, 100),
        ("res_v", 240, 100, 180, "12"), ("res_v", 270, 100, 180, "12"),
        ("res_v", 300, 100, 180, "12"), ("wire", 45, 180, 300, 180),
        ("node", 110, 100), ("node", 235, 100),
    ],
    "e_2_47": [
        ("term", 28, 110, "a"), ("wire", 28, 110, 42, 110),
        ("res_h", 42, 110, 95, "10"),
        ("res_h", 95, 95, 150, "5"), ("res_h", 95, 125, 150, "20"),
        ("wire", 95, 95, 95, 125), ("wire", 150, 95, 150, 125),
        ("res_h", 150, 95, 205, "6"), ("res_h", 150, 125, 205, "3"),
        ("wire", 205, 95, 205, 125),
        ("res_h", 205, 110, 258, "8"),
        ("term", 272, 110, "b"), ("wire", 258, 110, 272, 110),
    ],

    # --- Chapter 4: linearidade (grupo "Superposicao") ---
    "e_4_1": [
        ("vsrc_v", 50, 90, 175, "30V"), ("res_h", 50, 90, 130, "5"),
        ("res_h", 130, 90, 215, "25"), ("res_v", 130, 90, 175, "40"),
        ("res_v", 215, 90, 175, "15"), ("wire", 50, 175, 215, 175),
        ("node", 130, 90), ("node", 215, 90),
        ("arr_v", 232, 100, 152, "io", False),
    ],
    "e_4_4": [
        ("wire", 50, 90, 50, 170), ("res_h", 50, 90, 130, "3"),
        ("res_v", 130, 90, 170, "6"), ("res_h", 130, 90, 200, "2"),
        ("res_v", 200, 90, 170, "4"), ("wire", 200, 90, 255, 90),
        ("isrc_v", 255, 90, 170, "9A", True), ("wire", 50, 170, 255, 170),
        ("node", 130, 90), ("node", 200, 90),
        ("arr_v", 148, 100, 150, "io", False),
    ],
    "e_4_5": [
        ("vsrc_v", 48, 90, 175, "15V"), ("res_h", 48, 90, 112, "2"),
        ("res_h", 112, 90, 176, "3"), ("res_h", 176, 90, 240, "2"),
        ("res_v", 112, 90, 175, "6"), ("res_v", 176, 90, 175, "6"),
        ("res_v", 240, 90, 175, "4"), ("wire", 48, 175, 240, 175),
        ("node", 112, 90), ("node", 176, 90), ("lbl", "vo", 168, 74),
    ],
    "e_4_7": [
        ("vsrc_v", 50, 90, 175, "4V"), ("res_h", 50, 90, 130, "1"),
        ("res_h", 130, 90, 210, "4"), ("res_v", 130, 90, 175, "3"),
        ("res_v", 210, 90, 175, "2"), ("wire", 50, 175, 210, 175),
        ("node", 130, 90), ("node", 210, 90),
        ("vo", 230, 100, 152, "Vo"),
    ],

    # --- Chapter 2: Estrela/Triangulo ---
    "e_2_55": [
        ("vsrc_v", 45, 80, 190, "24V"),
        ("wire", 45, 80, 90, 80), ("arr_h", 90, 80, 150, "Io", True),
        ("wire", 150, 80, 220, 80),
        ("res_v", 120, 80, 130, "20"), ("res_v", 120, 130, 190, "10"),
        ("res_v", 220, 80, 130, "60"), ("res_v", 220, 130, 190, "50"),
        ("res_h", 120, 130, 220, "40"), ("res_h", 120, 190, 220, "20"),
        ("wire", 45, 190, 120, 190),
        ("node", 120, 130), ("node", 220, 130),
        ("node", 120, 190), ("node", 220, 190),
    ],

    # --- Chapter 3: Analise Nodal ---
    "e_3_3": [
        ("wire", 45, 85, 285, 85), ("wire", 45, 175, 285, 175),
        ("isrc_v", 45, 85, 175, "8A", True),
        ("res_v", 95, 85, 175, "10"), ("arr_v", 95, 90, 112, "I1", False),
        ("res_v", 140, 85, 175, "20"), ("arr_v", 140, 90, 112, "I2", False),
        ("res_v", 185, 85, 175, "30"), ("arr_v", 185, 90, 112, "I3", False),
        ("isrc_v", 235, 85, 175, "20A", False),
        ("res_v", 285, 85, 175, "60"), ("arr_v", 285, 90, 112, "I4", False),
        ("lbl", "vo", 150, 70),
    ],
    "e_3_5": [
        ("wire", 90, 78, 250, 78),
        ("vsrc_v", 90, 78, 128, "30V"), ("res_v", 90, 128, 178, "2k"),
        ("vsrc_v", 170, 78, 128, "20V"), ("res_v", 170, 128, 178, "5k"),
        ("res_v", 250, 78, 178, "4k"), ("wire", 90, 178, 250, 178),
        ("vo", 272, 90, 168, "vo"),
    ],
    "e_3_7": [
        ("wire", 50, 85, 250, 85), ("wire", 50, 175, 250, 175),
        ("isrc_v", 50, 85, 175, "2A", True),
        ("res_v", 110, 85, 175, "10"), ("res_v", 180, 85, 175, "20"),
        ("dis_v", 250, 85, 175, "0.2Vx", False),
        ("vo", 90, 95, 165, "Vx"),
    ],
    "e_3_9": [
        ("vsrc_v", 50, 90, 175, "24V"),
        ("res_h", 50, 90, 135, "250"), ("arr_h", 70, 76, 110, "Ib", True),
        ("dvs_h", 135, 90, 220, "60Ib"),
        ("res_v", 135, 90, 175, "50"), ("res_v", 220, 90, 175, "150"),
        ("wire", 50, 175, 220, 175), ("node", 135, 90), ("node", 220, 90),
    ],
    "e_3_13": [
        ("res_h", 60, 90, 140, "2"), ("vsrc_h", 140, 90, 210, "10V"),
        ("res_v", 60, 90, 175, "8"), ("res_v", 210, 90, 175, "4"),
        ("wire", 210, 90, 260, 90), ("isrc_v", 260, 90, 175, "15A", True),
        ("wire", 60, 175, 260, 175), ("gnd", 160, 175),
        ("node", 60, 90), ("node", 210, 90),
        ("lbl", "v1", 48, 74), ("lbl", "v2", 196, 74),
    ],
    "e_3_17": [
        ("wire", 70, 80, 90, 80), ("arr_h", 90, 80, 150, "io", True),
        ("wire", 150, 80, 250, 80), ("wire", 70, 180, 250, 180),
        ("res_v", 70, 80, 120, "4"), ("vsrc_v", 70, 120, 180, "60V"),
        ("res_v", 160, 80, 120, "2"), ("dis_v", 160, 120, 180, "3io", True),
        ("res_v", 250, 80, 180, "8"), ("res_h", 70, 120, 160, "10"),
        ("node", 70, 120), ("node", 160, 120),
    ],
    "e_3_19": [
        ("isrc_v", 40, 90, 175, "5A", True), ("wire", 40, 90, 70, 90),
        ("res_h", 70, 90, 150, "8"), ("res_h", 150, 90, 230, "4"),
        ("res_v", 70, 90, 175, "4"), ("res_v", 150, 90, 175, "2"),
        ("res_v", 230, 90, 135, "8"), ("vsrc_v", 230, 135, 175, "12V"),
        ("wire", 40, 175, 230, 175),
        ("node", 70, 90), ("node", 150, 90), ("node", 230, 90),
        ("lbl", "v1", 60, 74), ("lbl", "v2", 140, 74), ("lbl", "v3", 220, 74),
    ],
    "e_3_21": [
        ("wire", 60, 120, 60, 80), ("res_h", 60, 80, 230, "4k"),
        ("wire", 230, 80, 230, 120),
        ("res_h", 60, 120, 140, "2k"), ("dvs_h", 140, 120, 230, "3vo"),
        ("isrc_v", 60, 120, 180, "3mA", True), ("res_v", 230, 120, 180, "1k"),
        ("wire", 60, 180, 230, 180), ("gnd", 145, 180),
        ("node", 60, 120), ("node", 230, 120),
        ("vo", 252, 128, 172, "vo"),
        ("lbl", "v1", 46, 106), ("lbl", "v2", 214, 104),
    ],
    "e_3_23": [
        ("vsrc_v", 45, 90, 175, "30V"),
        ("res_h", 45, 90, 115, "1"), ("res_v", 115, 90, 175, "2"),
        ("res_h", 115, 90, 185, "4"), ("dvs_h", 185, 90, 255, "2Vo"),
        ("res_v", 255, 90, 175, "16"), ("wire", 255, 90, 290, 90),
        ("isrc_v", 290, 90, 175, "3A", True), ("wire", 45, 175, 290, 175),
        ("vo", 95, 98, 168, "Vo"), ("node", 115, 90), ("node", 255, 90),
    ],

    # --- Chapter 3: Analise de Malhas ---
    "e_3_33": [
        ("vsrc_v", 60, 80, 175, "12V"),
        ("res_h", 60, 80, 200, "3"), ("res_v", 200, 80, 175, "2"),
        ("res_h", 60, 175, 200, "1"),
        ("wire", 68, 88, 118, 123), ("wire", 142, 140, 192, 167),
        ("lbl", "4", 92, 104),
        ("wire", 192, 88, 142, 123), ("wire", 118, 140, 68, 167),
        ("lbl", "5", 150, 104),
        ("node", 60, 80), ("node", 200, 80), ("node", 60, 175), ("node", 200, 175),
    ],
    "e_3_41": [
        ("res_h", 50, 72, 230, "10"),
        ("wire", 50, 72, 50, 125), ("wire", 230, 72, 230, 125),
        ("res_h", 50, 125, 140, "2"), ("vsrc_h", 140, 125, 230, "6V"),
        ("res_v", 50, 125, 195, "4"), ("res_v", 230, 125, 195, "5"),
        ("res_v", 140, 125, 160, "1"), ("vsrc_v", 140, 160, 195, "8V"),
        ("wire", 50, 195, 230, 195), ("arr_v", 156, 134, 164, "i", True),
        ("lbl", "i1", 132, 90), ("lbl", "i2", 86, 150), ("lbl", "i3", 178, 150),
    ],
    "e_3_45": [
        ("res_h", 60, 72, 160, "4"), ("res_h", 160, 72, 260, "8"),
        ("isrc_v", 160, 72, 120, "4A", True),
        ("wire", 60, 72, 60, 120), ("wire", 260, 72, 260, 120),
        ("res_h", 60, 120, 160, "2"), ("res_h", 160, 120, 260, "6"),
        ("vsrc_v", 60, 120, 190, "30V"), ("arr_v", 44, 132, 158, "i", True),
        ("res_v", 160, 120, 190, "3"), ("res_v", 260, 120, 190, "1"),
        ("wire", 60, 190, 260, 190), ("node", 160, 120),
    ],
    "e_3_57": [
        ("vsrc_v", 48, 80, 180, "90V"),
        ("wire", 48, 80, 90, 80), ("arr_h", 90, 80, 140, "io", True),
        ("wire", 140, 80, 230, 80),
        ("res_v", 150, 80, 135, "R"), ("res_v", 230, 80, 135, "3k"),
        ("wire", 150, 135, 230, 135), ("res_v", 190, 135, 180, "4k"),
        ("wire", 48, 180, 190, 180),
        ("vo", 250, 88, 128, "V1"), ("vo", 210, 143, 172, "V2"),
        ("node", 150, 135),
    ],

    # --- Chapter 4: Transformacao de Fontes ---
    "e_4_21": [
        ("vsrc_v", 55, 90, 170, "V"),
        ("res_h", 55, 90, 150, "R1"), ("arr_h", 75, 78, 115, "io", True),
        ("res_v", 150, 90, 170, "R2"),
        ("wire", 150, 90, 210, 90), ("isrc_v", 210, 90, 170, "I", True),
        ("wire", 55, 170, 210, 170), ("node", 150, 90),
    ],
    "e_4_23": [
        ("isrc_v", 45, 90, 175, "3A", True), ("wire", 45, 90, 90, 90),
        ("res_v", 90, 90, 175, "10"), ("res_h", 90, 90, 170, "8"),
        ("arr_h", 108, 78, 152, "i", True),
        ("res_v", 170, 90, 175, "6"), ("res_h", 170, 90, 250, "3"),
        ("vsrc_v", 250, 90, 175, "15V"), ("wire", 45, 175, 250, 175),
        ("node", 90, 90), ("node", 170, 90),
    ],
    "e_4_25": [
        ("res_h", 110, 120, 210, "9"),
        ("wire", 110, 120, 110, 78), ("isrc_h", 110, 78, 210, "2A", True),
        ("wire", 210, 78, 210, 120),
        ("wire", 110, 120, 55, 120), ("isrc_v", 55, 120, 180, "3A", False),
        ("res_v", 110, 120, 180, "4"), ("res_v", 210, 120, 180, "5"),
        ("wire", 210, 120, 265, 120), ("isrc_v", 265, 120, 180, "6A", False),
        ("res_h", 110, 180, 170, "2"), ("vsrc_h", 170, 180, 210, "30V"),
        ("wire", 55, 180, 110, 180), ("wire", 210, 180, 265, 180),
        ("lbl", "+vo-", 116, 166),
        ("node", 110, 120), ("node", 210, 120),
        ("node", 110, 180), ("node", 210, 180),
    ],
    "e_4_31": [
        ("vsrc_v", 55, 90, 175, "12V"),
        ("res_h", 55, 90, 140, "3"), ("res_v", 140, 90, 175, "8"),
        ("res_h", 140, 90, 225, "6"), ("dvs_v", 225, 90, 175, "2vx"),
        ("wire", 55, 175, 225, 175), ("lbl", "+vx-", 78, 74),
        ("node", 140, 90), ("node", 225, 90),
    ],
}


# Exercises whose figure shows two independent circuits (a) and (b):
# each variant becomes its own "Circuito" page.
MULTI_CIRCUITS = {
    "e_2_43": [
        ("(a)", [
            ("term", 30, 90, "a"), ("wire", 30, 90, 40, 90),
            ("res_h", 40, 78, 140, "5"), ("res_h", 40, 102, 140, "20"),
            ("wire", 40, 78, 40, 102), ("wire", 140, 78, 140, 102),
            ("res_v", 140, 90, 170, "10"), ("wire", 140, 90, 205, 90),
            ("res_v", 205, 90, 170, "40"), ("wire", 40, 170, 205, 170),
            ("term", 30, 170, "b"), ("wire", 30, 170, 40, 170),
            ("node", 140, 90),
        ]),
        ("(b)", [
            ("term", 30, 80, "a"), ("wire", 30, 80, 55, 80),
            ("term", 30, 175, "b"), ("wire", 30, 175, 55, 175),
            ("res_v", 55, 80, 175, "80"), ("res_h", 55, 80, 140, "10"),
            ("wire", 140, 80, 250, 80), ("res_v", 140, 80, 175, "60"),
            ("res_v", 195, 80, 175, "20"), ("res_v", 250, 80, 175, "30"),
            ("wire", 55, 175, 250, 175), ("node", 55, 80), ("node", 140, 80),
        ]),
    ],
    "e_2_45": [
        ("(a)", [
            ("term", 25, 89, "a"), ("wire", 25, 89, 42, 89),
            ("res_h", 42, 62, 120, "10"), ("res_h", 42, 80, 120, "40"),
            ("res_h", 42, 98, 120, "20"), ("res_h", 42, 116, 120, "30"),
            ("wire", 42, 62, 42, 116), ("wire", 120, 62, 120, 116),
            ("res_h", 120, 89, 185, "5"), ("res_h", 185, 89, 265, "50"),
            ("term", 288, 89, "b"), ("wire", 265, 89, 288, 89),
            ("node", 120, 89),
        ]),
        ("(b)", [
            ("term", 28, 120, "a"), ("wire", 28, 120, 32, 120),
            ("term", 28, 176, "b"), ("wire", 28, 176, 32, 176),
            ("res_h", 32, 120, 96, "5"), ("res_h", 96, 72, 160, "30"),
            ("wire", 160, 72, 232, 72), ("wire", 96, 120, 96, 72),
            ("res_h", 96, 120, 168, "20"), ("res_v", 168, 72, 120, "12"),
            ("res_v", 168, 120, 176, "60"), ("wire", 232, 72, 232, 176),
            ("res_v", 96, 120, 176, "25"), ("res_h", 96, 176, 168, "10"),
            ("wire", 168, 176, 232, 176), ("res_h", 32, 176, 96, "15"),
            ("node", 96, 120), ("node", 168, 120), ("node", 96, 176),
        ]),
    ],
    "e_2_49": [
        ("(a)", [
            ("term", 60, 80, "a"), ("term", 205, 80, "b"),
            ("res_h", 60, 80, 205, "12"),
            ("res_v", 60, 80, 170, "12"), ("res_v", 205, 80, 170, "12"),
            ("wire", 60, 170, 205, 170),
            ("term", 128, 188, "c"), ("wire", 128, 170, 128, 188),
        ]),
        ("(b)", [
            ("term", 60, 80, "a"), ("term", 205, 80, "b"),
            ("res_h", 60, 80, 205, "60"),
            ("res_v", 60, 80, 170, "30"), ("res_v", 205, 80, 170, "10"),
            ("wire", 60, 170, 205, 170),
            ("term", 128, 188, "c"), ("wire", 128, 170, 128, 188),
        ]),
    ],
    "e_2_53": [
        ("(a)", [
            ("term", 22, 80, "a"), ("wire", 22, 80, 36, 80),
            ("res_h", 36, 80, 74, "20"),
            ("res_h", 74, 80, 182, "30"), ("res_v", 74, 80, 160, "60"),
            ("res_v", 182, 80, 160, "40"), ("res_h", 74, 160, 182, "50"),
            ("wire", 176, 86, 132, 116), ("wire", 124, 124, 80, 154),
            ("lbl", "10", 120, 110),
            ("res_v", 182, 160, 200, "80"),
            ("wire", 182, 200, 25, 200), ("term", 22, 200, "b"),
            ("node", 74, 80), ("node", 182, 80), ("node", 74, 160), ("node", 182, 160),
        ]),
        ("(b)", [
            ("term", 25, 60, "a"), ("wire", 25, 60, 150, 60),
            ("term", 25, 182, "b"), ("wire", 25, 182, 50, 182),
            ("wire", 150, 60, 50, 182), ("wire", 150, 60, 250, 182),
            ("wire", 50, 182, 250, 182),
            ("wire", 100, 121, 200, 121), ("wire", 100, 121, 150, 182),
            ("wire", 200, 121, 150, 182),
            ("node", 150, 60), ("node", 50, 182), ("node", 250, 182),
            ("node", 100, 121), ("node", 200, 121), ("node", 150, 182),
            ("lbl", "30 ohm cada", 158, 92),
        ]),
    ],
}


def all_draws():
    """Map every circuit draw-function name to its op list."""
    draws = {}
    for sid, ops in CIRCUITS.items():
        draws["draw_%s_circuit" % sid] = ops
    for sid, variants in MULTI_CIRCUITS.items():
        for i, (_label, ops) in enumerate(variants):
            draws["draw_%s_v%d_circuit" % (sid, i)] = ops
    return draws


# ----------------------------------------------------------------------------
# Exercise data
# ----------------------------------------------------------------------------

EXERCISES = [
    {
        "id": "p1_q1", "title": "Prova01 Q1", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "PROVAS Prova_01 p1",
        "statement": [
            "Fonte de 20 A alimenta a rede de",
            "resistores da figura. Ache a",
            "resistencia equivalente vista pela",
            "fonte e a tensao Vx.",
        ],
        "solution": [
            "# Reducao serie/paralelo:",
            "8||12 = 4.8; +1.2 -> 6 ohm",
            "3||6 = 2; +4 -> 6 ohm",
            "6||6 = 3 ohm; resta 2||4",
            "= Req = 1.33 ohm",
            "# Divisor de corrente:",
            "Ix = 2/(2+1+3) * 20 = 6.66 A",
            "= Vx = 6.66 V",
        ],
        "answer": ["Req = 1.33 ohm", "Vx = 6.66 V"], "final": "Req=1.33 ohm; Vx=6.66 V",
    },
    {
        "id": "p1_q2", "title": "Prova01 Q2", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "PROVAS Prova_01 p2",
        "statement": [
            "Na rede da figura sao dados 8 A e",
            "2 A nos ramos e tensoes 9 V e 3 V.",
            "Determine a corrente I e os",
            "resistores R1 e R2.",
        ],
        "solution": [
            "# KCL no no de cima:",
            "I = 8 - 2 = 6 A",
            "# Lei de Ohm em cada ramo:",
            "R1 = 9 V / 2 A = 4.5 ohm",
            "R2 = 3 V / 6 A = 0.5 ohm",
            "= R2 = 500 mohm",
        ],
        "answer": ["I = 6 A", "R1 = 4.5 ohm", "R2 = 500 mohm"], "final": "I=6 A; R1=4.5; R2=0.5",
    },
    {
        "id": "p1_q3", "title": "Prova01 Q3", "subject": "Analise Nodal",
        "kind": "Nodal", "source": "PROVAS Prova_01 p2",
        "statement": [
            "Use analise nodal para achar a",
            "tensao V1 no no central da figura",
            "(fontes de 12 V e 20 V).",
        ],
        "solution": [
            "# KCL no no V1 (soma=0):",
            "(V1-12)/5 + V1/10 +",
            "(V1-20)/4 = 0",
            "# Multiplicar por 20:",
            "4(V1-12)+2V1+5(V1-20)=0",
            "11 V1 = 148",
            "= V1 = 13.45 V",
        ],
        "answer": ["V1 = 13.45 V"], "final": "V1 = 13.45 V",
    },
    {
        "id": "p1_q4", "title": "Prova01 Q4", "subject": "Analise Malhas",
        "kind": "Malhas", "source": "PROVAS Prova_01 p3",
        "statement": [
            "Use analise de malhas (i1,i2,i3)",
            "para achar a corrente i pedida na",
            "rede com fontes 8 V, 6 V e 2 V.",
        ],
        "solution": [
            "# KVL nas 3 malhas:",
            "6 i1 - i2 = 4",
            "2 i1 - 7 i2 + i3 = 6",
            "i2 - 6 i3 = 2",
            "# Resolver o sistema:",
            "i = i3 - i2",
            "= i = 0.309 A = 309 mA",
        ],
        "answer": ["i = 309 mA"], "final": "i = 309 mA",
    },
    {
        "id": "p1_q5", "title": "Prova01 Q5", "subject": "Superposicao",
        "kind": "Superposicao", "source": "PROVAS Prova_01 p4",
        "statement": [
            "Use superposicao para achar i e a",
            "potencia no resistor de 3 ohm.",
            "Fontes: 20 V, 2 A e 16 V.",
        ],
        "solution": [
            "# Uma fonte de cada vez:",
            "So 20 V (2A aberto,16V curto):",
            "i1 = 2.5 A",
            "So 16 V: i3 = -1 A",
            "So 2 A: i2 = 0.375 A",
            "# Somar contribuicoes:",
            "= i = 2.5+0.375-1 = 1.875 A",
            "P3 = i^2*3 = 10.55 W",
        ],
        "answer": ["i = 1.875 A", "P(3 ohm) = 10.55 W"], "final": "i=1.875 A; P=10.55 W",
    },
    {
        "id": "rec_q1", "title": "Rec01 Q1", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "PROVAS Rec p1",
        "statement": [
            "Determine a resistencia Rab entre",
            "os terminais a e b da rede em",
            "escada da figura.",
        ],
        "solution": [
            "# Reduzir da direita p/ esquerda:",
            "4 + 5 = 9; 9||4 = 2.4 ohm",
            "2.4||12 -> ... ; 3||6 = 2 ohm",
            "ramo 1.2 em serie",
            "# Somar serie final:",
            "= Rab = 10 + 1.2 = 11.2 ohm",
        ],
        "answer": ["Rab = 11.2 ohm"], "final": "Rab = 11.2 ohm",
    },
    {
        "id": "rec_q2", "title": "Rec01 Q2", "subject": "Superposicao",
        "kind": "Superposicao", "source": "PROVAS Rec p2",
        "statement": [
            "Use superposicao para achar a",
            "tensao vo. Fontes: 2 A, 12 V e",
            "19 V.",
        ],
        "solution": [
            "# Uma fonte de cada vez:",
            "So 2 A: vo1 = 5 V",
            "So 12 V: vo2 = 2 V",
            "So 19 V: vo3 = -7.12 V",
            "# Somar contribuicoes:",
            "= vo = 5+2-7.12 = -0.12 V",
        ],
        "answer": ["vo = -120 mV"], "final": "vo = -120 mV",
    },
    {
        "id": "rec_q3", "title": "Rec01 Q3", "subject": "Analise Malhas",
        "kind": "Malhas", "source": "PROVAS Rec p3",
        "statement": [
            "Use analise de malhas para achar",
            "a corrente I. Fontes 12 V e 10 V.",
        ],
        "solution": [
            "# KVL nas 2 malhas:",
            "5 I1 - 3 I2 = 6",
            "-3 I1 + 4 I2 = -5",
            "# Resolver:",
            "I1 = 9/11; I2 = -7/11",
            "= I = I1 - I2 = 1.45 A",
        ],
        "answer": ["I = 1.45 A"], "final": "I = 1.45 A",
    },
    {
        "id": "rec_q4", "title": "Rec01 Q4", "subject": "Analise Nodal",
        "kind": "Nodal", "source": "PROVAS Rec p4",
        "statement": [
            "Use analise nodal para achar a",
            "tensao V0. Fontes 60 V e 24 V,",
            "resistores 12, 12 e 6 ohm.",
        ],
        "solution": [
            "# KCL no no V0:",
            "(V0-60)/12 + V0/12 +",
            "(V0+24)/6 = 0",
            "# Multiplicar por 12:",
            "(V0-60)+V0+2(V0+24)=0",
            "4 V0 - 12 = 0",
            "= V0 = 3 V",
        ],
        "answer": ["V0 = 3 V"], "final": "V0 = 3 V",
    },
    {
        "id": "rec_q5", "title": "Rec01 Q5", "subject": "Transf Fontes",
        "kind": "Transf Fontes", "source": "PROVAS Rec p4",
        "statement": [
            "Use transformacao de fontes para",
            "achar a corrente i. Fontes 2 A e",
            "20 V; resistores 5, 5, 4, 10 ohm.",
        ],
        "solution": [
            "# Transformar fontes:",
            "2 A || 5 ohm -> 10 V serie 5",
            "20 V serie 10 -> 2 A || 10",
            "# Combinar:",
            "10||10 = 5 ohm; fontes 2-1=1 A",
            "= i = 5/(5+4)*1 = 0.555 A",
        ],
        "answer": ["i = 555 mA"], "final": "i = 555 mA",
    },

    # --- Chapter 1: Tensao e Potencia ---
    {
        "id": "e_1_1", "title": "Ex 1.1", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.1",
        "circuit": None,
        "statement": [
            "Quantos coulombs sao representados",
            "pelas quantidades de eletrons:",
            "a) 6.482e17    b) 1.24e18",
            "c) 2.46e19     d) 1.628e20",
        ],
        "solution": [
            "# Carga de n eletrons:",
            "q = n * (-e),  e = 1.602e-19 C",
            "a) 6.482e17*(-1.602e-19)",
            "= -103.84 mC",
            "b) 1.24e18*(-1.602e-19)",
            "= -198.65 mC",
            "c) 2.46e19*(-1.602e-19)",
            "= -3.941 C",
            "d) 1.628e20*(-1.602e-19)",
            "= -26.08 C",
        ],
        "answer": ["a=-103.84 mC  b=-198.65 mC", "c=-3.941 C    d=-26.08 C"],
        "final": "q = n * 1.602e-19 C",
    },
    {
        "id": "e_1_7", "title": "Ex 1.7", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.7",
        "statement": [
            "A carga q(t) num fio segue o",
            "grafico: triangulo de +50 C em",
            "t=2 s a -50 C em t=6 s.",
            "Determine a corrente i(t).",
        ],
        "solution": [
            "# Corrente = derivada da carga:",
            "i = dq/dt (inclinacao)",
            "0<t<2: i=(50-0)/(2-0)",
            "= 25 A",
            "2<t<6: i=(-50-50)/(6-2)",
            "= -25 A",
            "6<t<8: i=(0-(-50))/(8-6)",
            "= 25 A",
        ],
        "answer": ["i=25 A (0<t<2)", "i=-25 A (2<t<6); i=25 A (6<t<8)"],
        "final": "i = dq/dt",
    },
    {
        "id": "e_1_11", "title": "Ex 1.11", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.11",
        "circuit": None,
        "statement": [
            "Bateria de lanterna fornece 90 mA",
            "por 12 h, sob tensao de 1.5 V.",
            "a) Quanta carga ela libera?",
            "b) Quanta energia ela libera?",
        ],
        "solution": [
            "# a) Carga: q = i * t",
            "t = 12 h = 12*3600 = 43200 s",
            "q = 0.090 * 43200",
            "= 3888 C = 3.888 kC",
            "# b) Energia: w = q * V",
            "w = 3888 * 1.5",
            "= 5832 J = 5.832 kJ",
        ],
        "answer": ["q = 3.888 kC", "w = 5.832 kJ"], "final": "q=i*t; w=q*V",
    },
    {
        "id": "e_1_17", "title": "Ex 1.17", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.17",
        "statement": [
            "Circuito com 5 elementos (figura).",
            "p1=-205 W, p2=60 W, p4=45 W,",
            "p5=30 W. Calcule a potencia p3",
            "do elemento 3.",
        ],
        "solution": [
            "# Conservacao de energia:",
            "soma das potencias = 0",
            "p1+p2+p3+p4+p5 = 0",
            "-205+60+p3+45+30 = 0",
            "p3 = 205-60-45-30",
            "= p3 = 70 W (absorvida)",
        ],
        "answer": ["p3 = 70 W"], "final": "Soma das potencias = 0",
    },
    {
        "id": "e_1_21", "title": "Ex 1.21", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.21",
        "circuit": None,
        "statement": [
            "Uma lampada de 60 W opera em",
            "120 V. Quantos coulombs e quantos",
            "eletrons passam por ela em um dia?",
        ],
        "solution": [
            "# Corrente: I = P / V",
            "I = 60 / 120 = 0.5 A",
            "# Carga em 1 dia (86400 s):",
            "q = I*t = 0.5*86400",
            "= 43200 C",
            "# Eletrons: n = q / e",
            "n = 43200 / 1.602e-19",
            "= 2.697e23 eletrons",
        ],
        "answer": ["q = 43200 C", "n = 2.697e23 eletrons"], "final": "I=P/V; q=I*t; n=q/e",
    },
    {
        "id": "e_1_23", "title": "Ex 1.23", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.23",
        "circuit": None,
        "statement": [
            "Aquecedor de 1.8 kW leva 15 min",
            "para ferver agua, 1 vez por dia.",
            "Tarifa 10 centavos/kWh.",
            "Custo de operacao em 30 dias?",
        ],
        "solution": [
            "# Energia por dia: w = P*t",
            "t = 15 min = 0.25 h",
            "w = 1.8 * 0.25 = 0.45 kWh",
            "# Em 30 dias:",
            "0.45 * 30 = 13.5 kWh",
            "# Custo = energia * tarifa:",
            "= 13.5 * 0.10 = US$ 1.35",
        ],
        "answer": ["Custo = US$ 1.35"], "final": "custo = energia * tarifa",
    },
    {
        "id": "e_1_25", "title": "Ex 1.25", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.25",
        "circuit": None,
        "statement": [
            "Torradeira de 1.5 kW leva 3.5 min",
            "por uso, 1 vez por dia, 30 dias.",
            "Tarifa 8.2 centavos/kWh.",
            "Determine o custo.",
        ],
        "solution": [
            "# Energia por uso: w = P*t",
            "t = 3.5 min = 3.5/60 h",
            "w = 1.5 * (3.5/60)",
            "= 0.0875 kWh",
            "# Em 30 usos:",
            "0.0875 * 30 = 2.625 kWh",
            "# Custo = 2.625 * 8.2 cent",
            "= 21.52 centavos",
        ],
        "answer": ["Custo = 21.52 centavos"], "final": "custo = energia * tarifa",
    },
    {
        "id": "e_1_31", "title": "Ex 1.31", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.31",
        "circuit": None,
        "statement": [
            "PC de 120 W usado 4 h/dia e",
            "lampada de 60 W usada 8 h/dia.",
            "Tarifa US$ 0.12/kWh.",
            "Custo por ano (PC + lampada)?",
        ],
        "solution": [
            "# Energia por dia: w = P*t",
            "PC: 120 W * 4 h = 0.48 kWh",
            "Lamp: 60 W * 8 h = 0.48 kWh",
            "Total = 0.96 kWh/dia",
            "# Por ano: 0.96 * 365",
            "= 350.4 kWh",
            "# Custo = 350.4 * 0.12",
            "= US$ 42.05",
        ],
        "answer": ["Custo anual = US$ 42.05"], "final": "custo = energia * tarifa",
    },
    {
        "id": "e_1_37", "title": "Ex 1.37", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.37",
        "circuit": None,
        "statement": [
            "Bateria de 12 V precisa de carga",
            "total de 40 Ah na recarga.",
            "Quantos joules sao fornecidos",
            "para a bateria?",
        ],
        "solution": [
            "# Energia: w = V * q",
            "q = 40 Ah = 40*3600",
            "= 144000 C",
            "w = 12 * 144000",
            "= 1728000 J",
            "= 1.728 MJ",
        ],
        "answer": ["w = 1.728 MJ"], "final": "w = V * q",
    },
    {
        "id": "e_1_39", "title": "Ex 1.39", "subject": "Tensao Pot",
        "kind": "Tensao Pot", "source": "Livro Cap.1 Problema 1.39",
        "circuit": None,
        "statement": [
            "TV de 600 W fica ligada 4 h sem",
            "ninguem assistir. Tarifa 10",
            "centavos/kWh. Qual o valor",
            "desperdicado?",
        ],
        "solution": [
            "# Energia: w = P * t",
            "w = 600 * 4 = 2400 Wh",
            "= 2.4 kWh",
            "# Custo = 2.4 * 10 cent",
            "= 24 centavos",
        ],
        "answer": ["Desperdicio = 24 centavos"], "final": "w=P*t; custo=w*tarifa",
    },

    # --- Chapter 2: Kirchhoff ---
    {
        "id": "e_2_5", "title": "Ex 2.5", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.5", "circuit": None,
        "statement": [
            "No grafo da rede da Fig. 2.69,",
            "determine o numero de nos (n),",
            "de ramos (b) e de lacos",
            "independentes (l).",
        ],
        "solution": [
            "# Contagem direta no grafo:",
            "nos:   n = 9",
            "ramos: b = 15",
            "# Lacos independentes:",
            "l = b - n + 1",
            "l = 15 - 9 + 1",
            "= l = 7",
        ],
        "answer": ["n = 9; b = 15; l = 7"], "final": "l = b - n + 1",
    },
    {
        "id": "e_2_7", "title": "Ex 2.7", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.7",
        "statement": [
            "Conte o numero de ramos e de nos",
            "no circuito da Fig. 2.71 (12 V;",
            "1, 4, 8, 5 ohm; fonte de 2 A).",
        ],
        "solution": [
            "# Cada elemento e um ramo:",
            "12V, 1, 8, 4, 5 ohm e 2A",
            "= 6 ramos",
            "# Nos = juncoes distintas:",
            "esquerdo, 2 centrais e a base",
            "= 4 nos",
        ],
        "answer": ["6 ramos e 4 nos"], "final": "6 ramos, 4 nos",
    },
    {
        "id": "e_2_9", "title": "Ex 2.9", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.9",
        "statement": [
            "Use a LKC para achar i1, i2 e i3",
            "no circuito da Fig. 2.73 (dados",
            "4 A, 5 A, 6 A, 1 A e 7 A).",
        ],
        "solution": [
            "# LKC no no A:",
            "entra i1; saem 1 A e 6 A",
            "= i1 = 1 + 6 = 7 A",
            "# LKC no no B:",
            "entra 6 A; saem i2 e 7 A",
            "= 6 = i2 + 7 -> i2 = -1 A",
            "# LKC no no superior:",
            "i2 + i3 = 4 -> i3 = 5 A",
        ],
        "answer": ["i1 = 7 A; i2 = -1 A; i3 = 5 A"], "final": "i1=7; i2=-1; i3=5 A",
    },
    {
        "id": "e_2_11", "title": "Ex 2.11", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.11",
        "statement": [
            "No circuito da Fig. 2.75 ache V1",
            "e V2. Quedas no topo: 1 V e 2 V;",
            "fonte central de 5 V.",
        ],
        "solution": [
            "# LKT na malha da esquerda:",
            "V1 = 1 V + 5 V",
            "= V1 = 6 V",
            "# LKT na malha da direita:",
            "V2 = 5 V - 2 V",
            "= V2 = 3 V",
        ],
        "answer": ["V1 = 6 V; V2 = 3 V"], "final": "V1 = 6 V; V2 = 3 V",
    },
    {
        "id": "e_2_13", "title": "Ex 2.13", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.13",
        "statement": [
            "Use a LKC para achar I1 a I4 no",
            "circuito da Fig. 2.77 (dados 2 A,",
            "7 A, 3 A e 4 A).",
        ],
        "solution": [
            "# LKC no no 2:",
            "I2 + 7 + 3 = 0",
            "= I2 = -10 A",
            "# LKC no no 1:",
            "I1 + I2 = 2 -> I1 = 12 A",
            "# LKC no no 4:",
            "2 = I4 + 4 -> I4 = -2 A",
            "# LKC no no 3:",
            "I3 = 7 + I4 = 5 A",
        ],
        "answer": ["I1=12 A; I2=-10 A", "I3=5 A; I4=-2 A"], "final": "I1=12;I2=-10;I3=5;I4=-2",
    },
    {
        "id": "e_2_15", "title": "Ex 2.15", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.15",
        "statement": [
            "Determine v (no resistor de 12",
            "ohm) e ix no circuito da Fig.",
            "2.79. Fontes 10 V, 4 V, 16 V e a",
            "fonte controlada 3ix.",
        ],
        "solution": [
            "# Tensoes de no pelas fontes:",
            "Va (sup. esq.) = 10 V",
            "Vb (no central) = 4 V",
            "# v no resistor de 12 ohm:",
            "v = Va - Vb = 10 - 4",
            "= v = 6 V",
            "# No superior direito Vc:",
            "Vc = Vb - 16 = -12 V",
            "fonte: Vc = 3 ix",
            "= ix = -12/3 = -4 A",
        ],
        "answer": ["v = 6 V; ix = -4 A"], "final": "v = 6 V; ix = -4 A",
    },
    {
        "id": "e_2_17", "title": "Ex 2.17", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.17",
        "statement": [
            "Obtenha v1, v2 e v3 no circuito",
            "da Fig. 2.81. Fontes 24 V, 12 V",
            "e 10 V; v2 e o ramo diagonal.",
        ],
        "solution": [
            "# Tensoes de no (base = 0 V):",
            "Va (sup. esq.) = 24 V",
            "Vd (inf. dir.) = 12 V",
            "Vb (sup. dir.) = 12 + 10 = 22 V",
            "# v1 no topo: v1 = Va - Vb",
            "= v1 = 24 - 22 = 2 V",
            "# v3 (// fonte de 10 V):",
            "= v3 = 10 V",
            "# v2 diagonal = 0 - Vb:",
            "= v2 = -22 V",
        ],
        "answer": ["v1=2 V; v2=-22 V; v3=10 V"], "final": "v1=2; v2=-22; v3=10 V",
    },
    {
        "id": "e_2_19", "title": "Ex 2.19", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.19",
        "statement": [
            "No circuito da Fig. 2.83 ache I,",
            "a potencia no resistor de 3 ohm e",
            "a potencia de cada fonte.",
            "Fontes 12 V, 10 V e -8 V.",
        ],
        "solution": [
            "# LKT (malha unica, I horario):",
            "12 - 10 - 8 = 3 I",
            "-6 = 3 I",
            "= I = -2 A",
            "# Resistor de 3 ohm:",
            "P = I^2 * R = (-2)^2 * 3",
            "= 12 W (dissipados)",
            "# Potencia fornecida (P=V*I):",
            "12V:-24 W; 10V:20 W; -8V:16 W",
        ],
        "answer": ["I = -2 A; P(3 ohm) = 12 W", "Fontes: -24 W, 20 W, 16 W"],
        "final": "I = -2 A; P(3) = 12 W",
    },
    {
        "id": "e_2_21", "title": "Ex 2.21", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.21",
        "statement": [
            "Determine Vx no circuito da Fig.",
            "2.85. Malha unica: 15 V, 1 ohm,",
            "5 ohm e a fonte controlada 2Vx.",
            "Vx e a tensao no resistor de 5.",
        ],
        "solution": [
            "# Vx no resistor de 5 ohm:",
            "Vx = 5 i (i da malha)",
            "# LKT na malha:",
            "15 = 1 i + 2 Vx + 5 i + 2 i",
            "15 = 8 i + 2(5 i) = 18 i",
            "i = 15/18 = 0.833 A",
            "= Vx = 5 * 0.833 = 4.167 V",
        ],
        "answer": ["Vx = 4.167 V"], "final": "Vx = 4.167 V",
    },
    {
        "id": "e_2_23", "title": "Ex 2.23", "subject": "Leis Kirchhoff", "kind": "Kirchhoff",
        "source": "Livro Cap.2 Problema 2.23",
        "statement": [
            "No circuito da Fig. 2.87 ache vx",
            "(no resistor de 1 ohm) e a",
            "potencia no resistor de 12 ohm.",
            "Fonte de 20 A.",
        ],
        "solution": [
            "# Reduzir ramos ao no central:",
            "3//6 = 2; 4 + 2 = 6 ohm",
            "8//12 = 4.8; 1.2 + 4.8 = 6 ohm",
            "no central: 6//6 = 3 ohm",
            "# No de entrada:",
            "Rin = 2 // (1+3) = 1.333 ohm",
            "V = 20 * 1.333 = 26.67 V",
            "i(1ohm) = 26.67/4 = 6.667 A",
            "= vx = 1 * 6.667 = 6.667 V",
            "# Resistor de 12 ohm:",
            "V12 = 16 V; P = 16^2/12",
            "= 21.33 W",
        ],
        "answer": ["vx = 6.667 V", "P(12 ohm) = 21.33 W"], "final": "vx=6.667 V; P12=21.33 W",
    },

    # --- Chapter 2: Serie/Paralelo ---
    {
        "id": "e_2_27", "title": "Ex 2.27", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.27",
        "statement": [
            "Calcule Io no circuito da Fig.",
            "2.91. Fonte 10 V; 8 ohm em serie;",
            "3 ohm // 6 ohm.",
        ],
        "solution": [
            "# Paralelo na saida:",
            "3 // 6 = (3*6)/(3+6) = 2 ohm",
            "# Resistencia total:",
            "Rt = 8 + 2 = 10 ohm",
            "# Lei de Ohm:",
            "Io = 10 V / 10 ohm",
            "= Io = 1 A",
        ],
        "answer": ["Io = 1 A"], "final": "Io = 1 A",
    },
    {
        "id": "e_2_29", "title": "Ex 2.29", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.29",
        "statement": [
            "Todos os resistores da Fig. 2.93",
            "valem 5 ohm. Determine a",
            "resistencia equivalente Req.",
        ],
        "solution": [
            "# Reduzir da direita p/ esquerda:",
            "ramo final = 5 ohm",
            "5 + 5 = 10; 10 // 5 = 3.333",
            "5 + 3.333 = 8.333",
            "8.333 // 5 = 3.125",
            "# Somar o ultimo serie:",
            "= Req = 5 + 3.125 = 8.125 ohm",
        ],
        "answer": ["Req = 8.125 ohm"], "final": "Req = 8.125 ohm",
    },
    {
        "id": "e_2_31", "title": "Ex 2.31", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.31",
        "statement": [
            "Determine i1 a i5 no circuito da",
            "Fig. 2.95. Fonte 200 V, 3 ohm em",
            "serie e 4 // 1 // 2 ohm.",
        ],
        "solution": [
            "# Paralelo 4 // 1 // 2:",
            "G = 1/4 + 1 + 1/2 = 1.75 S",
            "Rp = 1/1.75 = 0.571 ohm",
            "# Corrente total:",
            "i1 = 200/(3+0.571) = 56 A",
            "V no no = 56*0.571 = 32 V",
            "# Correntes dos ramos:",
            "i2 = 32/4 = 8; i4 = 32/1 = 32 A",
            "i5 = 32/2 = 16; i3 = i4+i5 = 48 A",
        ],
        "answer": ["i1=56; i2=8; i3=48 A", "i4=32 A; i5=16 A"],
        "final": "i1=56;i2=8;i3=48;i4=32;i5=16",
    },
    {
        "id": "e_2_33", "title": "Ex 2.33", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.33",
        "statement": [
            "Obtenha v e i no circuito da Fig.",
            "2.97. Fonte 9 A; condutancias",
            "1S, 4S, 2S, 6S, 3S (em siemens).",
        ],
        "solution": [
            "# Condutancia equivalente:",
            "dir: 6S serie 3S = 2S",
            "no central: 2S + 2S = 4S",
            "4S serie 4S = 2S",
            "entrada: 1S + 2S = 3S",
            "# Tensao da fonte:",
            "v = i/G = 9/3 = 3 V",
            "# Corrente no ramo de 4S:",
            "i = 9 - v*1S = 9 - 3 = 6 A",
        ],
        "answer": ["v = 3 V; i = 6 A"], "final": "v = 3 V; i = 6 A",
    },
    {
        "id": "e_2_35", "title": "Ex 2.35", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.35",
        "statement": [
            "Calcule Vo e Io no circuito da",
            "Fig. 2.99. Fonte 200 V; ramos",
            "70+20 ohm e 30+5 ohm (ponte).",
        ],
        "solution": [
            "# Os dois meios ligam no mesmo no:",
            "topo: 70 // 30 = 21 ohm",
            "base: 20 // 5 = 4 ohm",
            "# Divisor de tensao:",
            "Vo = 200 * 4/(21+4)",
            "= Vo = 32 V",
            "# Correntes dos ramos:",
            "i(70) = (200-32)/70 = 2.4 A",
            "i(20) = 32/20 = 1.6 A",
            "= Io = 2.4 - 1.6 = 0.8 A",
        ],
        "answer": ["Vo = 32 V; Io = 800 mA"], "final": "Vo = 32 V; Io = 0.8 A",
    },
    {
        "id": "e_2_37", "title": "Ex 2.37", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.37",
        "statement": [
            "Determine R no circuito da Fig.",
            "2.101. Malha com 20 V e 30 V (que",
            "se somam), R e 10 ohm; 10 V em R.",
        ],
        "solution": [
            "# As duas fontes se somam:",
            "V total = 20 + 30 = 50 V",
            "# Queda em R + 10 ohm = 50 V:",
            "V(R) = 10 V (dado)",
            "V(10) = 50 - 10 = 40 V",
            "# Corrente da malha:",
            "I = 40/10 = 4 A",
            "# Resistencia:",
            "= R = V(R)/I = 10/4 = 2.5 ohm",
        ],
        "answer": ["R = 2.5 ohm"], "final": "R = 2.5 ohm",
    },
    {
        "id": "e_2_41", "title": "Ex 2.41", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.41",
        "statement": [
            "Se Req = 50 ohm no circuito da",
            "Fig. 2.105, determine R. Rede com",
            "30, 60, 10, R e tres de 12 ohm.",
        ],
        "solution": [
            "# Tres de 12 em paralelo:",
            "12//12//12 = 4 ohm",
            "ramo de cima: 10 + R + 4",
            "# 60 // (14+R), em serie com 30:",
            "30 + 60//(14+R) = 50",
            "60//(14+R) = 20",
            "60(14+R) = 20(74+R)",
            "40 R = 640",
            "= R = 16 ohm",
        ],
        "answer": ["R = 16 ohm"], "final": "R = 16 ohm",
    },
    {
        "id": "e_2_43", "title": "Ex 2.43", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.43",
        "statement": [
            "Calcule a resistencia equivalente",
            "Rab para cada circuito da Fig.",
            "2.107, (a) e (b).",
        ],
        "solution": [
            "# Circuito (a):",
            "5 // 20 = 4 ohm",
            "10 // 40 = 8 ohm",
            "Rab(a) = 4 + 8 = 12 ohm",
            "# Circuito (b):",
            "60 // 20 // 30 = 10 ohm",
            "10 + 10 = 20 ohm",
            "= Rab(b) = 80 // 20 = 16 ohm",
        ],
        "answer": ["Rab(a) = 12 ohm", "Rab(b) = 16 ohm"], "final": "Rab: a=12; b=16 ohm",
    },
    {
        "id": "e_2_45", "title": "Ex 2.45", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.45",
        "statement": [
            "Determine a resistencia Rab de",
            "cada circuito da Fig. 2.109,",
            "(a) e (b).",
        ],
        "solution": [
            "# Circuito (a):",
            "10//40//20//30 = 4.8 ohm",
            "em serie com 5 e 50 ohm:",
            "Rab(a) = 4.8 + 5 + 50 = 59.8",
            "# Circuito (b):",
            "12//60 = 10; 20 + 10 = 30",
            "30 // 30 = 15; 15 + 10 = 25",
            "25 // 25 = 12.5",
            "Rab(b) = 5 + 12.5 + 15 = 32.5",
        ],
        "answer": ["Rab(a) = 59.8 ohm", "Rab(b) = 32.5 ohm"],
        "final": "Rab: a=59.8; b=32.5 ohm",
    },
    {
        "id": "e_2_47", "title": "Ex 2.47", "subject": "Serie/Paralelo",
        "kind": "Serie/Paralelo", "source": "Livro Cap.2 Problema 2.47",
        "statement": [
            "Determine Rab no circuito da Fig.",
            "2.111. Ponte com 5, 6, 10, 8, 20",
            "e 3 ohm; nos c e f em curto.",
        ],
        "solution": [
            "# c e f estao ligados por um fio:",
            "lado esquerdo: 5 // 20 = 4 ohm",
            "lado direito:  6 // 3 = 2 ohm",
            "# Vira uma serie de a ate b:",
            "Rab = 10 + 4 + 2 + 8",
            "= Rab = 24 ohm",
        ],
        "answer": ["Rab = 24 ohm"], "final": "Rab = 24 ohm",
    },

    # --- Chapter 2: Estrela/Triangulo ---
    {
        "id": "e_2_49", "title": "Ex 2.49", "subject": "Estrela Triang",
        "kind": "Estrela Triang", "source": "Livro Cap.2 Problema 2.49",
        "statement": [
            "Transforme cada circuito da Fig.",
            "2.113 de delta (triangulo) em Y",
            "(estrela): itens (a) e (b).",
        ],
        "solution": [
            "# Delta -> Y, resistor no no n:",
            "R(n) = (produto dos 2 lados)/soma",
            "# (a) delta 12, 12, 12:",
            "soma = 36; R = 12*12/36",
            "= R = 4 ohm (cada)",
            "# (b) delta ab=60, ac=30, bc=10:",
            "soma = 100",
            "Ra = 60*30/100 = 18 ohm",
            "Rb = 60*10/100 = 6 ohm",
            "Rc = 30*10/100 = 3 ohm",
        ],
        "answer": ["(a) Y = 4 ohm cada", "(b) Ra=18; Rb=6; Rc=3 ohm"],
        "final": "a: 4 ohm; b: 18/6/3 ohm",
    },
    {
        "id": "e_2_53", "title": "Ex 2.53", "subject": "Estrela Triang",
        "kind": "Estrela Triang", "source": "Livro Cap.2 Problema 2.53",
        "statement": [
            "Calcule Rab de cada circuito da",
            "Fig. 2.117. (a) ponte; em (b) todos",
            "os resistores valem 30 ohm.",
        ],
        "solution": [
            "# (a) ponte: usar delta -> Y",
            "delta P-Q-S (30,60,10), soma=100",
            "Rpo=18; Rqo=3; Rso=6",
            "(3+40)//(6+50) = 43//56 = 24.32",
            "R(P-R) = 18 + 24.32 = 42.32",
            "Rab(a) = 20 + 42.32 + 80 = 142.32",
            "# (b) rede simetrica de 30 ohm:",
            "delta -> Y no centro e reduz",
            "= Rab(b) = 33.33 ohm",
        ],
        "answer": ["Rab(a) = 142.32 ohm", "Rab(b) = 33.33 ohm"],
        "final": "a=142.32; b=33.33 ohm",
    },
    {
        "id": "e_2_55", "title": "Ex 2.55", "subject": "Estrela Triang",
        "kind": "Estrela Triang", "source": "Livro Cap.2 Problema 2.55",
        "statement": [
            "Calcule Io no circuito da Fig.",
            "2.119 (fonte 24 V; ponte com 20,",
            "60, 40, 10, 50 e 20 ohm).",
        ],
        "solution": [
            "# Analise nodal (T=24V, base=0):",
            "no M1: 7 V1 - V2 = 48",
            "(apos eliminar M2 e N2)",
            "220 V1 = 1851 -> V1 = 8.42 V",
            "V2 = 7*8.42 - 48 = 10.91 V",
            "# Corrente da fonte:",
            "Io = (24-8.42)/20 + (24-10.91)/60",
            "Io = 0.779 + 0.218",
            "= Io = 0.9974 A = 997.4 mA",
        ],
        "answer": ["Io = 997.4 mA"], "final": "Io = 997.4 mA",
    },

    # --- Chapter 3: Analise Nodal ---
    {
        "id": "e_3_3", "title": "Ex 3.3", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.3",
        "statement": [
            "Determine I1 a I4 e vo no circuito",
            "da Fig. 3.52. No no vo ligam-se",
            "10, 20, 30, 60 ohm e as fontes",
            "8 A e 20 A.",
        ],
        "solution": [
            "# KCL no no vo (use G = 1/R):",
            "G = 1/10+1/20+1/30+1/60 = 0.2 S",
            "fontes: 8 (entra) - 20 (sai)",
            "# Tensao do no:",
            "vo = (8-20)/0.2 = -12/0.2",
            "= vo = -60 V",
            "# Correntes (I = vo/R):",
            "I1=-6; I2=-3; I3=-2 A",
            "I4 = 1 A (60 ohm, sentido oposto)",
        ],
        "answer": ["vo = -60 V", "I1=-6; I2=-3; I3=-2; I4=1 A"],
        "final": "vo=-60 V; I=-6/-3/-2/1 A",
    },
    {
        "id": "e_3_5", "title": "Ex 3.5", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.5",
        "statement": [
            "Obtenha vo no circuito da Fig.",
            "3.54. No no vo: 30V em serie com",
            "2k, 20V em serie com 5k, e 4k",
            "(valores em kohm).",
        ],
        "solution": [
            "# KCL no no vo (mA, kohm):",
            "(vo-30)/2 + (vo-20)/5 + vo/4 = 0",
            "# Multiplicar por 20:",
            "10(vo-30) + 4(vo-20) + 5 vo = 0",
            "19 vo = 380",
            "= vo = 20 V",
        ],
        "answer": ["vo = 20 V"], "final": "vo = 20 V",
    },
    {
        "id": "e_3_7", "title": "Ex 3.7", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.7",
        "statement": [
            "Use analise nodal para achar Vx no",
            "circuito da Fig. 3.56. Fonte 2 A,",
            "10 ohm, 20 ohm e a fonte",
            "controlada 0.2Vx.",
        ],
        "solution": [
            "# KCL no no Vx:",
            "2 = Vx/10 + Vx/20 + 0.2 Vx",
            "2 = Vx(0.1 + 0.05 + 0.2)",
            "2 = 0.35 Vx",
            "= Vx = 2/0.35 = 5.714 V",
        ],
        "answer": ["Vx = 5.714 V"], "final": "Vx = 5.714 V",
    },
    {
        "id": "e_3_9", "title": "Ex 3.9", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.9",
        "statement": [
            "Determine Ib no circuito da Fig.",
            "3.58 por analise nodal. Fonte 24V,",
            "250, 50, 150 ohm e a fonte",
            "controlada 60Ib.",
        ],
        "solution": [
            "# Ib pelo resistor de 250 ohm:",
            "Ib = (24 - V1)/250",
            "# Superno (V1,V2), V2 = V1 - 60Ib:",
            "Ib = V1/50 + V2/150",
            "210 Ib = 4 V1 -> V1 = 52.5 Ib",
            "# Substituindo em Ib:",
            "250 Ib = 24 - 52.5 Ib",
            "302.5 Ib = 24",
            "= Ib = 79.34 mA",
        ],
        "answer": ["Ib = 79.34 mA"], "final": "Ib = 79.34 mA",
    },
    {
        "id": "e_3_13", "title": "Ex 3.13", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.13",
        "statement": [
            "Use analise nodal para achar v1 e",
            "v2 no circuito da Fig. 3.62.",
            "8, 2, 4 ohm, fonte 10 V e",
            "fonte 15 A.",
        ],
        "solution": [
            "# Ramo v1 -2ohm- 10V -v2:",
            "KCL v1: v1/8 + (v1-v2-10)/2 = 0",
            "KCL v2: (v1-v2-10)/2 + 15 = v2/4",
            "# Simplificando:",
            "5 v1 - 4 v2 = 40",
            "2 v1 - 3 v2 = -40",
            "= v1 = 40 V; v2 = 40 V",
        ],
        "answer": ["v1 = 40 V; v2 = 40 V"], "final": "v1 = v2 = 40 V",
    },
    {
        "id": "e_3_17", "title": "Ex 3.17", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.17",
        "statement": [
            "Use analise nodal para achar io no",
            "circuito da Fig. 3.66. Fonte 60V,",
            "4, 2, 8, 10 ohm e a fonte",
            "controlada 3io.",
        ],
        "solution": [
            "# io no resistor de 4 ohm:",
            "io = (60 - VT)/4  (VT = no de cima)",
            "# KCL no no T:",
            "(VT-60)/4 + (VT-VB)/2 + VT/8 = 0",
            "# KCL no no B (fonte 3io):",
            "(VB-VT)/2 + (VB-60)/10 = 3 io",
            "# Resolvendo: VT = 53.08 V",
            "= io = (60-53.08)/4 = 1.73 A",
        ],
        "answer": ["io = 1.73 A"], "final": "io = 1.73 A",
    },
    {
        "id": "e_3_19", "title": "Ex 3.19", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.19",
        "statement": [
            "Use analise nodal para achar v1,",
            "v2 e v3 no circuito da Fig. 3.68.",
            "Fonte 5 A, fonte 12 V e",
            "resistores 4, 8, 2, 4, 8 ohm.",
        ],
        "solution": [
            "# KCL nos tres nos:",
            "no v1: 3 v1 - v2 = 40",
            "no v2: -v1 + 7 v2 - 2 v3 = 0",
            "no v3: 3 v3 - 2 v2 = 12",
            "# Resolvendo o sistema:",
            "v2 = 4 V",
            "= v1 = 44/3 = 14.667 V",
            "= v3 = 20/3 = 6.667 V",
        ],
        "answer": ["v1=14.667 V; v2=4 V", "v3=6.667 V"],
        "final": "v1=14.67;v2=4;v3=6.67 V",
    },
    {
        "id": "e_3_21", "title": "Ex 3.21", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.21",
        "statement": [
            "Use analise nodal para achar v1 e",
            "v2 no circuito da Fig. 3.70.",
            "Fonte 3 mA, 4k, 2k, 1k ohm e a",
            "fonte controlada 3vo (vo no 1k).",
        ],
        "solution": [
            "# vo = v2 (tensao no 1k):",
            "superno M-v2, com V_M = -2 v2",
            "# KCL no v1 (mA, kohm):",
            "3 = (v1-v2)/4 + (v1+2v2)/2",
            "-> v1 + v2 = 4",
            "# Superno: v2 = 3 v1",
            "# Resolvendo:",
            "= v1 = 1 V ; v2 = 3 V",
        ],
        "answer": ["v1 = 1 V; v2 = 3 V"], "final": "v1 = 1 V; v2 = 3 V",
    },
    {
        "id": "e_3_23", "title": "Ex 3.23", "subject": "Analise Nodal", "kind": "Nodal",
        "source": "Livro Cap.3 Problema 3.23",
        "statement": [
            "Use analise nodal para achar Vo no",
            "circuito da Fig. 3.72. Fonte 30V,",
            "fonte 3A, 1, 2, 4, 16 ohm e a",
            "fonte controlada 2Vo.",
        ],
        "solution": [
            "# No Vo (A = 30 V pela fonte):",
            "(Vo-30)/1 + Vo/2 + (Vo-M)/4 = 0",
            "-> 7 Vo - M = 120",
            "# Superno M-N (N = M - 2Vo):",
            "(M-Vo)/4 + N/16 = 3",
            "-> 5 M - 6 Vo = 48",
            "# Resolvendo: 29 Vo = 648",
            "= Vo = 22.34 V",
        ],
        "answer": ["Vo = 22.34 V"], "final": "Vo = 22.34 V",
    },

    # --- Chapter 3: Analise de Malhas ---
    {
        "id": "e_3_33", "title": "Ex 3.33", "subject": "Analise Malhas", "kind": "Malhas",
        "source": "Livro Cap.3 Problema 3.33",
        "statement": [
            "Quais circuitos da Fig. 3.82 sao",
            "planares? Redesenhe o planar sem",
            "ramos se cruzando. (Mostrado: o b)",
        ],
        "solution": [
            "# Planar = pode ser desenhado sem",
            "ramos se cruzando.",
            "# (a): o ramo diagonal cruza e nao",
            "ha como evitar -> nao planar.",
            "# (b): e uma ponte de Wheatstone;",
            "o cruzamento de 4 e 5 ohm pode ser",
            "desfeito -> planar (redesenhavel).",
        ],
        "answer": ["(b) e planar; (a) nao e planar"], "final": "(b) planar; (a) nao planar",
    },
    {
        "id": "e_3_41", "title": "Ex 3.41", "subject": "Analise Malhas", "kind": "Malhas",
        "source": "Livro Cap.3 Problema 3.41",
        "statement": [
            "Use analise de malhas para achar i",
            "no circuito da Fig. 3.87. Tres",
            "malhas; fontes de 6 V e 8 V.",
        ],
        "solution": [
            "# Tres malhas (horario) i1, i2, i3:",
            "i1: 12 i1 - 2 i2 = 6",
            "i2: -2 i1 + 7 i2 - i3 = -8",
            "i3: -i2 + 6 i3 = 2",
            "# Resolvendo o sistema:",
            "i1=0.329; i2=-1.026; i3=0.162 A",
            "# i sobe pelo ramo central:",
            "= i = i3 - i2 = 1.188 A",
        ],
        "answer": ["i = 1.188 A"], "final": "i = 1.188 A",
    },
    {
        "id": "e_3_45", "title": "Ex 3.45", "subject": "Analise Malhas", "kind": "Malhas",
        "source": "Livro Cap.3 Problema 3.45",
        "statement": [
            "Determine a corrente i no circuito",
            "da Fig. 3.91 (analise de malhas).",
            "Fonte 30 V, fonte 4 A (supermalha),",
            "resistores 4, 8, 2, 6, 3, 1 ohm.",
        ],
        "solution": [
            "# A fonte de 4 A cria uma supermalha.",
            "Resolvendo (no L = 30 V fixo):",
            "V(TM)=32.21 V; V(MM)=11.77 V",
            "# Corrente da fonte de 30 V:",
            "i = (30-32.21)/4 + (30-11.77)/2",
            "i = -0.55 + 9.11",
            "= i = 8.561 A",
        ],
        "answer": ["i = 8.561 A"], "final": "i = 8.561 A",
    },
    {
        "id": "e_3_57", "title": "Ex 3.57", "subject": "Analise Malhas", "kind": "Malhas",
        "source": "Livro Cap.3 Problema 3.57",
        "statement": [
            "No circuito da Fig. 3.102 ache R,",
            "V1 e V2, sabendo que io = 15 mA.",
            "Fonte 90 V; R // 3k em serie com 4k.",
        ],
        "solution": [
            "# io passa pelo resistor de 4k:",
            "V2 = io * 4k = 15m * 4k = 60 V",
            "# LKT: 90 = V1 + V2",
            "= V1 = 90 - 60 = 30 V",
            "# No bloco R // 3k (V1 = 30 V):",
            "I(3k) = 30/3k = 10 mA",
            "I(R) = io - 10m = 5 mA",
            "= R = 30/5m = 6 kohm",
        ],
        "answer": ["R = 6 kohm", "V1 = 30 V; V2 = 60 V"], "final": "R=6k; V1=30; V2=60 V",
    },

    # --- Chapter 4: linearidade (grupo "Superposicao") ---
    {
        "id": "e_4_1", "title": "Ex 4.1", "subject": "Superposicao",
        "kind": "Superposicao", "source": "Livro Cap.4 Problema 4.1",
        "statement": [
            "Calcule io no circuito da Fig.",
            "4.69 (fonte 30 V). Que tensao de",
            "entrada faz io = 5 A? Use a",
            "propriedade da linearidade.",
        ],
        "solution": [
            "# Reduzir a rede (saida -> fonte):",
            "ramo de saida: 25 + 15 = 40 ohm",
            "no A: 40 // 40 = 20 ohm",
            "total: 5 + 20 = 25 ohm",
            "# Corrente e tensao no no A:",
            "Is = 30/25 = 1.2 A",
            "V(A) = 1.2*20 = 24 V",
            "io = 24/40 = 0.6 A",
            "# Linearidade (io ~ Vin):",
            "para io=5 A: V = 30*(5/0.6)",
            "= V = 250 V",
        ],
        "answer": ["io = 600 mA", "Vin = 250 V para io = 5 A"],
        "final": "io=600 mA; 250 V p/ 5 A",
    },
    {
        "id": "e_4_4", "title": "Ex 4.4", "subject": "Superposicao",
        "kind": "Superposicao", "source": "Livro Cap.4 Problema 4.4",
        "statement": [
            "Use a linearidade para determinar",
            "io no circuito da Fig. 4.72",
            "(fonte de 9 A).",
        ],
        "solution": [
            "# Suponha io = 1 A (no 6 ohm):",
            "V(M) = 6*1 = 6 V",
            "I(3 ohm) = 6/3 = 2 A",
            "no 2 ohm: 1 + 2 = 3 A",
            "V(N) = 6 + 2*3 = 12 V",
            "I(4 ohm) = 12/4 = 3 A",
            "fonte = 3 + 3 = 6 A",
            "# Linearidade (io ~ fonte):",
            "io = 1 * (9/6)",
            "= io = 1.5 A",
        ],
        "answer": ["io = 1.5 A"], "final": "io = 1.5 A",
    },
    {
        "id": "e_4_5", "title": "Ex 4.5", "subject": "Superposicao",
        "kind": "Superposicao", "source": "Livro Cap.4 Problema 4.5",
        "statement": [
            "No circuito da Fig. 4.73, suponha",
            "vo = 1 V e use a linearidade para",
            "achar o valor real de vo",
            "(fonte de 15 V).",
        ],
        "solution": [
            "# Suponha vo = 1 V (6 ohm central):",
            "no C: (1-Vc)/2 = Vc/4 -> Vc=0.667",
            "I(2 dir) = 0.667/4 = 0.167 A",
            "no B: 1/6 + 0.167 = 0.333 A",
            "V(A) = 1 + 3*0.333 = 2 V",
            "no A: 2/6 + 0.333 = 0.667 A",
            "fonte = 2 + 2*0.667 = 3.333 V",
            "# Linearidade (vo ~ fonte):",
            "vo = 1 * (15/3.333)",
            "= vo = 4.5 V",
        ],
        "answer": ["vo = 4.5 V"], "final": "vo = 4.5 V",
    },
    {
        "id": "e_4_7", "title": "Ex 4.7", "subject": "Superposicao",
        "kind": "Superposicao", "source": "Livro Cap.4 Problema 4.7",
        "statement": [
            "Use a linearidade e a hipotese",
            "Vo = 1 V para achar o valor real",
            "de Vo na Fig. 4.75 (fonte 4 V).",
        ],
        "solution": [
            "# Suponha Vo = 1 V (no 2 ohm):",
            "I(2) = 1/2 = 0.5 A",
            "I(4) = 0.5 A; V(A) = 1 + 4*0.5 = 3",
            "I(3) = 3/3 = 1 A",
            "I(1) = 1 + 0.5 = 1.5 A",
            "fonte = 3 + 1*1.5 = 4.5 V",
            "# Linearidade (Vo ~ fonte):",
            "Vo = 1 * (4/4.5)",
            "= Vo = 0.889 V = 888.9 mV",
        ],
        "answer": ["Vo = 888.9 mV"], "final": "Vo = 888.9 mV",
    },

    # --- Chapter 4: Transformacao de Fontes ---
    {
        "id": "e_4_21", "title": "Ex 4.21", "subject": "Transf Fontes", "kind": "Transf Fontes",
        "source": "Livro Cap.4 Problema 4.21",
        "statement": [
            "Use a Fig. 4.89 para elaborar um",
            "problema de transformacao de fontes",
            "(problema de projeto, aberto).",
        ],
        "solution": [
            "# Transformacao de fontes:",
            "V em serie com R <-> I = V/R em",
            "paralelo com o mesmo R.",
            "I em paralelo com R <-> V = I*R",
            "em serie com o mesmo R.",
            "# Aplique para reduzir a rede a uma",
            "unica fonte e achar io.",
            "# As respostas variam com os valores.",
        ],
        "answer": ["Problema de projeto", "(respostas variam)"],
        "final": "V serie R <-> I=V/R paralelo",
    },
    {
        "id": "e_4_23", "title": "Ex 4.23", "subject": "Transf Fontes", "kind": "Transf Fontes",
        "source": "Livro Cap.4 Problema 4.23",
        "statement": [
            "Use transformacao de fontes para",
            "achar a corrente e a potencia no",
            "resistor de 8 ohm (Fig. 4.91).",
            "Fontes de 3 A e 15 V.",
        ],
        "solution": [
            "# Transformar 3A // 10 ohm:",
            "-> 30 V em serie com 10 ohm",
            "# KCL no no M (entre 8 e 3 ohm):",
            "(VM-30)/18 + VM/6 + (VM-15)/3 = 0",
            "10 VM = 120 -> VM = 12 V",
            "# Corrente no 8 ohm:",
            "i = (30-12)/18 = 1 A",
            "# Potencia: P = i^2 * 8",
            "= i = 1 A ; P = 8 W",
        ],
        "answer": ["i = 1 A; P = 8 W"], "final": "i = 1 A; P = 8 W",
    },
    {
        "id": "e_4_25", "title": "Ex 4.25", "subject": "Transf Fontes", "kind": "Transf Fontes",
        "source": "Livro Cap.4 Problema 4.25",
        "statement": [
            "Determine vo no circuito da Fig.",
            "4.93 usando transformacao de",
            "fontes. Fontes 3A, 2A, 6A e 30 V.",
        ],
        "solution": [
            "# Transformar as fontes de corrente:",
            "3A//4 -> 12V; 2A//9 -> 18V;",
            "6A//5 -> 30V (cada em serie c/ R)",
            "# Vira uma malha unica:",
            "R total = 4 + 9 + 5 + 2 = 20 ohm",
            "corrente da malha I = -3.3 A",
            "# vo no resistor de 2 ohm:",
            "= vo = 2 * I = -6.6 V",
        ],
        "answer": ["vo = -6.6 V"], "final": "vo = -6.6 V",
    },
    {
        "id": "e_4_31", "title": "Ex 4.31", "subject": "Transf Fontes", "kind": "Transf Fontes",
        "source": "Livro Cap.4 Problema 4.31",
        "statement": [
            "Determine vo no circuito da Fig.",
            "4.99 usando transformacao de",
            "fontes. 12V, 3, 6, 8 ohm e a fonte",
            "controlada 2vx (vo = vx no 3 ohm).",
        ],
        "solution": [
            "# vx no resistor de 3 ohm:",
            "vx = 12 - VA (VA = no central)",
            "# KCL no no A (com 2vx = 2(12-VA)):",
            "(VA-12)/3 + VA/8 + (VA-2vx)/6 = 0",
            "23 VA = 192 -> VA = 8.348 V",
            "# Logo:",
            "= vo = vx = 12 - 8.348 = 3.652 V",
        ],
        "answer": ["vo = 3.652 V"], "final": "vo = vx = 3.652 V",
    },
]


SUBJECT_ORDER = [
    "Tensao Pot",
    "Leis Kirchhoff",
    "Serie/Paralelo",
    "Estrela Triang",
    "Analise Nodal",
    "Analise Malhas",
    "Superposicao",
    "Transf Fontes",
]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

TEXT_X = 14
TEXT_YS = [62, 82, 102, 122, 142, 162, 182]
MAX_TEXT_LINES = len(TEXT_YS)


def c_string(value):
    encoded = value.encode("ascii", "strict").decode("ascii")
    return '"' + encoded.replace("\\", "\\\\").replace('"', '\\"') + '"'


def wrap_text(line, width=37):
    if len(line) <= width:
        return [line]
    words = line.split()
    out, cur = [], ""
    for w in words:
        cand = w if not cur else cur + " " + w
        if len(cand) <= width:
            cur = cand
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out or [""]


def parse_markup(line):
    if line.startswith("# "):
        return line[2:], "COL_BLUE"
    if line.startswith("= "):
        return line[2:], "COL_RED"
    return line, "COL_BLACK"


def to_colored_lines(raw_lines):
    """Expand raw markup lines into wrapped (text, color) tuples."""
    items = []
    for raw in raw_lines:
        text, color = parse_markup(raw)
        for sub in wrap_text(text):
            items.append((sub, color))
    return items


def safe_id(text):
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


# ----------------------------------------------------------------------------
# Page model
# ----------------------------------------------------------------------------

def build_pages(ex):
    """Return a list of page dicts for one exercise."""
    pages = []

    # 1) Circuito FIRST: dedicated op list (CIRCUITS / MULTI_CIRCUITS),
    #    explicit None = skip, otherwise the subject generic fallback. The
    #    diagram is always the first page the user sees in an exercise.
    if ex["id"] in MULTI_CIRCUITS:
        for i, (label, _ops) in enumerate(MULTI_CIRCUITS[ex["id"]]):
            pages.append({"title": "Circuito", "subtitle": label, "items": [],
                          "body_name": "draw_%s_v%d_circuit" % (ex["id"], i)})
    elif ex["id"] in CIRCUITS:
        pages.append({"title": "Circuito", "subtitle": "", "items": [],
                      "body_name": "draw_%s_circuit" % ex["id"]})
    elif ex.get("circuit", "generic") is None:
        pass
    else:
        pages.append({"title": "Circuito", "subtitle": "", "items": [],
                      "body_name": GENERIC_DRAW[ex["kind"]]})

    # 2) Enunciado
    statement = ex.get("statement") or [
        "Exercicio do livro (ver figura).",
        "Resolva conforme o metodo do",
        "assunto e confira a resposta.",
    ]
    st_items = to_colored_lines(statement)
    st_chunks = [st_items[i:i + MAX_TEXT_LINES]
                 for i in range(0, len(st_items), MAX_TEXT_LINES)] or [[]]
    for idx, chunk in enumerate(st_chunks):
        sub = "" if len(st_chunks) == 1 else "parte %d/%d" % (idx + 1, len(st_chunks))
        pages.append({"title": "Enunciado", "subtitle": sub,
                      "items": chunk, "body": None})

    # 3) Resolucao
    solution = ex.get("solution") or METHODS[ex["kind"]]
    sol_items = to_colored_lines(solution)
    sol_chunks = [sol_items[i:i + MAX_TEXT_LINES]
                  for i in range(0, len(sol_items), MAX_TEXT_LINES)] or [[]]
    for idx, chunk in enumerate(sol_chunks):
        sub = "passo a passo" if len(sol_chunks) == 1 \
            else "parte %d/%d" % (idx + 1, len(sol_chunks))
        pages.append({"title": "Resolucao", "subtitle": sub,
                      "items": chunk, "body": None})

    # 4) Resultado
    res_items = [("Resposta final:", "COL_BLUE")]
    for a in ex["answer"]:
        for sub in wrap_text(a):
            res_items.append((sub, "COL_RED"))
    final = ex.get("final") or ex["answer"][0]
    if len(final) > 36:
        final = "Gabarito conferido"
    pages.append({"title": "Resultado", "subtitle": "Final",
                  "items": res_items, "result": final})

    return pages


def page_lines_xy(page):
    """Attach screen coordinates to a page's text items."""
    out = []
    for i, (text, color) in enumerate(page.get("items", [])):
        if i >= MAX_TEXT_LINES:
            break
        out.append((text, TEXT_X, TEXT_YS[i], color))
    return out


def result_y_for(n_lines):
    last_y = TEXT_YS[min(n_lines, MAX_TEXT_LINES) - 1] if n_lines else TEXT_YS[0]
    y = last_y + 22
    if y > 188:
        y = 188
    return y


# ----------------------------------------------------------------------------
# C generation
# ----------------------------------------------------------------------------

HELPERS_C = r"""static void label(const char *text, int x, int y) {
    gfx_SetTextFGColor(COL_BLACK);
    prn(text, x, y);
}

static void draw_arrow_h(int x1, int y, int x2,
                         const char *label_text, bool right) {
    int ah = right ? -1 : 1;
    int head = right ? x2 : x1;
    draw_wire(x1, y, x2, y);
    gfx_SetColor(COL_BLACK);
    gfx_Line(head, y, head + ah * 7, y - 4);
    gfx_Line(head, y, head + ah * 7, y + 4);
    label(label_text, (x1 + x2) / 2 - 8, y - 16);
}

static void draw_arrow_v(int x, int y1, int y2,
                         const char *label_text, bool up) {
    int ah = up ? 1 : -1;
    int head = up ? y1 : y2;
    draw_wire(x, y1, x, y2);
    gfx_SetColor(COL_BLACK);
    gfx_Line(x, head, x - 4, head + ah * 7);
    gfx_Line(x, head, x + 4, head + ah * 7);
    label(label_text, x + 6, (y1 + y2) / 2 - 4);
}

static void plus_minus_v(int x, int y1, int y2) {
    label("+", x, y1);
    label("-", x, y2);
}

static void draw_vo_marks(int x, int y_top, int y_bottom,
                          const char *label_text) {
    plus_minus_v(x, y_top, y_bottom);
    label(label_text, x - 8, (y_top + y_bottom) / 2 - 4);
}
"""


GENERIC_C = {
    "Tensao Pot": r"""static void draw_generic_tensao_pot(void) {
    draw_voltage_source(58, 88, 168, "V");
    draw_res_v(178, 88, 168, "R");
    draw_wire(58, 88, 178, 88);
    draw_wire(58, 168, 178, 168);
    draw_arrow_h(86, 74, 150, "i", true);
    draw_vo_marks(198, 102, 150, "v");
    label("p=v*i", 120, 186);
}
""",
    "Kirchhoff": r"""static void draw_generic_kirchhoff(void) {
    draw_voltage_source(56, 86, 168, "Vs");
    draw_res_h(56, 86, 142, "R1");
    draw_res_v(142, 86, 168, "R2");
    draw_res_h(142, 86, 226, "R3");
    draw_current_source_v_dir(226, 86, 168, "I", false);
    draw_wire(56, 168, 226, 168);
    draw_node(142, 86);
    draw_arrow_h(80, 72, 120, "i1", true);
    draw_arrow_v(158, 96, 144, "i2", false);
}
""",
    "Serie/Paralelo": r"""static void draw_generic_serie_paralelo(void) {
    draw_terminal(42, 88, "a");
    draw_terminal(42, 168, "b");
    draw_res_h(46, 88, 104, "R1");
    draw_res_h(104, 88, 166, "R2");
    draw_res_v(166, 88, 168, "R3");
    draw_res_h(166, 88, 230, "R4");
    draw_res_v(230, 88, 168, "R5");
    draw_wire(46, 168, 230, 168);
    draw_node(166, 88);
    draw_node(166, 168);
}
""",
    "Estrela Triang": r"""static void draw_generic_estrela_triang(void) {
    draw_terminal(70, 78, "a");
    draw_terminal(226, 78, "b");
    draw_terminal(148, 178, "c");
    draw_res_h(70, 78, 226, "Rab");
    draw_res_h(70, 78, 148, "Rac");
    draw_res_h(148, 178, 226, "Rbc");
    draw_wire(70, 78, 148, 178);
    draw_wire(226, 78, 148, 178);
    label("Delta / Y", 120, 194);
}
""",
    "Nodal": r"""static void draw_generic_nodal(void) {
    draw_voltage_source(50, 88, 168, "Vs");
    draw_res_h(50, 88, 120, "R1");
    draw_res_v(120, 88, 168, "R2");
    draw_res_h(120, 88, 205, "R3");
    draw_current_source_v_dir(205, 88, 168, "I", true);
    draw_wire(50, 168, 230, 168);
    draw_ground(120, 170);
    draw_node(120, 88);
    label("V1", 111, 68);
}
""",
    "Malhas": r"""static void draw_generic_malhas(void) {
    draw_voltage_source(52, 88, 168, "V1");
    draw_res_h(52, 88, 132, "R1");
    draw_res_v(132, 88, 168, "R2");
    draw_res_h(132, 88, 222, "R3");
    draw_voltage_source(222, 88, 168, "V2");
    draw_wire(52, 168, 222, 168);
    draw_arrow_h(76, 126, 106, "i1", true);
    draw_arrow_h(162, 126, 194, "i2", true);
}
""",
    "Superposicao": r"""static void draw_generic_superposicao(void) {
    draw_voltage_source(42, 98, 170, "V1");
    draw_res_h(42, 98, 108, "R1");
    draw_res_v(108, 98, 170, "R2");
    draw_res_h(108, 98, 174, "R3");
    draw_res_v(174, 98, 170, "R4");
    draw_res_h(174, 98, 240, "R5");
    draw_current_source_v_dir(240, 98, 170, "I1", true);
    draw_wire(42, 170, 240, 170);
    draw_vo_marks(188, 118, 150, "vo");
}
""",
    "Transf Fontes": r"""static void draw_generic_transf_fontes(void) {
    draw_voltage_source(46, 90, 154, "V");
    draw_res_h(46, 90, 114, "R");
    draw_terminal(124, 90, "a");
    draw_terminal(124, 154, "b");
    draw_wire(46, 154, 124, 154);
    draw_arrow_h(142, 122, 174, "", true);
    draw_current_source_v_dir(218, 90, 154, "I", true);
    draw_res_v(262, 90, 154, "R");
    draw_wire(218, 90, 262, 90);
    draw_wire(218, 154, 262, 154);
    label("I=V/R", 210, 174);
}
""",
}


def text_array_c(name, lines_xy):
    out = ["static const TextLine %s[] = {" % name]
    if not lines_xy:
        out.append('    { "", %d, %d, COL_BLACK },' % (TEXT_X, TEXT_YS[0]))
    for (text, x, y, color) in lines_xy:
        out.append("    { %s, %d, %d, %s }," % (c_string(text), x, y, color))
    out.append("};")
    return "\n".join(out)


def generate_exercise_c(ex):
    sid = ex["id"]
    pages = build_pages(ex)
    parts = []
    page_entries = []
    for pidx, page in enumerate(pages):
        lines_xy = page_lines_xy(page)
        arr = "%s_pg%d_lines" % (sid, pidx)
        parts.append(text_array_c(arr, lines_xy))
        body = page.get("body_name") or "0"
        if page.get("result"):
            result = c_string(page["result"])
            ry = result_y_for(len(lines_xy))
        else:
            result, ry = "0", 0
        title = c_string(page["title"])
        subtitle = c_string(page.get("subtitle", ""))
        page_entries.append(
            "    { %s, %s,\n      %s, COUNT_OF(%s), %s, %d, %s }"
            % (title, subtitle, arr, arr, result, ry, body)
        )
    block = "static const PageTemplate %s_pages[] = {\n%s\n};" % (
        sid, ",\n".join(page_entries))
    parts.append(block)
    return "\n\n".join(parts)


def generate_c():
    out = [
        '#include "cv3.h"',
        "",
        "/* Generated by tools/generate_exercises.py. Do not edit by hand. */",
        "",
        HELPERS_C,
        "",
    ]
    # generic fallbacks: emit only the ones actually referenced
    used_generic = {ex["kind"] for ex in EXERCISES
                    if ex["id"] not in CIRCUITS
                    and ex["id"] not in MULTI_CIRCUITS
                    and ex.get("circuit", "generic") is not None}
    for kind, src in GENERIC_C.items():
        if kind in used_generic:
            out.append(src)
            out.append("")
    # dedicated circuit draw functions (single source = CIRCUITS + MULTI)
    for name, ops in all_draws().items():
        out.append(cv_render.emit_circuit_c(name, ops))
        out.append("")

    for ex in EXERCISES:
        out.append(generate_exercise_c(ex))
        out.append("")

    for subject in SUBJECT_ORDER:
        items = [ex for ex in EXERCISES if ex["subject"] == subject]
        arr = "subject_%s" % safe_id(subject)
        out.append("static const Exercise %s[] = {" % arr)
        for ex in items:
            out.append("    { %s, %s_pages, COUNT_OF(%s_pages) },"
                       % (c_string(ex["title"]), ex["id"], ex["id"]))
        out.append("};")
        out.append("")

    out.append("const Subject subjects[] = {")
    for subject in SUBJECT_ORDER:
        arr = "subject_%s" % safe_id(subject)
        out.append("    { %s, %s, COUNT_OF(%s), 0, 0 }," % (c_string(subject), arr, arr))
    out.append("};")
    out.append("")
    out.append("const uint8_t subject_count = COUNT_OF(subjects);")
    out.append("")
    out.append("const MenuItem menu_items[] = {")
    for idx, subject in enumerate(SUBJECT_ORDER):
        out.append("    { %s, MENU_SUBJECT, %d }," % (c_string(subject), idx))
    out.append("};")
    out.append("")
    out.append("const uint8_t menu_count = COUNT_OF(menu_items);")
    out.append("")
    return "\n".join(out)


def generate_manifest():
    lines = [
        "# CIRCVIE3 Exercise Manifest",
        "",
        "Generated from tools/generate_exercises.py.",
        "",
        "| # | Subject | Exercise | Source | Result | Status |",
        "|---|---|---|---|---|---|",
    ]
    for idx, ex in enumerate(EXERCISES, 1):
        result = " / ".join(ex["answer"])
        authored = "full" if ex.get("solution") else "outline"
        lines.append("| %d | %s | %s | %s | %s | %s |"
                     % (idx, ex["subject"], ex["title"], ex["source"], result, authored))
    lines.extend([
        "",
        "Notes:",
        "- 'full' = dedicated statement, circuit and step-by-step solution.",
        "- 'outline' = still using the subject method fallback.",
        "- Circuits are redrawn with graphx primitives (tools/cv_render.py).",
    ])
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------
# Preview
# ----------------------------------------------------------------------------

def render_previews(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    draws = all_draws()
    count = 0
    for ex in EXERCISES:
        pages = build_pages(ex)
        total = len(pages)
        subj_items = [e for e in EXERCISES if e["subject"] == ex["subject"]]
        ex_no = subj_items.index(ex) + 1
        for pidx, page in enumerate(pages):
            lines_xy = page_lines_xy(page)
            view = {
                "title": page["title"],
                "subtitle": page.get("subtitle", ""),
                "lines": lines_xy,
                "body": None,
            }
            if page.get("body_name"):
                # dedicated/multi circuits render; generic fallbacks do not
                view["body"] = draws.get(page["body_name"])
            if page.get("result"):
                view["result"] = page["result"]
                view["result_y"] = result_y_for(len(lines_xy))
            meta = "Ex %02d Pg %d/%d" % (ex_no, pidx + 1, total)
            img = cv_render.render_page(view, subject=ex["subject"],
                                        ex_meta=meta, ex_title=ex["title"])
            img.save(out / ("%s_p%d.png" % (ex["id"], pidx)))
            count += 1
    print("rendered %d page previews to %s" % (count, out))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", metavar="DIR", default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    (root / "src" / "exercises.c").write_text(generate_c(), encoding="ascii")
    (root / "EXERCISE_MANIFEST.md").write_text(generate_manifest(), encoding="ascii")
    print("generated %d exercises" % len(EXERCISES))

    if args.preview:
        render_previews(args.preview)


if __name__ == "__main__":
    main()
