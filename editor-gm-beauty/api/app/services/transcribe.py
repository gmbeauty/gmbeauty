"""Transcrição em português com timestamps por palavra.

Dois caminhos reais (escolhidos por TRANSCRIBER):
- openai: API Whisper da OpenAI (precisa de OPENAI_API_KEY).
- local:  faster-whisper no próprio computador (gratuito; baixa o modelo na 1ª vez).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .. import config
from ..errors import ProcessingError

Word = dict  # {"w": str, "s": float, "e": float}


def _prompt(terms: list[str]) -> str | None:
    """Dica para o Whisper reconhecer marcas e produtos (Dicionário GM Beauty)."""
    return ("Vocabulário: " + ", ".join(terms) + ".") if terms else None


def transcribe(audio: Path, terms: list[str] | None = None) -> list[Word]:
    terms = terms or []
    provider = config.TRANSCRIBER
    if provider == "auto":
        provider = "openai" if config.OPENAI_API_KEY else "local"
    if provider == "openai":
        words = _openai(audio, terms)
    elif provider == "local":
        words = _local(audio, terms)
    elif provider == "fake":
        words = _fake()
    else:
        raise ProcessingError(detail=f"unknown TRANSCRIBER={provider}")
    return [w for w in words if w["w"]]


def _openai(audio: Path, terms: list[str]) -> list[Word]:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        with open(audio, "rb") as f:
            res = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="pt",
                response_format="verbose_json",
                timestamp_granularities=["word"],
                prompt=_prompt(terms),
            )
        return [{"w": w.word.strip(), "s": float(w.start), "e": float(w.end)} for w in (res.words or [])]
    except Exception as exc:  # noqa: BLE001 - qualquer falha vira mensagem amigável
        raise ProcessingError(
            "Não conseguimos transcrever o áudio. Verifique a conexão e a chave da OpenAI e tente novamente.", repr(exc)
        )


_local_model = None


def load_audio_16k(path: Path):
    """Lê o WAV mono 16 kHz que o próprio editor gera e devolve amostras float32 (-1..1).

    Entregar as amostras direto ao modelo evita a biblioteca de decodificação (PyAV), cuja versão
    instalada em alguns computadores é incompatível com o faster-whisper.
    """
    import wave

    import numpy as np

    with wave.open(str(path), "rb") as w:
        if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError(f"formato de áudio inesperado: {w.getframerate()} Hz, {w.getnchannels()} canal(is)")
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _local(audio: Path, terms: list[str]) -> list[Word]:
    global _local_model
    try:
        from faster_whisper import WhisperModel

        if _local_model is None:
            _local_model = WhisperModel(config.WHISPER_MODEL, device="auto", compute_type="int8")
        segments, _info = _local_model.transcribe(
            load_audio_16k(audio), language="pt", word_timestamps=True, initial_prompt=_prompt(terms), beam_size=5
        )
        words: list[Word] = []
        for seg in segments:
            for w in seg.words or []:
                words.append({"w": w.word.strip(), "s": float(w.start), "e": float(w.end)})
        return words
    except ImportError as exc:
        raise ProcessingError(
            "O componente de transcrição não iniciou neste computador. Abra o arquivo “diagnostico” para ver o motivo.", repr(exc)
        )
    except Exception as exc:  # noqa: BLE001
        probe = (type(exc).__name__ + repr(exc)).lower()
        if any(k in probe for k in ("connection", "timeout", "offline", "huggingface", "localentrynotfound", "ssl", "resolve", "http", "proxy", "forbidden", "403", "unreachable")):
            raise ProcessingError(
                "Não conseguimos baixar o modelo de transcrição. Verifique a internet (a primeira vez baixa ~500 MB) "
                "e clique em Tentar novamente. Se continuar, abra o arquivo “diagnostico”.",
                repr(exc),
            )
        raise ProcessingError(
            "Não conseguimos transcrever o áudio. Tente novamente; se continuar, abra o arquivo “diagnostico”.", repr(exc)
        )


def _fake() -> list[Word]:
    """Somente para testes automatizados: lê palavras de um JSON apontado por FAKE_TRANSCRIPT."""
    return json.loads(Path(os.environ["FAKE_TRANSCRIPT"]).read_text(encoding="utf-8"))
