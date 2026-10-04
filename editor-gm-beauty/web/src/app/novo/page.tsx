"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Button } from "@/components/Button";
import { OptionCard } from "@/components/OptionCard";
import { UploadDropzone, type VideoInfo } from "@/components/UploadDropzone";
import { CONTENT_TYPES } from "@/lib/content-types";
import { STYLE_PRESETS } from "@/lib/presets";
import type { ContentTypeId, StylePresetId } from "@/lib/types";

export default function NewVideoPage() {
  const router = useRouter();
  const [info, setInfo] = useState<VideoInfo | null>(null);
  const [contentType, setContentType] = useState<ContentTypeId | null>(null);
  const [style, setStyle] = useState<StylePresetId | null>(null);

  const ready = info && contentType && style;

  function start() {
    // Fase 1: abre o editor de demonstração. Na Fase 2 isto cria o projeto
    // de verdade e envia o vídeo ao servidor.
    router.push(`/editor/demo-1?tipo=${contentType}&estilo=${style}`);
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
                <OptionCard key={t.id} selected={contentType === t.id} title={t.label} description={t.description} onClick={() => setContentType(t.id)} />
              ))}
            </div>
          </section>
        )}

        {info && contentType && (
          <section>
            <h2 className="mb-1 text-xl font-semibold text-gm-purple">Escolha um estilo de edição</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {STYLE_PRESETS.map((s) => (
                <OptionCard key={s.id} selected={style === s.id} title={s.label} description={s.description} onClick={() => setStyle(s.id)} />
              ))}
            </div>
          </section>
        )}

        <div className="flex items-center justify-end gap-3">
          <p className="text-xs text-gm-muted">Fase 1: o vídeo ainda não é enviado; o editor abre com dados de demonstração.</p>
          <Button disabled={!ready} onClick={start}>Continuar para o editor</Button>
        </div>
      </main>
    </>
  );
}
