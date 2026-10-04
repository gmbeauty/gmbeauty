// DADOS FICTÍCIOS (Fase 1). Serão substituídos por chamadas à API (lib/api.ts).
import type { CaptionSegment, Project, SilenceRange } from "./types";

export const MOCK_PROJECTS: Project[] = [
  { id: "demo-1", name: "Truque de base fluida", createdAt: "2026-10-02T14:00:00Z", durationSec: 38, status: "ready", contentType: "tutorial", style: "gm-clean", thumbnailGradient: "from-[#B57EDC] to-[#4B1C71]" },
  { id: "demo-2", name: "Kit renovação – oferta", createdAt: "2026-10-03T10:30:00Z", durationSec: 24, status: "processing", contentType: "oferta", style: "gm-oferta", thumbnailGradient: "from-[#d9bdf0] to-[#B57EDC]" },
  { id: "demo-3", name: "Review gloss labial", createdAt: "2026-10-03T18:15:00Z", durationSec: 52, status: "draft", contentType: "ugc", style: "gm-viral", thumbnailGradient: "from-[#e9ddf5] to-[#9a6bc4]" },
  { id: "demo-4", name: "Skincare rotina noite", createdAt: "2026-10-01T09:00:00Z", durationSec: 61, status: "error", contentType: "produto", style: "gm-produto", thumbnailGradient: "from-[#cfc3da] to-[#6d3a99]" },
];

export const MOCK_CAPTIONS: CaptionSegment[] = [
  { id: "c1", startSec: 0, endSec: 2.4, text: "Você ainda aplica base desse jeito?", highlightWords: ["base"] },
  { id: "c2", startSec: 2.4, endSec: 5.5, text: "Então precisa conhecer esse truque." },
  { id: "c3", startSec: 5.5, endSec: 9.8, text: "Essa base tem acabamento natural e dura o dia todo.", highlightWords: ["natural"] },
  { id: "c4", startSec: 11.2, endSec: 15, text: "Aplique com a esponja em movimentos de batida." },
  { id: "c5", startSec: 15, endSec: 19.5, text: "Olha a diferença na pele." },
];

export const MOCK_SILENCES: SilenceRange[] = [
  { id: "s1", startSec: 9.8, endSec: 11.2 },
  { id: "s2", startSec: 19.5, endSec: 20.6 },
];

export const MOCK_VIDEO_DURATION_SEC = 22;

export function getMockProject(id: string): Project {
  return MOCK_PROJECTS.find((p) => p.id === id) ?? MOCK_PROJECTS[0];
}
