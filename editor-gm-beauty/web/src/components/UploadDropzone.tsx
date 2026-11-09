"use client";

import { useRef, useState } from "react";
import { formatDuration, formatSize } from "@/lib/format";

export interface VideoInfo {
  file: File;
  name: string;
  sizeBytes: number;
  // Podem faltar: alguns navegadores não leem certos formatos (ex.: HEVC de iPhone).
  // O servidor lê o vídeo de qualquer forma, então isso não bloqueia o envio.
  durationSec?: number;
  width?: number;
  height?: number;
}

const ACCEPTED = ["video/mp4", "video/quicktime"]; // MP4 e MOV

// Fase 1: lê as informações do vídeo no próprio navegador.
// O arquivo AINDA NÃO é enviado a nenhum servidor (isso é a Fase 2).
function readVideoInfo(file: File): Promise<VideoInfo> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      resolve({
        file,
        name: file.name,
        sizeBytes: file.size,
        durationSec: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
      });
      URL.revokeObjectURL(url);
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("unreadable"));
    };
    setTimeout(() => reject(new Error("timeout")), 8000);
    video.src = url;
  });
}

export function UploadDropzone({
  info,
  onInfo,
}: {
  info: VideoInfo | null;
  onInfo: (info: VideoInfo | null) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setError(null);
    const isVideo = ACCEPTED.includes(file.type) || /\.(mp4|mov)$/i.test(file.name);
    if (!isVideo) {
      setError("Formato não aceito. Envie um vídeo MP4 ou MOV.");
      return;
    }
    try {
      onInfo(await readVideoInfo(file));
    } catch {
      onInfo({ file, name: file.name, sizeBytes: file.size });
    }
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFile(e.dataTransfer.files[0]);
        }}
        className={`rounded-gm border-2 border-dashed p-8 text-center transition sm:p-12 ${
          dragging ? "border-gm-lilac bg-gm-lilac-soft" : "border-gm-lilac-mid bg-gm-bg"
        }`}
      >
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-gm-lilac-soft text-2xl text-gm-purple">↑</div>
        <p className="text-lg font-medium text-gm-purple">Arraste seu vídeo aqui</p>
        <p className="my-1 text-sm text-gm-muted">ou</p>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="rounded-full bg-gm-purple px-5 py-2.5 text-sm font-medium text-white hover:bg-[#3a1559]"
        >
          Selecionar vídeo
        </button>
        <p className="mt-3 text-xs text-gm-muted">MP4 ou MOV</p>
        <input
          ref={inputRef}
          type="file"
          accept="video/mp4,video/quicktime,.mp4,.mov"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      {error && <p role="alert" className="mt-3 text-sm text-rose-600">{error}</p>}

      {info && (
        <dl className="mt-4 grid grid-cols-2 gap-4 rounded-gm border border-gm-line bg-white p-4 text-sm sm:grid-cols-4">
          <Info label="Nome" value={info.name} />
          <Info label="Duração" value={info.durationSec ? formatDuration(info.durationSec) : "—"} />
          <Info label="Tamanho" value={formatSize(info.sizeBytes)} />
          <Info label="Resolução" value={info.width ? `${info.width}×${info.height}` : "—"} />
        </dl>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-gm-muted">{label}</dt>
      <dd className="truncate font-medium text-gm-ink" title={value}>{value}</dd>
    </div>
  );
}
