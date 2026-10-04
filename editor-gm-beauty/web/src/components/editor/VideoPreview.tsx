import { SAFE_ZONE } from "@/lib/safe-zone";
import type { CaptionSegment, EditorSettings } from "@/lib/types";

const SIZE = { sm: "text-sm", md: "text-lg", lg: "text-2xl" } as const;

// Fase 1: moldura 9:16 com fundo ilustrativo. O player real entra na Fase 2.
export function VideoPreview({ settings, caption }: { settings: EditorSettings; caption?: CaptionSegment }) {
  const pos =
    settings.position === "top"
      ? { top: `${SAFE_ZONE.topPct}%` }
      : settings.position === "middle"
        ? { top: "50%", transform: "translateY(-50%)" }
        : { bottom: `${SAFE_ZONE.bottomPct}%` };

  const words = caption?.text.split(" ") ?? [];
  const highlights = (caption?.highlightWords ?? []).map((w) => w.toLowerCase());

  return (
    <div className="relative mx-auto aspect-[9/16] w-full max-w-[300px] overflow-hidden rounded-[1.75rem] border-[6px] border-gm-ink bg-gradient-to-br from-[#d9bdf0] via-[#B57EDC] to-[#4B1C71] shadow-xl">
      <p className="absolute inset-x-0 top-1/3 text-center text-xs text-white/70">Prévia do vídeo<br />(player real na Fase 2)</p>

      {settings.showSafeZone && (
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div className="absolute inset-x-0 top-0 bg-rose-500/25" style={{ height: `${SAFE_ZONE.topPct}%` }} />
          <div className="absolute inset-x-0 bottom-0 bg-rose-500/25" style={{ height: `${SAFE_ZONE.bottomPct}%` }} />
          <div
            className="absolute bg-rose-500/25"
            style={{ right: 0, width: `${SAFE_ZONE.rightPct}%`, top: `${SAFE_ZONE.topPct}%`, bottom: `${SAFE_ZONE.bottomPct}%` }}
          />
          <span className="absolute left-2 top-1 text-[10px] font-medium text-white">Zona bloqueada</span>
        </div>
      )}

      {settings.logo !== "none" && (
        <span
          className={`absolute left-3 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-semibold text-gm-purple ${
            settings.logo === "top" ? "top-[13%]" : settings.logo === "bottom" ? "bottom-[23%]" : "top-[13%] opacity-50"
          }`}
        >
          GM Beauty
        </span>
      )}

      {caption && (
        <div
          className="absolute px-4 text-center font-bold leading-tight text-white"
          style={{ left: `${SAFE_ZONE.leftPct}%`, right: `${SAFE_ZONE.rightPct}%`, ...pos, textShadow: "0 2px 6px rgba(0,0,0,.55)" }}
        >
          <span className={SIZE[settings.fontSize]}>
            {words.map((w, i) => {
              const clean = w.replace(/[.,!?]/g, "").toLowerCase();
              const hl = settings.captionMode !== "traditional" && highlights.includes(clean);
              return (
                <span key={i} className={hl ? "rounded bg-gm-lilac px-1 text-white" : ""}>
                  {w}{" "}
                </span>
              );
            })}
          </span>
        </div>
      )}
    </div>
  );
}
