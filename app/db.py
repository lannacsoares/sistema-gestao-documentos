"""Cliente do Supabase (banco e Storage)."""
from functools import lru_cache

from supabase import Client, create_client

from app import config


@lru_cache(maxsize=1)
def obter_cliente() -> Client:
    """Uma única instância por processo, reaproveitada entre chamadas (serverless)."""
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
