"""Gera o relatório DOCX da validação do Priora a partir dos dados em val/."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(sys.argv[1])
OUT = Path(sys.argv[2])
plt.rcParams["font.family"] = ["Times New Roman", "DejaVu Serif"]

res = json.loads((BASE / "resultados" / "resultados.json").read_text(encoding="utf-8"))
resumo = json.loads((BASE / "resultados" / "resumo.json").read_text(encoding="utf-8"))
R = {r["id"]: r for r in res}
IDS = sorted(R, key=lambda i: (i[0] != "J", int(i[1:])))


def load(pasta, id_):
    return json.loads((BASE / pasta / f"{id_}.json").read_text(encoding="utf-8"))


CASOS = {i: load("casos", i) for i in IDS}
PESOS = {i: load("pesos", i) for i in IDS}
GAB = {i: load("gabaritos", i) for i in IDS}
EXCL = {}
for p in sorted((BASE / "excluidos" / "gabaritos").glob("*.json")) if (BASE / "excluidos" / "gabaritos").exists() else []:
    EXCL[p.stem] = json.loads(p.read_text(encoding="utf-8"))
MOTIVOS = json.loads((BASE / "motivos_exclusao.json").read_text(encoding="utf-8")) if (BASE / "motivos_exclusao.json").exists() else {}

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3), Cm(2), Cm(3), Cm(2)

st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.line_spacing = 1.5
st.paragraph_format.space_after = Pt(0)
for nome, tam in (("Heading 1", 12), ("Heading 2", 12), ("Heading 3", 12)):
    h = doc.styles[nome]
    h.font.name = "Times New Roman"
    h.font.size = Pt(tam)
    h.font.bold = True
    h.font.italic = False
    h.font.color.rgb = RGBColor(0, 0, 0)
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    h.paragraph_format.line_spacing = 1.5

FIG = [0]
TAB = [0]


def p(texto="", bold=False, italic=False, align=None, size=None, indent=True, spacing=None, after=None, keep=False):
    par = doc.add_paragraph()
    if align == "c":
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "j" or align is None:
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if indent and align is None:
        par.paragraph_format.first_line_indent = Cm(1.25)
    if spacing:
        par.paragraph_format.line_spacing = spacing
    if after is not None:
        par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.keep_with_next = keep
    r = par.add_run(texto)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    return par


def h1(t):
    doc.add_heading(t.upper(), level=1)


def h2(t):
    doc.add_heading(t, level=2)


def shade(cell, cor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), cor)
    tcPr.append(shd)


def cell_text(cell, texto, bold=False, size=9, align=None, italic=False):
    cell.text = ""
    par = cell.paragraphs[0]
    par.paragraph_format.line_spacing = 1.0
    par.paragraph_format.space_after = Pt(0)
    par.paragraph_format.first_line_indent = Cm(0)
    if align == "c":
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = par.add_run(str(texto))
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    r.font.name = "Times New Roman"


def tabela(cab, linhas, larguras, size=9, centro=(), caption=None, fonte="Fonte: elaborado pelos autores (2026)."):
    if caption:
        TAB[0] += 1
        c = p(f"Tabela {TAB[0]} - {caption}", align="c", size=10, indent=False, spacing=1.0, after=3, keep=True)
    t = doc.add_table(rows=1, cols=len(cab))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, ctext in enumerate(cab):
        cell_text(t.rows[0].cells[i], ctext, bold=True, size=size, align="c")
        shade(t.rows[0].cells[i], "D9D9D9")
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for linha in linhas:
        cells = t.add_row().cells
        for i, v in enumerate(linha):
            cell_text(cells[i], v, size=size, align="c" if i in centro else None)
    for row in t.rows:
        for i, w in enumerate(larguras):
            row.cells[i].width = Cm(w)
        trPr = row._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit")
        cs.set(qn("w:val"), "true")
        trPr.append(cs)
    if fonte:
        p(fonte, align="c", size=10, indent=False, spacing=1.0, after=8)
    else:
        p("", indent=False, spacing=1.0, after=4)
    return t


def figura(arq, titulo, largura=14.5):
    FIG[0] += 1
    p(f"Figura {FIG[0]} - {titulo}", align="c", size=10, indent=False, spacing=1.0, after=3, keep=True)
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.keep_with_next = True
    par.add_run().add_picture(str(arq), width=Cm(largura))
    p("Fonte: elaborado pelos autores (2026).", align="c", size=10, indent=False, spacing=1.0, after=8)


def pct(x):
    return f"{x:.1f}".replace(".", ",") + "%"


def num(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")



# --------------------------------------------------------------------- estatísticas auxiliares
def links(id_):
    inc = {s["id"]: 0 for s in CASOS[id_]["suspeitos"]}
    ino = {s["id"]: 0 for s in CASOS[id_]["suspeitos"]}
    for pe in PESOS[id_]["pesos"]:
        for v in pe["vinculos"]:
            (ino if v["efeito"] == "Inocenta" else inc)[v["suspeito"]] += 1
    return inc, ino


def nao_autores(i):
    return R[i]["n_suspeitos"] - len(R[i]["culpado"])


def agrega(lista):
    n = len(lista)
    if n == 0:
        return None
    k1 = sum(r["acertou_top1"] for r in lista)
    k2 = sum(r["acertou_top2"] for r in lista)
    lo, hi = wilson(k1, n)
    return {
        "n": n, "top1": k1, "top1_pct": 100 * k1 / n, "ic": (100 * lo, 100 * hi), "top2": k2, "top2_pct": 100 * k2 / n,
        "pos": sum(r["posicao_culpado"] for r in lista) / n, "mrr": sum(1 / r["posicao_culpado"] for r in lista) / n,
        "prob": sum(r["prob_culpado"] for r in lista) / n,
        "brier": sum((1 - r["prob_culpado"] / 100) ** 2 for r in lista) / n,
        "alea": 100 * sum(r["base_aleatoria"] for r in lista) / n,
        "vinc": 100 * sum(r["base_mais_vinculos_incrimina"] for r in lista) / n,
        "cit": 100 * sum(r["base_mais_citado"] for r in lista) / n,
        "semino": 100 * sum(r["sem_inocenta_top1"] for r in lista) / n,
        "mc": sum(r["mc_culpado_primeiro_pct"] for r in lista) / n,
        "susp": sum(r["n_suspeitos"] for r in lista) / n, "pist": sum(r["n_evidencias"] for r in lista) / n,
        "autores": sum(len(r["culpado"]) for r in lista) / n,
    }


def wilson(k, n, z=1.96):
    import math
    if n == 0:
        return (0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


todos = [R[i] for i in IDS]
A_ = [R[i] for i in IDS if nao_autores(i) >= 2]   # critérios completos (pelo menos 2 suspeitos não autores)
B_ = [R[i] for i in IDS if nao_autores(i) < 2]
G = agrega(todos)
GA = agrega(A_)
GB = agrega(B_)
nt = G["n"]

# --------------------------------------------------------------------- figuras
arq1 = BASE / "resultados" / "fig_acerto.png"
fig, ax = plt.subplots(figsize=(7.5, 4.2))
grupos = [(f"Todos os casos (n={G['n']})", G)] + ([(f"Com 2 ou mais suspeitos\nnão autores (n={GA['n']})", GA)] if GA else []) + ([(f"Demais (n={GB['n']})", GB)] if GB else [])
x = range(len(grupos))
w = 0.2
series = [("Priora (1º lugar)", "top1_pct", "#2a7f62"), ("Mais vínculos que incriminam", "vinc", "#8a8a8a"),
          ("Mais pistas citadas", "cit", "#b5b5b5"), ("Sorteio ao acaso", "alea", "#dddddd")]
for k, (rot, chave, cor) in enumerate(series):
    vals = [g[1][chave] for g in grupos]
    bars = ax.bar([i + (k - 1.5) * w for i in x], vals, w, label=rot, color=cor, edgecolor="black", linewidth=0.5)
    for b_, v_ in zip(bars, vals):
        ax.text(b_.get_x() + b_.get_width() / 2, v_ + 1, f"{v_:.0f}", ha="center", fontsize=8)
ax.set_xticks(list(x))
ax.set_xticklabels([g[0] for g in grupos], fontsize=9)
ax.set_ylabel("Casos com o culpado em 1º lugar (%)")
ax.set_ylim(0, 110)
ax.legend(fontsize=8, loc="upper right", ncol=2)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(arq1, dpi=200)
plt.close(fig)

arq2 = BASE / "resultados" / "fig_posicao.png"
fig, ax = plt.subplots(figsize=(7.5, 3.6))
maxp = max(r["posicao_culpado"] for r in todos)
cont = [sum(1 for r in todos if r["posicao_culpado"] == pos) for pos in range(1, maxp + 1)]
bars = ax.bar(range(1, maxp + 1), cont, 0.6, color="#2a7f62", edgecolor="black", linewidth=0.5)
for b_, v_ in zip(bars, cont):
    if v_:
        ax.text(b_.get_x() + b_.get_width() / 2, v_ + 0.2, str(v_), ha="center", fontsize=9)
ax.set_xlabel("Posição do culpado no ranking do Priora (melhor posição entre os autores)")
ax.set_ylabel("Número de casos")
ax.set_xticks(range(1, maxp + 1))
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(arq2, dpi=200)
plt.close(fig)

# --------------------------------------------------------------------- capa
p("VALIDAÇÃO DO PRIORA COM CASOS REAIS", bold=True, align="c", indent=False, after=6)
p("Relatório técnico complementar à documentação do sistema Priora", align="c", indent=False, after=6)
p(f"Documento de apoio à seção “Validação” da documentação, com a descrição completa do método, das pistas, dos pesos e dos resultados de {nt} casos reais já julgados",
  align="c", indent=False, size=11, after=18)
p("2026", align="c", indent=False)
doc.add_page_break()

p("SUMÁRIO", bold=True, align="c", indent=False, after=6)
par = doc.add_paragraph()
run = par.add_run()
for tipo, txt in (("begin", None), (None, 'TOC \\o "1-2" \\h \\z \\u'), ("separate", None), ("text", "Clique com o botão direito e escolha Atualizar campo para gerar o sumário."), ("end", None)):
    if tipo == "text":
        par.add_run(txt)
        continue
    el = OxmlElement("w:fldChar") if tipo else OxmlElement("w:instrText")
    if tipo:
        el.set(qn("w:fldCharType"), tipo)
    else:
        el.set(qn("xml:space"), "preserve")
        el.text = txt
    run._r.append(el) if tipo in ("begin", None) else par.add_run()._r.append(el)
doc.add_page_break()

# --------------------------------------------------------------------- 1 introdução
h1("1 Introdução")
p("Este documento reúne o registro completo da validação do ranking de suspeitos produzido pelo Priora. A pergunta é simples: dado um conjunto de pistas sobre um caso já resolvido, "
  "o suspeito que o modelo coloca em primeiro lugar é o autor do crime? Para responder, o motor probabilístico real do sistema (módulo app.bayes.model, o mesmo usado pela aplicação) "
  f"foi executado sobre {nt} casos reais já julgados, sem acesso do avaliador à solução, e o resultado foi comparado com o desfecho oficial de cada caso, definido por decisão judicial ou por prova comprovada.")
p("A seção de validação da documentação traz apenas os resultados. Aqui estão o método, cada caso, cada pista, cada peso e as análises de apoio, de modo que qualquer resultado possa ser conferido e reproduzido. "
  "Os casos reais variam em tipo de crime, época, país, número de suspeitos e número de pistas. Os limites dessa variedade, que dependeu de fontes públicas e gratuitas, estão descritos na seção 4.")

# --------------------------------------------------------------------- 2 método
h1("2 Método")
h2("2.1 Seleção dos casos e das fontes")
p("A seleção ocorreu em duas etapas, e a diferença entre elas importa para a leitura dos resultados. Na primeira, foram coletados 20 casos reais já julgados com 3 a 10 suspeitos nomeados, de 8 a 40 pistas independentes, "
  "autor definido por decisão judicial ou prova comprovada e texto público e gratuito. Esses critérios não exigiam que houvesse suspeitos não autores, e em alguns casos todos os suspeitos listados foram condenados.")
p("Para corrigir isso, a segunda etapa fixou critérios mais estritos antes da busca: de 4 a 10 suspeitos nomeados, pelo menos 2 deles não autores, de 12 a 35 pistas, autor não preso em flagrante nem confesso antes de a investigação o identificar, "
  "e uso apenas de informação anterior à identificação do autor. A busca foi feita em frentes diferentes (Brasil, Estados Unidos e Canadá, Reino Unido e Oceania, Europa continental, Ásia, África e América Latina, crimes que não são homicídio, "
  "e decisões de tribunais de apelação por décadas), com 60 casos pedidos no total. Apenas 5 casos cumpriram todos os critérios; os critérios não foram afrouxados para completar a cota, e nenhum caso foi trocado depois de conhecido o resultado. "
  "A amostra final tem, portanto, 25 casos, dos quais 20 vêm da primeira etapa e 5 da segunda.")
p("As fontes de cada caso (Wikipédia, decisões judiciais abertas e imprensa), as URLs e as condições de uso constam nas fichas do Apêndice A. As pistas foram reescritas com palavras próprias, como fatos neutros, sem reprodução de trechos.")
h2("2.2 Extração das pistas")
p("A extração foi feita por assistentes de inteligência artificial (modelo de linguagem), que seguiram um protocolo escrito: cada pista é um fato ou testemunho, em uma a três frases, sem concluir quem é o culpado; "
  "devem entrar também as pistas que afastam suspeitos (álibis, contradições, pistas falsas); só entra o que os investigadores sabiam antes da solução, sem a sentença nem a confissão do autor; "
  "a mesma informação não entra duas vezes. Cada pista recebe um tipo (por exemplo, Depoimento, Pericial, Documental, Telefônica) e a lista dos suspeitos a que se refere.")
h2("2.3 Anonimização e cegueira")
p("Cada caso gerou dois arquivos separados. O arquivo cego contém o resumo, os suspeitos (identificados como S1, S2 e assim por diante, com perfil neutro) e as pistas, com nomes, cidades, datas exatas e empresas trocados por termos genéricos, "
  "para que o avaliador não reconhecesse o caso. O arquivo de gabarito contém o título, a fonte, o autor e a solução e nunca foi aberto pelos avaliadores de pesos.")
h2("2.4 Atribuição dos pesos")
p("Os pesos foram atribuídos por avaliadores independentes (outros assistentes de inteligência artificial, em sessões separadas das que extraíram as pistas), que receberam apenas o arquivo cego e a escala escrita, sem acesso ao gabarito nem à internet. "
  "A escala tem cinco níveis (0,1; 0,3; 0,5; 0,7; 0,9), cada um com critério escrito, inspirada nos sistemas de graduação de fontes e informações usados em inteligência. Níveis discretos evitam a falsa precisão e tornam cada escolha justificável. "
  "Os dois pesos respondem a perguntas distintas. O peso da evidência mede a confiabilidade da informação em si. O peso do vínculo mede quanto a evidência aponta para (ou afasta) cada suspeito, e cada vínculo recebe também o efeito Incrimina ou Inocenta. A escala completa está no Apêndice B.")
h2("2.5 Execução")
p("Os pesos de cada caso foram cadastrados no mesmo formato do sistema (peso da evidência r, peso do vínculo v e efeito por suspeito) e o motor do Priora foi executado: contribuição C = 1 + r·v/|S| para evidências que incriminam, "
  "em que |S| é o número de suspeitos incriminados pela evidência, e C = 1/(1 + r·v) para as que inocentam, com prior uniforme e normalização global. Os pesos foram limitados ao intervalo de 0,05 a 0,95, como o sistema exige (estritamente entre 0 e 1).")
h2("2.6 Métricas")
p("Para cada caso, registrou-se a posição do culpado no ranking (quando há mais de um autor, a melhor posição entre eles) e a soma das probabilidades dos autores. No conjunto, calcularam-se: "
  "acerto no primeiro lugar (top-1) e entre os dois primeiros (top-2), com intervalo de confiança de Wilson de 95% para o top-1; posição média do culpado; inverso médio da posição (MRR); "
  "e o erro quadrático médio da probabilidade atribuída ao culpado (escore de Brier; quanto menor, melhor). Como referência, usaram-se três linhas de base sem modelo probabilístico: sorteio ao acaso entre os suspeitos, "
  "escolha do suspeito com mais vínculos que incriminam e escolha do suspeito citado em mais pistas (empates repartem o acerto).")
p("Para medir a dependência em relação aos pesos, o resultado de cada caso foi recalculado em 2.000 sorteios em que todos os pesos variam ao acaso em até ±0,2, registrando-se em quantos o culpado fica em primeiro lugar. "
  "Mediu-se também o valor do efeito Inocenta, repetindo o cálculo com os vínculos que inocentam removidos, e a dependência de uma única evidência, retirando uma pista por vez e verificando se o líder muda.")
h2("2.7 Reprodutibilidade")
p("Os arquivos de todos os casos (cegos, pesos e gabaritos) e os scripts de execução e de geração deste relatório acompanham a documentação. Os resultados são reproduzíveis com o script rodar_validacao.py e a mesma semente aleatória.")

# --------------------------------------------------------------------- 3 resultados
h1("3 Resultados")
h2("3.1 Resultados gerais")


def col(g):
    return g


cabs = ["Medida", f"Todos os casos (n={G['n']})"] + ([f"Com 2 ou mais suspeitos não autores (n={GA['n']})"] if GA else []) + ([f"Demais (n={GB['n']})"] if GB else [])
gs = [G] + ([GA] if GA else []) + ([GB] if GB else [])
linhas = [
    ("Culpado em 1º lugar (top-1)", lambda g: f"{g['top1']} ({pct(g['top1_pct'])})"),
    ("Intervalo de confiança de 95% do top-1", lambda g: f"{pct(g['ic'][0])} a {pct(g['ic'][1])}"),
    ("Culpado entre os 2 primeiros (top-2)", lambda g: f"{g['top2']} ({pct(g['top2_pct'])})"),
    ("Posição média do culpado", lambda g: num(g["pos"], 2)),
    ("Inverso médio da posição (MRR)", lambda g: num(g["mrr"], 3)),
    ("Probabilidade média atribuída ao culpado", lambda g: pct(g["prob"])),
    ("Escore de Brier (menor é melhor)", lambda g: num(g["brier"], 3)),
    ("Linha de base: sorteio ao acaso", lambda g: pct(g["alea"])),
    ("Linha de base: mais vínculos que incriminam", lambda g: pct(g["vinc"])),
    ("Linha de base: mais pistas citadas", lambda g: pct(g["cit"])),
    ("Top-1 sem o efeito Inocenta", lambda g: pct(g["semino"])),
    ("Culpado em 1º nos sorteios de pesos (±0,2), média", lambda g: pct(g["mc"])),
    ("Autores por caso (média)", lambda g: num(g["autores"])),
    ("Suspeitos por caso (média)", lambda g: num(g["susp"])),
    ("Pistas por caso (média)", lambda g: num(g["pist"])),
]
lin = [[nome] + [f(g) for g in gs] for nome, f in linhas]
wd = [6.4] + [9.6 / len(gs)] * len(gs)
tabela(cabs, lin, wd, centro=tuple(range(1, len(gs) + 1)), caption="Resultados gerais da validação")
figura(arq1, "Casos com o culpado em primeiro lugar, comparados com as linhas de base")
figura(arq2, "Posição do culpado no ranking do Priora")

dif_acaso = G["top1_pct"] - G["alea"]
dif_vinc = G["top1_pct"] - G["vinc"]
dif_cit = G["top1_pct"] - G["cit"]
p(f"O Priora colocou o culpado em primeiro lugar em {G['top1']} dos {nt} casos ({pct(G['top1_pct'])}; intervalo de 95% de {pct(G['ic'][0])} a {pct(G['ic'][1])}) e entre os dois primeiros em {G['top2']} ({pct(G['top2_pct'])}). "
  f"O sorteio ao acaso acertaria {pct(G['alea'])} em média nestes casos, de modo que o Priora ficou {num(dif_acaso)} pontos percentuais acima dele.")
if dif_vinc < 0 or dif_cit < 0:
    p(f"As linhas de base que contam pistas acertaram mais: {pct(G['vinc'])} ao escolher o suspeito com mais vínculos que incriminam e {pct(G['cit'])} ao escolher o mais citado, "
      f"ou seja, {num(-dif_vinc)} e {num(-dif_cit)} pontos percentuais a mais do que o Priora. Portanto, nestes casos o modelo não superou a contagem simples de pistas. "
      "Parte da explicação é que a contagem é favorecida quando há mais de um autor por caso, pois o acerto é contado sobre todos os autores, e quando as pistas coletadas se concentram nos condenados, um viés de retrospectiva discutido na seção 4.")
else:
    p(f"A contagem simples de vínculos que incriminam acertou {pct(G['vinc'])} e a de pistas citadas, {pct(G['cit'])}; o Priora ficou acima dessas referências, mas a diferença é pequena para {nt} casos e não é estatisticamente distinguível.")
if GA and GB:
    p(f"Entre os {GA['n']} casos que cumprem o critério de ter pelo menos 2 suspeitos não autores, o Priora acertou {GA['top1']} ({pct(GA['top1_pct'])}), contra {pct(GA['vinc'])} da contagem de vínculos que incriminam e {pct(GA['alea'])} do sorteio ao acaso. "
      f"Nos {GB['n']} demais casos, o acerto foi de {GB['top1']} ({pct(GB['top1_pct'])}), contra {pct(GB['vinc'])} da contagem de vínculos. Os grupos são pequenos, e a comparação entre eles é uma observação sobre os dados, sem teste estatístico.")
p(f"O efeito Inocenta, nestes casos, deixou o acerto no primeiro lugar em {pct(G['top1_pct'])}, igual ao obtido sem ele ({pct(G['semino'])}).")

h2("3.2 Resultados por caso")
lin = []
for i in IDS:
    r = R[i]
    rk = " > ".join(f"{s} {num(pc)}%" for s, pc in r["ranking"][:3])
    lin.append([i, ", ".join(r["culpado"]), r["n_suspeitos"], r["n_evidencias"], r["posicao_culpado"], pct(r["prob_culpado"]), rk, pct(r["mc_culpado_primeiro_pct"])])
tabela(["Caso", "Autor(es)", "Susp.", "Pistas", "Posição", "Prob. do culpado", "Três primeiros do ranking", "Culpado em 1º nos sorteios"], lin,
       [1.1, 2.0, 1.1, 1.2, 1.4, 1.8, 4.8, 2.0], size=8, centro=(0, 1, 2, 3, 4, 5, 7), caption="Resultado do Priora em cada caso")

h2("3.3 Casos em que o culpado não ficou em primeiro lugar")
err = [r for r in todos if not r["acertou_top1"]]
lin = []
for r in sorted(err, key=lambda x: x["id"]):
    i = r["id"]
    inc, ino = links(i)
    cul = min(r["culpado"], key=lambda c: [s for s, _ in r["ranking"]].index(c))
    lider = r["lider"]
    lin.append([i, r["posicao_culpado"], pct(r["prob_culpado"]), lider, pct(dict(r["ranking"])[lider]), f"{inc[cul]}/{ino[cul]}", f"{inc[lider]}/{ino[lider]}"])
tabela(["Caso", "Posição do culpado", "Prob. do culpado", "Líder", "Prob. do líder", "Vínculos do culpado (incrimina/inocenta)", "Vínculos do líder (incrimina/inocenta)"], lin,
       [1.3, 2.0, 2.0, 1.4, 2.0, 3.8, 3.5], size=8, centro=(0, 1, 2, 3, 4, 5, 6), caption="Casos em que o culpado não foi o primeiro do ranking")
nlider_mais = sum(1 for r in err if links(r["id"])[0][r["lider"]] > min(links(r["id"])[0][c] for c in r["culpado"]))
p(f"Em {nlider_mais} dos {len(err)} casos errados, o suspeito que liderou tinha mais vínculos que incriminam do que o culpado, o que é coerente com a propriedade do modelo, em que cada evidência incriminadora só soma ao suspeito (a contribuição é sempre maior que 1). "
  "A tabela descreve o que aconteceu, sem explicar por que cada caso errou. Uma análise caso a caso exigiria reler as pistas, o que é possível nas fichas do Apêndice A.")

h2("3.4 Sensibilidade aos pesos")
estaveis = [r for r in todos if r["mc_culpado_primeiro_pct"] >= 95]
instaveis = [r for r in todos if r["mc_culpado_primeiro_pct"] <= 5]
p(f"Variando todos os pesos ao acaso em até ±0,2, o culpado permaneceu em primeiro lugar em pelo menos 95% dos sorteios em {len(estaveis)} dos {nt} casos e em no máximo 5% dos sorteios em {len(instaveis)} casos. "
  f"A média, entre os casos, da proporção de sorteios com o culpado em primeiro foi de {pct(G['mc'])}. "
  f"Entre os {len(err)} casos em que o culpado não ficou em primeiro lugar, em {sum(1 for r in err if r['mc_culpado_primeiro_pct'] < 10)} o culpado ficou em primeiro em menos de 10% dos sorteios, "
  f"isto é, a variação dos pesos dentro de ±0,2 raramente corrige o erro; nos outros {sum(1 for r in err if r['mc_culpado_primeiro_pct'] >= 10)}, o resultado é sensível à variação dos pesos. "
  f"Entre os {sum(1 for r in todos if r['acertou_top1'])} casos em que o culpado ficou em primeiro lugar, {sum(1 for r in todos if r['acertou_top1'] and r['mc_culpado_primeiro_pct'] >= 90)} mantiveram essa posição em pelo menos 90% dos sorteios.")
mud = sum(1 for r in todos if r["retirar_1_evidencia_muda_lider"] > 0)
p(f"Retirando uma pista por vez, o líder do ranking mudou em pelo menos um cenário em {mud} dos {nt} casos.")

# --------------------------------------------------------------------- 4 limitações
h1("4 Limitações")
for t in [
    "Os pesos foram atribuídos por assistentes de inteligência artificial, e não por investigadores. A escala é a mesma da validação anterior, mas o julgamento de cada pista pode diferir do que faria uma equipe investigativa.",
    "As pistas foram extraídas por assistentes de inteligência artificial a partir de textos públicos, em sua maioria resumos da Wikipédia e de imprensa, que trazem poucos laudos, álibis e dados telefônicos. As fichas do Apêndice A trazem as observações de cada extração.",
    "A amostra é pequena (25 casos) e foi formada em duas etapas com critérios diferentes. Os 20 casos da primeira etapa não exigiam suspeitos não autores, e em vários deles todos os suspeitos listados foram condenados, o que favorece as linhas de base que contam pistas. Dos 60 casos pedidos na segunda etapa, só 5 cumpriram os critérios completos.",
    "Em vários casos há mais de um autor, e alguns casos usam como suspeitos adicionais hipóteses levantadas pela defesa, que não foram formalmente investigadas. As fichas indicam o desfecho de cada suspeito.",
    "Há viés de retrospectiva. As pistas foram levantadas depois da condenação, a partir de fontes que já resumem o caso, e mesmo sem a sentença e a confissão a seleção do que é relevante tende a favorecer quem foi condenado. Nos casos da segunda etapa, parte da prova vem de decisões de apelação, que descrevem a prova apresentada no julgamento.",
    "Alguns casos podem ser reconhecidos pelo avaliador mesmo anonimizados, o que pode ter influenciado os pesos.",
    "O modelo pressupõe independência condicional entre as pistas. Pistas de um mesmo caso costumam depender umas das outras, e o tratamento dado (reduzir o peso da pista repetida) é apenas uma aproximação.",
    "O intervalo de confiança do acerto é largo, e os resultados mostram o comportamento do modelo nestes casos, não uma taxa de acerto em investigações reais.",
    "Os casos foram escolhidos entre os que tinham texto público, gratuito e acessível às ferramentas de busca, o que favorece casos documentados em inglês e em português e não forma uma amostra aleatória de investigações.",
]:
    par = doc.add_paragraph(style="List Bullet")
    par.paragraph_format.line_spacing = 1.5
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.add_run(t)

h1("5 Conclusão")
p(f"Em {nt} casos reais, o Priora colocou o culpado em primeiro lugar em {pct(G['top1_pct'])} das vezes e entre os dois primeiros em {pct(G['top2_pct'])}, acima do sorteio ao acaso ({pct(G['alea'])}), "
  + (f"mas abaixo da contagem simples de vínculos que incriminam ({pct(G['vinc'])}) e da contagem de pistas citadas ({pct(G['cit'])}). " if (dif_vinc < 0 and dif_cit < 0) else f"e em linha com a contagem simples de pistas ({pct(G['vinc'])} e {pct(G['cit'])}). ")
  + "Os resultados mostram que o modelo é coerente com o desfecho em boa parte dos casos, e que o desempenho depende da qualidade e do equilíbrio das pistas e dos pesos. "
  "Com uma amostra pequena e as limitações descritas, não permitem afirmar a precisão do sistema em investigações reais.")
doc.add_page_break()

# --------------------------------------------------------------------- apêndice A
h1("Apêndice A - Fichas dos casos")
p("Cada ficha traz a identificação do caso, os suspeitos e seu desfecho, as pistas com os pesos atribuídos, o ranking calculado pelo Priora e as observações da extração. "
  "Os suspeitos aparecem de forma anonimizada, como no arquivo cego. Legenda dos vínculos: suspeito (v = peso do vínculo, + incrimina, − inocenta).", indent=False)


def vinc_txt(pe):
    if not pe["vinculos"]:
        return "sem vínculo"
    return "; ".join(f"{v['suspeito']} ({'+' if v['efeito'] != 'Inocenta' else chr(0x2212)}{num(v['v'])})" for v in pe["vinculos"])


for i in IDS:
    c, g, w, r = CASOS[i], GAB[i], PESOS[i], R[i]
    doc.add_heading(f"Caso {i}: {g.get('titulo', '')}", level=2)
    meta = [("Tipo de crime", g.get("tipo_crime", "")), ("País e época", g.get("pais_epoca", "")),
            ("Fonte", f"{g.get('fonte', '')} ({g.get('url', '')})"), ("Condição de uso", g.get("licenca_ou_uso", ""))]
    for k, v in meta:
        par = p("", indent=False, spacing=1.0, after=2, align="j")
        a = par.add_run(f"{k}: ")
        a.bold = True
        a.font.size = Pt(10)
        b_ = par.add_run(str(v))
        b_.font.size = Pt(10)
    p("Resumo (arquivo cego): " + c.get("resumo", ""), indent=False, spacing=1.0, size=10, after=4)
    inc, ino = links(i)
    lin = []
    for s in c["suspeitos"]:
        eh = "autor" if s["id"] in g["culpado"] else "não autor"
        lin.append([s["id"], s.get("perfil", ""), eh, f"{inc[s['id']]}/{ino[s['id']]}", pct(dict(r["ranking"])[s["id"]])])
    tabela(["Suspeito", "Descrição", "Desfecho", "Vínculos (incr./inoc.)", "Probabilidade"], lin, [1.4, 8.0, 1.7, 2.3, 1.9], size=8, centro=(0, 2, 3, 4), fonte=None)
    pesos_por = {pe["evidencia"]: pe for pe in w["pesos"]}
    lin = []
    for e in c["evidencias"]:
        pe = pesos_por.get(e["id"])
        if pe:
            lin.append([e["id"], e.get("tipo", ""), e["texto"], num(pe["r"]), vinc_txt(pe)])
    tabela(["Pista", "Tipo", "Texto", "r", "Vínculos"], lin, [1.1, 1.9, 8.1, 0.8, 4.1], size=8, centro=(0, 3), fonte=None)
    rk = " > ".join(f"{s} ({num(pc)}%)" for s, pc in r["ranking"])
    p(f"Ranking do Priora: {rk}. Autor(es): {', '.join(g['culpado'])}, na posição {r['posicao_culpado']}, com {pct(r['prob_culpado'])}. "
      f"Nos sorteios de pesos (±0,2), o culpado ficou em primeiro em {pct(r['mc_culpado_primeiro_pct'])}.", indent=False, spacing=1.0, size=10, after=3)
    p("Desfecho oficial (gabarito): " + g.get("solucao", ""), indent=False, spacing=1.0, size=10, after=3)
    if g.get("observacoes"):
        p("Observações da extração: " + g["observacoes"], indent=False, spacing=1.0, size=10, after=10)

# --------------------------------------------------------------------- apêndice B
doc.add_page_break()
h1("Apêndice B - Escala de pesos")
tabela(["Nível", "Peso da evidência (confiabilidade)", "Peso do vínculo que incrimina", "Peso do vínculo que inocenta"], [
    ["0,9", "Laudo pericial oficial com cadeia de custódia documentada, ou registro eletrônico íntegro", "Praticamente exclusiva do suspeito, sem explicação inocente", "Afasta de forma praticamente conclusiva"],
    ["0,7", "Registro ou documento oficial, ou testemunho presencial sem interesse e corroborado", "Forte, com poucas pessoas compatíveis", "Afasta com força"],
    ["0,5", "Testemunho sem corroboração, ou registro sem cadeia de custódia", "Compatível com um grupo pequeno ou com explicação inocente plausível", "Afasta parcialmente"],
    ["0,3", "Informação de segunda mão, interpretação de terceiros ou caracterização feita por uma parte interessada", "Circunstancial, compatível com muitas pessoas", "Afasta de forma circunstancial"],
    ["0,1", "Denúncia anônima ou boato", "Mera associação (parentesco, contato)", "Mera sugestão"],
], [1.3, 5.2, 4.9, 4.6], size=9, centro=(0,), caption="Escala de cinco níveis usada na atribuição dos pesos")

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("salvo", OUT)
