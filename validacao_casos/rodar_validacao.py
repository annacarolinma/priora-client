"""Roda o motor bayesiano real do Priora (app.bayes.model) sobre os casos de validação.

Uso:  python rodar_validacao.py <pasta_val> [--mc 2000]
Entrada: casos/<ID>.json (cego), pesos/<ID>.json (avaliador), gabaritos/<ID>.json
Saída:   resultados/resultados.json, resultados/resumo.json, resultados/resumo.md
"""
import json
import math
import random
import sys
from pathlib import Path

SERVER = Path(r"C:\Users\laisa\OneDrive\Desktop\Projetos\priora_server")
sys.path.insert(0, str(SERVER))
from app.bayes.model import BayesianNetwork, Evidence, EvidenceStatus, EvidenceType, Suspect  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(sys.argv[1])
MC = 2000
if "--mc" in sys.argv:
    MC = int(sys.argv[sys.argv.index("--mc") + 1])
LO, HI = 0.05, 0.95
NET = BayesianNetwork()
TIPOS = {t.value: t for t in EvidenceType}


def carregar(pasta, id_):
    p = BASE / pasta / f"{id_}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def montar(caso, pesos, sem_inocenta=False, vec=None, drop=None):
    """Monta suspeitos e evidências. vec: dict {(i,'r'|s):valor} substitui pesos (para sensibilidade)."""
    suspects = [Suspect(id=s["id"], name=s["id"]) for s in caso["suspeitos"]]
    tipos = {e["id"]: e.get("tipo", "Outra") for e in caso["evidencias"]}
    evs = []
    for i, p in enumerate(pesos["pesos"]):
        if drop is not None and p["evidencia"] == drop:
            continue
        links, efeitos = {}, {}
        for v in p["vinculos"]:
            if sem_inocenta and v["efeito"] == "Inocenta":
                continue
            val = v["v"] if vec is None else vec[(i, v["suspeito"])]
            links[v["suspeito"]] = min(HI, max(LO, val))
            efeitos[v["suspeito"]] = v["efeito"]
        if not links:
            continue
        r = p["r"] if vec is None else vec[(i, "r")]
        evs.append(Evidence(
            id=p["evidencia"], name=p["evidencia"], type=TIPOS.get(tipos.get(p["evidencia"]), EvidenceType.OUTRA),
            status=EvidenceStatus.COLETADA, reliability=min(HI, max(LO, r)),
            suspect_links=links, suspect_effects=efeitos,
        ))
    return suspects, evs


def rodar(caso, pesos, **kw):
    suspects, evs = montar(caso, pesos, **kw)
    res = NET.run(caso["id"], suspects, evs).ranking
    return {r.suspect.id: r.probability_pct for r in res}, [r.suspect.id for r in res]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def analisar(id_):
    caso, pesos, gab = carregar("casos", id_), carregar("pesos", id_), carregar("gabaritos", id_)
    if not (caso and pesos and gab):
        return None
    culp = set(gab["culpado"])
    pct, ordem = rodar(caso, pesos)
    n = len(ordem)
    rank = min(ordem.index(c) + 1 for c in culp)
    prob_culp = sum(pct[c] for c in culp)
    top = ordem[0]
    seg = pct[ordem[1]] if n > 1 else 0.0
    # linhas de base
    inc = {s["id"]: 0 for s in caso["suspeitos"]}
    men = {s["id"]: 0 for s in caso["suspeitos"]}
    for p in pesos["pesos"]:
        for v in p["vinculos"]:
            men[v["suspeito"]] += 1
            if v["efeito"] != "Inocenta":
                inc[v["suspeito"]] += 1
    def acerto_contagem(d):
        mx = max(d.values())
        lideres = [k for k, v in d.items() if v == mx]
        return (len(set(lideres) & culp) / len(lideres)) if lideres else 0.0
    base_aleatoria = len(culp) / n
    base_inc = acerto_contagem(inc)
    base_men = acerto_contagem(men)
    # ablação: sem o efeito Inocenta
    pct_si, ord_si = rodar(caso, pesos, sem_inocenta=True)
    rank_si = min(ord_si.index(c) + 1 for c in culp)
    n_inocenta = sum(1 for p in pesos["pesos"] for v in p["vinculos"] if v["efeito"] == "Inocenta")
    n_incrimina = sum(1 for p in pesos["pesos"] for v in p["vinculos"] if v["efeito"] != "Inocenta")
    # retirar uma evidência por vez
    muda_lider = 0
    for p in pesos["pesos"]:
        _, o2 = rodar(caso, pesos, drop=p["evidencia"])
        muda_lider += o2[0] != top
    # Monte Carlo: todos os pesos variam ±0,2
    rng = random.Random(7)
    chaves = []
    for i, p in enumerate(pesos["pesos"]):
        chaves.append(((i, "r"), p["r"]))
        for v in p["vinculos"]:
            chaves.append(((i, v["suspeito"]), v["v"]))
    lider_igual = culp_primeiro = 0
    for _ in range(MC):
        vec = {k: b + rng.uniform(-0.2, 0.2) for k, b in chaves}
        _, o2 = rodar(caso, pesos, vec=vec)
        lider_igual += o2[0] == top
        culp_primeiro += o2[0] in culp
    return {
        "id": id_, "tipo": caso["tipo"], "titulo": gab.get("titulo"), "tipo_crime": gab.get("tipo_crime"),
        "pais_epoca": gab.get("pais_epoca"), "n_suspeitos": n, "n_evidencias": len(pesos["pesos"]),
        "n_vinculos_incrimina": n_incrimina, "n_vinculos_inocenta": n_inocenta,
        "culpado": sorted(culp), "ranking": [(s, round(pct[s], 1)) for s in ordem],
        "posicao_culpado": rank, "prob_culpado": round(prob_culp, 1), "lider": top,
        "acertou_top1": rank == 1, "acertou_top2": rank <= 2,
        "margem_1o_2o": round(pct[ordem[0]] - seg, 1),
        "base_aleatoria": round(base_aleatoria, 3), "base_mais_vinculos_incrimina": round(base_inc, 3),
        "base_mais_citado": round(base_men, 3),
        "sem_inocenta_posicao": rank_si, "sem_inocenta_top1": rank_si == 1,
        "retirar_1_evidencia_muda_lider": muda_lider,
        "mc_lider_igual_pct": round(100 * lider_igual / MC, 1), "mc_culpado_primeiro_pct": round(100 * culp_primeiro / MC, 1),
    }


def agregar(linhas):
    n = len(linhas)
    if n == 0:
        return {}
    k1 = sum(l["acertou_top1"] for l in linhas)
    k2 = sum(l["acertou_top2"] for l in linhas)
    lo, hi = wilson(k1, n)
    brier = sum((1 - l["prob_culpado"] / 100) ** 2 for l in linhas) / n
    return {
        "n_casos": n, "top1": k1, "top1_pct": round(100 * k1 / n, 1), "top1_ic95": [round(100 * lo, 1), round(100 * hi, 1)],
        "top2": k2, "top2_pct": round(100 * k2 / n, 1),
        "posicao_media_culpado": round(sum(l["posicao_culpado"] for l in linhas) / n, 2),
        "mrr": round(sum(1 / l["posicao_culpado"] for l in linhas) / n, 3),
        "prob_media_culpado": round(sum(l["prob_culpado"] for l in linhas) / n, 1),
        "brier": round(brier, 3),
        "base_aleatoria_pct": round(100 * sum(l["base_aleatoria"] for l in linhas) / n, 1),
        "base_mais_vinculos_pct": round(100 * sum(l["base_mais_vinculos_incrimina"] for l in linhas) / n, 1),
        "base_mais_citado_pct": round(100 * sum(l["base_mais_citado"] for l in linhas) / n, 1),
        "sem_inocenta_top1_pct": round(100 * sum(l["sem_inocenta_top1"] for l in linhas) / n, 1),
        "mc_culpado_primeiro_medio_pct": round(sum(l["mc_culpado_primeiro_pct"] for l in linhas) / n, 1),
        "suspeitos_media": round(sum(l["n_suspeitos"] for l in linhas) / n, 1),
        "evidencias_media": round(sum(l["n_evidencias"] for l in linhas) / n, 1),
    }


ids = sorted(p.stem for p in (BASE / "pesos").glob("*.json"))
linhas = [a for a in (analisar(i) for i in ids) if a]
(BASE / "resultados").mkdir(exist_ok=True)
(BASE / "resultados" / "resultados.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
resumo = {"real": agregar([l for l in linhas if l["tipo"] == "real"]),
          "todos": agregar(linhas)}
(BASE / "resultados" / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(resumo, ensure_ascii=False, indent=1))
for l in linhas:
    print(l["id"], l["tipo"], f'n={l["n_suspeitos"]}/{l["n_evidencias"]}', "culpado em", l["posicao_culpado"], f'({l["prob_culpado"]}%)', "| MC", l["mc_culpado_primeiro_pct"])
