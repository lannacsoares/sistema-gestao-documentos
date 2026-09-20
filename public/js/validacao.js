// Validação no navegador (1ª camada). O servidor e o bucket repetem as mesmas regras.
import { ErroApi } from './api.js';

export const LIMITE_MB = 10;
const LIMITE_BYTES = LIMITE_MB * 1024 * 1024;

// extensão -> tipo MIME e assinatura (primeiros bytes) esperada
const TIPOS = {
  pdf: { mime: 'application/pdf', assinatura: [0x25, 0x50, 0x44, 0x46, 0x2d] },
  jpg: { mime: 'image/jpeg', assinatura: [0xff, 0xd8, 0xff] },
  jpeg: { mime: 'image/jpeg', assinatura: [0xff, 0xd8, 0xff] },
  png: { mime: 'image/png', assinatura: [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a] },
};

function recusar(codigo, mensagem) {
  return new ErroApi({ codigo, mensagem });
}

/** Confere título, tamanho, tipo e conteúdo real. Devolve o tipo MIME ou lança ErroApi. */
export async function validarEnvio(titulo, arquivo) {
  if (!titulo.trim()) throw recusar('TITULO_INVALIDO');
  if (titulo.trim().length > 200) throw recusar('TITULO_INVALIDO');
  if (!arquivo) throw recusar('ARQUIVO_NAO_ESCOLHIDO');

  if (arquivo.size === 0) throw recusar('ARQUIVO_VAZIO');
  if (arquivo.size > LIMITE_BYTES) {
    const mb = Math.round((arquivo.size / (1024 * 1024)) * 10) / 10;
    throw recusar('TAMANHO_EXCEDIDO', `O arquivo tem ${String(mb).replace('.', ',')} MB; o limite é ${LIMITE_MB} MB.`);
  }

  const extensao = arquivo.name.includes('.') ? arquivo.name.split('.').pop().toLowerCase() : '';
  const tipo = TIPOS[extensao];
  // `type` pode vir vazio em alguns navegadores; quando vem, precisa bater com a extensão.
  if (!tipo || (arquivo.type && arquivo.type !== tipo.mime)) throw recusar('TIPO_NAO_PERMITIDO');

  const inicio = new Uint8Array(await arquivo.slice(0, 8).arrayBuffer());
  if (!tipo.assinatura.every((byte, i) => inicio[i] === byte)) throw recusar('ARQUIVO_INVALIDO');

  return tipo.mime;
}
