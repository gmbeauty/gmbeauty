"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/Button";
import { deleteSfx, listSfx, sfxAudioUrl, uploadSfx } from "@/lib/api";
import { SFX_CATEGORIES, type SfxCategory, type SfxSound } from "@/lib/types";

const msg = (e: unknown) => (e instanceof Error ? e.message : "Algo deu errado. Tente novamente.");

export function SfxLibrary() {
  const [sounds, setSounds] = useState<SfxSound[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<SfxCategory>("transicao");
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const audio = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    listSfx()
      .then((l) => !cancelled && setSounds(l))
      .catch((e) => !cancelled && setError(msg(e)));
    return () => {
      cancelled = true;
    };
  }, []);

  async function onFiles(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    setError(null);
    try {
      for (const f of Array.from(files)) {
        await uploadSfx(f, f.name.replace(/\.[^.]+$/, ""), category);
      }
      setSounds(await listSfx());
    } catch (e) {
      setError(msg(e));
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  async function remove(s: SfxSound) {
    if (!confirm(`Remover "${s.name}" da biblioteca? Ele também sai dos vídeos que o usam.`)) return;
    try {
      await deleteSfx(s.id);
      setSounds((cur) => cur?.filter((x) => x.id !== s.id) ?? null);
    } catch (e) {
      setError(msg(e));
    }
  }

  function play(id: string) {
    audio.current?.pause();
    audio.current = new Audio(sfxAudioUrl(id));
    audio.current.play().catch(() => setError("Não foi possível tocar este som."));
  }

  return (
    <section>
      <h2 className="text-xl font-semibold text-gm-purple">Efeitos sonoros</h2>
      <p className="mt-1 text-sm text-gm-muted">
        Envie seus próprios sons (MP3, WAV, M4A, AAC ou OGG, até 15 s). Confira se a licença de cada arquivo permite uso comercial.
        O editor só usa os sons que estão aqui e nunca mais de um a cada poucos segundos.
      </p>

      <div className="mt-4 rounded-gm border border-gm-line bg-gm-bg p-4">
        <div className="mb-3 text-xs font-medium uppercase tracking-wide text-gm-muted">Tipo dos próximos arquivos</div>
        <div className="grid gap-2 sm:grid-cols-2">
          {SFX_CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setCategory(c.id)}
              aria-pressed={category === c.id}
              className={`rounded-gm border p-3 text-left text-sm ${category === c.id ? "border-gm-lilac bg-gm-lilac-soft ring-2 ring-gm-lilac" : "border-gm-line bg-white hover:border-gm-lilac-mid"}`}
            >
              <div className="font-medium text-gm-purple">{c.label}</div>
              <div className="text-xs text-gm-muted">{c.hint}</div>
            </button>
          ))}
        </div>
        <input ref={input} type="file" multiple accept=".mp3,.wav,.m4a,.aac,.ogg,audio/*" className="hidden" onChange={(e) => onFiles(e.target.files)} />
        <Button className="mt-4" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "Enviando…" : "Enviar sons"}
        </Button>
      </div>

      {error && <p role="alert" className="mt-4 rounded-gm bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

      <ul className="mt-6 divide-y divide-gm-line rounded-gm border border-gm-line bg-white">
        {sounds === null && !error && <li className="p-4 text-sm text-gm-muted">Carregando…</li>}
        {sounds?.length === 0 && <li className="p-4 text-sm text-gm-muted">Nenhum som ainda. Envie alguns para o editor poder sugerir efeitos.</li>}
        {sounds?.map((s) => (
          <li key={s.id} className="flex items-center gap-3 p-3">
            <button type="button" onClick={() => play(s.id)} aria-label={`Ouvir ${s.name}`} className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gm-purple text-white hover:bg-[#3a1559]">▶</button>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-gm-ink">{s.name}</div>
              <div className="text-xs text-gm-muted">
                {SFX_CATEGORIES.find((c) => c.id === s.category)?.label} · {s.durationSec.toFixed(1).replace(".", ",")} s
              </div>
            </div>
            <button type="button" onClick={() => remove(s)} className="rounded-full px-3 py-1 text-sm text-gm-muted hover:bg-rose-50 hover:text-rose-700">Remover</button>
          </li>
        ))}
      </ul>
    </section>
  );
}
