// Tipos do Editor GM Beauty. Espelham o que a API (FastAPI) devolve.

export type ProjectStatus = "draft" | "processing" | "ready" | "error";
export type ContentTypeId = "ugc" | "produto" | "tutorial" | "oferta" | "falando-camera";
export type StylePresetId = "gm-clean" | "gm-viral" | "gm-produto" | "gm-oferta";

export type CaptionMode = "traditional" | "highlight" | "word-by-word";
export type CaptionSize = "sm" | "md" | "lg";
export type CaptionPosition = "top" | "middle" | "bottom";
export type GmColor = "white" | "lilac" | "purple";
export type LogoPosition = "none" | "top" | "bottom" | "watermark";
export type HighlightStrategy = "none" | "keywords" | "offer";
export type ZoomMode = "off" | "subtle" | "dynamic";

// Tudo o que o painel lateral controla e vai para a renderização.
export interface RenderSettings {
  captionMode: CaptionMode;
  fontSize: CaptionSize;
  position: CaptionPosition;
  textColor: GmColor;
  highlightColor: GmColor;
  highlightStrategy: HighlightStrategy;
  removeSilences: boolean;
  silenceMinSec: number;
  trimStartSec: number; // corta o silêncio antes da primeira fala
  zoomMode: ZoomMode;
  sfxEnabled: boolean;
  sfxGainDb: number; // volume do efeito sobre a fala (dB, negativo)
  logoPosition: LogoPosition;
  logoSizePct: number;
  logoOpacity: number;
}

export interface Word {
  w: string;
  s: number;
  e: number;
}

export interface CaptionSegment {
  id: string;
  startSec: number;
  endSec: number;
  text: string;
  highlightWords: string[]; // palavras em minúsculas e sem pontuação
  words: Word[] | null;
}

export interface SilenceRange {
  id: string;
  startSec: number;
  endSec: number;
}

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  stage: string | null;
  progress: number;
  contentType: ContentTypeId;
  style: StylePresetId;
  originalName: string;
  durationSec: number;
  width: number;
  height: number;
  sizeBytes: number;
  settings: RenderSettings;
  captions: CaptionSegment[];
  silences: SilenceRange[];
  sfxEvents: SfxEvent[];
  analyzed: boolean;
  hasOutput: boolean;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ZoomEvent {
  startSec: number;
  endSec: number;
  amp: number;
  kind: "in" | "settle";
}

export interface HookCheck {
  id: string;
  ok: boolean;
  label: string;
  tip: string | null;
  action: "trim_start" | "highlight_hook" | null;
}

export interface Hook {
  level: "strong" | "good" | "weak";
  firstSpeechSec: number | null;
  suggestedTrimSec: number | null;
  checks: HookCheck[];
}

export interface Insights {
  zoomPlan: ZoomEvent[];
  hook: Hook | null;
}

export type SfxCategory = "transicao" | "destaque" | "oferta" | "outro";

export interface SfxSound {
  id: string;
  name: string;
  category: SfxCategory;
  durationSec: number;
  createdAt: string;
}

export interface SfxEvent {
  id: string;
  startSec: number; // no tempo do vídeo original
  sfxId: string;
}

export const SFX_CATEGORIES: { id: SfxCategory; label: string; hint: string }[] = [
  { id: "transicao", label: "Transição", hint: "entra junto com os zooms (ex.: whoosh)" },
  { id: "destaque", label: "Destaque", hint: "entra na palavra destacada (ex.: pop)" },
  { id: "oferta", label: "Oferta", hint: "entra no preço ou desconto (ex.: ding)" },
  { id: "outro", label: "Outro", hint: "só uso manual" },
];
