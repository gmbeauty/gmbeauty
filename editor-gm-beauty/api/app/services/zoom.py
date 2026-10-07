"""Zooms automáticos discretos.

Regras para não parecer edição artificial:
- poucos zooms, sempre com um intervalo mínimo entre eles;
- movimento suave (entra e sai com aceleração/desaceleração);
- nunca corta mais que ~9% da imagem (modo dinâmico) ou ~5% (sutil);
- só no centro da imagem; sem deslocar o enquadramento (o produto continua inteiro).

O plano é calculado no tempo do vídeo ORIGINAL. A prévia (site) e a exportação
usam exatamente o mesmo plano.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..schemas import Caption
from .cuts import TimeMap


@dataclass(frozen=True)
class ZoomEvent:
    start: float
    end: float
    amp: float  # 0.06 = 6% de aproximação
    kind: str  # "in" (aproxima e volta) | "settle" (começa aproximado e relaxa)

    @property
    def ramp(self) -> float:
        return min(0.6, (self.end - self.start) / 2)


MODES = {
    # amp, intervalo mínimo entre zooms, duração (min, max), tipos alternados, zoom de abertura
    "subtle": dict(amp=0.05, min_gap=6.0, dur=(1.8, 3.0), kinds=("in",), opening=False),
    "dynamic": dict(amp=0.09, min_gap=3.5, dur=(1.4, 2.6), kinds=("in", "settle"), opening=True),
}
OPENING_SEC = 1.6
MIN_MAPPED_SEC = 0.4


def plan_zoom(captions: list[Caption], duration: float, mode: str) -> list[ZoomEvent]:
    cfg = MODES.get(mode)
    if not cfg or not captions or duration < 3:
        return []
    events: list[ZoomEvent] = []
    last_end = -1e9
    first = min(captions, key=lambda c: c.start_sec)

    # Abertura: o vídeo começa levemente aproximado e relaxa, reforçando o gancho.
    if cfg["opening"] and first.start_sec < 1.5:
        events.append(ZoomEvent(0.0, min(OPENING_SEC, duration), cfg["amp"], "settle"))
        last_end = events[-1].end

    kind_i = 0
    for c in sorted(captions, key=lambda c: c.start_sec):
        if c.start_sec - last_end < cfg["min_gap"] or c.start_sec > duration - 1.0:
            continue
        if c.end_sec - c.start_sec < 1.0:
            continue  # fala curta demais para justificar movimento
        lo, hi = cfg["dur"]
        end = min(c.start_sec + min(max(c.end_sec - c.start_sec, lo), hi), duration)
        kind = cfg["kinds"][kind_i % len(cfg["kinds"])]
        kind_i += 1
        events.append(ZoomEvent(c.start_sec, end, cfg["amp"], kind))
        last_end = end
    return events


def _smooth(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def zoom_at(events: list[ZoomEvent], t: float) -> float:
    """Fator de zoom em `t` (1.0 = sem zoom). Mesma fórmula do FFmpeg e do site."""
    z = 1.0
    for e in events:
        if e.kind == "settle":
            z += e.amp * (1 - _smooth((t - e.start) / (e.end - e.start))) * (1 if e.start <= t <= e.end else 0)
        else:
            r = e.ramp
            z += e.amp * _smooth((t - e.start) / r) * (1 - _smooth((t - (e.end - r)) / r))
    return z


def _s(expr: str) -> str:
    u = f"clip(({expr}),0,1)"
    return f"({u}*{u}*(3-2*{u}))"


def ffmpeg_zoom_expr(events: list[ZoomEvent], tmap: TimeMap | None) -> str | None:
    """Expressão do fator de zoom em função de `t` (tempo do vídeo de saída)."""
    terms = []
    for e in events:
        a, b = (tmap(e.start), tmap(e.end)) if tmap else (e.start, e.end)
        if b - a < MIN_MAPPED_SEC:
            continue  # caiu quase todo num trecho cortado
        ev = ZoomEvent(a, b, e.amp, e.kind)
        if ev.kind == "settle":
            terms.append(f"{ev.amp:.4f}*between(t,{a:.3f},{b:.3f})*(1-{_s(f'(t-{a:.3f})/{b - a:.3f}')})")
        else:
            r = ev.ramp
            terms.append(f"{ev.amp:.4f}*{_s(f'(t-{a:.3f})/{r:.3f}')}*(1-{_s(f'(t-{b - r:.3f})/{r:.3f}')})")
    return ("1+" + "+".join(terms)) if terms else None
