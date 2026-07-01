# Adicionando exercicios ao CIRCVIE3

_github.com/daniSoares08 - Open source (MIT License): free to use, copy, modify and redistribute._

`src/exercises.c` e **gerado** por `tools/generate_exercises.py`. Nunca edite
o `.c` a mao: edite o gerador e rode-o de novo.

## 1. Modelo de dados

Cada exercicio e um dict na lista `EXERCISES`:

```python
{
    "id": "e_2_27",            # id unico (vira nomes de simbolos no C)
    "title": "Ex 2.27",
    "subject": "Serie/Paralelo",  # tem que estar em SUBJECT_ORDER
    "kind": "Serie/Paralelo",
    "source": "Livro Cap.2 Problema 2.27",
    "statement": [ "...", "..." ],   # pagina Enunciado (linhas curtas)
    "solution":  [ "# ...", "..." ], # paginas Resolucao (paginadas em 7 linhas)
    "answer":    [ "Io = 1 A" ],     # pagina Resultado
    "final":     "Io = 1 A",         # texto curto da caixa de resultado
    # "circuit": None,               # opcional: None = sem pagina de circuito
}
```

Paginas geradas, nesta ordem: **Circuito -> Enunciado -> Resolucao ->
Resultado**. Marcacao nas linhas de texto: `# ` = titulo azul, `= ` =
linha de resultado em vermelho. Quebra automatica em 37 chars; literais C
ficam <= 39 chars.

## 2. Desenho do circuito (ops)

O circuito e uma lista de "ops" (tuplas) em `CIRCUITS[id]`. Cada op mapeia
1:1 para uma primitiva de `src/ui.c`. Exemplos:

```python
"e_2_27": [
    ("vsrc_v", 55, 90, 170, "10V"),   # fonte de tensao vertical
    ("res_h", 55, 90, 150, "8"),      # resistor horizontal
    ("res_v", 150, 90, 170, "3"),
    ("wire", 150, 90, 210, 90),
    ("arr_h", 80, 78, 128, "Io", True),  # seta de corrente
    ("node", 150, 90),
],
```

Ops disponiveis: `wire, node, term, res_h, res_v, cap_h, cap_v, ind_h,
ind_v, vsrc_v, vsrc_h, isrc_v, isrc_h, gnd, sw_h, opamp, dvs_v, dvs_h`
(fontes de tensao controladas, diamante), `dis_v` (fonte de corrente
controlada), `arr_h, arr_v, vo, pm, lbl`. Tela = 320x240; mantenha tudo
entre ~x[30..305] e ~y[58..205].

- Exercicio com **dois** circuitos (a) e (b): use `MULTI_CIRCUITS[id]`.
- Sem circuito (problemas so de conta): use `"circuit": None` no dict.
- Tela e geometria sao espelhadas em `tools/cv_render.py` para o preview.

## 3. Gerar, conferir e compilar

```bash
# gera src/exercises.c + EXERCISE_MANIFEST.md e renderiza previews PNG
python tools/generate_exercises.py --preview /tmp/preview
# confere ASCII e tamanho das strings
python tools/audit_strings.py
# compila (CEdev em C:\CEdev)
export PATH="/c/CEdev/bin:$PATH"
/c/CEdev/bin/make.exe clean && /c/CEdev/bin/make.exe
```

Abra os PNGs de `/tmp/preview` e confira que nada sai da tela, cobre texto
ou se sobrepoe **antes** de mandar para a calculadora.

## 4. Regras de seguranca da calculadora

- ASCII puro (sem acentos): use `ohm`, `Sum`, `xbar`, etc.
- Strings C <= 39 chars (o wrap em 37 ja cuida das linhas de texto).
- Nao alterar a logica de `src/main.c`/`src/ui.c`; so adicionar primitivas
  novas e autocontidas em `ui.c` quando necessario (e espelha-las em
  `cv_render.py` + no map de ops do gerador).
- Re-derive as respostas: o manifesto/`.md` antigos do codex tem erros.
