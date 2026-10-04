// Tipos centrais do Editor GM Beauty.
// Quando o backend (FastAPI) existir, estes tipos espelham o que a API devolve.

export type ProjectStatus = "draft" | "processing" | "ready" | "error";

export type ContentTypeId =
  | "ugc"
  | "produto"
  | "tutorial"
  | "oferta"
  | "falando-camera";

export type StylePresetId = "gm-clean" | "gm-viral" | "gm-produto" | "gm-oferta";

export interface Project {
  id: string;
  name: string;
  createdAt: string; // ISO
  durationSec: number;
  status: ProjectStatus;
  contentType: ContentTypeId;
  style: StylePresetId;
  thumbnailGradient: string; // Fase 1: gradiente no lugar de thumbnail real
}

export interface CaptionSegment {
  id: string;
  startSec: number;
  endSec: number;
  text: string;
  highlightWords?: string[];
}

export interface SilenceRange {
  id: string;
  startSec: number;
  endSec: number;
}

export type CaptionMode = "traditional" | "highlight" | "word-by-word";
export type CaptionSize = "sm" | "md" | "lg";
export type CaptionPosition = "top" | "middle" | "bottom";
export type LogoPosition = "none" | "top" | "bottom" | "watermark";

// Tudo o que o painel lateral controla. Na Fase 5 estas opções viram
// parâmetros de renderização enviados ao backend.
export interface EditorSettings {
  contentType: ContentTypeId;
  style: StylePresetId;
  captionMode: CaptionMode;
  fontSize: CaptionSize;
  position: CaptionPosition;
  logo: LogoPosition;
  removeSilences: boolean;
  showSafeZone: boolean;
}
