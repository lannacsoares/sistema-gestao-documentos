from datetime import datetime, timedelta, timezone

import pytest

from app.erros import ErroApi
from app.validadores import (
    MB,
    dias_restantes,
    lixeira_vencida,
    validar_comentario,
    validar_conteudo,
    validar_cota,
    validar_tamanho,
    validar_tipo,
    validar_titulo,
)

LIMITE = 10 * MB


def codigo(funcao, *args, **kwargs):
    """Executa e devolve o código do erro levantado (ou None se passou)."""
    try:
        funcao(*args, **kwargs)
    except ErroApi as e:
        return e.codigo
    return None


# --- título ---
def test_titulo_valido_remove_espacos():
    assert validar_titulo("  Contrato  ") == "Contrato"


@pytest.mark.parametrize("titulo", ["", "   ", "x" * 201])
def test_titulo_invalido(titulo):
    assert codigo(validar_titulo, titulo) == "TITULO_INVALIDO"


def test_titulo_no_limite():
    assert len(validar_titulo("x" * 200)) == 200


# --- tamanho ---
@pytest.mark.parametrize("tamanho,esperado", [
    (0, "ARQUIVO_VAZIO"),
    (1, None),
    (LIMITE, None),
    (LIMITE + 1, "TAMANHO_EXCEDIDO"),
])
def test_tamanho(tamanho, esperado):
    assert codigo(validar_tamanho, tamanho, LIMITE) == esperado


def test_mensagem_de_tamanho_informa_mb():
    with pytest.raises(ErroApi) as e:
        validar_tamanho(14 * MB, LIMITE)
    assert e.value.mensagem == "O arquivo tem 14 MB; o limite é 10 MB."
    assert e.value.status == 413


# --- tipo e extensão ---
@pytest.mark.parametrize("mime,nome,esperado", [
    ("application/pdf", "a.pdf", "pdf"),
    ("application/pdf", "A.PDF", "pdf"),
    ("image/jpeg", "foto.jpg", "jpg"),
    ("image/jpeg", "foto.jpeg", "jpg"),
    ("image/png", "img.png", "png"),
])
def test_tipo_coerente(mime, nome, esperado):
    assert validar_tipo(mime, nome) == esperado


@pytest.mark.parametrize("mime,nome", [
    ("image/png", "a.pdf"),
    ("application/pdf", "a.png"),
    ("application/pdf", "semextensao"),
    ("text/plain", "a.txt"),
    ("application/zip", "a.pdf"),
    ("", ""),
])
def test_tipo_incoerente(mime, nome):
    assert codigo(validar_tipo, mime, nome) == "TIPO_NAO_PERMITIDO"


# --- conteúdo real (magic bytes) ---
@pytest.mark.parametrize("tipo,inicio", [
    ("pdf", b"%PDF-1.7\n"),
    ("png", b"\x89PNG\r\n\x1a\n\x00\x00"),
    ("jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF"),
])
def test_conteudo_valido(tipo, inicio):
    assert codigo(validar_conteudo, tipo, inicio) is None


@pytest.mark.parametrize("tipo,inicio", [
    ("pdf", b"Isto e apenas texto renomeado"),
    ("pdf", b""),
    ("png", b"%PDF-1.7"),
    ("jpg", b"\x89PNG\r\n\x1a\n"),
])
def test_conteudo_falso(tipo, inicio):
    assert codigo(validar_conteudo, tipo, inicio) == "ARQUIVO_INVALIDO"


# --- cota ---
def test_cota_exatamente_no_limite():
    assert codigo(validar_cota, 900 * MB - 5, 5, 900 * MB) is None


def test_cota_um_byte_acima():
    assert codigo(validar_cota, 900 * MB - 5, 6, 900 * MB) == "SEM_ESPACO"


def test_cota_informa_quanto_falta():
    with pytest.raises(ErroApi) as e:
        validar_cota(895 * MB, 10 * MB, 900 * MB)
    assert "faltam 5 MB" in e.value.mensagem
    assert e.value.status == 507


# --- comentário ---
def test_comentario_valido_e_autor_vazio_vira_none():
    assert validar_comentario("  Olá ", "  ") == ("Olá", None)


@pytest.mark.parametrize("texto,autor,esperado", [
    ("", None, "COMENTARIO_INVALIDO"),
    ("   ", None, "COMENTARIO_INVALIDO"),
    ("x" * 2001, None, "COMENTARIO_INVALIDO"),
    ("ok", "a" * 81, "AUTOR_INVALIDO"),
    ("x" * 2000, "a" * 80, None),
])
def test_comentario(texto, autor, esperado):
    assert codigo(validar_comentario, texto, autor) == esperado


# --- lixeira ---
AGORA = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)


def test_dias_restantes():
    assert dias_restantes(AGORA, AGORA, 30) == 30
    assert dias_restantes(AGORA - timedelta(days=29, hours=1), AGORA, 30) == 1
    assert dias_restantes(AGORA - timedelta(days=45), AGORA, 30) == 0


def test_lixeira_vencida():
    assert not lixeira_vencida(AGORA - timedelta(days=29), AGORA, 30)
    assert lixeira_vencida(AGORA - timedelta(days=30), AGORA, 30)
