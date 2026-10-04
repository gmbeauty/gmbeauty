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
  analyzed: boolean;
  hasOutput: boolean;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}
