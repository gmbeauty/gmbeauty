"""Remoção de silêncios sem cortar a fala natural.

Regra: de cada pausa longa, removemos só o miolo e deixamos `KEEP_EDGE_SEC`
de respiro em cada ponta. Assim a fala continua humana, não "picotada".
"""
from __future__ import annotations

KEEP_EDGE_SEC = 0.25
MIN_REMOVED_SEC = 0.15  # não vale cortar menos que isso


def cut_ranges(silences: list[tuple[float, float]], min_sec: float) -> list[tuple[float, float]]:
    cuts = []
    for s, e in silences:
        if e - s < min_sec:
            continue
        a, b = s + KEEP_EDGE_SEC, e - KEEP_EDGE_SEC
        if b - a >= MIN_REMOVED_SEC:
            cuts.append((round(a, 3), round(b, 3)))
    return cuts


def keep_ranges(duration: float, cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    keeps, pos = [], 0.0
    for a, b in sorted(cuts):
        if a > pos:
            keeps.append((pos, a))
        pos = max(pos, b)
    if pos < duration:
        keeps.append((pos, duration))
    return keeps


class TimeMap:
    """Converte tempo do vídeo original para o tempo do vídeo já sem os cortes."""

    def __init__(self, keeps: list[tuple[float, float]]):
        self.keeps = keeps
        self.offsets, acc = [], 0.0
        for a, b in keeps:
            self.offsets.append(acc)
            acc += b - a
        self.total = acc

    def __call__(self, t: float) -> float:
        for (a, b), off in zip(self.keeps, self.offsets):
            if t < a:
                return off  # caiu num trecho cortado: gruda no início do próximo
            if t <= b:
                return off + (t - a)
        return self.total
