import { allCuts } from "@/lib/cuts";
import { formatDuration } from "@/lib/format";
import type { CaptionSegment, BrollEvent, RenderSettings, SfxEvent, SilenceRange, ZoomEvent } from "@/lib/types";

export function Timeline({
  durationSec,
  captions,
  silences,
  zoomPlan,
  sfxEvents,
  brollEvents,
  settings,
  selectedId,
  currentSec,
  onSelect,
  onSeek,
}: {
  durationSec: number;
  captions: CaptionSegment[];
  silences: SilenceRange[];
  zoomPlan: ZoomEvent[];
  sfxEvents: SfxEvent[];
  brollEvents: BrollEvent[];
  settings: RenderSettings;
  selectedId: string | null;
  currentSec: number;
  onSelect: (id: string) => void;
  onSeek: (t: number) => void;
}) {
  const pct = (s: number) => `${(Math.min(s, durationSec) / durationSec) * 100}%`;
  const w = (a: number, b: number) => `${((Math.min(b, durationSec) - a) / durationSec) * 100}%`;
  const cuts = allCuts(silences, settings);

  return (
    <div className="overflow-x-auto rounded-gm border border-gm-line bg-white p-4">
      <div className="min-w-[560px]">
        <div className="mb-1 flex justify-between pl-24 text-[11px] text-gm-muted">
          <span>0:00</span>
          <span>{formatDuration(durationSec)}</span>
        </div>
        <div className="flex gap-2">
          <div className="grid w-22 shrink-0 grid-rows-6 gap-2 text-xs text-gm-muted">
            <span className="flex items-center">🎬 Vídeo</span>
            <span className="flex items-center">💬 Legendas</span>
            <span className="flex items-center">✂️ Cortes</span>
            <span className="flex items-center">🔍 Zoom</span>
            <span className="flex items-center">🔊 Sons</span>
            <span className="flex items-center">🎞️ B-roll</span>
          </div>
          <div className="relative grid flex-1 grid-rows-6 gap-2">
            {/* Vídeo: clique para ir a um ponto */}
            <button
              type="button"
              aria-label="Ir para este ponto do vídeo"
              className="relative h-10 rounded-md bg-gm-lilac-mid"
              onClick={(e) => {
                const r = e.currentTarget.getBoundingClientRect();
                onSeek(((e.clientX - r.left) / r.width) * durationSec);
              }}
            />

            {/* Legendas */}
            <div className="relative h-10 rounded-md bg-gm-bg">
              {captions.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => onSelect(c.id)}
                  title={c.text}
                  className={`absolute inset-y-1 truncate rounded-md px-1.5 text-left text-[10px] text-white ${
                    selectedId === c.id ? "bg-gm-purple ring-2 ring-gm-lilac" : "bg-gm-lilac hover:bg-gm-purple"
                  }`}
                  style={{ left: pct(c.startSec), width: w(c.startSec, c.endSec) }}
                >
                  {c.text}
                </button>
              ))}
            </div>

            {/* Cortes: tracejado = pausa encontrada; cheio = trecho que será removido */}
            <div className="relative h-10 rounded-md bg-gm-bg">
              {silences.map((s) => (
                <div key={s.id} title="Pausa encontrada" className="absolute inset-y-1 rounded-md border border-dashed border-rose-300 bg-rose-50" style={{ left: pct(s.startSec), width: w(s.startSec, s.endSec) }} />
              ))}
              {cuts.map(([a, b]) => (
                <div key={a} title="Será removido" className="absolute inset-y-2 rounded-md bg-rose-400" style={{ left: pct(a), width: w(a, b) }} />
              ))}
            </div>

            {/* Zoom: onde a imagem se aproxima suavemente */}
            <div className="relative h-10 rounded-md bg-gm-bg">
              {zoomPlan.map((z) => (
                <div
                  key={z.startSec}
                  title={`${z.kind === "settle" ? "Abertura" : "Zoom"} +${Math.round(z.amp * 100)}%`}
                  className="absolute inset-y-2 rounded-md bg-gm-lilac-mid ring-1 ring-gm-lilac"
                  style={{ left: pct(z.startSec), width: w(z.startSec, z.endSec) }}
                />
              ))}
            </div>

            {/* Sons: um traço por efeito sonoro */}
            <div className="relative h-10 rounded-md bg-gm-bg">
              {sfxEvents.map((e) => (
                <div
                  key={e.id}
                  title="Efeito sonoro"
                  className={`absolute inset-y-2 w-1.5 rounded-full ${settings.sfxEnabled ? "bg-gm-purple" : "bg-gm-lilac-mid"}`}
                  style={{ left: pct(e.startSec) }}
                />
              ))}
            </div>

            {/* B-roll: trechos em que um clipe seu cobre a imagem */}
            <div className="relative h-10 rounded-md bg-gm-bg">
              {brollEvents.map((e) => (
                <div
                  key={e.id}
                  title="B-roll"
                  className={`absolute inset-y-2 rounded-md ${settings.brollEnabled ? "bg-gm-lilac" : "bg-gm-lilac-mid"}`}
                  style={{ left: pct(e.startSec), width: w(e.startSec, e.endSec) }}
                />
              ))}
            </div>

            <div aria-hidden className="pointer-events-none absolute inset-y-0 w-0.5 bg-gm-purple" style={{ left: pct(currentSec) }} />
          </div>
        </div>
      </div>
    </div>
  );
}
