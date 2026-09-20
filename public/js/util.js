// Utilitários: criação segura de elementos, datas, tamanhos e avisos.

/** Cria um elemento. Textos entram como nós de texto (nunca innerHTML), o que evita injeção. */
export function el(tag, props = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [nome, valor] of Object.entries(props)) {
    if (valor === false || valor == null) continue;
    if (nome === 'class') e.className = valor;
    else if (nome.startsWith('on')) e.addEventListener(nome.slice(2).toLowerCase(), valor);
    else e.setAttribute(nome, valor === true ? '' : valor);
  }
  for (const filho of filhos.flat()) {
    if (filho != null && filho !== false) e.append(filho);
  }
  return e;
}

export function formatarData(iso) {
  return new Date(iso).toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    dateStyle: 'short',
    timeStyle: 'short',
  });
}

const MB = 1024 * 1024;

/** 2411724 -> "2,3 MB"; abaixo de 1 MB usa KB. */
export function formatarTamanho(bytes) {
  if (bytes >= MB) return `${(bytes / MB).toFixed(1).replace('.', ',')} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function plural(n, singular, pluralTexto) {
  return `${n} ${n === 1 ? singular : pluralTexto}`;
}

/**
 * Mostra uma mensagem numa região de status (role/aria-live no HTML).
 * tipo: 'erro' | 'sucesso' | 'info'. `acao` opcional cria um botão ("Tentar novamente").
 */
export function avisar(regiao, tipo, texto, acao) {
  const rotulos = { erro: 'Atenção:', sucesso: 'Pronto:', info: 'Aviso:' };
  regiao.className = `aviso aviso--${tipo}`;
  regiao.hidden = false;
  const botao = acao && el('button', { type: 'button', class: 'botao botao--secundario botao--pequeno', onclick: acao.aoClicar }, acao.rotulo);
  // replaceChildren transformaria um valor vazio em texto "undefined": só passa o que existe.
  regiao.replaceChildren(...[
    el('span', { class: 'aviso__rotulo' }, rotulos[tipo]),
    el('span', { class: 'aviso__texto' }, texto),
    botao,
  ].filter(Boolean));
}

export function limparAviso(regiao) {
  regiao.hidden = true;
  regiao.replaceChildren();
}

/** Mostra a faixa "sem internet" enquanto o navegador estiver offline. */
export function monitorarConexao(faixa) {
  const atualizar = () => { faixa.hidden = navigator.onLine; };
  window.addEventListener('online', atualizar);
  window.addEventListener('offline', atualizar);
  atualizar();
}
