"""Uso do armazenamento em relação à cota (CB04)."""
from fastapi import APIRouter

from app import config, servicos

router = APIRouter(prefix="/api", tags=["armazenamento"])


@router.get("/armazenamento")
def uso():
    servicos.descartar_pendentes_vencidos()
    usado = servicos.uso_atual_bytes()
    return {
        "usado_bytes": usado,
        "limite_bytes": config.QUOTA_BYTES,
        "percentual": round(usado * 100 / config.QUOTA_BYTES, 1),
    }
