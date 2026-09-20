"""Validações puras (sem rede nem banco), fáceis de testar. Levantam ErroApi."""
from datetime import datetime, timedelta, timezone

from app import config
from app.erros import erro

MB = 1024 * 1024

# tipo_mime aceito -> (tipo_arquivo gravado no banco, extensões coerentes)
TIPOS = {
    "application/pdf": ("pdf", {"pdf"}),
    "image/jpeg": ("jpg", {"jpg", "jpeg"}),
    "image/png": ("png", {"png"}),
}

# Assinaturas dos primeiros bytes (conteúdo real do arquivo)
ASSINATURAS = {
    "pdf": b"%PDF-",
    "jpg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
}
TAMANHO_ASSINATURA = 8


def validar_titulo(titulo: str) -> str:
    """Devolve o título sem espaços nas pontas; exige de 1 a 200 caracteres."""
    limpo = (titulo or "").strip()
    if not 1 <= len(limpo) <= 200:
        raise erro("TITULO_INVALIDO")
    return limpo


def validar_tamanho(tamanho_bytes: int, limite_bytes: int | None = None) -> None:
    limite = config.MAX_FILE_BYTES if limite_bytes is None else limite_bytes
    if tamanho_bytes <= 0:
        raise erro("ARQUIVO_VAZIO")
    if tamanho_bytes > limite:
        raise erro("TAMANHO_EXCEDIDO", tamanho_mb=_mb(tamanho_bytes), limite_mb=limite // MB)


def validar_tipo(tipo_mime: str, nome_original: str) -> str:
    """Confere o tipo informado e a extensão do nome. Devolve 'pdf', 'jpg' ou 'png'."""
    tipo = TIPOS.get((tipo_mime or "").strip().lower())
    extensao = (nome_original or "").rsplit(".", 1)[-1].lower() if "." in (nome_original or "") else ""
    if tipo is None or extensao not in tipo[1]:
        raise erro("TIPO_NAO_PERMITIDO")
    return tipo[0]


def validar_conteudo(tipo_arquivo: str, primeiros_bytes: bytes) -> None:
    """O início real do arquivo precisa bater com o tipo declarado (barra texto renomeado)."""
    assinatura = ASSINATURAS.get(tipo_arquivo)
    if assinatura is None or not primeiros_bytes.startswith(assinatura):
        raise erro("ARQUIVO_INVALIDO")


def validar_cota(uso_atual_bytes: int, novo_bytes: int, cota_bytes: int | None = None) -> None:
    """CB04: o total (ativos + lixeira) depois do envio não pode passar da cota."""
    cota = config.QUOTA_BYTES if cota_bytes is None else cota_bytes
    excedente = uso_atual_bytes + novo_bytes - cota
    if excedente > 0:
        raise erro("SEM_ESPACO", faltam_mb=max(1, -(-excedente // MB)))


def validar_comentario(texto: str, autor: str | None) -> tuple[str, str | None]:
    """Devolve (texto, autor) limpos. Autor vazio vira None."""
    texto_limpo = (texto or "").strip()
    if not 1 <= len(texto_limpo) <= 2000:
        raise erro("COMENTARIO_INVALIDO")
    autor_limpo = (autor or "").strip() or None
    if autor_limpo is not None and len(autor_limpo) > 80:
        raise erro("AUTOR_INVALIDO")
    return texto_limpo, autor_limpo


def dias_restantes(data_exclusao: datetime, agora: datetime | None = None, dias_lixeira: int | None = None) -> int:
    """Dias que faltam para a limpeza automática da lixeira (nunca negativo)."""
    agora = agora or datetime.now(timezone.utc)
    prazo = config.TRASH_DAYS if dias_lixeira is None else dias_lixeira
    restante = (data_exclusao + timedelta(days=prazo)) - agora
    return max(0, -(-int(restante.total_seconds()) // 86400))


def lixeira_vencida(data_exclusao: datetime, agora: datetime | None = None, dias_lixeira: int | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    prazo = config.TRASH_DAYS if dias_lixeira is None else dias_lixeira
    return agora >= data_exclusao + timedelta(days=prazo)


def _mb(bytes_: int) -> str:
    """Tamanho em MB com 1 casa decimal só quando necessário (14 ou 10,5)."""
    valor = round(bytes_ / MB, 1)
    return str(int(valor)) if valor == int(valor) else str(valor).replace(".", ",")
