"""Transforma palavras com timestamp em blocos de legenda e sugere destaques.

Nada aqui inventa conteúdo: só usa o texto transcrito ou digitado por você.
"""
from __future__ import annotations

import re
import uuid

PAUSE_SPLIT_SEC = 0.5  # pausa entre palavras que inicia uma nova legenda
MAX_CHARS = 34
MAX_DURATION_SEC = 3.5

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "pra", "com", "sem", "e", "ou", "mas", "que", "se", "eu", "você", "voce", "vc", "ele", "ela",
    "isso", "esse", "essa", "esses", "essas", "este", "esta", "isto", "aqui", "ali", "lá", "já", "muito", "mais",
    "meu", "minha", "seu", "sua", "tem", "tá", "ta", "é", "foi", "ser", "são", "vai", "vou", "então", "entao",
    "como", "quando", "onde", "pois", "só", "so", "bem", "também", "tambem", "ao", "à", "num", "numa", "né", "ne",
}
OFFER_WORDS = {
    "desconto", "off", "promoção", "promocao", "oferta", "frete", "grátis", "gratis", "kit", "cupom", "últimas",
    "ultimas", "unidades", "hoje", "agora", "cashback", "reais", "real",
}


def clean(word: str) -> str:
    """Palavra sem pontuação e em minúsculas, usada para comparar destaques."""
    return re.sub(r"[^\wÀ-ÿ$%]", "", word, flags=re.UNICODE).lower()


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def build_captions(words: list[dict]) -> list[dict]:
    captions: list[dict] = []
    current: list[dict] = []

    def flush() -> None:
        if not current:
            return
        captions.append(
            {
                "id": _new_id(),
                "startSec": round(current[0]["s"], 2),
                "endSec": round(current[-1]["e"], 2),
                "text": " ".join(w["w"] for w in current),
                "highlightWords": [],
                "words": [{"w": w["w"], "s": round(w["s"], 2), "e": round(w["e"], 2)} for w in current],
            }
        )
        current.clear()

    for w in words:
        if current:
            gap = w["s"] - current[-1]["e"]
            chars = len(" ".join(x["w"] for x in current)) + 1 + len(w["w"])
            ended_sentence = current[-1]["w"].endswith((".", "!", "?")) and chars > 14
            if gap > PAUSE_SPLIT_SEC or chars > MAX_CHARS or (w["e"] - current[0]["s"]) > MAX_DURATION_SEC or ended_sentence:
                flush()
        current.append(w)
    flush()
    return captions


def suggest_highlights(text: str, strategy: str) -> list[str]:
    tokens = [clean(t) for t in text.split()]
    tokens = [t for t in tokens if t]
    if strategy == "offer":
        picked = [t for t in tokens if any(c.isdigit() for c in t) or t in OFFER_WORDS or "%" in t or t.startswith("r$")]
        # "R$" costuma vir separado do número: "R$ 29,90" -> destaca o número
        return list(dict.fromkeys(picked))
    if strategy == "keywords":
        candidates = [t for t in tokens if t not in STOPWORDS and len(t) >= 5]
        return [max(candidates, key=len)] if candidates else []
    return []


def apply_strategy(captions: list[dict], strategy: str) -> list[dict]:
    for c in captions:
        c["highlightWords"] = suggest_highlights(c["text"], strategy)
    return captions
