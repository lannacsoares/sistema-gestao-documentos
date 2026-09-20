"""Testa pela API pública os casos de borda que não dependem do navegador (CB01 a CB06).

Uso: python scripts/testar_deploy.py [URL_BASE]
Cria documentos marcados "TESTE-BORDA" e os apaga definitivamente no fim. Precisa de exemplos/
(rode antes scripts/gerar_exemplos.py). Imprime uma linha por verificação: OK ou FALHOU.
"""
import sys
from pathlib import Path
from urllib.parse import unquote

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://sistema-gestao-documentos.onrender.com").rstrip("/")
API = f"{BASE}/api"
EX = Path(__file__).resolve().parent.parent / "exemplos"
MB = 1024 * 1024
c = httpx.Client(timeout=180)
criados: list[str] = []
falhas = 0


def verificar(nome: str, condicao: bool, detalhe: str = "") -> None:
    global falhas
    falhas += 0 if condicao else 1
    print(f"{'OK    ' if condicao else 'FALHOU'} {nome}" + (f"  [{detalhe}]" if detalhe else ""))


def iniciar(titulo, nome, mime, tamanho):
    return c.post(f"{API}/documentos", json={"titulo": f"TESTE-BORDA {titulo}", "descricao": None,
                                            "nome_original": nome, "tipo_mime": mime, "tamanho_bytes": tamanho})


def codigo(r):
    try:
        return r.json()["erro"]["codigo"]
    except Exception:
        return f"sem-erro({r.status_code})"


def enviar_completo(titulo, arquivo: Path, mime, nome=None):
    """Fluxo em 3 etapas. Devolve (id, resposta_da_confirmacao)."""
    dados = arquivo.read_bytes()
    r = iniciar(titulo, nome or arquivo.name, mime, len(dados))
    assert r.status_code == 201, f"iniciar falhou: {r.status_code} {r.text}"
    j = r.json()
    criados.append(j["id"])
    p = c.put(j["upload"]["url_assinada"], content=dados, headers={"Content-Type": mime})
    assert p.status_code == 200, f"PUT falhou: {p.status_code}"
    return j["id"], c.post(f"{API}/documentos/{j['id']}/confirmar")


def limpar():
    for id_ in criados:
        c.delete(f"{API}/documentos/{id_}")  # pode estar pendente ou já na lixeira: ignora o resultado
        c.delete(f"{API}/documentos/{id_}/definitivo")


def main():
    print(f"Testando {BASE}\n")
    verificar("saúde", c.get(f"{API}/saude").json().get("status") == "ok")

    # --- CB01 tamanho ---
    r = iniciar("grande", "grande.png", "image/png", 11 * MB)
    verificar("CB01 API recusa 11 MB (TAMANHO_EXCEDIDO/413)", codigo(r) == "TAMANHO_EXCEDIDO" and r.status_code == 413, f"{r.status_code} {codigo(r)}")
    r = iniciar("grande", "grande.png", "image/png", 10 * MB + 1)
    verificar("CB01 API recusa 10 MB + 1 byte", codigo(r) == "TAMANHO_EXCEDIDO", codigo(r))

    r = iniciar("bucket", "pequeno.pdf", "application/pdf", 1000)  # declara pouco, envia muito
    j = r.json()
    criados.append(j["id"])
    p = c.put(j["upload"]["url_assinada"], content=b"%PDF-1.4\n" + b"x" * (11 * MB), headers={"Content-Type": "application/pdf"})
    verificar("CB01 bucket recusa upload de 11 MB (3ª camada)", p.status_code >= 400, f"PUT {p.status_code}")
    r = c.post(f"{API}/documentos/{j['id']}/confirmar")
    verificar("CB01 confirmar não aceita o envio recusado", r.status_code >= 400, f"{r.status_code} {codigo(r)}")

    id10, r = enviar_completo("exatamente 10 MB", EX / "exatamente_10mb.pdf", "application/pdf")
    verificar("CB01 arquivo de exatamente 10 MB é aceito", r.status_code == 200, f"{r.status_code} {codigo(r)}")

    # --- CB02 tipos ---
    r = iniciar("txt", "nao_permitido.txt", "text/plain", 30)
    verificar("CB02 .txt recusado", r.status_code >= 400, f"{r.status_code} {codigo(r)}")
    r = iniciar("docx", "nao_permitido.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 50)
    verificar("CB02 .docx recusado", r.status_code >= 400, f"{r.status_code} {codigo(r)}")
    r = iniciar("vazio", "vazio.pdf", "application/pdf", 0)
    verificar("CB02 arquivo vazio recusado", r.status_code >= 400, f"{r.status_code} {codigo(r)}")
    id_falso, r = enviar_completo("falso", EX / "falso.pdf", "application/pdf")
    verificar("CB02 falso.pdf recusado na confirmação (conteúdo real)", r.status_code >= 400, f"{r.status_code} {codigo(r)}")
    lista = c.get(f"{API}/documentos").json()
    verificar("CB02/CB03 falso.pdf não ficou na lista", id_falso not in [d["id"] for d in lista])

    acento = EX / "nome com acento e símbolos (1).pdf"
    id_ac, r = enviar_completo("nome com acento", acento, "application/pdf")
    verificar("CB02 nome com acento/símbolos aceito", r.status_code == 200, f"{r.status_code} {codigo(r)}")
    doc = next((d for d in c.get(f"{API}/documentos").json() if d["id"] == id_ac), {})
    verificar("CB02 nome original guardado no banco", doc.get("nome_original") == acento.name, doc.get("nome_original", ""))
    link = c.get(f"{API}/documentos/{id_ac}/link", params={"modo": "baixar"}).json()["url"]
    baixado = c.get(link)
    disp = baixado.headers.get("content-disposition", "")
    nome_baixado = unquote(disp.split("filename*=UTF-8''")[-1])
    verificar("CB02 download devolve o nome original", nome_baixado == acento.name, nome_baixado)
    verificar("CB02 objeto no Storage tem nome UUID (não o original)", "acento" not in link.split("?")[0], link.split("?")[0].rsplit("/", 1)[-1])

    # Duplicado: dois registros independentes
    id_d1, r1 = enviar_completo("duplicado", EX / "procuracao_ficticia.pdf", "application/pdf")
    id_d2, r2 = enviar_completo("duplicado", EX / "procuracao_ficticia.pdf", "application/pdf")
    verificar("Duplicado: aceito como dois registros independentes", r1.status_code == 200 and r2.status_code == 200 and id_d1 != id_d2)

    # --- CB05 / CB06 comentário, lixeira, restauração ---
    r = c.post(f"{API}/documentos/{id_d1}/comentarios", json={"texto": "primeiro"})
    r2_ = c.post(f"{API}/documentos/{id_d1}/comentarios", json={"texto": "segundo"})
    verificar("Comentários criados com data e hora", r.status_code == 201 and "T" in r.json().get("data_hora", ""))
    verificar("Comentário vazio recusado", c.post(f"{API}/documentos/{id_d1}/comentarios", json={"texto": "   "}).status_code >= 400)
    verificar("Comentário em documento inexistente recusado", c.post(f"{API}/documentos/00000000-0000-0000-0000-000000000000/comentarios", json={"texto": "x"}).status_code >= 400)

    verificar("CB05 excluir manda para a lixeira", c.delete(f"{API}/documentos/{id_d1}").status_code == 204)
    r = c.post(f"{API}/documentos/{id_d1}/comentarios", json={"texto": "na lixeira"})
    verificar("CB05 lixeira não aceita comentário (DOCUMENTO_EXCLUIDO)", codigo(r) == "DOCUMENTO_EXCLUIDO", f"{r.status_code} {codigo(r)}")
    item = next((d for d in c.get(f"{API}/lixeira").json() if d["id"] == id_d1), {})
    verificar("CB05 lixeira informa a quantidade de comentários (2)", item.get("total_comentarios") == 2, str(item.get("total_comentarios")))
    verificar("CB06 lixeira informa dias restantes (30)", item.get("dias_restantes") == 30, str(item.get("dias_restantes")))
    verificar("CB05 comentários continuam legíveis na lixeira", len(c.get(f"{API}/documentos/{id_d1}/comentarios").json()) == 2)

    verificar("CB06 restaurar devolve à lista", c.post(f"{API}/documentos/{id_d1}/restaurar").status_code == 200
              and id_d1 in [d["id"] for d in c.get(f"{API}/documentos").json()])
    verificar("CB06 restaurado mantém os comentários", len(c.get(f"{API}/documentos/{id_d1}/comentarios").json()) == 2)

    verificar("Exclusão definitiva exige passar pela lixeira", c.delete(f"{API}/documentos/{id_d1}/definitivo").status_code >= 400)
    c.delete(f"{API}/documentos/{id_d1}")
    verificar("CB05 exclusão definitiva", c.delete(f"{API}/documentos/{id_d1}/definitivo").status_code == 204)
    verificar("CB05 comentários somem junto (cascata)", c.get(f"{API}/documentos/{id_d1}/comentarios").status_code == 404)
    r = c.get(f"{API}/documentos/{id_d1}/link", params={"modo": "visualizar"})
    verificar("CB05 arquivo some do Storage (link recusado)", r.status_code >= 400, f"{r.status_code} {codigo(r)}")

    # --- CB04 (parte que não altera a cota) ---
    uso = c.get(f"{API}/armazenamento")
    verificar("CB04 rota de armazenamento responde", uso.status_code == 200, uso.text[:120])

    limpar()
    resto = [d["titulo"] for d in c.get(f"{API}/documentos").json() + c.get(f"{API}/lixeira").json() if d["titulo"].startswith("TESTE-BORDA")]
    verificar("Limpeza: nenhum documento de teste sobrou", not resto, str(resto))
    print(f"\n{'TUDO OK' if not falhas else f'{falhas} verificação(ões) FALHOU'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    try:
        main()
    finally:
        limpar()
