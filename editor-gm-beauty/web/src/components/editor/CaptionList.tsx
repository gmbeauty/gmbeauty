"use client";

import { useEffect, useRef } from "react";
import { cleanWord } from "@/lib/captions";
import { formatTimestamp } from "@/lib/format";
import type { CaptionSegment } from "@/lib/types";

export function CaptionList({
  captions,
  selectedId,
  onSelect,
  onChange,
  saveState,
}: {
  captions: CaptionSegment[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onChange: (id: string, patch: Partial<CaptionSegment>) => void;
  saveState: "idle" | "saving" | "saved" | "error";
}) {
  const selectedRef = useRef<HTMLLIElement>(null);
  useEffect(() => {
    selectedRef.current?.scrollIntoView({ block: "nearest" });
  }, [selectedId]);

  return (
    <div className="flex min-h-0 flex-col rounded-gm border border-gm-line bg-white">
      <div className="flex items-center justify-between border-b border-gm-line px-4 py-3">
        <h3 className="text-sm font-medium text-gm-purple">Falas e legendas</h3>
        <span className="text-xs text-gm-muted" aria-live="polite">
          {saveState === "saving" && "Salvando…"}
          {saveState === "saved" && "Salvo ✓"}
          {saveState === "error" && <span className="text-rose-600">Não foi possível salvar</span>}
        </span>
      </div>
      <p className="px-4 pt-3 text-xs text-gm-muted">Clique para corrigir qualquer palavra (nomes de marcas e produtos, por exemplo).</p>
      <ul className="max-h-[440px] divide-y divide-gm-line overflow-y-auto">
        {captions.map((c) => {
          const selected = c.id === selectedId;
          const tokens = c.text.split(/\s+/).filter(Boolean);
          return (
            <li key={c.id} ref={selected ? selectedRef : undefined} onClick={() => onSelect(c.id)} className={`space-y-2 px-4 py-3 ${selected ? "bg-gm-lilac-soft" : ""}`}>
              <div className="flex flex-wrap items-center gap-2 text-xs text-gm-muted">
                {selected ? (
                  <>
                    <TimeInput label="Início" value={c.startSec} onChange={(v) => onChange(c.id, { startSec: v })} />
                    <TimeInput label="Fim" value={c.endSec} onChange={(v) => onChange(c.id, { endSec: v })} />
                  </>
                ) : (
                  <span>{formatTimestamp(c.startSec)}</span>
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
              {selected && tokens.length > 0 && (
                <div>
                  <div className="mb-1 text-[11px] text-gm-muted">Palavras em destaque (clique para marcar):</div>
                  <div className="flex flex-wrap gap-1">
                    {tokens.map((t, i) => {
                      const key = cleanWord(t);
                      const on = c.highlightWords.includes(key);
                      return (
                        <button
                          key={i}
                          type="button"
                          aria-pressed={on}
                          onClick={() =>
                            onChange(c.id, { highlightWords: on ? c.highlightWords.filter((w) => w !== key) : [...c.highlightWords, key] })
                          }
                          className={`rounded-full px-2 py-0.5 text-xs ${on ? "bg-gm-lilac text-white" : "bg-white text-gm-purple ring-1 ring-gm-line hover:ring-gm-lilac"}`}
                        >
                          {t}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </li>
          );
        })}
        {captions.length === 0 && <li className="px-4 py-6 text-sm text-gm-muted">Nenhuma fala encontrada neste vídeo.</li>}
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
      s
    </label>
  );
}
