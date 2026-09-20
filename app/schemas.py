"""Modelos de entrada. Regras finas (título, tamanho, tipo) ficam em validadores.py,
para devolver o erro específico e amigável em vez de um erro genérico de formato."""
from pydantic import BaseModel, Field


class IniciarUpload(BaseModel):
    titulo: str = Field(max_length=1000)
    descricao: str | None = Field(default=None, max_length=2000)
    nome_original: str = Field(max_length=255)
    tipo_mime: str = Field(max_length=100)
    tamanho_bytes: int


class NovoComentario(BaseModel):
    texto: str = Field(max_length=20000)
    autor: str | None = Field(default=None, max_length=1000)
