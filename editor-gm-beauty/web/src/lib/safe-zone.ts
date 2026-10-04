// Área segura para Reels/TikTok em vídeo 1080x1920, em porcentagem da tela.
// São valores iniciais aproximados; ajustamos na Fase 5 com testes reais.
export const SAFE_ZONE = {
  topPct: 12, // perfil/abas no topo
  bottomPct: 22, // descrição, nome do perfil, música
  rightPct: 14, // botões de curtir/comentar/compartilhar
  leftPct: 5,
} as const;
