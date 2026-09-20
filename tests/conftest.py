"""Os testes são de funções puras: não usam o Supabase. Valores de mentira permitem rodar `pytest`
sem um .env (o .env real, se existir, tem prioridade)."""
import os

os.environ.setdefault("SUPABASE_URL", "https://exemplo.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "chave-de-teste")
