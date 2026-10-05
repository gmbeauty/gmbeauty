"use client";

import { useEffect, useRef, useState } from "react";
import { urls } from "@/lib/api";
import { activeWordIndex, cleanWord, FONT_PX, GM_COLORS, MAX_CHARS, OUTLINE_FOR, wrapLines } from "@/lib/captions";
import { allCuts } from "@/lib/cuts";
import { formatDuration } from "@/lib/format";
import { SAFE_ZONE } from "@/lib/safe-zone";
import { zoomAt } from "@/lib/zoom";
import type { CaptionSegment, Project, RenderSettings, ZoomEvent } from "@/lib/types";

export function VideoPreview({
  project,
  settings,
  captions,
  showSafeZone,
  zoomPlan,
  logoUrl,
  videoRef,
  currentSec,
  onTime,
}: {
  project: Project;
  settings: RenderSettings;
  captions: CaptionSegment[];
  showSafeZone: boolean;
  zoomPlan: ZoomEvent[];
  logoUrl: string | null;
  videoRef: React.RefObject<HTMLVideoElement | null>;
  currentSec: number;
  onTime: (t: number) => void;
}) {
  const [playing, setPlaying] = useState(false);
  const cutsRef = useRef<[number, number][]>([]);
  useEffect(() => {
    cutsRef.current = allCuts(project.silences, settings);
  }, [settings, project.silences]);

  // Acompanha o vídeo quadro a quadro e, se "remover silêncios" estiver ligado,
  // pula os trechos que serão cortados (prévia fiel ao resultado).
  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    const tick = () => {
      const v = videoRef.current;
      if (v) {
        const cut = cutsRef.current.find(([a, b]) => v.currentTime >= a && v.currentTime < b);
        if (cut) v.currentTime = cut[1];
        onTime(v.currentTime);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, videoRef, onTime]);

  const active = captions.find((c) => currentSec >= c.startSec && currentSec < c.endSec);
  const toggle = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) v.play();
    else v.pause();
  };

  return (
    <div>
      <div
        className="relative mx-auto aspect-[9/16] w-full max-w-[300px] overflow-hidden rounded-[1.75rem] border-[6px] border-gm-ink bg-gm-ink shadow-xl"
        style={{ containerType: "inline-size" }}
      >
        <video
          ref={videoRef}
          src={urls.video(project.id)}
          playsInline
          preload="metadata"
          onClick={toggle}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onSeeked={(e) => onTime(e.currentTarget.currentTime)}
          className="absolute inset-0 h-full w-full cursor-pointer object-contain"
          style={{ transform: `scale(${zoomAt(zoomPlan, currentSec)})` }}
        />

        {showSafeZone && (
          <div aria-hidden className="pointer-events-none absolute inset-0">
            <div className="absolute inset-x-0 top-0 bg-rose-500/25" style={{ height: `${SAFE_ZONE.topPct}%` }} />
            <div className="absolute inset-x-0 bottom-0 bg-rose-500/25" style={{ height: `${SAFE_ZONE.bottomPct}%` }} />
            <div className="absolute bg-rose-500/25" style={{ right: 0, width: `${SAFE_ZONE.rightPct}%`, top: `${SAFE_ZONE.topPct}%`, bottom: `${SAFE_ZONE.bottomPct}%` }} />
          </div>
        )}

        {settings.logoPosition !== "none" && logoUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={logoUrl}
            alt=""
            className="pointer-events-none absolute h-auto"
            style={{
              width: `${settings.logoSizePct}%`,
              opacity: settings.logoPosition === "watermark" ? Math.min(settings.logoOpacity, 0.4) : settings.logoOpacity,
              ...(settings.logoPosition === "bottom"
                ? { left: `${SAFE_ZONE.leftPct}%`, bottom: `calc(${SAFE_ZONE.bottomPct}% + 1%)` }
                : settings.logoPosition === "watermark"
                  ? { left: "50%", transform: "translateX(-50%)", top: `calc(${SAFE_ZONE.topPct}% + 1%)` }
                  : { left: `${SAFE_ZONE.leftPct}%`, top: `calc(${SAFE_ZONE.topPct}% + 1%)` }),
            }}
          />
        )}

        {active && <CaptionOverlay caption={active} settings={settings} t={currentSec} />}
      </div>

      <div className="mx-auto mt-3 flex max-w-[300px] items-center gap-3">
        <button
          type="button"
          onClick={toggle}
          aria-label={playing ? "Pausar" : "Reproduzir"}
          className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gm-purple text-white hover:bg-[#3a1559]"
        >
          {playing ? "❚❚" : "▶"}
        </button>
        <input
          type="range"
          min={0}
          max={project.durationSec}
          step={0.05}
          value={currentSec}
          onChange={(e) => {
            const t = Number(e.target.value);
            if (videoRef.current) videoRef.current.currentTime = t;
            onTime(t);
          }}
          aria-label="Posição do vídeo"
          className="w-full accent-[#4B1C71]"
        />
        <span className="w-10 shrink-0 text-right text-xs tabular-nums text-gm-muted">{formatDuration(currentSec)}</span>
      </div>
    </div>
  );
}

function CaptionOverlay({ caption, settings, t }: { caption: CaptionSegment; settings: RenderSettings; t: number }) {
  const tokens = caption.text.split(/\s+/).filter(Boolean);
  const lines = wrapLines(tokens, MAX_CHARS[settings.fontSize]);
  const marked = new Set(caption.highlightWords);
  const activeIdx = settings.captionMode === "word-by-word" ? activeWordIndex(caption, tokens, t) : -1;
  const fontPx = FONT_PX[settings.fontSize];

  const pos =
    settings.position === "top"
      ? { top: `${SAFE_ZONE.topPct}%` }
      : settings.position === "middle"
        ? { top: "50%", transform: "translateY(-50%)" }
        : { bottom: `${SAFE_ZONE.bottomPct}%` };

  const styleFor = (color: keyof typeof GM_COLORS, bold: boolean) => ({
    color: GM_COLORS[color],
    fontWeight: bold ? 800 : 700,
    WebkitTextStroke: `${(color === "purple" ? 5 : 4) / 10.8}cqw ${OUTLINE_FOR[color]}`,
    paintOrder: "stroke fill" as const,
    textShadow: "0 0.2cqw 0.5cqw rgba(0,0,0,.45)",
  });

  return (
    <div
      className="pointer-events-none absolute text-center leading-[1.15]"
      style={{ left: `${SAFE_ZONE.leftPct}%`, right: `${SAFE_ZONE.rightPct}%`, fontSize: `${(fontPx / 1080) * 100}cqw`, ...pos }}
    >
      {lines.map((line, li) => (
        <div key={li}>
          {line.map((i) => {
            const hl =
              settings.captionMode === "word-by-word" ? i === activeIdx : settings.captionMode === "highlight" && marked.has(cleanWord(tokens[i]));
            return (
              <span key={i} style={hl ? styleFor(settings.highlightColor, true) : styleFor(settings.textColor, false)}>
                {tokens[i]}{" "}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
}
