import type { ZoomEvent } from "./types";

const smooth = (x: number) => {
  const c = Math.min(1, Math.max(0, x));
  return c * c * (3 - 2 * c);
};

/** Fator de zoom em `t` (tempo do vídeo original). Mesma fórmula do servidor (api/app/services/zoom.py). */
export function zoomAt(events: ZoomEvent[], t: number): number {
  let z = 1;
  for (const e of events) {
    if (e.kind === "settle") {
      if (t >= e.startSec && t <= e.endSec) z += e.amp * (1 - smooth((t - e.startSec) / (e.endSec - e.startSec)));
    } else {
      const r = Math.min(0.6, (e.endSec - e.startSec) / 2);
      z += e.amp * smooth((t - e.startSec) / r) * (1 - smooth((t - (e.endSec - r)) / r));
    }
  }
  return z;
}
