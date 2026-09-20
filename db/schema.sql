-- Sistema de Gestão de Documentos — esquema do banco (Supabase / PostgreSQL)
-- Execute no SQL Editor do Supabase. Pode ser executado mais de uma vez.

-- Tabelas
create table if not exists public.documentos (
  id              uuid primary key default gen_random_uuid(),
  titulo          text not null check (char_length(titulo) between 1 and 200),
  descricao       text,
  nome_original   text not null,
  tipo_arquivo    text not null check (tipo_arquivo in ('pdf','jpg','png')),
  tamanho_bytes   bigint not null check (tamanho_bytes > 0),
  caminho_arquivo text not null unique,   -- nome gerado (UUID + extensão) no Storage
  status          text not null default 'pendente'
                    check (status in ('pendente','ativo','lixeira')),
  data_upload     timestamptz not null default now(),
  data_exclusao   timestamptz,
  -- coerência: só há data_exclusao quando está na lixeira
  constraint ck_lixeira_data check ((status = 'lixeira') = (data_exclusao is not null))
);

create table if not exists public.comentarios (
  id            uuid primary key default gen_random_uuid(),
  documento_id  uuid not null references public.documentos(id) on delete cascade,
  texto         text not null check (char_length(texto) between 1 and 2000),
  autor         text check (autor is null or char_length(autor) <= 80),
  data_hora     timestamptz not null default now()
);

create index if not exists idx_comentarios_doc on public.comentarios (documento_id, data_hora);
create index if not exists idx_documentos_status on public.documentos (status, data_upload desc);

-- Segurança: RLS ligado e SEM políticas = ninguém acessa pelas chaves anon/authenticated.
-- Só a API (service_role) acessa.
alter table public.documentos  enable row level security;
alter table public.comentarios enable row level security;

-- Uso de armazenamento (soma de ativos + lixeira), usado na cota
create or replace function public.uso_armazenamento_bytes()
returns bigint language sql stable as $$
  select coalesce(sum(tamanho_bytes), 0)::bigint
  from public.documentos
  where status in ('ativo','lixeira');
$$;
revoke execute on function public.uso_armazenamento_bytes() from public, anon, authenticated;

-- Bucket privado, com limite e tipos permitidos (3ª camada de validação)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('documentos', 'documentos', false, 10485760,
        array['application/pdf','image/jpeg','image/png'])
on conflict (id) do nothing;
