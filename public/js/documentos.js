// Tela principal: formulário de envio e lista de documentos.
import { api } from './api.js';
import { iniciarComentarios } from './comentarios.js';
import { confirmar } from './dialogo.js';
import { mensagemDoErro } from './mensagens.js';
import { criarEnvio } from './upload.js';
import { avisar, el, formatarData, formatarTamanho, limparAviso, monitorarConexao } from './util.js';
import { validarEnvio } from './validacao.js';

const form = document.querySelector('#form-envio');
const campoTitulo = document.querySelector('#campo-titulo');
const campoDescricao = document.querySelector('#campo-descricao');
const campoArquivo = document.querySelector('#campo-arquivo');
const botaoEnviar = document.querySelector('#botao-enviar');
const areaProgresso = document.querySelector('#area-progresso');
const progresso = document.querySelector('#progresso');
const textoProgresso = document.querySelector('#texto-progresso');
const statusEnvio = document.querySelector('#status-envio');
const statusLista = document.querySelector('#status-lista');
const listaDocumentos = document.querySelector('#lista-documentos');
const vazioDocumentos = document.querySelector('#vazio-documentos');

const envio = criarEnvio();
const comentarios = iniciarComentarios({ aoAtualizar: carregarLista });
let enviando = false;

monitorarConexao(document.querySelector('#faixa-offline'));

// --- Envio ---------------------------------------------------------------

function mostrarEnvio(ativo) {
  enviando = ativo;
  botaoEnviar.disabled = ativo;
  botaoEnviar.textContent = ativo ? 'Enviando…' : 'Enviar documento';
  areaProgresso.hidden = !ativo;
  if (ativo) atualizarProgresso(0);
}

function atualizarProgresso(percentual) {
  progresso.value = percentual;
  textoProgresso.textContent = percentual >= 100 ? 'Finalizando…' : `Enviando… ${percentual}%`;
}

async function aoEnviar(evento) {
  evento.preventDefault();
  if (enviando) return;
  limparAviso(statusEnvio);

  const titulo = campoTitulo.value.trim();
  const arquivo = campoArquivo.files[0];
  let mime;
  try {
    mime = await validarEnvio(titulo, arquivo);
  } catch (e) {
    avisar(statusEnvio, 'erro', mensagemDoErro(e));
    return;
  }

  mostrarEnvio(true);
  let enviado = false;
  try {
    await envio.enviar({ titulo, descricao: campoDescricao.value.trim() || null, arquivo, mime }, atualizarProgresso);
    enviado = true;
    form.reset();
    envio.reiniciar();
    avisar(statusEnvio, 'sucesso', 'Documento enviado com sucesso.');
  } catch (e) {
    // O formulário e o arquivo escolhido permanecem como estão.
    const acao = e.rede ? { rotulo: 'Tentar novamente', aoClicar: () => form.requestSubmit() } : undefined;
    avisar(statusEnvio, 'erro', mensagemDoErro(e), acao);
  } finally {
    mostrarEnvio(false); // nunca deixa o botão travado
  }
  if (enviado) carregarLista();
}

form.addEventListener('submit', aoEnviar);
// Mudou algum campo: a tentativa anterior não vale mais.
form.addEventListener('input', () => envio.reiniciar());

// --- Lista ---------------------------------------------------------------

function desenharItem(doc) {
  const botoes = [
    el('button', { type: 'button', class: 'botao botao--secundario botao--pequeno', onclick: (e) => abrirLink(doc, 'visualizar', e.currentTarget) }, 'Visualizar'),
    el('button', { type: 'button', class: 'botao botao--secundario botao--pequeno', onclick: (e) => abrirLink(doc, 'baixar', e.currentTarget) }, 'Baixar'),
    el('button', { type: 'button', class: 'botao botao--secundario botao--pequeno', onclick: () => comentarios.abrir(doc) }, `Comentários (${doc.total_comentarios})`),
    el('button', { type: 'button', class: 'botao botao--perigo botao--pequeno', onclick: () => excluir(doc) }, 'Excluir'),
  ];
  return el('li', { class: 'item' },
    el('h3', { class: 'item__titulo' }, doc.titulo),
    el('p', { class: 'item__meta' }, `Enviado em ${formatarData(doc.data_upload)} · ${doc.tipo_arquivo.toUpperCase()} · ${formatarTamanho(doc.tamanho_bytes)}`),
    doc.descricao && el('p', { class: 'item__descricao' }, doc.descricao),
    el('div', { class: 'item__acoes' }, botoes),
  );
}

async function carregarLista() {
  try {
    const documentos = await api.listarDocumentos();
    listaDocumentos.replaceChildren(...documentos.map(desenharItem));
    vazioDocumentos.hidden = documentos.length > 0;
    limparAviso(statusLista);
  } catch (e) {
    avisar(statusLista, 'erro', mensagemDoErro(e), { rotulo: 'Tentar novamente', aoClicar: carregarLista });
  }
}

/** Visualizar abre em nova aba; baixar força o download. O link é temporário e gerado pela API. */
async function abrirLink(doc, modo, botao) {
  // A aba é aberta já no clique, senão o navegador bloqueia o pop-up após a espera da API.
  const aba = modo === 'visualizar' ? window.open('about:blank', '_blank') : null;
  botao.disabled = true;
  try {
    const { url } = await api.gerarLink(doc.id, modo);
    if (aba) {
      aba.opener = null;
      aba.location.href = url;
    } else {
      const link = el('a', { href: url, download: doc.nome_original });
      document.body.append(link); // Firefox só dispara o clique com o link no documento
      link.click();
      link.remove();
    }
  } catch (e) {
    aba?.close();
    avisar(statusLista, 'erro', mensagemDoErro(e));
    if (e.codigo === 'NAO_ENCONTRADO' || e.codigo === 'ESTADO_INVALIDO') carregarLista();
  } finally {
    botao.disabled = false;
  }
}

async function excluir(doc) {
  const ok = await confirmar({
    titulo: 'Enviar para a lixeira?',
    texto: `“${doc.titulo}” ficará na lixeira por 30 dias e poderá ser restaurado nesse período.`,
    rotuloConfirmar: 'Enviar para a lixeira',
    perigo: true,
  });
  if (!ok) return;
  try {
    await api.excluirDocumento(doc.id);
    limparAviso(statusLista);
  } catch (e) {
    avisar(statusLista, 'erro', mensagemDoErro(e));
  }
  carregarLista();
}

carregarLista();
