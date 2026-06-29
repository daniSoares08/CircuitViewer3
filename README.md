# CIRCVIE3

CIRCVIE3 e a V3 do CircuitViewer para TI-84 Plus CE. O app usa a mesma base
simples da V2: menus fixos, paginas curtas e circuitos redesenhados com
primitivas `graphx`, sem imagens do livro dentro do `.8xp`.

## Navegacao

- `UP/DOWN`: escolhe item no menu.
- `ENTER`: abre menu/assunto ou avanca pagina.
- `RIGHT`: proxima pagina.
- `LEFT`: pagina anterior.
- Dentro de um assunto, `UP/DOWN` muda o exercicio do mesmo assunto.
- `CLEAR`: volta ao menu anterior.
- `ON`: sai imediatamente.

Cada exercicio segue a ordem de paginas: **Circuito -> Enunciado ->
Resolucao (passo a passo) -> Resultado**. O circuito e sempre a primeira
pagina; exercicios sem desenho (calculos de carga/energia/custo) abrem
direto no Enunciado.

## Conteudo

64 exercicios, todos com enunciado, desenho dedicado em `graphx` e resolucao
passo a passo completa (formula -> valores -> resposta com unidade):

- 10 questoes das provas `Prova_01` e `Prova_01_Rec`.
- 54 problemas do livro (Sadiku) cobrindo: Tensao/Potencia, Leis de
  Kirchhoff, Serie/Paralelo, Estrela-Triangulo (Y-delta), Analise Nodal,
  Analise de Malhas, Superposicao/Linearidade e Transformacao de Fontes.

Todas as respostas foram re-derivadas a mao (os `.md`/manifesto do codex
tinham erros, ex.: 2.23, 3.19). Veja `EXERCISE_MANIFEST.md`.

## Estrutura do codigo

- `src/main.c`: menus e loops de navegacao (logica do app, nao alterada).
- `src/ui.c`: teclado, tela e primitivas de desenho (`draw_res_h`,
  `draw_voltage_source`, fontes controladas `draw_dep_vsource_*` e
  `draw_dep_isource_v`, etc.).
- `src/exercises.c`: **GERADO** por `tools/generate_exercises.py`. Nao editar
  a mao.
- `src/cv3.h`: tipos compartilhados.
- `tools/generate_exercises.py`: dados dos exercicios (enunciado, circuito como
  lista de "ops", resolucao) + geracao do C e do manifesto.
- `tools/cv_render.py`: espelha a geometria de `ui.c`; usado para renderizar
  cada pagina em PNG 320x240 (`--preview DIR`) e conferir layout sem a
  calculadora.
- `tools/audit_strings.py`: confere ASCII e strings <= 39 chars.
- `tools/render_pdf.py`: renderiza paginas de PDFs para PNG.
- `ADDING_EXERCISES.md`: guia para adicionar exercicios no gerador.

## Fluxo para alterar exercicios

```bash
# 1) editar tools/generate_exercises.py (dados/ops)
# 2) gerar C + manifesto + previews para conferir layout
python tools/generate_exercises.py --preview /tmp/preview
# 3) auditar e compilar
python tools/audit_strings.py
```

## Compilacao no WSL

O CEdev Windows foi encontrado em dois locais. O caminho abaixo foi usado com
sucesso no WSL:

```text
C:\CEdev
```

Na raiz deste projeto, rode:

```bash
export PATH="/mnt/c/CEdev/bin:$PATH"
/mnt/c/CEdev/bin/make.exe clean
/mnt/c/CEdev/bin/make.exe
```

O arquivo final esperado e:

```text
bin/CIRCVIE3.8xp
```

Envie apenas esse `.8xp` para a calculadora. Este pacote nao deve gerar
AppVars `.8xv`; se aparecer algum `.8xv`, rode `make clean` e recompile.

Antes de compilar depois de adicionar exercicios, rode:

```bash
python tools/audit_strings.py
```
