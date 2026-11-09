import type { CaptionSegment, CaptionSize, GmColor } from "./types";

export const GM_COLORS: Record<GmColor, string> = { white: "#ffffff", lilac: "#B57EDC", purple: "#4B1C71" };
export const OUTLINE_FOR: Record<GmColor, string> = { white: "#2a1040", lilac: "#2a1040", purple: "#ffffff" };

// Tamanho da fonte no vídeo final (1080 px de largura) e caracteres por linha.
// Mesmos valores de api/app/services/ass.py, para a prévia ficar fiel.
export const FONT_PX: Record<CaptionSize, number> = { sm: 58, md: 74, lg: 94 };
export const MAX_CHARS: Record<CaptionSize, number> = { sm: 26, md: 21, lg: 16 };

/** Mesma limpeza do backend: sem pontuação e em minúsculas. */
export function cleanWord(word: string): string {
  return word.replace(/[^\p{L}\p{N}_$%]/gu, "").toLowerCase();
}

function greedy(tokens: string[], max: number): number[][] {
  const lines: number[][] = [[]];
  let size = 0;
  tokens.forEach((t, i) => {
    let add = t.length + (lines[lines.length - 1].length ? 1 : 0);
    if (lines[lines.length - 1].length && size + add > max) {
      lines.push([]);
      size = 0;
      add = t.length;
    }
    lines[lines.length - 1].push(i);
    size += add;
  });
  return lines;
}

/** Quebra em linhas equilibradas (sem palavra solta na última linha). */
export function wrapLines(tokens: string[], max: number): number[][] {
  const lines = greedy(tokens, max);
  const n = lines.length;
  if (n > 1) {
    const total = tokens.reduce((a, t) => a + t.length, 0) + tokens.length - 1;
    for (let limit = Math.ceil(total / n); limit <= max; limit++) {
      const c = greedy(tokens, limit);
      if (c.length === n) return c;
    }
  }
  return lines;
}

/** Índice da palavra falada em `t` (para o modo palavra por palavra). */
export function activeWordIndex(cap: CaptionSegment, tokens: string[], t: number): number {
  if (cap.words && cap.words.length === tokens.length) {
    const i = cap.words.findIndex((w, k) => t < (cap.words![k + 1]?.s ?? cap.endSec) && t >= w.s);
    return i === -1 ? (t < cap.words[0].s ? 0 : tokens.length - 1) : i;
  }
  const total = tokens.reduce((a, w) => a + w.length, 0) || 1;
  const span = cap.endSec - cap.startSec;
  let pos = cap.startSec;
  for (let i = 0; i < tokens.length; i++) {
    pos += (span * tokens[i].length) / total;
    if (t < pos) return i;
  }
  return tokens.length - 1;
}
