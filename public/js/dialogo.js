// Confirmação simples com <dialog> (acessível: foco preso, Esc cancela).
import { el } from './util.js';

/** Pergunta e devolve true (confirmou) ou false (cancelou). */
export function confirmar({ titulo, texto, rotuloConfirmar, perigo = false }) {
  return new Promise((resolver) => {
    const dialogo = el('dialog', { 'aria-labelledby': 'dlg-conf-titulo' });
    const terminar = (resposta) => { dialogo.close(); dialogo.remove(); resolver(resposta); };

    dialogo.append(
      el('h2', { id: 'dlg-conf-titulo' }, titulo),
      el('p', {}, texto),
      el('div', { class: 'dialogo__acoes' },
        el('button', { type: 'button', class: 'botao botao--secundario', onclick: () => terminar(false) }, 'Cancelar'),
        el('button', { type: 'button', class: `botao ${perigo ? 'botao--perigo' : ''}`, onclick: () => terminar(true) }, rotuloConfirmar),
      ),
    );
    dialogo.addEventListener('cancel', (e) => { e.preventDefault(); terminar(false); });
    document.body.append(dialogo);
    dialogo.showModal();
  });
}
