"""Acesso ao banco e regras compartilhadas entre as rotas."""
import logging
from datetime import datetime, timedelta, timezone

from app import config, storage
from app.db import obter_cliente
from app.erros import ErroApi, erro

log = logging.getLogger("app.servicos")


def agora() -> datetime:
    return datetime.now(timezone.utc)


def executar(consulta):
    """Executa uma consulta do Supabase; falhas de rede/banco viram BANCO_INDISPONIVEL."""
    try:
        return consulta.execute()
    except ErroApi:
        raise
    except Exception as exc:
        # Só o tipo vai para o log: a mensagem crua pode trazer detalhes internos.
        log.error("Falha no banco: %s", type(exc).__name__)
        raise erro("BANCO_INDISPONIVEL") from None


def tabela(nome: str):
    return obter_cliente().table(nome)


def obter_documento(documento_id) -> dict:
    """Busca o documento pelo id ou levanta NAO_ENCONTRADO."""
    linhas = executar(tabela("documentos").select("*").eq("id", str(documento_id))).data
    if not linhas:
        raise erro("NAO_ENCONTRADO")
    return linhas[0]


def exigir_status(documento: dict, *permitidos: str) -> None:
    """Garante o estado do documento. Pendente nunca é visível; lixeira vira ESTADO_INVALIDO."""
    status = documento["status"]
    if status in permitidos:
        return
    if status == "pendente":
        raise erro("NAO_ENCONTRADO")
    raise erro("ESTADO_INVALIDO")


def uso_atual_bytes() -> int:
    """Soma de documentos ativos + lixeira (função SQL uso_armazenamento_bytes)."""
    resposta = executar(obter_cliente().rpc("uso_armazenamento_bytes"))
    return int(resposta.data or 0)


def descartar_pendentes_vencidos() -> None:
    """Apaga (objeto e linha) uploads que nunca foram confirmados dentro de PENDING_TTL_MIN."""
    limite = (agora() - timedelta(minutes=config.PENDING_TTL_MIN)).isoformat()
    vencidos = executar(
        tabela("documentos").select("id,caminho_arquivo").eq("status", "pendente").lt("data_upload", limite)
    ).data
    if not vencidos:
        return
    try:
        storage.remover([d["caminho_arquivo"] for d in vencidos])
    except ErroApi:
        return  # sem acesso ao Storage agora: mantém as linhas e tenta na próxima vez
    executar(tabela("documentos").delete().in_("id", [d["id"] for d in vencidos]))


def documento_publico(d: dict) -> dict:
    """Campos do documento expostos pela API (nunca o caminho interno no Storage)."""
    return {
        "id": d["id"],
        "titulo": d["titulo"],
        "descricao": d["descricao"],
        "nome_original": d["nome_original"],
        "tipo_arquivo": d["tipo_arquivo"],
        "tamanho_bytes": d["tamanho_bytes"],
        "data_upload": d["data_upload"],
    }


def total_comentarios(d: dict) -> int:
    """Lê o total da contagem embutida (`comentarios(count)`) numa consulta com relacionamento."""
    contagem = d.get("comentarios") or [{"count": 0}]
    return int(contagem[0]["count"])
