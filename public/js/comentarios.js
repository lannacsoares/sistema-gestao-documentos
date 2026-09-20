// Painel de comentários (<dialog id="dlg-comentarios">).
import { api } from './api.js';
import { mensagemDoErro } from './mensagens.js';
import { avisar, el, formatarData, limparAviso } from './util.js';

const LIMITE = 2000;

/** `aoAtualizar` é chamado quando algo mudou e a lista de documentos precisa recarregar. */
export function iniciarComentarios({ aoAtualizar }) {
  const dialogo = document.querySelector('#dlg-comentarios');
  const titulo = document.querySelector('#dlg-com-titulo');
  const lista = document.querySelector('#lista-comentarios');
  const vazio = document.querySelector('#vazio-comentarios');
  const form = document.querySelector('#form-comentario');
  const campo = document.querySelector('#campo-comentario');
  const contador = document.querySelector('#contador-comentario');
  const botao = document.querySelector('#botao-comentar');
  const status = document.querySelector('#status-comentario');
  let documento = null;

  function desenhar(itens) {
    lista.replaceChildren(...itens.map((c) => el('li', { class: 'comentario' },
      el('p', { class: 'comentario__meta' }, [formatarData(c.data_hora), c.autor ? ` · ${c.autor}` : '']),
      el('p', { class: 'comentario__texto' }, c.texto),
    )));
    vazio.hidden = itens.length > 0;
    lista.scrollTop = lista.scrollHeight;
  }

  async function carregar() {
    try {
      desenhar(await api.listarComentarios(documento.id));
      limparAviso(status);
    } catch (e) {
      avisar(status, 'erro', mensagemDoErro(e), { rotulo: 'Tentar novamente', aoClicar: carregar });
    }
  }

  async function enviar(evento) {
    evento?.preventDefault();
    const texto = campo.value.trim();
    if (!texto || texto.length > LIMITE) {
      avisar(status, 'erro', mensagemDoErro({ codigo: 'COMENTARIO_INVALIDO' }));
      return;
    }
    botao.disabled = true;
    try {
      await api.incluirComentario(documento.id, { texto });
      campo.value = '';
      atualizarContador();
      limparAviso(status);
      await carregar();
      aoAtualizar();
    } catch (e) {
      // O texto permanece na caixa: nada é perdido.
      if (e.codigo === 'DOCUMENTO_EXCLUIDO') {
        avisar(status, 'erro', mensagemDoErro(e));
        campo.disabled = true;
        aoAtualizar(); // o documento sai da lista
      } else if (e.rede) {
        avisar(status, 'erro', 'Falha na conexão. Seu comentário foi mantido.', { rotulo: 'Tentar novamente', aoClicar: () => enviar() });
      } else {
        avisar(status, 'erro', mensagemDoErro(e));
      }
    } finally {
      botao.disabled = campo.disabled;
    }
  }

  function atualizarContador() {
    contador.textContent = `${campo.value.length} / ${LIMITE}`;
  }

  form.addEventListener('submit', enviar);
  campo.addEventListener('input', atualizarContador);
  document.querySelector('#dlg-com-fechar').addEventListener('click', () => dialogo.close());
  // A lista de documentos já é recarregada quando um comentário muda algo; ao fechar não precisa de novo.
  dialogo.addEventListener('close', () => { documento = null; });

  return {
    abrir(doc) {
      documento = doc;
      titulo.textContent = `Comentários: ${doc.titulo}`;
      campo.value = '';
      campo.disabled = false;
      botao.disabled = false;
      atualizarContador();
      limparAviso(status);
      lista.replaceChildren();
      vazio.hidden = true;
      dialogo.showModal();
      titulo.focus(); // o leitor de tela começa pelo título, sem abrir o teclado no celular
      carregar();
    },
  };
}
