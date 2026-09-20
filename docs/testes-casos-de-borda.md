# Testes dos casos de borda (CB01 a CB06)

Execução de **20/09/2026** contra o deploy público (`https://sistema-gestao-documentos.onrender.com`), com `MAX_FILE_MB=10`, `QUOTA_MB=900` e `TRASH_DAYS=30`. Todos os documentos de teste foram apagados definitivamente ao final (lista, lixeira e uso do armazenamento voltaram a zero).

Como repetir: `python scripts/gerar_exemplos.py` e depois `python scripts/testar_deploy.py`. Os testes marcados como **local** usaram o código do repositório contra o mesmo Supabase, com a variável indicada reduzida só naquele processo (o deploy nunca foi alterado).

Legenda: **A** = automatizado pelo script; **L** = feito em ambiente local com parâmetro reduzido; **M** = manual no navegador.

| ID | Caso | Como | Resultado esperado | Resultado obtido | Status |
|---|---|---|---|---|---|
| CB01.1 | Arquivo de 27 MB (`grande.png`) | M | Recusado no navegador, sem chamar a API | — | Pendente (navegador) |
| CB01.2 | API com 11 MB e com 10 MB + 1 byte | A | `TAMANHO_EXCEDIDO` (413) | 413 `TAMANHO_EXCEDIDO` nos dois | Aprovado |
| CB01.3 | Envio de 11 MB direto ao bucket com URL assinada válida | A | Storage recusa | `PUT` respondeu 400; a confirmação respondeu 422 `ENVIO_INCOMPLETO` | Aprovado |
| CB01.4 | Arquivo de exatamente 10 MB | A | Aceito | Confirmação 200 | Aprovado |
| CB02.1 | `.txt` e `.docx` | A | Recusa de tipo | 415 `TIPO_NAO_PERMITIDO` | Aprovado |
| CB02.2 | `falso.pdf` (texto com extensão `.pdf`) | A | Recusa pelo conteúdo real | Confirmação 422 `ARQUIVO_INVALIDO`; não aparece na lista | Aprovado (API); recusa no navegador: M |
| CB02.3 | `vazio.pdf` | A | Recusa de arquivo vazio | 422 `ARQUIVO_VAZIO` | Aprovado |
| CB02.4 | Nome com acento e símbolos | A | Aceito; nome original preservado; objeto com nome UUID | Aceito; banco e download devolvem `nome com acento e símbolos (1).pdf`; objeto no Storage `c52b8335-….pdf` | Aprovado |
| CB02.5 | Duplicado (mesmo PDF duas vezes) | A | Dois registros independentes | Dois IDs distintos, ambos aceitos | Aprovado (comportamento documentado, não é erro) |
| CB03.1 | Upload com a rede offline (DevTools) | M | Mensagem de falha, formulário preenchido, "Tentar novamente" | — | Pendente (navegador) |
| CB03.2 | Comentar offline | M | Texto permanece na caixa | — | Pendente (navegador) |
| CB03.3 | Falha no meio do upload não deixa documento na lista | A | Registro fica `pendente` e não aparece | Envio recusado pelo bucket e `falso.pdf` não aparecem na lista | Aprovado |
| CB03.4 | Chave do Supabase inválida | L | Mensagem amigável, sem erro técnico | 503 `BANCO_INDISPONIVEL`: "Não foi possível acessar os dados agora. Tente novamente em instantes." O log só registra o nome da classe do erro, nunca a chave | Aprovado |
| CB04.1 | Cota reduzida (`QUOTA_MB=1`) | L | `SEM_ESPACO` antes do upload | Com 0,7 MB usados, o 2º envio recebeu 507 `SEM_ESPACO` já ao iniciar (nenhuma URL de upload foi emitida): "faltam 1 MB. Exclua definitivamente itens da lixeira para liberar espaço." | Aprovado |
| CB04.2 | Lixeira conta para o uso; excluir definitivamente libera | L | Uso permanece na lixeira e zera ao excluir de vez | Uso ficou em 718115 bytes com o item na lixeira; após excluir definitivamente, novo envio aceito (201) e uso final 0 | Aprovado |
| CB04.3 | Cota do deploy real | A | 900 MB | `/api/armazenamento` no deploy: limite 943718400 bytes (900 MB) | Aprovado |
| CB05.1 | Comentar em documento excluído | A | `DOCUMENTO_EXCLUIDO` | 409 `DOCUMENTO_EXCLUIDO` (a tela mostra "Este documento foi excluído." e atualiza a lista: M) | Aprovado (API); tela: pendente (duas abas) |
| CB05.2 | Comentários na lixeira | A | Continuam existindo | 2 comentários legíveis e contados (`total_comentarios` = 2) | Aprovado |
| CB05.3 | Exclusão definitiva | A | Apaga documento, comentários (cascata) e arquivo | Definitivo 204; comentários 404; link do arquivo 404 | Aprovado |
| CB06.1 | Excluir, Lixeira, Restaurar | A | Volta à lista com os comentários | Restaurado 200, na lista, com 2 comentários | Aprovado |
| CB06.2 | Dias restantes | A | 30 dias logo após excluir | `dias_restantes` = 30 | Aprovado |
| CB06.3 | Limpeza automática de itens vencidos | L | Ao abrir a lixeira, o vencido é removido (arquivo e linha) | Com `TRASH_DAYS=0`: item removido e link do arquivo 404. Com o Storage falhando, o item foi mantido | Aprovado |
| CB06.4 | Excluir definitivamente com o Storage falhando | L | Item continua na lixeira e pode ser tentado de novo | 503 `ARMAZENAMENTO_INDISPONIVEL`; o item ficou na lixeira; a nova tentativa respondeu 204 | Aprovado |

## Pendências (dependem do navegador)

Devem ser feitas por uma pessoa em https://sistema-gestao-documentos.onrender.com e registradas aqui:

1. **CB01.1:** enviar `exemplos/grande.png`; deve aparecer "O arquivo tem 27,2 MB; o limite é 10 MB." sem nenhuma chamada à API (aba Network vazia).
2. **CB02.2 (navegador):** enviar `exemplos/falso.pdf`, `nao_permitido.txt` e `vazio.pdf` e ler as mensagens.
3. **CB03.1 e CB03.2:** DevTools, aba Network, **Offline**; tentar enviar e comentar; conferir "Tentar novamente" e que os textos continuam.
4. **CB05.1 (tela):** abrir os comentários de um documento, excluí-lo em outra aba e tentar comentar.

## Limitações conhecidas
- O serviço gratuito do Render dorme após alguns minutos sem uso; a primeira abertura pode levar cerca de 1 minuto.
- Documentos duplicados são aceitos (dois registros independentes).
