// Fluxo de envio em duas etapas, com retentativa (CB03).
// 1) API cria o registro e devolve uma URL assinada; 2) o navegador envia o arquivo direto
// ao Storage (nunca passa pela API); 3) a API confirma.
import { ErroApi, api } from './api.js';

const TEMPO_LIMITE_ENVIO_MS = 120000;

// A URL assinada expirou ou o registro sumiu: recomeça do passo 1.
const STATUS_URL_EXPIRADA = new Set([400, 401, 403, 404]);
const CODIGOS_RECOMECAR = new Set(['NAO_ENCONTRADO', 'ESTADO_INVALIDO', 'ENVIO_INCOMPLETO']);

/** PUT do arquivo na URL assinada, com progresso (fetch ainda não informa progresso de envio). */
function enviarAoStorage(url, arquivo, mime, aoProgredir) {
  return new Promise((resolver, rejeitar) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', url);
    xhr.timeout = TEMPO_LIMITE_ENVIO_MS;
    xhr.setRequestHeader('Content-Type', mime);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) aoProgredir?.(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolver();
      else rejeitar(new ErroApi({ codigo: 'UPLOAD_RECUSADO', status: xhr.status }));
    };
    xhr.onerror = () => rejeitar(new ErroApi({ codigo: 'FALHA_CONEXAO', rede: true }));
    xhr.ontimeout = () => rejeitar(new ErroApi({ codigo: 'FALHA_CONEXAO', rede: true }));
    xhr.send(arquivo);
  });
}

/**
 * Cria um "envio" que lembra em que etapa parou. Se a rede cair no meio, chamar `enviar`
 * de novo continua de onde parou (reaproveita a URL assinada); se ela expirou, recomeça.
 */
export function criarEnvio() {
  let sessao = null; // { id, upload, enviado }

  async function tentar(dados, aoProgredir) {
    if (!sessao) {
      const { id, upload } = await api.iniciarUpload({
        titulo: dados.titulo,
        descricao: dados.descricao,
        nome_original: dados.arquivo.name,
        tipo_mime: dados.mime,
        tamanho_bytes: dados.arquivo.size,
      });
      sessao = { id, upload, enviado: false };
    }
    if (!sessao.enviado) {
      await enviarAoStorage(sessao.upload.url_assinada, dados.arquivo, dados.mime, aoProgredir);
      sessao.enviado = true;
    }
    const documento = await api.confirmarUpload(sessao.id);
    sessao = null;
    return documento;
  }

  return {
    /** Esquece a sessão atual (use quando o usuário trocar o arquivo ou os campos). */
    reiniciar() { sessao = null; },

    async enviar(dados, aoProgredir) {
      for (let tentativa = 1; ; tentativa++) {
        try {
          return await tentar(dados, aoProgredir);
        } catch (e) {
          const recomecavel = (e.codigo === 'UPLOAD_RECUSADO' && STATUS_URL_EXPIRADA.has(e.status))
            || (sessao && CODIGOS_RECOMECAR.has(e.codigo));
          if (recomecavel && tentativa === 1) { sessao = null; continue; }
          // Falha de rede: mantém a sessão para retomar. Qualquer outro erro: descarta.
          if (!e.rede) sessao = null;
          throw e;
        }
      }
    },
  };
}
