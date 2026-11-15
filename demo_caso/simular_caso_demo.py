"""Confere, com o motor real do Priora, o que acontece em cada passo da demonstração.

Roda offline (não acessa o banco). Uso:
    python simular_caso_demo.py [caminho_do_priora_server]
"""
import json
import sys
from pathlib import Path

SERVER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\laisa\OneDrive\Desktop\Projetos\priora_server")
sys.path.insert(0, str(SERVER))
sys.stdout.reconfigure(encoding="utf-8")
from app.bayes.model import BayesianNetwork, Evidence, EvidenceStatus, EvidenceType, Suspect  # noqa: E402
import app.repositories.priority_repository as pr  # noqa: E402

D = json.loads((Path(__file__).parent / "caso_demo.json").read_text(encoding="utf-8"))
NOMES = {s["chave"]: s["nome"] for s in D["suspeitos"]}
NOMES[D["demonstracao"]["novo_suspeito"]["chave"]] = D["demonstracao"]["novo_suspeito"]["nome"]
TIPOS = {t.value: t for t in EvidenceType}
STATUS = {s.value: s for s in EvidenceStatus}
net = BayesianNetwork()
anterior = None


def montar(evs, chaves):
    suspeitos = [Suspect(id=k, name=NOMES[k]) for k in chaves]
    evidencias = [Evidence(id=e["chave"], name=e["nome"], type=TIPOS.get(e["tipo"], EvidenceType.OUTRA), status=STATUS[e["status"]],
                           reliability=e["peso"], suspect_links={v["suspeito"]: v["pesoVinculo"] for v in e["vinculos"]},
                           suspect_effects={v["suspeito"]: v["efeito"] for v in e["vinculos"]}) for e in evs]
    return suspeitos, evidencias


def passo(titulo, evs, chaves):
    global anterior
    S, E = montar(evs, chaves)
    res = net.run("demo", S, E, previous_results=anterior)
    anterior = res.ranking
    print(f"\n== {titulo}")
    for r in res.ranking:
        print(f"  {r.position}º {r.suspect.name:22} {r.probability_pct:5.1f}%  {r.trend.value}")
    return S, E


def acoes(S, E):
    # as sugestões pareiam suspeitos e probabilidades pela ordem da lista; aqui a lista vem na ordem do ranking
    ordem = [r.suspect for r in net.run("demo", S, E).ranking]
    pr.get_suspects_for_bayes = lambda tx, c: ordem
    pr.get_evidences_for_bayes = lambda tx, c: E
    for c in pr.compute_candidate_actions(None, "demo")[:8]:
        print(f"   [{c['impacto']:5}] {c['recompensa']:5.1f}%  {c['titulo']}")


chaves = [s["chave"] for s in D["suspeitos"]]
base = D["evidencias"]
novo = D["demonstracao"]["novo_suspeito"]["chave"]
passo("Estado inicial do caso (pronto, não concluído)", base, chaves)
passo("Recálculo logo após o cadastro (setas estáveis)", base, chaves)
passo("Passo 1: cadastrar o novo suspeito", base, chaves + [novo])
passo("Passo 2: evidência fraca ligada ao novo suspeito", base + [D["demonstracao"]["evidencia_1"]], chaves + [novo])
S, E = passo("Passo 3: evidência forte ligada a outro suspeito", base + [D["demonstracao"]["evidencia_1"], D["demonstracao"]["evidencia_2"]], chaves + [novo])
print("\nPróximas ações sugeridas no fim da demonstração:")
acoes(S, E)
