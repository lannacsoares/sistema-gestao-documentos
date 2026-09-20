// Mapa único: código de erro -> texto amigável. O usuário nunca vê erro técnico.

const MENSAGENS = {
  TITULO_INVALIDO: 'Informe um título de até 200 caracteres.',
  ARQUIVO_VAZIO: 'O arquivo está vazio. Escolha outro arquivo.',
  ARQUIVO_NAO_ESCOLHIDO: 'Escolha um arquivo para enviar.',
  TAMANHO_EXCEDIDO: 'O arquivo é maior que o limite permitido. Tente reduzir o arquivo.',
  TIPO_NAO_PERMITIDO: 'Só é possível enviar arquivos PDF, JPG ou PNG.',
  ARQUIVO_INVALIDO: 'O conteúdo do arquivo não corresponde ao tipo informado.',
  ENVIO_INCOMPLETO: 'O envio do arquivo não foi concluído. Tente enviar novamente.',
  SEM_ESPACO: 'Não há espaço suficiente. Exclua definitivamente itens da lixeira para liberar espaço.',
  COMENTARIO_INVALIDO: 'Escreva um comentário de até 2000 caracteres.',
  AUTOR_INVALIDO: 'O nome deve ter até 80 caracteres.',
  DOCUMENTO_EXCLUIDO: 'Este documento foi excluído.',
  NAO_ENCONTRADO: 'Documento não encontrado. Ele pode ter sido removido.',
  ESTADO_INVALIDO: 'Esta ação não está disponível para este documento.',
  DADOS_INVALIDOS: 'Os dados enviados são inválidos. Confira e tente novamente.',
  ARMAZENAMENTO_INDISPONIVEL: 'Não foi possível acessar o armazenamento agora. Tente novamente em instantes.',
  BANCO_INDISPONIVEL: 'Não foi possível acessar os dados agora. Tente novamente em instantes.',
  ERRO_INTERNO: 'Algo deu errado. Tente novamente.',
  // Erros do próprio navegador
  FALHA_CONEXAO: 'Falha na conexão. Seus dados foram mantidos.',
  UPLOAD_RECUSADO: 'Não foi possível enviar o arquivo. Tente novamente.',
};

const GENERICA = 'Algo deu errado. Tente novamente.';

// Nestes casos a mensagem do servidor traz números úteis ("14 MB", "faltam 5 MB").
const USA_MENSAGEM_DO_SERVIDOR = new Set(['TAMANHO_EXCEDIDO', 'SEM_ESPACO']);

export function mensagemDoErro(erro) {
  const codigo = erro?.codigo;
  if (USA_MENSAGEM_DO_SERVIDOR.has(codigo) && erro.mensagem) return erro.mensagem;
  return MENSAGENS[codigo] ?? GENERICA;
}
