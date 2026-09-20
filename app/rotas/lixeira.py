"""Lixeira: listar (com limpeza automática), restaurar e excluir definitivamente (CB06)."""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Response

from app import config, servicos, storage, validadores
from app.erros import ErroApi

router = APIRouter(prefix="/api", tags=["lixeira"])


def limpar_lixeira_vencida() -> None:
    """Apaga de vez (objeto e linha) o que está na lixeira há mais de TRASH_DAYS. Comentários vão em cascata."""
    limite = (servicos.agora() - timedelta(days=config.TRASH_DAYS)).isoformat()
    vencidos = servicos.executar(
        servicos.tabela("documentos").select("id,caminho_arquivo").eq("status", "lixeira").lt("data_exclusao", limite)
    ).data
    if not vencidos:
        return
    try:
        storage.remover([d["caminho_arquivo"] for d in vencidos])
    except ErroApi:
        return  # sem acesso ao Storage agora: mantém tudo e tenta na próxima abertura
    servicos.executar(servicos.tabela("documentos").delete().in_("id", [d["id"] for d in vencidos]))


@router.get("/lixeira")
def listar_lixeira():
    """Limpa o que venceu e lista o restante, do excluído mais recentemente ao mais antigo."""
    limpar_lixeira_vencida()
    linhas = servicos.executar(
        servicos.tabela("documentos")
        .select("id,titulo,tipo_arquivo,tamanho_bytes,data_exclusao,comentarios(count)")
        .eq("status", "lixeira")
        .order("data_exclusao", desc=True)
    ).data
    return [
        {
            "id": d["id"],
            "titulo": d["titulo"],
            "tipo_arquivo": d["tipo_arquivo"],
            "tamanho_bytes": d["tamanho_bytes"],
            "data_exclusao": d["data_exclusao"],
            "dias_restantes": validadores.dias_restantes(datetime.fromisoformat(d["data_exclusao"])),
            "total_comentarios": servicos.total_comentarios(d),
        }
        for d in linhas
    ]


@router.post("/documentos/{documento_id}/restaurar")
def restaurar(documento_id: UUID):
    """Volta para os ativos. Os comentários continuam vinculados; a cota não muda (já contava)."""
    documento = servicos.obter_documento(documento_id)
    servicos.exigir_status(documento, "lixeira")
    restaurado = servicos.executar(
        servicos.tabela("documentos").update({"status": "ativo", "data_exclusao": None}).eq("id", documento["id"])
    ).data[0]
    return servicos.documento_publico(restaurado)


@router.delete("/documentos/{documento_id}/definitivo", status_code=204)
def excluir_definitivo(documento_id: UUID):
    """Apaga o arquivo primeiro e só então a linha (comentários somem em cascata).
    Se o Storage falhar, a linha fica na lixeira para nova tentativa."""
    documento = servicos.obter_documento(documento_id)
    servicos.exigir_status(documento, "lixeira")
    storage.remover([documento["caminho_arquivo"]])
    servicos.executar(servicos.tabela("documentos").delete().eq("id", documento["id"]))
    return Response(status_code=204)
