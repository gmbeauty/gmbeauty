"""Formato dos dados trocados com o frontend (JSON em camelCase)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

CaptionMode = Literal["traditional", "highlight", "word-by-word"]
FontSize = Literal["sm", "md", "lg"]
Position = Literal["top", "middle", "bottom"]
Color = Literal["white", "lilac", "purple"]
LogoPosition = Literal["none", "top", "bottom", "watermark"]
HighlightStrategy = Literal["none", "keywords", "offer"]
ZoomMode = Literal["off", "subtle", "dynamic"]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RenderSettings(CamelModel):
    caption_mode: CaptionMode = "traditional"
    font_size: FontSize = "md"
    position: Position = "bottom"
    text_color: Color = "white"
    highlight_color: Color = "lilac"
    highlight_strategy: HighlightStrategy = "none"
    remove_silences: bool = False
    silence_min_sec: float = Field(0.6, ge=0.3, le=3.0)
    trim_start_sec: float = Field(0.0, ge=0.0, le=10.0)  # corta o silêncio antes da 1ª fala
    zoom_mode: ZoomMode = "off"
    logo_position: LogoPosition = "none"
    logo_size_pct: int = Field(22, ge=8, le=50)
    logo_opacity: float = Field(0.9, ge=0.1, le=1.0)


class Word(CamelModel):
    w: str
    s: float
    e: float


class Caption(CamelModel):
    id: str
    start_sec: float = Field(ge=0)
    end_sec: float = Field(ge=0)
    text: str
    highlight_words: list[str] = []
    words: list[Word] | None = None


class Silence(CamelModel):
    id: str
    start_sec: float
    end_sec: float


class ProjectOut(CamelModel):
    id: str
    name: str
    status: str
    stage: str | None
    progress: float
    content_type: str
    style: str
    original_name: str
    duration_sec: float
    width: int
    height: int
    size_bytes: int
    settings: RenderSettings
    captions: list[Caption]
    silences: list[Silence]
    analyzed: bool
    has_output: bool
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ProjectPatch(CamelModel):
    name: str | None = None
    content_type: str | None = None
    style: str | None = None
    settings: RenderSettings | None = None


class CaptionsIn(CamelModel):
    captions: list[Caption]


class HighlightsIn(CamelModel):
    strategy: HighlightStrategy


class DictionaryIn(CamelModel):
    term: str = Field(min_length=1, max_length=80)


class ZoomEventOut(CamelModel):
    start_sec: float
    end_sec: float
    amp: float
    kind: Literal["in", "settle"]


class HookCheck(CamelModel):
    id: str
    ok: bool
    label: str
    tip: str | None = None
    action: Literal["trim_start", "highlight_hook"] | None = None


class HookOut(CamelModel):
    level: Literal["strong", "good", "weak"]
    first_speech_sec: float | None
    suggested_trim_sec: float | None
    checks: list[HookCheck]


class InsightsOut(CamelModel):
    zoom_plan: list[ZoomEventOut]
    hook: HookOut | None
