"""Erros da API no formato padrão: {"erro": {"codigo": "...", "mensagem": "..."}}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# Tabela única de erros: código -> (status HTTP, mensagem padrão em português).
# Mensagens com {chaves} são preenchidas por quem levanta o erro (ver `erro`).
ERROS = {
    "TITULO_INVALIDO": (422, "Informe um título de até 200 caracteres."),
    "ARQUIVO_VAZIO": (422, "O arquivo está vazio. Escolha outro arquivo."),
    "TAMANHO_EXCEDIDO": (413, "O arquivo tem {tamanho_mb} MB; o limite é {limite_mb} MB."),
    "TIPO_NAO_PERMITIDO": (415, "Só é possível enviar arquivos PDF, JPG ou PNG."),
    "ARQUIVO_INVALIDO": (422, "O conteúdo do arquivo não corresponde ao tipo informado."),
    "ENVIO_INCOMPLETO": (422, "O envio do arquivo não foi concluído. Tente enviar novamente."),
    "SEM_ESPACO": (
        507,
        "Não há espaço suficiente: faltam {faltam_mb} MB. "
        "Exclua definitivamente itens da lixeira para liberar espaço.",
    ),
    "DOCUMENTO_EXCLUIDO": (409, "Este documento foi excluído."),
    "NAO_ENCONTRADO": (404, "Documento não encontrado."),
    "ESTADO_INVALIDO": (409, "Esta ação não está disponível para este documento."),
    "COMENTARIO_INVALIDO": (422, "Escreva um comentário de até 2000 caracteres."),
    "AUTOR_INVALIDO": (422, "O nome do autor deve ter até 80 caracteres."),
    "ARMAZENAMENTO_INDISPONIVEL": (
        503,
        "Não foi possível acessar o armazenamento agora. Tente novamente em instantes.",
    ),
    "BANCO_INDISPONIVEL": (503, "Não foi possível acessar os dados agora. Tente novamente em instantes."),
    "ERRO_INTERNO": (500, "Algo deu errado. Tente novamente."),
}


class ErroApi(Exception):
    """Erro de negócio com código estável e mensagem amigável em português."""

    def __init__(self, codigo: str, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.status = status


def erro(codigo: str, **valores) -> ErroApi:
    """Monta o ErroApi de um código da tabela ERROS (use com `raise erro("CODIGO")`)."""
    status, mensagem = ERROS[codigo]
    return ErroApi(codigo, mensagem.format(**valores), status)


def resposta_erro(status: int, codigo: str, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"erro": {"codigo": codigo, "mensagem": mensagem}})


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroApi)
    async def _erro_api(_: Request, exc: ErroApi):
        return resposta_erro(exc.status, exc.codigo, exc.mensagem)

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, __: RequestValidationError):
        return resposta_erro(422, "DADOS_INVALIDOS", "Os dados enviados são inválidos. Confira e tente novamente.")

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return resposta_erro(404, "NAO_ENCONTRADO", "Não encontramos o que você procurou.")
        return resposta_erro(exc.status_code, "ERRO_HTTP", "Não foi possível concluir a solicitação.")

    @app.exception_handler(Exception)
    async def _inesperado(_: Request, __: Exception):
        # Nunca vaza detalhes internos para o usuário.
        return resposta_erro(500, "ERRO_INTERNO", ERROS["ERRO_INTERNO"][1])
