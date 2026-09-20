// Roda antes da página ser desenhada, para não piscar no tema errado.
// Sem escolha salva, nada é definido e vale a preferência do sistema (prefers-color-scheme).
try {
  const salvo = localStorage.getItem('tema');
  if (salvo === 'claro' || salvo === 'escuro') {
    document.documentElement.dataset.theme = salvo === 'escuro' ? 'dark' : 'light';
  }
} catch { /* armazenamento bloqueado: segue o sistema */ }
