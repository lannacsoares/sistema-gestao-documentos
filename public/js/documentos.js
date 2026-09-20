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
const zonaArquivo = document.querySelector('#zona-arquivo');
const nomeArquivo = document.querySelector('#nome-arquivo');
const TEXTO_SEM_ARQUIVO = nomeArquivo.textContent;
const TEMPO_MENSAGEM_MS = 8000;
const TEMPO_SAIDA_MS = 180; // igual à transição .item--saindo
const reduzirMovimento = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const envio = criarEnvio();
const comentarios = iniciarComentarios({ aoAtualizar: () => carregarLista() });
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
  let idNovo = null;
  try {
    const documento = await envio.enviar({ titulo, descricao: campoDescricao.value.trim() || null, arquivo, mime }, atualizarProgresso);
    enviado = true;
    idNovo = documento?.id ?? null;
    form.reset();
    envio.reiniciar();
    avisar(statusEnvio, 'sucesso', `“${titulo}” foi enviado e já está na lista de documentos.`);
    // A confirmação some sozinha; um erro nunca some sozinho.
    setTimeout(() => { if (statusEnvio.classList.contains('aviso--sucesso')) limparAviso(statusEnvio); }, TEMPO_MENSAGEM_MS);
  } catch (e) {
    // O formulário e o arquivo escolhido permanecem como estão.
    const acao = e.rede ? { rotulo: 'Tentar novamente', aoClicar: () => form.requestSubmit() } : undefined;
    avisar(statusEnvio, 'erro', mensagemDoErro(e), acao);
  } finally {
    mostrarEnvio(false); // nunca deixa o botão travado
  }
  if (enviado) carregarLista(idNovo);
}

form.addEventListener('submit', aoEnviar);
// Mudou algum campo: a tentativa anterior não vale mais.
form.addEventListener('input', () => envio.reiniciar());

// --- Escolha de arquivo (botão em português, com nome e tamanho, e área de soltar) ---

function mostrarArquivoEscolhido() {
  const arquivo = campoArquivo.files[0];
  nomeArquivo.textContent = arquivo ? `${arquivo.name} (${formatarTamanho(arquivo.size)})` : TEXTO_SEM_ARQUIVO;
  nomeArquivo.classList.toggle('arquivo__nome--escolhido', Boolean(arquivo));
}

campoArquivo.addEventListener('change', mostrarArquivoEscolhido);
form.addEventListener('reset', () => setTimeout(mostrarArquivoEscolhido, 0));

zonaArquivo.addEventListener('dragover', (e) => { e.preventDefault(); zonaArquivo.classList.add('arquivo--sobre'); });
zonaArquivo.addEventListener('dragleave', () => zonaArquivo.classList.remove('arquivo--sobre'));
zonaArquivo.addEventListener('drop', (e) => {
  e.preventDefault();
  zonaArquivo.classList.remove('arquivo--sobre');
  const soltado = e.dataTransfer?.files[0];
  if (!soltado || enviando) return;
  const lote = new DataTransfer();
  lote.items.add(soltado);
  campoArquivo.files = lote.files;
  campoArquivo.dispatchEvent(new Event('change', { bubbles: true }));
  campoArquivo.dispatchEvent(new Event('input', { bubbles: true })); // a tentativa anterior não vale mais
});

// --- Lista ---------------------------------------------------------------

function desenharItem(doc) {
  const botoes = [
    el('button', { type: 'button', class: 'botao botao--pequeno botao--principal', onclick: (e) => abrirLink(doc, 'visualizar', e.currentTarget) }, 'Visualizar'),
    el('button', { type: 'button', class: 'botao botao--secundario botao--pequeno', onclick: (e) => abrirLink(doc, 'baixar', e.currentTarget) }, 'Baixar'),
    el('button', { type: 'button', class: 'botao botao--secundario botao--pequeno', onclick: () => comentarios.abrir(doc) }, `Comentários (${doc.total_comentarios})`),
    el('button', { type: 'button', class: 'botao botao--perigo-discreto botao--pequeno', onclick: () => excluir(doc) }, 'Excluir'),
  ];
  return el('li', { class: 'item', 'data-id': doc.id },
    el('div', { class: 'item__topo' },
      el('h3', { class: 'item__titulo' }, doc.titulo),
      el('span', { class: 'chip' }, doc.tipo_arquivo.toUpperCase()),
    ),
    el('p', { class: 'item__meta' }, `Enviado em ${formatarData(doc.data_upload)} · ${formatarTamanho(doc.tamanho_bytes)}`),
    doc.descricao && el('p', { class: 'item__descricao' }, doc.descricao),
    el('div', { class: 'item__acoes' }, botoes),
  );
}

/** `destacarId`: documento recém-enviado; a lista rola até ele e ele pisca uma vez. */
async function carregarLista(destacarId) {
  try {
    const documentos = await api.listarDocumentos();
    listaDocumentos.replaceChildren(...documentos.map(desenharItem));
    vazioDocumentos.hidden = documentos.length > 0;
    limparAviso(statusLista);
    const novo = typeof destacarId === 'string' && listaDocumentos.querySelector(`[data-id="${CSS.escape(destacarId)}"]`);
    if (novo) {
      novo.classList.add('item--novo');
      novo.scrollIntoView({ block: 'nearest', behavior: reduzirMovimento() ? 'auto' : 'smooth' });
    }
  } catch (e) {
    avisar(statusLista, 'erro', mensagemDoErro(e), { rotulo: 'Tentar novamente', aoClicar: () => carregarLista() });
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
    // O item se despede antes de a lista recarregar: mostra para onde o documento foi.
    const item = listaDocumentos.querySelector(`[data-id="${CSS.escape(doc.id)}"]`);
    if (item) {
      item.classList.add('item--saindo');
      await new Promise((r) => setTimeout(r, TEMPO_SAIDA_MS));
    }
  } catch (e) {
    avisar(statusLista, 'erro', mensagemDoErro(e));
  }
  carregarLista();
}

avisar(statusLista, 'info', 'Carregando documentos…');
carregarLista();
