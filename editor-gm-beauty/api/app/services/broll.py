"""Sugestão de B-roll.

O editor só sugere um clipe seu quando a fala CITA o produto que você etiquetou
(ex.: etiqueta "base Ruby Rose" + fala "essa base Ruby Rose..."). Nada é inventado:
sem menção na fala, não há sugestão.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..schemas import Caption
from .captions import clean

HOOK_SAFE_SEC = 1.5  # o começo fica com a pessoa
DEFAULT_SEC = 2.5
MIN_SEC = 0.8
MIN_GAP_SEC = 3.0  # entre o fim de um B-roll e o início do próximo
MAX_COVERAGE = 0.40  # no máximo 40% do vídeo coberto


@dataclass(frozen=True)
class Clip:
    id: str
    tag: str
    duration: float

    @property
    def aliases(self) -> list[list[str]]:
        """Cada variação da etiqueta vira uma sequência de palavras limpas."""
        out = []
        for part in self.tag.split(","):
            toks = [clean(t) for t in part.split()]
            toks = [t for t in toks if t]
            if toks:
                out.append(toks)
        return out


def _find(seq: list[str], sub: list[str]) -> int | None:
    n = len(sub)
    for i in range(len(seq) - n + 1):
        if seq[i : i + n] == sub:
            return i
    return None


def _mention_time(cap: Caption, tokens: list[str], idx: int) -> float:
    if cap.words and len(cap.words) == len(tokens):
        return cap.words[idx].s
    return cap.start_sec


def plan_broll(captions: list[Caption], clips: list[Clip], duration: float) -> list[dict]:
    usable = [c for c in clips if c.duration >= MIN_SEC and c.aliases]
    if not usable:
        return []

    candidates: list[tuple[float, int, Clip]] = []  # (tempo, tamanho da etiqueta, clipe)
    for cap in sorted(captions, key=lambda c: c.start_sec):
        tokens = [clean(t) for t in cap.text.split()]
        best: tuple[float, int, Clip] | None = None
        for clip in usable:
            for alias in clip.aliases:
                i = _find(tokens, alias)
                if i is not None and (best is None or len(alias) > best[1]):
                    best = (_mention_time(cap, tokens, i), len(alias), clip)
        if best:
            candidates.append(best)

    events: list[dict] = []
    covered, last_end = 0.0, -1e9
    for t, _n, clip in candidates:
        start = max(t, HOOK_SAFE_SEC)
        length = min(DEFAULT_SEC, clip.duration, duration - start)
        if length < MIN_SEC or start - last_end < MIN_GAP_SEC:
            continue
        if (covered + length) / duration > MAX_COVERAGE:
            continue
        events.append({"id": uuid.uuid4().hex[:8], "startSec": round(start, 2), "endSec": round(start + length, 2), "clipId": clip.id})
        covered += length
        last_end = start + length
    return events
