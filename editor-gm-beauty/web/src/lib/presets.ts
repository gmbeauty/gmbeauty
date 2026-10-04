import type { StylePresetId } from "./types";

export interface StylePreset {
  id: StylePresetId;
  label: string;
  description: string;
}

// Fase 1: só nome e descrição. As regras reais (cortes, zoom, legenda)
// entram na Fase 7.
export const STYLE_PRESETS: StylePreset[] = [
  { id: "gm-clean", label: "GM Clean", description: "Elegante, poucos efeitos, zooms sutis. Ideal para skincare e lançamentos." },
  { id: "gm-viral", label: "GM Viral", description: "Dinâmico, cortes rápidos e palavras em destaque. Boa retenção." },
  { id: "gm-produto", label: "GM Produto", description: "O produto é o protagonista; legenda posicionada com cuidado." },
  { id: "gm-oferta", label: "GM Oferta", description: "Destaca preço, desconto, urgência e CTA final." },
];
