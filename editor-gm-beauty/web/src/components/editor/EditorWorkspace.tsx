"use client";

import { useState } from "react";
import { Button } from "@/components/Button";
import { CaptionList } from "./CaptionList";
import { SidePanel } from "./SidePanel";
import { Timeline } from "./Timeline";
import { VideoPreview } from "./VideoPreview";
import { MOCK_CAPTIONS, MOCK_SILENCES, MOCK_VIDEO_DURATION_SEC } from "@/lib/mock-data";
import type { CaptionSegment, EditorSettings } from "@/lib/types";

export function EditorWorkspace({ initial }: { initial: Pick<EditorSettings, "contentType" | "style"> }) {
  const [settings, setSettings] = useState<EditorSettings>({
    ...initial,
    captionMode: "highlight",
    fontSize: "md",
    position: "bottom",
    logo: "none",
    removeSilences: false,
    showSafeZone: true,
  });
  const [captions, setCaptions] = useState<CaptionSegment[]>(MOCK_CAPTIONS);
  const [selectedId, setSelectedId] = useState<string | null>(MOCK_CAPTIONS[0].id);
  const [currentSec, setCurrentSec] = useState(1);

  const active = captions.find((c) => currentSec >= c.startSec && currentSec < c.endSec);
  const selected = captions.find((c) => c.id === selectedId);

  function select(id: string) {
    setSelectedId(id);
    const c = captions.find((x) => x.id === id);
    if (c) setCurrentSec(c.startSec + 0.01);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="min-w-0 space-y-6">
        <div className="grid gap-6 md:grid-cols-[300px_1fr]">
          <div>
            <VideoPreview settings={settings} caption={active ?? selected} />
            <input
              type="range"
              min={0}
              max={MOCK_VIDEO_DURATION_SEC}
              step={0.1}
              value={currentSec}
              onChange={(e) => setCurrentSec(Number(e.target.value))}
              aria-label="Posição do vídeo (demonstração)"
              className="mt-4 w-full accent-[#4B1C71]"
            />
          </div>
          <CaptionList
            captions={captions}
            selectedId={selectedId}
            onSelect={select}
            onChange={(id, patch) => setCaptions((cs) => cs.map((c) => (c.id === id ? { ...c, ...patch } : c)))}
          />
        </div>

        <Timeline
          durationSec={MOCK_VIDEO_DURATION_SEC}
          captions={captions}
          silences={MOCK_SILENCES}
          removeSilences={settings.removeSilences}
          selectedId={selectedId}
          currentSec={currentSec}
          onSelect={select}
        />
      </div>

      <div className="space-y-4">
        <SidePanel settings={settings} onChange={(p) => setSettings((s) => ({ ...s, ...p }))} silenceCount={MOCK_SILENCES.length} />
        <Button className="w-full" disabled title="Exportação chega na Fase 8">Exportar vídeo</Button>
        <p className="text-center text-xs text-gm-muted">Fase 1: a exportação ainda não está ativa.</p>
      </div>
    </div>
  );
}
