"""Configuração lida das variáveis de ambiente."""
import os

from dotenv import load_dotenv

# Em desenvolvimento lê o arquivo .env; no Render as variáveis já vêm do ambiente.
load_dotenv()


class ConfiguracaoIncompleta(RuntimeError):
    """Falta alguma variável de ambiente obrigatória."""


def _obrigatoria(nome: str) -> str:
    valor = os.getenv(nome, "").strip()
    if not valor:
        raise ConfiguracaoIncompleta(
            f"A variável de ambiente {nome} não foi definida. "
            "Copie .env.example para .env e preencha os valores."
        )
    return valor


def _inteiro(nome: str, padrao: int) -> int:
    bruto = os.getenv(nome, "").strip()
    if not bruto:
        return padrao
    try:
        return int(bruto)
    except ValueError:
        raise ConfiguracaoIncompleta(f"A variável {nome} deve ser um número inteiro.") from None


SUPABASE_URL = _obrigatoria("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = _obrigatoria("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "documentos").strip() or "documentos"

MAX_FILE_MB = _inteiro("MAX_FILE_MB", 10)
QUOTA_MB = _inteiro("QUOTA_MB", 900)
TRASH_DAYS = _inteiro("TRASH_DAYS", 30)
PENDING_TTL_MIN = _inteiro("PENDING_TTL_MIN", 60)
SIGNED_URL_TTL_S = _inteiro("SIGNED_URL_TTL_S", 300)

MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024
QUOTA_BYTES = QUOTA_MB * 1024 * 1024
