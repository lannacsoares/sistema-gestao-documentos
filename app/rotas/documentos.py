"""Upload em duas etapas, listagem, link temporário e envio para a lixeira."""
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Query

from app import config, servicos, storage, validadores
from app.erros import ErroApi, erro
from app.schemas import IniciarUpload

router = APIRouter(prefix="/api/documentos", tags=["documentos"])


@router.post("", status_code=201)
def iniciar_upload(dados: IniciarUpload):
    """Etapa 1: valida os metadados, cria o registro `pendente` e devolve a URL assinada de upload."""
    titulo = validadores.validar_titulo(dados.titulo)
    validadores.validar_tamanho(dados.tamanho_bytes)
    tipo_arquivo = validadores.validar_tipo(dados.tipo_mime, dados.nome_original)

    servicos.descartar_pendentes_vencidos()
    validadores.validar_cota(servicos.uso_atual_bytes(), dados.tamanho_bytes)

    # Nome gerado no Storage; o nome original fica só no banco.
    caminho = f"{uuid4()}.{tipo_arquivo}"
    descricao = (dados.descricao or "").strip() or None
    linha = servicos.executar(
        servicos.tabela("documentos").insert(
            {
                "titulo": titulo,
                "descricao": descricao,
                "nome_original": dados.nome_original,
                "tipo_arquivo": tipo_arquivo,
                "tamanho_bytes": dados.tamanho_bytes,
                "caminho_arquivo": caminho,
                "status": "pendente",
            }
        )
    ).data[0]

    try:
        upload = storage.criar_url_upload(caminho)
    except ErroApi:
        # Não deixa registro pela metade se não foi possível preparar o envio.
        servicos.executar(servicos.tabela("documentos").delete().eq("id", linha["id"]))
        raise
    return {"id": linha["id"], "upload": upload}


@router.post("/{documento_id}/confirmar")
def confirmar_upload(documento_id: UUID):
    """Etapa 2: confere o arquivo enviado (existência, tamanho e conteúdo real) e ativa o documento."""
    documento = servicos.obter_documento(documento_id)
    if documento["status"] == "ativo":
        return servicos.documento_publico(documento)  # idempotente
    servicos.exigir_status(documento, "pendente")

    caminho = documento["caminho_arquivo"]
    tamanho_real = storage.tamanho_objeto(caminho)
    try:
        if tamanho_real is None:
            raise erro("ENVIO_INCOMPLETO")
        if tamanho_real != documento["tamanho_bytes"]:
            validadores.validar_tamanho(tamanho_real)  # acima do limite: mensagem de tamanho
            raise erro("ARQUIVO_INVALIDO")  # tamanho diferente do informado
        validadores.validar_conteudo(
            documento["tipo_arquivo"], storage.ler_primeiros_bytes(caminho, validadores.TAMANHO_ASSINATURA)
        )
    except ErroApi as e:
        if e.codigo != "ARMAZENAMENTO_INDISPONIVEL":
            _descartar(documento)
        raise

    ativo = servicos.executar(
        servicos.tabela("documentos").update({"status": "ativo"}).eq("id", documento["id"])
    ).data[0]
    return servicos.documento_publico(ativo)


def _descartar(documento: dict) -> None:
    """Remove objeto e linha de um upload reprovado (nunca deixa registro pela metade)."""
    try:
        storage.remover([documento["caminho_arquivo"]])
    except ErroApi:
        return  # a limpeza de pendentes vencidos remove depois
    servicos.executar(servicos.tabela("documentos").delete().eq("id", documento["id"]))


@router.get("")
def listar():
    """Documentos ativos, mais recentes primeiro."""
    linhas = servicos.executar(
        servicos.tabela("documentos")
        .select("*, comentarios(count)")
        .eq("status", "ativo")
        .order("data_upload", desc=True)
    ).data
    return [{**servicos.documento_publico(d), "total_comentarios": servicos.total_comentarios(d)} for d in linhas]


@router.get("/{documento_id}/link")
def gerar_link(documento_id: UUID, modo: Literal["visualizar", "baixar"] = Query("visualizar")):
    """Link temporário (visualizar no navegador ou baixar com o nome original)."""
    documento = servicos.obter_documento(documento_id)
    servicos.exigir_status(documento, "ativo")
    baixar_como = documento["nome_original"] if modo == "baixar" else None
    url = storage.criar_url_leitura(documento["caminho_arquivo"], baixar_como)
    return {"url": url, "expira_em_s": config.SIGNED_URL_TTL_S}

