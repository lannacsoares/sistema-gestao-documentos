"""Popula (ou repopula) o sistema com documentos de exemplo e comentários.

Uso, na raiz do projeto, com o .env apontando para o Supabase do deploy:
    python scripts/gerar_exemplos.py     # cria os arquivos fictícios em exemplos/
    python scripts/seed.py

Passa pelas mesmas validações da API (validadores.py) e envia os arquivos pelo servidor.
É idempotente: o título identifica cada exemplo. Se ele já existe, não duplica; se foi excluído de vez,
é recriado. Os exemplos públicos ficam na lista (se um visitante os mandou para a lixeira, são
restaurados). Os documentos fictícios de teste ficam na lixeira, para demonstrar a Lixeira.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
load_dotenv(RAIZ / ".env")

from app import servicos, storage, validadores  # noqa: E402  (depois do .env)
from app.erros import ErroApi  # noqa: E402

EXEMPLOS = RAIZ / "exemplos"
LIMITE_SEED = 2 * 1024 * 1024  # cada exemplo tem até 2 MB
MIMES = {"pdf": "application/pdf", "jpg": "image/jpeg", "png": "image/png"}

# (arquivo, título, descrição, dias atrás, comentários [(texto, autor)])
FICTICIOS = [
    ("procuracao_ficticia.pdf", "Procuração (fictícia)", "Modelo de procuração com dados inventados. DOCUMENTO FICTÍCIO.", 9,
     [("Conferir se os poderes especiais estão descritos.", "Equipe jurídica"), ("Vigência de 12 meses, renovar em setembro.", None)]),
    ("laudo_ficticio.pdf", "Laudo técnico (fictício)", "Laudo de vistoria inventado para demonstração. DOCUMENTO FICTÍCIO.", 7,
     [("Anexar as fotografias da vistoria antes do protocolo.", "Ana")]),
    ("comprovante_ficticio.png", "Comprovante em imagem PNG (fictício)", "Imagem de teste em formato PNG. DOCUMENTO FICTÍCIO.", 5,
     [("Imagem legível, pode seguir para o arquivo.", None), ("Guardar também em PDF.", "Bruno")]),
    ("comprovante_ficticio.jpg", "Comprovante em imagem JPG (fictício)", "Imagem de teste em formato JPG. DOCUMENTO FICTÍCIO.", 4,
     [("Mesmo conteúdo da versão PNG.", None)]),
]
DESCRICAO_PUBLICA = "Documento público da Câmara dos Deputados. Origem e data de acesso em exemplos/publicos/ORIGEM.md."
COMENTARIOS_PUBLICOS = [("Texto público, útil como exemplo de leitura e comentários.", "Equipe jurídica"), ("Revisar a tramitação atual antes de citar.", None)]


def _lista_de_exemplos():
    itens = [(EXEMPLOS / nome, *resto) for nome, *resto in FICTICIOS]
    for i, arquivo in enumerate(sorted((EXEMPLOS / "publicos").glob("*.pdf"))):
        titulo = "Proposição pública: " + arquivo.stem.replace("_", " ")
        itens.append((arquivo, titulo, DESCRICAO_PUBLICA, 12 + i, COMENTARIOS_PUBLICOS))
    return itens


def _existente(titulo: str):
    linhas = servicos.executar(
        servicos.tabela("documentos").select("id,status").eq("titulo", titulo).in_("status", ["ativo", "lixeira"])
    ).data
    return linhas[0] if linhas else None


def _mudar_status(id_: str, status: str) -> None:
    dados = {"status": status, "data_exclusao": datetime.now(timezone.utc).isoformat() if status == "lixeira" else None}
    servicos.executar(servicos.tabela("documentos").update(dados).eq("id", id_))


def _criar(arquivo: Path, titulo: str, descricao: str, dias: int, comentarios) -> None:
    dados = arquivo.read_bytes()
    if len(dados) > LIMITE_SEED:
        raise SystemExit(f"{arquivo.name} tem mais de 2 MB: escolha um arquivo menor.")
    mime = MIMES[arquivo.suffix.lstrip(".").lower().replace("jpeg", "jpg")]
    # Mesmas validações da API, sem atalhos.
    validadores.validar_titulo(titulo)
    validadores.validar_tamanho(len(dados))
    tipo = validadores.validar_tipo(mime, arquivo.name)
    validadores.validar_conteudo(tipo, dados[: validadores.TAMANHO_ASSINATURA])
    validadores.validar_cota(servicos.uso_atual_bytes(), len(dados))

    caminho = f"{uuid4()}.{tipo}"
    data_upload = datetime.now(timezone.utc) - timedelta(days=dias)
    storage._bucket().upload(caminho, dados, {"content-type": mime})
    try:
        linha = servicos.executar(servicos.tabela("documentos").insert({
            "titulo": titulo, "descricao": descricao, "nome_original": arquivo.name, "tipo_arquivo": tipo,
            "tamanho_bytes": len(dados), "caminho_arquivo": caminho, "status": "ativo",
            "data_upload": data_upload.isoformat(),
        })).data[0]
    except Exception:
        storage.remover([caminho])  # não deixa arquivo sem registro
        raise
    for i, (texto, autor) in enumerate(comentarios):
        texto, autor = validadores.validar_comentario(texto, autor)
        quando = data_upload + timedelta(hours=3 + 5 * i)  # sempre depois do envio
        servicos.executar(servicos.tabela("comentarios").insert(
            {"documento_id": linha["id"], "texto": texto, "autor": autor, "data_hora": quando.isoformat()}))


def main() -> None:
    for arquivo, titulo, descricao, dias, comentarios in _lista_de_exemplos():
        fictício = arquivo.parent == EXEMPLOS  # os fictícios ficam na lixeira; os públicos, na lista
        if not arquivo.exists():
            print(f"PULADO   {titulo}: {arquivo.name} não existe (rode scripts/gerar_exemplos.py)")
            continue
        atual = _existente(titulo)
        if atual is None:
            try:
                _criar(arquivo, titulo, descricao, dias, comentarios)
            except ErroApi as e:
                raise SystemExit(f"FALHOU   {titulo}: {e.codigo}") from None
            print(f"CRIADO   {titulo}")
            atual = _existente(titulo)
        elif fictício and atual["status"] == "lixeira" or not fictício and atual["status"] == "ativo":
            print(f"JÁ EXISTE {titulo}")
            continue
        if fictício and atual["status"] == "ativo":
            _mudar_status(atual["id"], "lixeira")
            print(f"  -> enviado para a lixeira")
        elif not fictício and atual["status"] == "lixeira":
            _mudar_status(atual["id"], "ativo")
            print(f"RESTAURADO {titulo}")


if __name__ == "__main__":
    main()
