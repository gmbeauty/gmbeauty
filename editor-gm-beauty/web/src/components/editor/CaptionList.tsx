"use client";

import { formatTimestamp } from "@/lib/format";
import type { CaptionSegment } from "@/lib/types";

export function CaptionList({
  captions,
  selectedId,
  onSelect,
  onChange,
}: {
  captions: CaptionSegment[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onChange: (id: string, patch: Partial<CaptionSegment>) => void;
}) {
  return (
    <div className="rounded-gm border border-gm-line bg-white">
      <h3 className="border-b border-gm-line px-4 py-3 text-sm font-medium text-gm-purple">Falas e legendas</h3>
      <ul className="divide-y divide-gm-line">
        {captions.map((c) => {
          const selected = c.id === selectedId;
          return (
            <li key={c.id} onClick={() => onSelect(c.id)} className={`space-y-2 px-4 py-3 ${selected ? "bg-gm-lilac-soft" : ""}`}>
              <div className="flex items-center gap-2 text-xs text-gm-muted">
                <span>{formatTimestamp(c.startSec)}</span>
                {selected && (
                  <>
                    <span>→</span>
                    <TimeInput label="Início" value={c.startSec} onChange={(v) => onChange(c.id, { startSec: v })} />
                    <TimeInput label="Fim" value={c.endSec} onChange={(v) => onChange(c.id, { endSec: v })} />
                  </>
                )}
              </div>
              <textarea
                value={c.text}
                rows={2}
                onFocus={() => onSelect(c.id)}
                onChange={(e) => onChange(c.id, { text: e.target.value })}
                aria-label={`Texto da legenda em ${formatTimestamp(c.startSec)}`}
                className="w-full resize-none rounded-lg border border-transparent bg-transparent p-1 text-sm text-gm-ink hover:border-gm-line focus:border-gm-lilac focus:bg-white focus:outline-none"
              />
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function TimeInput({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="flex items-center gap-1">
      {label}
      <input
        type="number"
        step={0.1}
        min={0}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-16 rounded border border-gm-line px-1 py-0.5 text-gm-ink"
      />
    </label>
  );
}
