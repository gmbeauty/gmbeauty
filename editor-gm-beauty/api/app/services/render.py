"""Renderização final: corta silêncios, enquadra em 9:16, grava legendas e logo."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from .. import config
from ..errors import ProcessingError
from ..schemas import Caption, RenderSettings
from .ass import SAFE_BOTTOM_PCT, SAFE_LEFT_PCT, SAFE_TOP_PCT, build_ass
from .cuts import TimeMap, cut_ranges, keep_ranges
from .zoom import ffmpeg_zoom_expr, plan_zoom

SFX_MAX_SEC = 5.0  # um efeito nunca passa disso
MIN_BROLL_SEC = 0.8  # B-roll mais curto que isso não vale a troca de imagem

OUT_W, OUT_H = 1080, 1920


def _fit_stage(src_w: int, src_h: int, src: str = "v", dst: str = "fit") -> str:
    """Enquadra em 1080x1920 sem cortar o produto: se não for vertical, usa fundo desfocado."""
    if abs(src_w / src_h - OUT_W / OUT_H) < 0.01:
        return f"[{src}]scale={OUT_W}:{OUT_H},setsar=1[{dst}]"
    return (
        f"[{src}]split=2[{dst}bg][{dst}fg];"
        f"[{dst}bg]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H},boxblur=25:3[{dst}bgb];"
        f"[{dst}fg]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease[{dst}fgs];"
        f"[{dst}bgb][{dst}fgs]overlay=(W-w)/2:(H-h)/2,setsar=1[{dst}]"
    )


def _logo_stage(s: RenderSettings, last: str) -> tuple[str, str]:
    """Posiciona a logo dentro da zona segura. Retorna (filtro, rótulo de saída)."""
    w = round(OUT_W * s.logo_size_pct / 100)
    margin = round(OUT_W * SAFE_LEFT_PCT / 100)
    top_y = round(OUT_H * SAFE_TOP_PCT / 100) + 20
    bottom_y = f"H-h-{round(OUT_H * SAFE_BOTTOM_PCT / 100) + 20}"
    pos = {
        "top": (f"{margin}", f"{top_y}"),
        "bottom": (f"{margin}", bottom_y),
        "watermark": ("(W-w)/2", f"{top_y}"),  # discreta, centralizada no alto
    }[s.logo_position]
    opacity = min(s.logo_opacity, 0.4) if s.logo_position == "watermark" else s.logo_opacity
    f = (
        f"[1:v]scale={w}:-1,format=rgba,colorchannelmixer=aa={opacity:.2f}[lg];"
        f"[{last}][lg]overlay={pos[0]}:{pos[1]}[logo]"
    )
    return f, "logo"


def render(
    video: Path,
    out: Path,
    work_dir: Path,
    src_w: int,
    src_h: int,
    duration: float,
    has_audio: bool,
    captions: list[Caption],
    silences: list[tuple[float, float]],
    settings: RenderSettings,
    logo: Path | None,
    sfx: list[tuple[float, Path]],
    broll: list[tuple[float, float, Path, int, int]],
    on_progress: Callable[[float], None],
) -> None:
    cuts = cut_ranges(silences, settings.silence_min_sec) if settings.remove_silences else []
    if settings.trim_start_sec > 0:  # corta o silêncio antes da primeira fala
        cuts = [(0.0, min(settings.trim_start_sec, max(0.0, duration - 1.0)))] + cuts
    keeps = keep_ranges(duration, cuts)
    tmap = TimeMap(keeps)
    out_duration = tmap.total if cuts else duration

    # Entradas extras do FFmpeg, na ordem: vídeo(0), logo, efeitos sonoros, B-roll.
    use_logo = settings.logo_position != "none" and logo is not None
    sfx_used: list[tuple[float, Path]] = []
    if has_audio and settings.sfx_enabled:
        for t, path in sfx:
            out_t = tmap(t) if cuts else t
            if out_t < out_duration - 0.2:
                sfx_used.append((out_t, path))
    broll_used: list[tuple[float, float, Path, int, int]] = []
    if settings.broll_enabled:
        for st, en, path, cw, ch in broll:
            a, b = (tmap(st), tmap(en)) if cuts else (st, en)
            if b - a >= MIN_BROLL_SEC:
                broll_used.append((a, min(b, out_duration), path, cw, ch))
    sfx_base = 1 + (1 if use_logo else 0)
    broll_base = sfx_base + len(sfx_used)

    (work_dir / "captions.ass").write_text(build_ass(captions, settings, tmap if cuts else None), encoding="utf-8")

    # --- grafo de filtros: cada etapa é um bloco; novas etapas (ex.: zoom) entram aqui ---
    stages: list[str] = []
    if cuts:
        v_parts, a_parts = [], []
        for i, (a, b) in enumerate(keeps):
            stages.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
            v_parts.append(f"[v{i}]")
            if has_audio:
                stages.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
                a_parts.append(f"[a{i}]")
        n = len(keeps)
        if has_audio:
            stages.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
        else:
            stages.append("".join(v_parts) + f"concat=n={n}:v=1:a=0[v]")
    else:
        stages.append("[0:v]null[v]")

    stages.append(_fit_stage(src_w, src_h))
    last = "fit"
    zoom = ffmpeg_zoom_expr(plan_zoom(captions, duration, settings.zoom_mode), tmap if cuts else None)
    if zoom:  # zoom depois do enquadramento e antes de logo/legenda: eles ficam parados
        stages.append(
            f"[fit]scale=w='2*trunc({OUT_W}*({zoom})/2)':h='2*trunc({OUT_H}*({zoom})/2)':eval=frame,"
            f"crop={OUT_W}:{OUT_H},setsar=1[zoomed]"
        )
        last = "zoomed"
    for i, (a, b, _path, cw, ch) in enumerate(broll_used):  # B-roll cobre a imagem (sem zoom), a fala continua
        k = broll_base + i
        stages.append(f"[{k}:v]trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB[bv{i}]")
        stages.append(_fit_stage(cw, ch, f"bv{i}", f"bf{i}"))
        stages.append(f"[{last}][bf{i}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[bo{i}]")
        last = f"bo{i}"
    if use_logo:
        f, last = _logo_stage(settings, last)
        stages.append(f)

    fonts = f":fontsdir={config.CAPTION_FONTS_DIR}" if config.CAPTION_FONTS_DIR else ""
    stages.append(f"[{last}]ass=captions.ass{fonts}[outv]")  # caminho relativo: cwd = work_dir

    # --- efeitos sonoros: cada um entra no seu instante (já remapeado pelos cortes) e é mixado à fala ---
    mixed_audio = False
    if sfx_used:
        labels = []
        for j, (out_t, _path) in enumerate(sfx_used):
            ms = round(out_t * 1000)
            stages.append(
                f"[{sfx_base + j}:a]atrim=0:{SFX_MAX_SEC},aformat=sample_rates=44100:channel_layouts=stereo,"
                f"volume={settings.sfx_gain_db:.1f}dB,adelay={ms}|{ms}[sx{j}]"
            )
            labels.append(f"[sx{j}]")
        base = "[a]" if cuts else "[0:a]"
        stages.append(f"{base}aformat=sample_rates=44100:channel_layouts=stereo[am]")
        stages.append(f"[am]{''.join(labels)}amix=inputs={len(labels) + 1}:normalize=0:duration=first:dropout_transition=0[aout]")
        mixed_audio = True

    cmd = [config.FFMPEG, "-y", "-v", "error", "-nostats", "-progress", "pipe:1", "-i", str(video)]
    if use_logo:
        cmd += ["-i", str(logo)]
    for _t, p_ in sfx_used:
        cmd += ["-i", str(p_)]
    for _a, _b, p_, _w, _h in broll_used:
        cmd += ["-i", str(p_)]
    cmd += ["-filter_complex", ";".join(stages), "-map", "[outv]"]
    if has_audio:
        cmd += ["-map", "[aout]" if mixed_audio else ("[a]" if cuts else "0:a:0")]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += ["-movflags", "+faststart", str(out)]

    err_log = work_dir / "ffmpeg_stderr.log"
    try:
        with open(err_log, "w", encoding="utf-8") as errf:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=errf, text=True, cwd=work_dir)
            assert proc.stdout is not None
            for line in proc.stdout:
                if line.startswith("out_time_us=") and out_duration > 0:
                    try:
                        on_progress(min(99.0, int(line.split("=")[1]) / 1e6 / out_duration * 100))
                    except ValueError:
                        pass
            code = proc.wait()
    except FileNotFoundError as exc:
        raise ProcessingError("O processador de vídeo (FFmpeg) não está instalado neste computador.", repr(exc))
    if code != 0:
        raise ProcessingError(
            "Não conseguimos exportar este vídeo. Tente novamente.",
            f"ffmpeg exit {code}\n{err_log.read_text(encoding='utf-8', errors='replace')[-4000:]}\nCMD: {' '.join(cmd)}",
        )
