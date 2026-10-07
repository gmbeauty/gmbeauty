"""Erros com duas camadas: mensagem simples para a pessoa e detalhe técnico para debug."""
import logging

from . import config

logger = logging.getLogger("editor_gm_beauty")

GENERIC_MESSAGE = "Não conseguimos processar este vídeo. Tente novamente."


class ProcessingError(Exception):
    """`user_message` aparece na tela; `detail` (saída do FFmpeg etc.) só vai para o log."""

    def __init__(self, user_message: str = GENERIC_MESSAGE, detail: str = ""):
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail


def setup_logging() -> None:
    config.ensure_dirs()
    if logger.handlers:
        return
    handler = logging.FileHandler(config.LOGS_DIR / "app.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
