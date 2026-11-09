"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/Button";
import { formatTimestamp } from "@/lib/format";
import type { BrollClip, BrollEvent } from "@/lib/types";

export function BrollCard({
  enabled,
  events,
  clips,
  currentSec,
  durationSec,
  suggested,
  onToggle,
  onSuggest,
  onAdd,
  onChange,
  onRemove,
  onSeek,
}: {
  enabled: boolean;
  events: BrollEvent[];
  clips: BrollClip[];
  currentSec: number;
  durationSec: number;
  suggested: boolean; // já clicou em "Sugerir" neste vídeo (para explicar lista vazia)
  onToggle: (v: boolean) => void;
  onSuggest: () => void;
  onAdd: (clipId: string) => void;
  onChange: (id: string, patch: Partial<BrollEvent>) => void;
  onRemove: (id: string) => void;
  onSeek: (t: number) => void;
}) {
  const [pick, setPick] = useState("");
  const chosen = pick || clips[0]?.id || "";
  const clipOf = (id: string) => clips.find((c) => c.id === id);

  return (
    <section className="rounded-gm border border-gm-line bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-gm-purple">B-roll</h3>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-gm-ink">
          Usar na exportação
          <input type="checkbox" checked={enabled} onChange={(e) => onToggle(e.target.checked)} className="h-5 w-5 accent-[#4B1C71]" />
        </label>
      </div>

      {clips.length === 0 ? (
        <p className="text-sm text-gm-muted">
          A Biblioteca GM ainda não tem clipes. <Link href="/biblioteca" className="underline hover:text-gm-purple">Envie alguns</Link> e escreva como você fala cada produto.
        </p>
      ) : (
        <>
          <Button variant="soft" className="!px-4 !py-1.5 text-xs" onClick={onSuggest}>Sugerir B-roll</Button>
          <p className="mt-2 text-xs text-gm-muted">O B-roll cobre a imagem, mas a sua fala continua. Só é sugerido quando a fala cita um produto etiquetado.</p>

          <ul className="mt-3 divide-y divide-gm-line text-sm">
            {events.map((e) => {
              const clip = clipOf(e.clipId);
              const max = Math.min(clip?.durationSec ?? 5, durationSec - e.startSec);
              return (
                <li key={e.id} className="flex flex-wrap items-center gap-2 py-2">
                  <button type="button" onClick={() => onSeek(e.startSec)} className="w-14 shrink-0 text-left text-xs tabular-nums text-gm-muted underline hover:text-gm-purple">
                    {formatTimestamp(e.startSec)}
                  </button>
                  <select value={e.clipId} onChange={(ev) => onChange(e.id, { clipId: ev.target.value })} aria-label="Clipe deste B-roll" className="min-w-0 flex-1 rounded-lg border border-gm-line px-2 py-1 text-xs text-gm-ink">
                    {!clip && <option value={e.clipId}>(removido)</option>}
                    {clips.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                  <label className="flex items-center gap-1 text-xs text-gm-muted">
                    Duração
                    <input
                      type="number" step={0.1} min={0.8} max={Math.max(0.8, max)}
                      value={Number((e.endSec - e.startSec).toFixed(1))}
                      onChange={(ev) => onChange(e.id, { endSec: e.startSec + Number(ev.target.value) })}
                      className="w-14 rounded border border-gm-line px-1 py-0.5 text-gm-ink"
                    />
                    s
                  </label>
                  <button type="button" onClick={() => onRemove(e.id)} className="shrink-0 text-xs text-gm-muted underline hover:text-rose-700">Remover</button>
                </li>
              );
            })}
            {events.length === 0 && (
              <li className="py-3 text-xs text-gm-muted">
                {suggested
                  ? "Nenhum trecho deste vídeo cita um produto etiquetado na biblioteca. Confira se a etiqueta está escrita do jeito que você fala, ou adicione manualmente."
                  : "Nenhum B-roll neste vídeo. Clique em “Sugerir B-roll” ou adicione um manualmente."}
              </li>
            )}
          </ul>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <select value={chosen} onChange={(e) => setPick(e.target.value)} aria-label="Clipe para adicionar" className="rounded-lg border border-gm-line px-2 py-1 text-gm-ink">
              {clips.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <button type="button" disabled={!chosen} onClick={() => onAdd(chosen)} className="rounded-full bg-gm-lilac-soft px-3 py-1 text-gm-purple hover:bg-gm-lilac-mid disabled:opacity-50">
              Adicionar em {formatTimestamp(currentSec)}
            </button>
          </div>
        </>
      )}
    </section>
  );
}
