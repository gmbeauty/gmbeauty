"""Análise do gancho (primeiros ~3 segundos).

É uma checagem por regras simples sobre a transcrição — não é inteligência
artificial e não inventa conteúdo. Os avisos são dicas gerais de edição.
"""
from __future__ import annotations

import re

from ..schemas import Caption, RenderSettings
from .captions import STOPWORDS, clean

HOOK_WINDOW_SEC = 3.0
FAST_START_SEC = 0.8
TRIM_BREATH_SEC = 0.15
MAX_HOOK_WORDS = 8

# Padrões comuns de abertura que prendem atenção: chamar a pessoa, sinalizar erro/segredo/novidade.
ATTENTION_WORDS = {
    "você", "voce", "vc", "seu", "sua", "olha", "olhe", "pare", "atenção", "atencao", "cuidado", "segredo",
    "truque", "erro", "nunca", "jamais", "ainda", "descobri", "novidade", "lançamento", "lancamento", "dica",
    "sabia", "imagina", "quer", "preciso", "precisa", "resultado",
}


def _first_speech(captions: list[Caption]) -> float | None:
    if not captions:
        return None
    first = min(captions, key=lambda c: c.start_sec)
    return first.words[0].s if first.words else first.start_sec


def hook_caption(captions: list[Caption]) -> Caption | None:
    return min(captions, key=lambda c: c.start_sec) if captions else None


def suggest_hook_highlight(text: str) -> list[str]:
    """Palavra mais forte da primeira fala: a maior que não seja palavra de ligação."""
    tokens = [clean(t) for t in text.split()]
    cands = [t for t in tokens if t and t not in STOPWORDS and len(t) >= 4]
    return [max(cands, key=len)] if cands else []


def analyze_hook(captions: list[Caption], settings: RenderSettings) -> dict | None:
    first = hook_caption(captions)
    if first is None:
        return None
    speech = _first_speech(captions) or 0.0
    effective = max(0.0, speech - settings.trim_start_sec)
    in_window = [c for c in captions if c.start_sec < HOOK_WINDOW_SEC + settings.trim_start_sec]
    text = " ".join(c.text for c in in_window).lower()
    tokens = {clean(t) for t in text.split()}

    checks = []
    fast = effective <= FAST_START_SEC
    checks.append(
        dict(
            id="fast_start",
            ok=fast,
            label="A fala começa logo",
            tip=None if fast else f"Há {effective:.1f} s antes da primeira fala. Cortar esse trecho deixa o começo mais forte.",
            action=None if fast else "trim_start",
        )
    )
    attention = "?" in text or bool(tokens & ATTENTION_WORDS) or bool(re.search(r"\d", text))
    checks.append(
        dict(
            id="attention_opening",
            ok=attention,
            label="A abertura chama a pessoa",
            tip=None if attention else "Abrir com uma pergunta, um aviso ou um resultado costuma prender mais nos primeiros segundos.",
        )
    )
    short = len(first.text.split()) <= MAX_HOOK_WORDS
    checks.append(
        dict(
            id="short_first_caption",
            ok=short,
            label="A primeira legenda é curta",
            tip=None if short else "A primeira legenda é longa; legendas curtas no início são lidas mais rápido.",
        )
    )
    emphasized = bool(first.highlight_words) or settings.caption_mode == "word-by-word"
    checks.append(
        dict(
            id="hook_emphasis",
            ok=emphasized,
            label="O gancho tem destaque",
            tip=None if emphasized else "Destacar uma palavra da primeira fala ajuda a prender o olhar.",
            action=None if emphasized else "highlight_hook",
        )
    )

    ok = sum(c["ok"] for c in checks)
    level = "strong" if ok == len(checks) else "good" if ok >= len(checks) - 1 else "weak"
    return {
        "level": level,
        "firstSpeechSec": round(speech, 2),
        "suggestedTrimSec": round(speech - TRIM_BREATH_SEC, 2) if speech > FAST_START_SEC else None,
        "checks": checks,
    }
