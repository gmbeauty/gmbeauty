"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/Button";
import { formatTimestamp } from "@/lib/format";
import type { SfxEvent, SfxSound } from "@/lib/types";

export function SfxCard({
  enabled,
  gainDb,
  events,
  sounds,
  currentSec,
  onToggle,
  onGain,
  onSuggest,
  onAdd,
  onChangeSound,
  onRemove,
  onPreview,
}: {
  enabled: boolean;
  gainDb: number;
  events: SfxEvent[];
  sounds: SfxSound[];
  currentSec: number;
  onToggle: (v: boolean) => void;
  onGain: (db: number) => void;
  onSuggest: () => void;
  onAdd: (sfxId: string) => void;
  onChangeSound: (id: string, sfxId: string) => void;
  onRemove: (id: string) => void;
  onPreview: (sfxId: string) => void;
}) {
  const [pick, setPick] = useState("");
  const chosen = pick || sounds[0]?.id || "";
  const name = (id: string) => sounds.find((s) => s.id === id)?.name ?? "(removido)";

  return (
    <section className="rounded-gm border border-gm-line bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-gm-purple">Efeitos sonoros</h3>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-gm-ink">
          Usar na exportação
          <input type="checkbox" checked={enabled} onChange={(e) => onToggle(e.target.checked)} className="h-5 w-5 accent-[#4B1C71]" />
        </label>
      </div>

      {sounds.length === 0 ? (
        <p className="text-sm text-gm-muted">
          A Biblioteca GM ainda não tem sons. <Link href="/biblioteca" className="underline hover:text-gm-purple">Envie alguns</Link> para o editor sugerir efeitos.
        </p>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="soft" className="!px-4 !py-1.5 text-xs" onClick={onSuggest}>Sugerir efeitos</Button>
            <label className="flex flex-1 items-center gap-2 text-xs text-gm-muted">
              Volume
              <input type="range" min={-30} max={-4} step={1} value={gainDb} onChange={(e) => onGain(Number(e.target.value))} className="min-w-24 flex-1 accent-[#4B1C71]" />
              <span className="w-12 text-right tabular-nums">{gainDb} dB</span>
            </label>
          </div>

          <ul className="mt-3 divide-y divide-gm-line text-sm">
            {events.map((e) => (
              <li key={e.id} className="flex items-center gap-2 py-2">
                <span className="w-14 shrink-0 text-xs tabular-nums text-gm-muted">{formatTimestamp(e.startSec)}</span>
                <select
                  value={e.sfxId}
                  onChange={(ev) => onChangeSound(e.id, ev.target.value)}
                  aria-label="Som deste efeito"
                  className="min-w-0 flex-1 rounded-lg border border-gm-line px-2 py-1 text-xs text-gm-ink"
                >
                  {!sounds.some((s) => s.id === e.sfxId) && <option value={e.sfxId}>(removido)</option>}
                  {sounds.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
                <button type="button" onClick={() => onPreview(e.sfxId)} aria-label={`Ouvir ${name(e.sfxId)}`} className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-gm-lilac-soft text-xs text-gm-purple hover:bg-gm-lilac-mid">▶</button>
                <button type="button" onClick={() => onRemove(e.id)} className="shrink-0 text-xs text-gm-muted underline hover:text-rose-700">Remover</button>
              </li>
            ))}
            {events.length === 0 && (
              <li className="py-3 text-xs text-gm-muted">
                Nenhum efeito neste vídeo. Clique em “Sugerir efeitos” (usa zooms, palavras destacadas e preços) ou adicione um manualmente.
              </li>
            )}
          </ul>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <select value={chosen} onChange={(e) => setPick(e.target.value)} aria-label="Som para adicionar" className="rounded-lg border border-gm-line px-2 py-1 text-gm-ink">
              {sounds.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
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
