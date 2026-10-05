import type { ContentTypeId, RenderSettings, StylePresetId } from "./types";

export interface StylePreset {
  id: StylePresetId;
  label: string;
  description: string;
  settings: Partial<RenderSettings>; // o que o estilo define; a logo não é alterada
}

// Cada estilo é só um conjunto de configurações. Para ajustar um estilo,
// edite aqui; para criar outro, acrescente um item (e o id em types.ts).
export const STYLE_PRESETS: StylePreset[] = [
  {
    id: "gm-clean",
    label: "GM Clean",
    description: "Elegante, poucos efeitos, só pausas longas cortadas. Ideal para skincare e lançamentos.",
    settings: {
      captionMode: "traditional", fontSize: "md", position: "bottom", textColor: "white",
      highlightColor: "lilac", highlightStrategy: "none", removeSilences: true, silenceMinSec: 0.8, zoomMode: "subtle", sfxEnabled: false,
    },
  },
  {
    id: "gm-viral",
    label: "GM Viral",
    description: "Dinâmico: palavra a palavra, destaque nas palavras fortes e ritmo mais rápido.",
    settings: {
      captionMode: "word-by-word", fontSize: "lg", position: "bottom", textColor: "white",
      highlightColor: "lilac", highlightStrategy: "keywords", removeSilences: true, silenceMinSec: 0.5, zoomMode: "dynamic", sfxEnabled: true,
    },
  },
  {
    id: "gm-produto",
    label: "GM Produto",
    description: "O produto é o protagonista: legenda menor, na base da zona segura, com destaque nos termos-chave.",
    settings: {
      captionMode: "highlight", fontSize: "sm", position: "bottom", textColor: "white",
      highlightColor: "lilac", highlightStrategy: "keywords", removeSilences: true, silenceMinSec: 0.8, zoomMode: "off", sfxEnabled: false, // produto sempre inteiro e parado
    },
  },
  {
    id: "gm-oferta",
    label: "GM Oferta",
    description: "Destaca preço, desconto, promoção e urgência que aparecerem na fala.",
    settings: {
      captionMode: "highlight", fontSize: "lg", position: "bottom", textColor: "white",
      highlightColor: "lilac", highlightStrategy: "offer", removeSilences: true, silenceMinSec: 0.6, zoomMode: "subtle", sfxEnabled: true,
    },
  },
];

export const DEFAULT_SETTINGS: RenderSettings = {
  captionMode: "traditional", fontSize: "md", position: "bottom", textColor: "white",
  highlightColor: "lilac", highlightStrategy: "none", removeSilences: false, silenceMinSec: 0.6, trimStartSec: 0, zoomMode: "off", sfxEnabled: false, sfxGainDb: -14,
  logoPosition: "none", logoSizePct: 22, logoOpacity: 0.9,
};

export function settingsForPreset(id: StylePresetId, base: RenderSettings = DEFAULT_SETTINGS): RenderSettings {
  const preset = STYLE_PRESETS.find((p) => p.id === id);
  return { ...base, ...(preset?.settings ?? {}) };
}

// Sugestão inicial de estilo por tipo de vídeo (a pessoa pode trocar).
export const SUGGESTED_STYLE: Record<ContentTypeId, StylePresetId> = {
  ugc: "gm-viral",
  produto: "gm-produto",
  tutorial: "gm-clean",
  oferta: "gm-oferta",
  "falando-camera": "gm-clean",
};
