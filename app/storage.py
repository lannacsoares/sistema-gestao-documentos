"""Operações no Supabase Storage (bucket privado). Falhas viram ARMAZENAMENTO_INDISPONIVEL."""
import logging

import httpx

from app import config
from app.db import obter_cliente
from app.erros import ErroApi, erro

log = logging.getLogger("app.storage")


def _bucket():
    return obter_cliente().storage.from_(config.SUPABASE_BUCKET)


def _indisponivel(operacao: str, exc: Exception) -> ErroApi:
    # Só o tipo da exceção vai para o log: a mensagem crua pode conter URLs assinadas.
    log.error("Falha no Storage (%s): %s", operacao, type(exc).__name__)
    return erro("ARMAZENAMENTO_INDISPONIVEL")


def criar_url_upload(caminho: str) -> dict:
    """URL assinada para o navegador enviar o arquivo direto ao Storage (PUT)."""
    try:
        r = _bucket().create_signed_upload_url(caminho)
    except Exception as exc:
        raise _indisponivel("url de upload", exc) from None
    return {"caminho": r["path"], "url_assinada": r["signed_url"], "token": r["token"]}


def criar_url_leitura(caminho: str, baixar_como: str | None = None) -> str:
    """URL temporária para visualizar; com `baixar_como`, força o download com esse nome."""
    opcoes = {"download": baixar_como} if baixar_como else None
    try:
        r = _bucket().create_signed_url(caminho, config.SIGNED_URL_TTL_S, opcoes)
    except Exception as exc:
        raise _indisponivel("url de leitura", exc) from None
    return r["signedURL"]


def tamanho_objeto(caminho: str) -> int | None:
    """Tamanho real em bytes, ou None se o objeto não existe."""
    try:
        if not _bucket().exists(caminho):
            return None
        return int(_bucket().info(caminho)["size"])
    except Exception as exc:
        raise _indisponivel("consulta do objeto", exc) from None


def ler_primeiros_bytes(caminho: str, quantidade: int = 16) -> bytes:
    """Lê só o início do objeto (Range), sem baixar o arquivo inteiro."""
    url = criar_url_leitura(caminho)
    try:
        resposta = httpx.get(url, headers={"Range": f"bytes=0-{quantidade - 1}"}, timeout=15)
        resposta.raise_for_status()
    except Exception as exc:
        raise _indisponivel("leitura do início do objeto", exc) from None
    return resposta.content[:quantidade]


def remover(caminhos: list[str]) -> None:
    """Remove objetos. Objeto que já não existe não é erro."""
    if not caminhos:
        return
    try:
        _bucket().remove(caminhos)
    except Exception as exc:
        raise _indisponivel("remoção", exc) from None
