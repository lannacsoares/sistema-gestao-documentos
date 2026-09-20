"""Erros da API no formato padrão: {"erro": {"codigo": "...", "mensagem": "..."}}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErroApi(Exception):
    """Erro de negócio com código estável e mensagem amigável em português."""

    def __init__(self, codigo: str, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.status = status


def resposta_erro(status: int, codigo: str, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"erro": {"codigo": codigo, "mensagem": mensagem}})


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroApi)
    async def _erro_api(_: Request, exc: ErroApi):
        return resposta_erro(exc.status, exc.codigo, exc.mensagem)

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, __: RequestValidationError):
        return resposta_erro(422, "dados_invalidos", "Os dados enviados são inválidos. Confira e tente novamente.")

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return resposta_erro(404, "nao_encontrado", "Não encontramos o que você procurou.")
        return resposta_erro(exc.status_code, "erro_http", "Não foi possível concluir a solicitação.")

    @app.exception_handler(Exception)
    async def _inesperado(_: Request, __: Exception):
        # Nunca vaza detalhes internos para o usuário.
        return resposta_erro(500, "erro_interno", "Algo deu errado do nosso lado. Tente novamente em instantes.")
