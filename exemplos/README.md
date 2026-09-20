# Exemplos

Arquivos de teste e de demonstração do sistema. **Tudo é fictício ou público.**

## Arquivos fictícios (gerados)
`python scripts/gerar_exemplos.py` recria esta pasta: procuração, laudo, comprovantes em PNG e JPG (todos marcados "DOCUMENTO FICTÍCIO", sem CPF/RG reais) e os arquivos usados nos testes de casos de borda (`vazio.pdf`, `falso.pdf`, `nao_permitido.*`, nome com acento e os grandes). Os arquivos grandes (`grande.png`, `exatamente_10mb.pdf`) não vão para o Git.

## Documentos públicos (`publicos/`)
PDFs de proposições da Câmara dos Deputados, baixados uma única vez. A origem de cada um (link e data de acesso) está em `publicos/ORIGEM.md`. Cada arquivo tem até 2 MB e não contém dados pessoais de cidadãos.

## Popular o sistema
Com o `.env` apontando para o Supabase do deploy:

```
python scripts/gerar_exemplos.py
python scripts/seed.py
```

O `seed.py` cria os documentos e comentários de exemplo passando pelas mesmas validações da API. Pode ser executado de novo sem duplicar: itens que já existem são mantidos, itens enviados para a lixeira são restaurados e itens excluídos de vez são recriados.
