"""Ponto de entrada da API. A Vercel detecta a instância `app` neste arquivo."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import obter_cliente
from app.erros import erro, registrar_handlers
from app.rotas import armazenamento, comentarios, documentos, lixeira

app = FastAPI(title="Sistema de Gestão de Documentos", docs_url="/api/docs", openapi_url="/api/openapi.json")
registrar_handlers(app)
app.include_router(documentos.router)
app.include_router(comentarios.router)
app.include_router(lixeira.router)
app.include_router(armazenamento.router)


@app.get("/api/saude")
def saude():
    """Consulta trivial ao banco. Usada também pela rotina que evita a pausa do Supabase."""
    try:
        obter_cliente().table("documentos").select("id").limit(1).execute()
    except Exception:
        raise erro("BANCO_INDISPONIVEL") from None
    return {"status": "ok"}


# Em desenvolvimento a própria API serve o front-end. Na Vercel, `public/` é servido pela CDN
# antes de chegar aqui (e a pasta nem vai junto com a função), então o bloco é ignorado.
_PUBLIC = Path(__file__).resolve().parent.parent / "public"
if _PUBLIC.is_dir():
    app.mount("/", StaticFiles(directory=_PUBLIC, html=True), name="front")
