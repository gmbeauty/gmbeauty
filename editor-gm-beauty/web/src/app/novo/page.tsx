"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Button } from "@/components/Button";
import { OptionCard } from "@/components/OptionCard";
import { UploadDropzone, type VideoInfo } from "@/components/UploadDropzone";
import { analyzeProject, createProject } from "@/lib/api";
import { CONTENT_TYPES } from "@/lib/content-types";
import { STYLE_PRESETS, SUGGESTED_STYLE, settingsForPreset } from "@/lib/presets";
import type { ContentTypeId, StylePresetId } from "@/lib/types";

export default function NewVideoPage() {
  const router = useRouter();
  const [info, setInfo] = useState<VideoInfo | null>(null);
  const [contentType, setContentType] = useState<ContentTypeId | null>(null);
  const [style, setStyle] = useState<StylePresetId | null>(null);
  const [uploadPct, setUploadPct] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ready = info && contentType && style && uploadPct === null;

  function pickType(id: ContentTypeId) {
    setContentType(id);
    setStyle((current) => current ?? SUGGESTED_STYLE[id]); // sugestão; dá para trocar
  }

  async function start() {
    if (!info || !contentType || !style) return;
    setError(null);
    setUploadPct(0);
    try {
      const project = await createProject(
        info.file,
        { contentType, style, settings: settingsForPreset(style) },
        setUploadPct,
      );
      await analyzeProject(project.id); // edição automática começa já
      router.push(`/editor/${project.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Algo deu errado. Tente novamente.");
      setUploadPct(null);
    }
  }

  return (
    <>
      <Header>
        <Link href="/" className="text-sm text-gm-muted hover:text-gm-purple">← Voltar</Link>
      </Header>
      <main className="mx-auto w-full max-w-3xl flex-1 space-y-10 px-4 py-8 sm:px-6">
        <section>
          <h1 className="mb-4 text-2xl font-semibold tracking-tight text-gm-purple">Novo vídeo</h1>
          <UploadDropzone info={info} onInfo={setInfo} />
        </section>

        {info && (
          <section>
            <h2 className="mb-1 text-xl font-semibold text-gm-purple">Que tipo de vídeo você está criando?</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {CONTENT_TYPES.map((t) => (
                <OptionCard key={t.id} selected={contentType === t.id} title={t.label} description={t.description} onClick={() => pickType(t.id)} />
              ))}
            </div>
          </section>
        )}

        {info && contentType && (
          <section>
            <h2 className="mb-1 text-xl font-semibold text-gm-purple">Escolha um estilo de edição</h2>
            <p className="text-sm text-gm-muted">Já deixamos um sugerido para esse tipo de vídeo. Você pode trocar.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {STYLE_PRESETS.map((s) => (
                <OptionCard key={s.id} selected={style === s.id} title={s.label} description={s.description} onClick={() => setStyle(s.id)} />
              ))}
            </div>
          </section>
        )}

        {error && <p role="alert" className="rounded-gm bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}

        {uploadPct !== null && (
          <div aria-live="polite">
            <div className="h-2 overflow-hidden rounded-full bg-gm-lilac-soft">
              <div className="h-full bg-gm-purple transition-all" style={{ width: `${uploadPct}%` }} />
            </div>
            <p className="mt-2 text-sm text-gm-muted">
              {uploadPct < 100 ? `Enviando vídeo… ${Math.round(uploadPct)}%` : "Preparando a edição automática…"}
            </p>
          </div>
        )}

        <div className="flex items-center justify-end">
          <Button disabled={!ready} onClick={start}>Editar automaticamente</Button>
        </div>
      </main>
    </>
  );
}
