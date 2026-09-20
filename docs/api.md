# Contrato da API

Prefixo `/api`. Datas em ISO 8601 (UTC); o front-end formata para o fuso de Brasília.
Erros sempre no formato `{"erro": {"codigo": "...", "mensagem": "..."}}`, com a mensagem pronta para exibir ao usuário.

## Upload em duas etapas

O arquivo **nunca passa pela API** (a API fica leve e o envio, rápido): vai direto do navegador ao Storage.

### 1. `POST /api/documentos` → 201
Entrada (JSON): `titulo`, `descricao` (opcional), `nome_original`, `tipo_mime`, `tamanho_bytes`.

```json
{ "id": "uuid", "upload": { "caminho": "uuid.pdf", "url_assinada": "https://...", "token": "..." } }
```

### 2. Enviar o arquivo (navegador → Storage)
`PUT` na `upload.url_assinada`, com o arquivo no corpo e o cabeçalho `Content-Type` igual ao `tipo_mime` informado na etapa 1. Resposta 200 = enviado.

### 3. `POST /api/documentos/{id}/confirmar` → 200
Confere existência, tamanho real e conteúdo (primeiros bytes) e ativa o documento. Devolve o documento. É idempotente: confirmar de novo um documento já ativo devolve 200.
Se o arquivo for reprovado, o registro e o objeto são removidos e o navegador deve recomeçar da etapa 1.
`ARMAZENAMENTO_INDISPONIVEL` não remove nada: dá para repetir a confirmação ("Tentar novamente").

## Documentos

| Rota | Resposta |
|---|---|
| `GET /api/documentos` | 200, lista de ativos (mais recentes primeiro): `id, titulo, descricao, nome_original, tipo_arquivo, tamanho_bytes, data_upload, total_comentarios` |
| `GET /api/documentos/{id}/link?modo=visualizar\|baixar` | 200 `{ "url", "expira_em_s" }`. `baixar` força o download com o nome original |
| `DELETE /api/documentos/{id}` | 204. Envia para a lixeira (só documentos ativos) |

## Comentários

| Rota | Resposta |
|---|---|
| `GET /api/documentos/{id}/comentarios` | 200, ordem cronológica: `id, documento_id, texto, autor, data_hora`. Vale também para documentos na lixeira |
| `POST /api/documentos/{id}/comentarios` | 201, o comentário criado. Entrada: `texto` (1–2000), `autor` (opcional, até 80) |

## Lixeira

| Rota | Resposta |
|---|---|
| `GET /api/lixeira` | 200. Antes de listar, apaga de vez o que passou de `TRASH_DAYS`. Itens: `id, titulo, tipo_arquivo, tamanho_bytes, data_exclusao, dias_restantes, total_comentarios` |
| `POST /api/documentos/{id}/restaurar` | 200, o documento. Só para itens na lixeira |
| `DELETE /api/documentos/{id}/definitivo` | 204. Apaga arquivo, registro e comentários (use `total_comentarios` para avisar antes) |

## Armazenamento e saúde

| Rota | Resposta |
|---|---|
| `GET /api/armazenamento` | 200 `{ "usado_bytes", "limite_bytes", "percentual" }` |
| `GET /api/saude` | 200 `{ "status": "ok" }` |

## Códigos de erro

| Código | HTTP | Quando |
|---|---|---|
| `TITULO_INVALIDO` | 422 | Título vazio ou com mais de 200 caracteres |
| `ARQUIVO_VAZIO` | 422 | Tamanho 0 |
| `TAMANHO_EXCEDIDO` | 413 | Acima de `MAX_FILE_MB` |
| `TIPO_NAO_PERMITIDO` | 415 | Tipo ou extensão fora de PDF/JPG/PNG, ou incoerentes entre si |
| `ARQUIVO_INVALIDO` | 422 | Conteúdo não corresponde ao tipo, ou tamanho diferente do informado |
| `ENVIO_INCOMPLETO` | 422 | A confirmação chegou mas o arquivo não está no Storage |
| `SEM_ESPACO` | 507 | Passaria da cota (`QUOTA_MB`) |
| `COMENTARIO_INVALIDO` | 422 | Texto vazio ou acima de 2000 caracteres |
| `AUTOR_INVALIDO` | 422 | Autor acima de 80 caracteres |
| `DOCUMENTO_EXCLUIDO` | 409 | Comentar em documento na lixeira |
| `NAO_ENCONTRADO` | 404 | Documento inexistente (ou ainda pendente) |
| `ESTADO_INVALIDO` | 409 | Ação incompatível com o estado atual (ex.: excluir o que já está na lixeira) |
| `DADOS_INVALIDOS` | 422 | Formato inválido (JSON malformado, id que não é UUID, `modo` desconhecido) |
| `ARMAZENAMENTO_INDISPONIVEL` | 503 | Falha ao acessar o Storage |
| `BANCO_INDISPONIVEL` | 503 | Falha ao acessar o banco |
| `ERRO_INTERNO` | 500 | Qualquer falha inesperada (detalhes só no log do servidor) |
