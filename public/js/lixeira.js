// Tela da lixeira: restaurar e excluir definitivamente.
import { api } from './api.js';
import { confirmar } from './dialogo.js';
import { mensagemDoErro } from './mensagens.js';
import { avisar, el, formatarData, formatarTamanho, limparAviso, monitorarConexao, plural } from './util.js';

const status = document.querySelector('#status-lixeira');
const lista = document.querySelector('#lista-lixeira');
const vazio = document.querySelector('#vazio-lixeira');

monitorarConexao(document.querySelector('#faixa-offline'));

function textoPrazo(dias) {
  if (dias <= 0) return 'Será removido em breve';
  return `Restam ${plural(dias, 'dia', 'dias')}`;
}

function desenharItem(doc) {
  return el('li', { class: 'item' },
    el('div', { class: 'item__topo' },
      el('h3', { class: 'item__titulo' }, doc.titulo),
      el('span', { class: 'chip' }, doc.tipo_arquivo.toUpperCase()),
    ),
    el('p', { class: 'item__meta' },
      `Excluído em ${formatarData(doc.data_exclusao)} · ${textoPrazo(doc.dias_restantes)} · ${formatarTamanho(doc.tamanho_bytes)}`),
    el('div', { class: 'item__acoes' },
      el('button', { type: 'button', class: 'botao botao--secundario botao--pequeno', onclick: (e) => restaurar(doc, e.currentTarget) }, 'Restaurar'),
      el('button', { type: 'button', class: 'botao botao--perigo botao--pequeno', onclick: () => excluirDefinitivo(doc) }, 'Excluir definitivamente'),
    ),
  );
}

async function carregar() {
  try {
    const itens = await api.listarLixeira();
    lista.replaceChildren(...itens.map(desenharItem));
    vazio.hidden = itens.length > 0;
  } catch (e) {
    avisar(status, 'erro', mensagemDoErro(e), { rotulo: 'Tentar novamente', aoClicar: carregar });
  }
}

async function restaurar(doc, botao) {
  botao.disabled = true;
  try {
    await api.restaurar(doc.id);
    avisar(status, 'sucesso', `“${doc.titulo}” voltou para a lista de documentos.`);
  } catch (e) {
    avisar(status, 'erro', mensagemDoErro(e));
  }
  carregar();
}

async function excluirDefinitivo(doc) {
  const n = doc.total_comentarios;
  const aviso = n > 0
    ? `Este documento tem ${plural(n, 'comentário', 'comentários')}. ${n === 1 ? 'Ele será apagado' : 'Eles serão apagados'} junto. Esta ação não pode ser desfeita.`
    : 'Esta ação não pode ser desfeita.';
  const ok = await confirmar({
    titulo: 'Excluir definitivamente?',
    texto: `“${doc.titulo}” será removido para sempre. ${aviso}`,
    rotuloConfirmar: 'Excluir definitivamente',
    perigo: true,
  });
  if (!ok) return;
  try {
    await api.excluirDefinitivo(doc.id);
    avisar(status, 'sucesso', 'Documento excluído definitivamente.');
  } catch (e) {
    avisar(status, 'erro', mensagemDoErro(e));
  }
  carregar();
}

carregar();
