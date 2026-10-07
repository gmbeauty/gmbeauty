"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/Button";
import { brollThumbUrl, deleteBroll, listBroll, patchBroll, uploadBroll } from "@/lib/api";
import type { BrollClip } from "@/lib/types";

const msg = (e: unknown) => (e instanceof Error ? e.message : "Algo deu errado. Tente novamente.");

export function BrollLibrary() {
  const [clips, setClips] = useState<BrollClip[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tag, setTag] = useState("");
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    listBroll()
      .then((l) => !cancelled && setClips(l))
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
        await uploadBroll(f, f.name.replace(/\.[^.]+$/, ""), tag);
      }
      setClips(await listBroll());
      setTag("");
    } catch (e) {
      setError(msg(e));
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  async function saveTag(c: BrollClip, value: string) {
    if (value === c.tag) return;
    try {
      const updated = await patchBroll(c.id, { tag: value });
      setClips((cur) => cur?.map((x) => (x.id === c.id ? updated : x)) ?? null);
    } catch (e) {
      setError(msg(e));
    }
  }

  async function remove(c: BrollClip) {
    if (!confirm(`Remover "${c.name}" da biblioteca? Ele também sai dos vídeos que o usam.`)) return;
    try {
      await deleteBroll(c.id);
      setClips((cur) => cur?.filter((x) => x.id !== c.id) ?? null);
    } catch (e) {
      setError(msg(e));
    }
  }

  return (
    <section>
      <h2 className="text-xl font-semibold text-gm-purple">B-roll (clipes de produto e aplicação)</h2>
      <p className="mt-1 text-sm text-gm-muted">
        Envie vídeos seus (MP4 ou MOV, até 500 MB). Em “Como você fala”, escreva o nome do jeito que costuma dizer no vídeo — o editor só sugere o clipe quando a fala citar esse nome.
        Separe variações por vírgula.
      </p>

      <div className="mt-4 rounded-gm border border-gm-line bg-gm-bg p-4">
        <label className="block text-xs font-medium uppercase tracking-wide text-gm-muted" htmlFor="broll-tag">Como você fala (para os próximos clipes)</label>
        <input
          id="broll-tag"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          placeholder="ex.: base Ruby Rose, base da Ruby Rose"
          className="mt-2 w-full rounded-lg border border-gm-line bg-white px-3 py-2 text-sm text-gm-ink focus:border-gm-lilac focus:outline-none"
        />
        <input ref={input} type="file" multiple accept=".mp4,.mov,video/mp4,video/quicktime" className="hidden" onChange={(e) => onFiles(e.target.files)} />
        <Button className="mt-4" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "Enviando…" : "Enviar clipes"}
        </Button>
      </div>

      {error && <p role="alert" className="mt-4 rounded-gm bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

      <ul className="mt-6 grid gap-4 sm:grid-cols-2">
        {clips === null && !error && <li className="text-sm text-gm-muted">Carregando…</li>}
        {clips?.length === 0 && <li className="text-sm text-gm-muted sm:col-span-2">Nenhum clipe ainda.</li>}
        {clips?.map((c) => (
          <li key={c.id} className="overflow-hidden rounded-gm border border-gm-line bg-white">
            <div className="flex gap-3 p-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={brollThumbUrl(c.id)} alt="" className="h-24 w-16 shrink-0 rounded-lg bg-gm-lilac-soft object-cover" />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-gm-ink" title={c.name}>{c.name}</div>
                <div className="text-xs text-gm-muted">{c.durationSec.toFixed(1).replace(".", ",")} s · {c.width}×{c.height}</div>
                <label className="mt-2 block text-[11px] text-gm-muted">
                  Como você fala
                  <input
                    key={c.tag}
                    defaultValue={c.tag}
                    onBlur={(e) => saveTag(c, e.target.value.trim())}
                    placeholder="(sem etiqueta: não é sugerido)"
                    className="mt-0.5 w-full rounded-lg border border-gm-line px-2 py-1 text-xs text-gm-ink focus:border-gm-lilac focus:outline-none"
                  />
                </label>
              </div>
            </div>
            <div className="border-t border-gm-line px-3 py-2 text-right">
              <button type="button" onClick={() => remove(c)} className="text-xs text-gm-muted hover:text-rose-700">Remover</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
