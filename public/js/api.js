// Cliente da API (/api). Todo erro vira ErroApi, com código estável.

const TEMPO_LIMITE_MS = 20000;

export class ErroApi extends Error {
  constructor({ codigo, mensagem = '', status = 0, rede = false }) {
    super(mensagem || codigo);
    this.codigo = codigo;
    this.mensagem = mensagem; // mensagem do servidor (pode ser mostrada só em casos específicos)
    this.status = status;
    this.rede = rede; // true = falha de conexão/tempo esgotado (vale "Tentar novamente")
  }
}

async function requisitar(metodo, caminho, corpo) {
  const controle = new AbortController();
  const cronometro = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS);
  let resposta;
  try {
    resposta = await fetch(`/api${caminho}`, {
      method: metodo,
      headers: corpo ? { 'Content-Type': 'application/json' } : undefined,
      body: corpo ? JSON.stringify(corpo) : undefined,
      signal: controle.signal,
    });
  } catch {
    throw new ErroApi({ codigo: 'FALHA_CONEXAO', rede: true });
  } finally {
    clearTimeout(cronometro);
  }

  if (resposta.status === 204) return null;

  let dados = null;
  try {
    dados = await resposta.json();
  } catch { /* corpo vazio ou não JSON */ }

  if (!resposta.ok) {
    const e = dados?.erro;
    throw new ErroApi({ codigo: e?.codigo ?? 'ERRO_INTERNO', mensagem: e?.mensagem, status: resposta.status });
  }
  return dados;
}

const enc = encodeURIComponent;

export const api = {
  listarDocumentos: () => requisitar('GET', '/documentos'),
  iniciarUpload: (dados) => requisitar('POST', '/documentos', dados),
  confirmarUpload: (id) => requisitar('POST', `/documentos/${enc(id)}/confirmar`),
  gerarLink: (id, modo) => requisitar('GET', `/documentos/${enc(id)}/link?modo=${modo}`),
  excluirDocumento: (id) => requisitar('DELETE', `/documentos/${enc(id)}`),
  listarComentarios: (id) => requisitar('GET', `/documentos/${enc(id)}/comentarios`),
  incluirComentario: (id, dados) => requisitar('POST', `/documentos/${enc(id)}/comentarios`, dados),
  usoArmazenamento: () => requisitar('GET', '/armazenamento'),
  listarLixeira: () => requisitar('GET', '/lixeira'),
  restaurar: (id) => requisitar('POST', `/documentos/${enc(id)}/restaurar`),
  excluirDefinitivo: (id) => requisitar('DELETE', `/documentos/${enc(id)}/definitivo`),
};
