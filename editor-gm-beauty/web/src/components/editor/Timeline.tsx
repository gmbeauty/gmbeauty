import type { CaptionSegment, SilenceRange } from "@/lib/types";
import { formatDuration } from "@/lib/format";

export function Timeline({
  durationSec,
  captions,
  silences,
  removeSilences,
  selectedId,
  currentSec,
  onSelect,
}: {
  durationSec: number;
  captions: CaptionSegment[];
  silences: SilenceRange[];
  removeSilences: boolean;
  selectedId: string | null;
  currentSec: number;
  onSelect: (id: string) => void;
}) {
  const pct = (s: number) => `${(s / durationSec) * 100}%`;
  const w = (a: number, b: number) => `${((b - a) / durationSec) * 100}%`;

  return (
    <div className="overflow-x-auto rounded-gm border border-gm-line bg-white p-4">
      <div className="min-w-[560px] space-y-2">
        <div className="flex justify-between pl-24 text-[11px] text-gm-muted">
          <span>0:00</span>
          <span>{formatDuration(durationSec)}</span>
        </div>

        <Track label="🎬 Vídeo">
          <div className="absolute inset-y-1 left-0 right-0 rounded-md bg-gm-lilac-mid" />
        </Track>

        <Track label="💬 Legendas">
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
        </Track>

        <Track label="✂️ Cortes">
          {silences.map((s) => (
            <div
              key={s.id}
              title="Silêncio detectado"
              className={`absolute inset-y-1 rounded-md ${
                removeSilences ? "bg-rose-400" : "border border-dashed border-rose-400 bg-rose-50"
              }`}
              style={{ left: pct(s.startSec), width: w(s.startSec, s.endSec) }}
            />
          ))}
        </Track>

        {/* posição atual (playhead) */}
        <div className="pointer-events-none relative -mt-[calc(3*2.5rem+1.5rem)] ml-24 h-[calc(3*2.5rem+1rem)]">
          <div className="absolute inset-y-0 w-0.5 bg-gm-purple" style={{ left: pct(currentSec) }} />
        </div>
      </div>
    </div>
  );
}

function Track({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-22 shrink-0 text-xs text-gm-muted">{label}</span>
      <div className="relative h-10 flex-1 rounded-md bg-gm-bg">{children}</div>
    </div>
  );
}
