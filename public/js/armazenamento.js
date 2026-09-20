// Barra de uso do armazenamento (DE01). Só informa: se a API falhar, a barra simplesmente não aparece.
import { api } from './api.js';
import { el, formatarTamanho } from './util.js';

const MB = 1024 * 1024;
const LIMITE_AVISO = 80; // a partir daqui, texto de aviso além da cor

/** 312 MB; abaixo de 10 MB usa uma casa decimal (ou KB), como no resto da tela. */
function formatarMb(bytes) {
  return bytes >= 10 * MB ? `${Math.round(bytes / MB)} MB` : formatarTamanho(bytes);
}

export function iniciarUso(regiao) {
  return async function atualizarUso() {
    try {
      const { usado_bytes: usado, limite_bytes: limite, percentual } = await api.usoArmazenamento();
      const arredondado = Math.min(100, Math.round(percentual));
      const alerta = percentual >= LIMITE_AVISO;
      regiao.className = `uso${alerta ? ' uso--alerta' : ''}`;
      regiao.replaceChildren(
        el('p', { class: 'uso__texto', id: 'uso-texto' }, `${formatarMb(usado)} de ${formatarMb(limite)} usados`),
        el('div', {
          class: 'uso__barra', role: 'progressbar', 'aria-labelledby': 'uso-texto',
          'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': String(arredondado),
        }, el('div', { class: 'uso__preenchimento', style: `width: ${Math.max(arredondado, percentual > 0 ? 1 : 0)}%` })),
        ...(alerta ? [el('p', { class: 'uso__aviso' }, 'O espaço está acabando. Exclua definitivamente itens da lixeira.')] : []),
      );
      regiao.hidden = false;
    } catch {
      regiao.hidden = true; // informação secundária: não atrapalha a tela
    }
  };
}
