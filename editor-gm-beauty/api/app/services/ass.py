"""Gera o arquivo de legendas ASS (o FFmpeg grava esse texto estilizado no vídeo).

Mantém as mesmas regras do preview: zona segura, no máximo 3 linhas, cores GM,
contorno e sombra leves.
"""
from __future__ import annotations

from .. import config
from ..schemas import Caption, RenderSettings
from .captions import clean
from .cuts import TimeMap

W, H = 1080, 1920
# Zona segura de Reels/TikTok (mesmos valores de web/src/lib/safe-zone.ts), em % da tela.
SAFE_TOP_PCT, SAFE_BOTTOM_PCT, SAFE_LEFT_PCT, SAFE_RIGHT_PCT = 12, 22, 5, 14

RGB = {"white": (255, 255, 255), "lilac": (0xB5, 0x7E, 0xDC), "purple": (0x4B, 0x1C, 0x71)}
DARK_OUTLINE = (0x2A, 0x10, 0x40)
FONT_PX = {"sm": 58, "md": 74, "lg": 94}
MAX_CHARS = {"sm": 26, "md": 21, "lg": 16}  # caracteres por linha
ALIGN = {"bottom": 2, "middle": 5, "top": 8}


def _c(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"&H00{b:02X}{g:02X}{r:02X}&"  # ASS usa ordem BGR


def _outline_for(color: str) -> tuple[int, int, int]:
    return RGB["white"] if color == "purple" else DARK_OUTLINE


def _ts(t: float) -> str:
    cs = max(0, round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def _greedy(tokens: list[str], max_chars: int) -> list[list[int]]:
    lines: list[list[int]] = [[]]
    size = 0
    for i, t in enumerate(tokens):
        add = len(t) + (1 if lines[-1] else 0)
        if lines[-1] and size + add > max_chars:
            lines.append([])
            size = 0
            add = len(t)
        lines[-1].append(i)
        size += add
    return lines


def _wrap(tokens: list[str], max_chars: int) -> list[list[int]]:
    """Quebra em linhas (listas de índices de palavras) e equilibra o tamanho delas,
    para não sobrar uma palavra solta na última linha."""
    lines = _greedy(tokens, max_chars)
    n = len(lines)
    if n > 1:
        total = sum(len(t) for t in tokens) + len(tokens) - 1
        for limit in range(-(-total // n), max_chars + 1):  # menor largura que mantém n linhas
            candidate = _greedy(tokens, limit)
            if len(candidate) == n:
                return candidate
    return lines


def _esc(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def _render_text(tokens: list[str], lines: list[list[int]], hl: set[int], s: RenderSettings) -> str:
    hl_tag = f"{{\\c{_c(RGB[s.highlight_color])}\\3c{_c(_outline_for(s.highlight_color))}\\b1}}"
    out_lines = []
    for line in lines:
        parts = []
        for i in line:
            t = _esc(tokens[i])
            parts.append(f"{hl_tag}{t}{{\\r}}" if i in hl else t)
        out_lines.append(" ".join(parts))
    return "\\N".join(out_lines)


def _word_times(cap: Caption, tokens: list[str]) -> list[tuple[float, float]]:
    """Tempo de cada palavra. Se o texto foi editado, distribui proporcionalmente ao tamanho."""
    if cap.words and len(cap.words) == len(tokens):
        return [(w.s, w.e) for w in cap.words]
    total = sum(len(t) for t in tokens) or 1
    span = cap.end_sec - cap.start_sec
    out, pos = [], cap.start_sec
    for t in tokens:
        dur = span * len(t) / total
        out.append((pos, pos + dur))
        pos += dur
    return out


def build_ass(captions: list[Caption], s: RenderSettings, tmap: TimeMap | None = None) -> str:
    tmap = tmap or (lambda t: t)  # type: ignore[assignment]
    align = ALIGN[s.position]
    margin_v = {"bottom": round(H * SAFE_BOTTOM_PCT / 100), "top": round(H * SAFE_TOP_PCT / 100), "middle": 0}[s.position]
    ml, mr = round(W * SAFE_LEFT_PCT / 100), round(W * SAFE_RIGHT_PCT / 100)
    outline_w = 5 if s.text_color != "white" else 4

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{config.CAPTION_FONT},{FONT_PX[s.font_size]},{_c(RGB[s.text_color])},&H000000FF&,{_c(_outline_for(s.text_color))},&H80000000&,-1,0,0,0,100,100,0,0,1,{outline_w},2,{align},{ml},{mr},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    for cap in captions:
        tokens = cap.text.split()
        if not tokens:
            continue
        start, end = tmap(cap.start_sec), tmap(cap.end_sec)
        if end - start < 0.05:
            continue  # legenda caiu inteira num trecho cortado
        lines = _wrap(tokens, MAX_CHARS[s.font_size])
        marked = {i for i, t in enumerate(tokens) if clean(t) in set(cap.highlight_words)}

        if s.caption_mode == "word-by-word":
            times = _word_times(cap, tokens)
            starts = [start] + [tmap(t[0]) for t in times[1:]]
            for i, st in enumerate(starts):
                en = starts[i + 1] if i + 1 < len(starts) else end
                if en - st < 0.03:
                    continue
                events.append(f"Dialogue: 0,{_ts(st)},{_ts(en)},Default,,0,0,0,,{_render_text(tokens, lines, {i}, s)}")
        else:
            hl = marked if s.caption_mode == "highlight" else set()
            events.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Default,,0,0,0,,{_render_text(tokens, lines, hl, s)}")
    return header + "\n".join(events) + "\n"
