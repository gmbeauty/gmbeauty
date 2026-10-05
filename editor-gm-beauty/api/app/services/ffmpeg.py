"""Chamadas ao FFmpeg/FFprobe. Qualquer falha vira ProcessingError com detalhe técnico separado."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .. import config
from ..errors import ProcessingError


def _run(cmd: list[str], user_message: str, timeout: int = 600, cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    except FileNotFoundError as exc:
        raise ProcessingError(
            "O processador de vídeo (FFmpeg) não está instalado neste computador.", f"{cmd[0]} not found: {exc}"
        )
    except subprocess.TimeoutExpired:
        raise ProcessingError(user_message, f"timeout after {timeout}s: {' '.join(cmd)}")
    if proc.returncode != 0:
        raise ProcessingError(user_message, f"exit {proc.returncode}: {' '.join(cmd)}\n{proc.stderr[-4000:]}")
    return proc


def probe(path: Path) -> dict:
    """Duração, resolução (já considerando rotação de celular) e se há áudio."""
    msg = "Não conseguimos ler este vídeo. Verifique se o arquivo é MP4 ou MOV válido."
    proc = _run(
        [config.FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        msg,
        timeout=60,
    )
    data = json.loads(proc.stdout or "{}")
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise ProcessingError(msg, "no video stream")
    width, height = int(video.get("width", 0)), int(video.get("height", 0))

    rotation = 0
    for sd in video.get("side_data_list", []) or []:
        if "rotation" in sd:
            rotation = int(sd["rotation"])
    if not rotation and "rotate" in video.get("tags", {}):
        rotation = int(video["tags"]["rotate"])
    if abs(rotation) % 180 == 90:
        width, height = height, width

    duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
    if duration <= 0 or width <= 0 or height <= 0:
        raise ProcessingError(msg, f"invalid probe: {duration=} {width=} {height=}")
    return {
        "duration": duration,
        "width": width,
        "height": height,
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }


def extract_audio(video: Path, out_wav: Path) -> None:
    """Áudio mono 16 kHz, o formato ideal para o Whisper."""
    _run(
        [config.FFMPEG, "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(out_wav)],
        "Não conseguimos extrair o áudio deste vídeo. Tente novamente.",
    )


def make_thumbnail(video: Path, out_jpg: Path, duration: float) -> None:
    at = min(1.0, duration / 2)
    _run(
        [config.FFMPEG, "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", str(video), "-frames:v", "1", "-vf", "scale=360:-2", str(out_jpg)],
        "Não conseguimos gerar a miniatura do vídeo.",
        timeout=60,
    )


_START = re.compile(r"silence_start:\s*(-?[\d.]+)")
_END = re.compile(r"silence_end:\s*(-?[\d.]+)")


def detect_silences(audio: Path, duration: float, min_sec: float = 0.5, noise_db: int = -35) -> list[tuple[float, float]]:
    """Trechos sem fala maiores que `min_sec`. Ignora silêncio no começo/fim do vídeo."""
    proc = _run(
        [config.FFMPEG, "-v", "info", "-i", str(audio), "-af", f"silencedetect=noise={noise_db}dB:d={min_sec}", "-f", "null", "-"],
        "Não conseguimos analisar as pausas deste vídeo.",
    )
    ranges: list[tuple[float, float]] = []
    start: float | None = None
    for line in proc.stderr.splitlines():
        if m := _START.search(line):
            start = max(0.0, float(m.group(1)))
        elif (m := _END.search(line)) and start is not None:
            ranges.append((start, min(duration, float(m.group(1)))))
            start = None
    if start is not None:  # silêncio que vai até o fim do arquivo
        ranges.append((start, duration))
    return ranges


def probe_audio(path: Path) -> float:
    """Duração (s) de um arquivo de som; erro amigável se não for áudio."""
    msg = "Não conseguimos ler este arquivo de som. Verifique se ele não está corrompido."
    proc = _run([config.FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)], msg, timeout=60)
    data = json.loads(proc.stdout or "{}")
    if not any(s.get("codec_type") == "audio" for s in data.get("streams", [])):
        raise ProcessingError(msg, "no audio stream")
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration <= 0:
        raise ProcessingError(msg, "zero duration")
    return duration
