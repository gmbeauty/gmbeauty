import type { SilenceRange } from "./types";

// Mesma regra do backend (api/app/services/cuts.py): de cada pausa longa só
// o miolo é removido, deixando um respiro de 0,25 s em cada ponta.
const KEEP_EDGE_SEC = 0.25;
const MIN_REMOVED_SEC = 0.15;

export function cutRanges(silences: SilenceRange[], minSec: number): [number, number][] {
  const cuts: [number, number][] = [];
  for (const s of silences) {
    if (s.endSec - s.startSec < minSec) continue;
    const a = s.startSec + KEEP_EDGE_SEC;
    const b = s.endSec - KEEP_EDGE_SEC;
    if (b - a >= MIN_REMOVED_SEC) cuts.push([a, b]);
  }
  return cuts;
}

export function removedSeconds(cuts: [number, number][]): number {
  return cuts.reduce((acc, [a, b]) => acc + (b - a), 0);
}
