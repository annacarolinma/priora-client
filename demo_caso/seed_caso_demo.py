"""Carrega o caso de demonstração (pronto, não concluído) no Priora pela API.

Cria o caso, 4 suspeitos, 17 evidências e o quadro investigativo, e recalcula o ranking.
NÃO cadastra o que será feito ao vivo (novo suspeito, evidência 18, evidência 19 e perfil estimado).

Uso:
    python seed_caso_demo.py --dry-run                      # só valida os dados, sem rede
    python seed_caso_demo.py --base-url http://127.0.0.1:8000 --email SEU_EMAIL --senha SUA_SENHA

O e-mail e a senha podem vir também das variáveis PRIORA_EMAIL e PRIORA_SENHA.
Atenção: grava no banco para o qual a API aponta (local ou Aura). Confira antes de rodar.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).parent
D = json.loads((AQUI / "caso_demo.json").read_text(encoding="utf-8"))


def validar(server: Path):
    """Valida todos os dados contra os esquemas reais da API (sem rede)."""
    sys.path.insert(0, str(server))
    from app.schemas.case_schema import CreateCaseRequest
    from app.schemas.suspect_schema import CreateSuspectRequest
    from app.schemas.evidence_schema import CreateEvidenceRequest
    from app.schemas.investigation_board_schema import SaveBoardRequest

    CreateCaseRequest(userId="x", **D["caso"])
    ids = {}
    for s in D["suspeitos"] + [D["demonstracao"]["novo_suspeito"]]:
        ids[s["chave"]] = s["chave"]
        CreateSuspectRequest(casoId="x", **{k: v for k, v in s.items() if k != "chave"})
    for e in D["evidencias"] + [D["demonstracao"]["evidencia_1"], D["demonstracao"]["evidencia_2"]]:
        CreateEvidenceRequest(casoId="x", **payload_evidencia(e, ids))
    SaveBoardRequest(**D["quadro"])
    print(f"Dados válidos: {len(D['suspeitos'])} suspeitos, {len(D['evidencias'])} evidências, "
          f"{len(D['quadro']['nodes'])} elementos no quadro.")


def payload_evidencia(e, ids):
    return dict(
        nome=e["nome"], tipo=e["tipo"], status=e["status"], descricao=e["descricao"], fonte=e["fonte"],
        dataColeta=e["dataColeta"], peso=e["peso"],
        vinculos=[dict(suspeitoId=ids[v["suspeito"]], pesoVinculo=v["pesoVinculo"], efeito=v["efeito"]) for v in e["vinculos"]],
    )


class Api:
    def __init__(self, base):
        self.base, self.token = base.rstrip("/"), None

    def call(self, metodo, caminho, corpo=None):
        cab = {"Content-Type": "application/json"}
        if self.token:
            cab["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(self.base + caminho, data=json.dumps(corpo).encode() if corpo is not None else None, headers=cab, method=metodo)
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            sys.exit(f"Erro {e.code} em {metodo} {caminho}: {e.read().decode()[:300]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--email", default=os.environ.get("PRIORA_EMAIL"))
    ap.add_argument("--senha", default=os.environ.get("PRIORA_SENHA"))
    ap.add_argument("--server", default=r"C:\Users\laisa\OneDrive\Desktop\Projetos\priora_server", help="pasta do priora_server (usada na validação)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    validar(Path(a.server))
    if a.dry_run:
        return
    if not (a.email and a.senha):
        sys.exit("Informe --email e --senha (ou PRIORA_EMAIL e PRIORA_SENHA).")

    api = Api(a.base_url)
    login = api.call("POST", "/users/login", {"email": a.email, "senha": a.senha})
    api.token, uid = login["token"], login["user"]["id"]

    caso = api.call("POST", "/cases/", dict(userId=uid, **D["caso"]))
    cid = caso["id"]
    print("Caso criado:", cid)

    ids = {}
    for s in D["suspeitos"]:
        r = api.call("POST", "/suspects/", dict(casoId=cid, **{k: v for k, v in s.items() if k != "chave"}))
        ids[s["chave"]] = r["id"]
        print("  suspeito:", s["nome"])
    for e in D["evidencias"]:
        api.call("POST", "/evidences/", dict(casoId=cid, **payload_evidencia(e, ids)))
        print("  evidência:", e["nome"])

    api.call("POST", f"/bayes/preview/{cid}")            # recalcula: as setas de tendência ficam estáveis
    api.call("GET", f"/priority-actions/case/{cid}")      # gera as ações sugeridas
    api.call("PUT", f"/cases/{cid}/board", D["quadro"])   # quadro investigativo já desenhado
    print("\nPronto. Abra o caso 'Furto na Joalheria Meridiana' no Priora.")


if __name__ == "__main__":
    main()
