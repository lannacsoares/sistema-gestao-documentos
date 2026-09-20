// Botão "Modo escuro" do cabeçalho. Segue o sistema até a pessoa escolher; a escolha fica salva.
const botao = document.querySelector('#botao-tema');
const consulta = window.matchMedia('(prefers-color-scheme: dark)');

function guardado() {
  try { return localStorage.getItem('tema'); } catch { return null; }
}

function escuroAtivo() {
  const escolha = guardado();
  return escolha ? escolha === 'escuro' : consulta.matches;
}

function atualizarBotao() {
  botao?.setAttribute('aria-pressed', String(escuroAtivo()));
}

botao?.addEventListener('click', () => {
  const novo = escuroAtivo() ? 'claro' : 'escuro';
  document.documentElement.dataset.theme = novo === 'escuro' ? 'dark' : 'light';
  try { localStorage.setItem('tema', novo); } catch { /* sem armazenamento: vale só nesta visita */ }
  atualizarBotao();
});

// Sem escolha salva, acompanha o sistema em tempo real.
consulta.addEventListener('change', atualizarBotao);
atualizarBotao();
