"""Sugestão de efeitos sonoros.

Princípios: poucos, discretos e só com sons que VOCÊ colocou na Biblioteca GM.
- transição: no início de um zoom;
- destaque: na palavra destacada da legenda;
- oferta: no preço/desconto/promoção (quando existirem na fala).
O resultado é só uma sugestão: a pessoa revisa a lista antes de exportar.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..schemas import Caption, RenderSettings
from .captions import clean
from .zoom import ZoomEvent

MIN_GAP_SEC = 1.5
MAX_PER_SECOND = 1 / 6  # no máximo um efeito a cada ~6 s, em média
PRIORITY = {"oferta": 3, "destaque": 2, "transicao": 1}
LEAD_SEC = 0.05  # o som entra um instante antes do movimento


@dataclass(frozen=True)
class Sound:
    id: str
    category: str


def _word_time(cap: Caption) -> float:
    """Início da palavra destacada (ou da legenda, se não houver tempo por palavra)."""
    marked = set(cap.highlight_words)
    if cap.words:
        for w in cap.words:
            if clean(w.w) in marked:
                return w.s
    return cap.start_sec


def plan_sfx(
    captions: list[Caption],
    zoom_plan: list[ZoomEvent],
    settings: RenderSettings,
    sounds: list[Sound],
    duration: float,
) -> list[dict]:
    by_cat: dict[str, list[str]] = {}
    for s in sorted(sounds, key=lambda s: s.id):
        by_cat.setdefault(s.category, []).append(s.id)
    if not by_cat:
        return []

    candidates: list[tuple[float, str]] = []  # (tempo, categoria)
    for z in zoom_plan:
        if z.kind == "in" and "transicao" in by_cat:
            candidates.append((max(0.0, z.start - LEAD_SEC), "transicao"))
    shows_highlight = settings.caption_mode in ("highlight", "word-by-word")
    for c in captions:
        if not c.highlight_words or not shows_highlight:
            continue
        if settings.highlight_strategy == "offer" and "oferta" in by_cat:
            candidates.append((max(0.0, _word_time(c) - LEAD_SEC), "oferta"))
        elif "destaque" in by_cat:
            candidates.append((max(0.0, _word_time(c) - LEAD_SEC), "destaque"))

    accepted: list[tuple[float, str]] = []
    for t, cat in sorted(candidates):
        if t > duration - 0.3:
            continue
        if accepted and t - accepted[-1][0] < MIN_GAP_SEC:
            if PRIORITY[cat] > PRIORITY[accepted[-1][1]]:
                accepted[-1] = (t, cat)  # o mais importante fica
            continue
        accepted.append((t, cat))

    limit = max(2, int(duration * MAX_PER_SECOND) + 1)
    if len(accepted) > limit:  # mantém os mais importantes, na ordem do vídeo
        keep = sorted(sorted(accepted, key=lambda a: -PRIORITY[a[1]])[:limit])
        accepted = keep

    events, last_by_cat = [], {}
    for t, cat in accepted:
        pool = by_cat[cat]
        idx = (last_by_cat.get(cat, -1) + 1) % len(pool)  # alterna entre os sons da categoria
        last_by_cat[cat] = idx
        events.append({"id": uuid.uuid4().hex[:8], "startSec": round(t, 2), "sfxId": pool[idx]})
    return events
