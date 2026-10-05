"""Diagnóstico da transcrição: testa, passo a passo, o que o editor precisa para transcrever.

Rode pelo arquivo `diagnostico` (dois cliques) na pasta do editor.
"""
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import config  # noqa: E402

problemas: list[str] = []


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def falha(msg: str, dica: str) -> None:
    print(f"  [ERRO] {msg}")
    print(f"         -> {dica}")
    problemas.append(dica)


def passo(n: int, titulo: str) -> None:
    print(f"\n{n}. {titulo}")


print("=== Diagnóstico do Editor GM Beauty ===")
print(f"Sistema: {platform.system()} {platform.release()} | Python {platform.python_version()}")

passo(1, "FFmpeg (processador de vídeo)")
ffmpeg = shutil.which(config.FFMPEG)
if ffmpeg:
    try:
        v = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, timeout=20).stdout.splitlines()[0]
        ok(v[:70])
    except Exception as exc:  # noqa: BLE001
        falha(f"FFmpeg não executou ({exc!r})", "Reinstale o FFmpeg: winget install ffmpeg")
else:
    falha("FFmpeg não encontrado", "Instale com: winget install ffmpeg (depois feche e abra o editor de novo)")

passo(2, "Componente de transcrição (faster-whisper)")
whisper_ok = False
try:
    import faster_whisper  # noqa: F401
    import ctranslate2

    ok(f"faster-whisper instalado (ctranslate2 {ctranslate2.__version__})")
    whisper_ok = True
except Exception as exc:  # noqa: BLE001
    falha(f"não carregou: {exc!r}", "Instale o 'Microsoft Visual C++' (https://aka.ms/vs/17/release/vc_redist.x64.exe) e abra o iniciador de novo")

passo(3, "Internet para baixar o modelo de voz (huggingface.co)")
internet_ok = False
try:
    with urllib.request.urlopen("https://huggingface.co", timeout=20) as r:
        ok(f"conectou (código {r.status})")
        internet_ok = True
except Exception as exc:  # noqa: BLE001
    falha(
        f"não conectou: {exc!r}",
        "Sua internet está bloqueando ou instável para esse site. Tente: outra rede (ex.: hotspot do celular), desligar VPN/antivírus, "
        "ou usar a transcrição pela OpenAI (arquivo chave-openai.txt).",
    )

passo(4, f"Modelo de voz '{config.WHISPER_MODEL}' (baixa ~500 MB na primeira vez) e transcrição de teste")
if whisper_ok:
    try:
        from faster_whisper import WhisperModel

        t0 = time.time()
        print("  baixando/carregando o modelo... (pode demorar vários minutos na primeira vez)")
        model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
        ok(f"modelo carregado em {time.time() - t0:.0f} s")
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "teste.wav"
            subprocess.run(
                [config.FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "2", str(wav)],
                check=True,
            )
            segs, _ = model.transcribe(str(wav), language="pt")
            list(segs)
        ok("transcrição de teste funcionou")
    except Exception as exc:  # noqa: BLE001
        falha(
            f"{type(exc).__name__}: {exc}",
            "Falhou ao baixar ou usar o modelo. Se for erro de conexão, tente outra rede. "
            "Para um download menor, crie a variável WHISPER_MODEL=base (modelo mais leve, ~145 MB).",
        )
else:
    print("  (pulado: o componente do passo 2 não carregou)")

passo(5, "Últimas linhas do registro do editor")
log = config.LOGS_DIR / "app.log"
if log.exists():
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]:
        print("   ", line[:200])
else:
    print("  (ainda não há registro)")

print("\n=== Resultado ===")
if problemas:
    print("Encontrei problema(s). Tire um print desta janela inteira e envie para quem está ajudando.")
else:
    print("Tudo certo por aqui. Se ainda falhar, tire um print desta janela e envie.")
