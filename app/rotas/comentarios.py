"""Comentários por documento."""
from uuid import UUID

from fastapi import APIRouter

from app import servicos, validadores
from app.erros import erro
from app.schemas import NovoComentario

router = APIRouter(prefix="/api/documentos/{documento_id}/comentarios", tags=["comentários"])

CAMPOS = "id,documento_id,texto,autor,data_hora"


@router.get("")
def listar(documento_id: UUID):
    """Ordem cronológica. Também vale para documentos na lixeira (somente leitura)."""
    documento = servicos.obter_documento(documento_id)
    if documento["status"] == "pendente":
        raise erro("NAO_ENCONTRADO")
    return servicos.executar(
        servicos.tabela("comentarios").select(CAMPOS).eq("documento_id", documento["id"]).order("data_hora")
    ).data


@router.post("", status_code=201)
def incluir(documento_id: UUID, dados: NovoComentario):
    """Grava o comentário com a data e hora do servidor. Documento na lixeira não aceita (CB05)."""
    documento = servicos.obter_documento(documento_id)
    if documento["status"] == "pendente":
        raise erro("NAO_ENCONTRADO")
    if documento["status"] == "lixeira":
        raise erro("DOCUMENTO_EXCLUIDO")
    texto, autor = validadores.validar_comentario(dados.texto, dados.autor)
    return servicos.executar(
        servicos.tabela("comentarios").insert({"documento_id": documento["id"], "texto": texto, "autor": autor})
    ).data[0]
