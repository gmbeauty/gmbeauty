from app.schemas import Caption, RenderSettings
from app.services import captions as cap
from app.services.ass import build_ass
from app.services.cuts import TimeMap, cut_ranges, keep_ranges


def test_cut_ranges_keeps_natural_pauses():
    # pausa de 0,4 s: não corta; 0,7 s: corta só 0,2 s do miolo; 2 s: corta 1,5 s
    cuts = cut_ranges([(1, 1.4), (2, 2.7), (5, 7)], min_sec=0.6)
    assert cuts == [(2.25, 2.45), (5.25, 6.75)]


def test_keep_ranges_and_timemap():
    keeps = keep_ranges(10, [(2.0, 3.0), (6.0, 7.0)])
    assert keeps == [(0.0, 2.0), (3.0, 6.0), (7.0, 10)]
    m = TimeMap(keeps)
    assert m.total == 8
    assert m(1.0) == 1.0
    assert m(4.0) == 3.0  # 2 s de trecho + 1 s dentro do segundo trecho
    assert m(2.5) == 2.0  # dentro de um corte: gruda no próximo trecho
    assert m(9.0) == 7.0  # 5 s de deslocamento + 2 s dentro do terceiro trecho


def test_build_captions_splits_on_pause_and_length():
    words = [{"w": "a", "s": 0, "e": 0.3}, {"w": "b", "s": 0.3, "e": 0.6}, {"w": "c", "s": 2.0, "e": 2.3}]
    caps = cap.build_captions(words)
    assert [c["text"] for c in caps] == ["a b", "c"]


def test_highlight_strategies():
    assert "2990" in cap.suggest_highlights("Só R$ 29,90 hoje", "offer")
    assert "hoje" in cap.suggest_highlights("Só R$ 29,90 hoje", "offer")
    assert cap.suggest_highlights("Essa base tem acabamento natural", "keywords") == ["acabamento"]
    assert cap.suggest_highlights("qualquer coisa", "none") == []


def _caption(**kw):
    base = dict(id="c1", start_sec=1.0, end_sec=3.0, text="Você ainda aplica base desse jeito?", highlight_words=["base"])
    base.update(kw)
    return Caption(**base)


def test_ass_uses_safe_zone_and_gm_colors():
    s = RenderSettings(caption_mode="highlight", position="bottom")
    out = build_ass([_caption()], s)
    assert "PlayResX: 1080" in out and "PlayResY: 1920" in out
    assert ",2,54,151,422,1" in out  # alinhado embaixo, margens da zona segura
    assert "&H00DC7EB5&" in out  # lilás GM (BGR)
    assert "Dialogue: 0,0:00:01.00,0:00:03.00" in out
    assert "\\N" in out  # quebra em linhas


def test_ass_traditional_has_no_highlight_and_word_by_word_has_one_event_per_word():
    out = build_ass([_caption()], RenderSettings(caption_mode="traditional"))
    assert "\\c&H00DC7EB5" not in out
    wbw = build_ass([_caption()], RenderSettings(caption_mode="word-by-word"))
    assert wbw.count("Dialogue:") == 6


def test_ass_remaps_times_and_drops_captions_inside_cuts():
    tmap = TimeMap(keep_ranges(10, [(2.0, 3.0)]))
    caps = [_caption(start_sec=4.0, end_sec=5.0), _caption(id="c2", start_sec=2.1, end_sec=2.9)]
    out = build_ass(caps, RenderSettings(), tmap)
    assert out.count("Dialogue:") == 1
    assert "0:00:03.00,0:00:04.00" in out


def test_wrap_balances_lines():
    from app.services.ass import _wrap

    lines = _wrap(["Então", "olha", "R$", "29,90"], 16)
    assert lines == [[0, 1], [2, 3]]  # e não [Então olha R$] + [29,90]


# ---------- Fase 9: zoom ----------
from app.services import zoom as zoom_svc  # noqa: E402
from app.services.hook import analyze_hook  # noqa: E402


def _caps(spec):
    return [Caption(id=f"c{i}", start_sec=a, end_sec=b, text=t) for i, (a, b, t) in enumerate(spec)]


def test_zoom_plan_is_sparse_and_gentle():
    caps = _caps([(0.2 + i * 2.2, 2.0 + i * 2.2, "a b c") for i in range(14)])  # ~31 s de fala contínua
    sub = zoom_svc.plan_zoom(caps, 32, "subtle")
    dyn = zoom_svc.plan_zoom(caps, 32, "dynamic")
    assert zoom_svc.plan_zoom(caps, 32, "off") == []
    assert len(sub) < len(dyn)
    for plan, gap in ((sub, 6.0), (dyn, 3.5)):
        assert all(e.amp <= 0.09 for e in plan)
        for a, b in zip(plan, plan[1:]):
            assert b.start - a.end >= gap - 1e-9  # intervalo mínimo; nada sobreposto
    assert dyn[0].kind == "settle" and dyn[0].start == 0  # abertura reforça o gancho


def test_zoom_curve_is_smooth_and_bounded():
    ev = [zoom_svc.ZoomEvent(2.0, 5.0, 0.08, "in")]
    assert zoom_svc.zoom_at(ev, 1.0) == 1.0 and zoom_svc.zoom_at(ev, 6.0) == 1.0
    assert abs(zoom_svc.zoom_at(ev, 3.5) - 1.08) < 1e-9
    zs = [zoom_svc.zoom_at(ev, 2 + i * 0.05) for i in range(61)]
    assert max(abs(b - a) for a, b in zip(zs, zs[1:])) < 0.01  # sem saltos
    settle = [zoom_svc.ZoomEvent(0, 1.6, 0.09, "settle")]
    assert abs(zoom_svc.zoom_at(settle, 0) - 1.09) < 1e-9 and zoom_svc.zoom_at(settle, 1.6) == 1.0


def test_zoom_expr_follows_cuts():
    tmap = TimeMap(keep_ranges(20, [(1.0, 3.0)]))
    expr = zoom_svc.ffmpeg_zoom_expr([zoom_svc.ZoomEvent(5.0, 8.0, 0.05, "in")], tmap)
    assert expr and "(t-3.000)" in expr  # 5 s original -> 3 s no vídeo cortado
    assert zoom_svc.ffmpeg_zoom_expr([zoom_svc.ZoomEvent(1.2, 1.5, 0.05, "in")], tmap) is None  # dentro do corte


# ---------- Fase 10: gancho ----------
def test_hook_flags_slow_start_and_suggests_trim():
    caps = _caps([(1.6, 3.0, "Então hoje vou mostrar uma base muito boa que eu testei bastante")])
    h = analyze_hook(caps, RenderSettings())
    by_id = {c["id"]: c for c in h["checks"]}
    assert not by_id["fast_start"]["ok"] and by_id["fast_start"]["action"] == "trim_start"
    assert h["suggestedTrimSec"] == 1.45
    assert not by_id["short_first_caption"]["ok"]
    assert h["level"] == "weak"
    # depois de cortar o início, a checagem passa
    assert {c["id"]: c for c in analyze_hook(caps, RenderSettings(trim_start_sec=1.45))["checks"]}["fast_start"]["ok"]


def test_hook_strong_opening():
    caps = _caps([(0.2, 2.0, "Você ainda aplica base assim?")])
    caps[0].highlight_words = ["base"]
    h = analyze_hook(caps, RenderSettings())
    assert h["level"] == "strong" and all(c["ok"] for c in h["checks"])
    assert analyze_hook([], RenderSettings()) is None


# ---------- Fase 12: efeitos sonoros ----------
from app.services import sfx as sfx_svc  # noqa: E402

SOUNDS = [sfx_svc.Sound("w1", "transicao"), sfx_svc.Sound("p1", "destaque"), sfx_svc.Sound("d1", "oferta")]


def test_sfx_empty_library_gives_no_events():
    assert sfx_svc.plan_sfx(_caps([(0, 2, "a b")]), [], RenderSettings(), [], 10) == []


def test_sfx_plan_is_sparse_and_prioritizes_offer():
    caps = _caps([(0.2 + i * 2.2, 2.0 + i * 2.2, "so R$ 29,90 hoje") for i in range(14)])
    for c in caps:
        c.highlight_words = ["2990"]
    s = RenderSettings(caption_mode="highlight", highlight_strategy="offer", zoom_mode="subtle")
    plan = zoom_svc.plan_zoom(caps, 32, "subtle")
    ev = sfx_svc.plan_sfx(caps, plan, s, SOUNDS, 32)
    assert ev and len(ev) <= 32 / 6 + 1  # nunca exagera
    assert all(b["startSec"] - a["startSec"] >= sfx_svc.MIN_GAP_SEC - 1e-6 for a, b in zip(ev, ev[1:]))
    assert {e["sfxId"] for e in ev} == {"d1"}  # preço vence transição/destaque nos mesmos pontos


def test_sfx_uses_only_categories_present_and_respects_caption_mode():
    caps = _caps([(1.0, 3.0, "olha essa base")])
    caps[0].highlight_words = ["base"]
    only_transition = [sfx_svc.Sound("w1", "transicao")]
    plan = [zoom_svc.ZoomEvent(1.0, 3.0, 0.05, "in")]
    ev = sfx_svc.plan_sfx(caps, plan, RenderSettings(caption_mode="highlight"), only_transition, 10)
    assert [e["sfxId"] for e in ev] == ["w1"]
    # legenda tradicional não mostra destaque, então não há som de destaque
    ev = sfx_svc.plan_sfx(caps, [], RenderSettings(caption_mode="traditional"), SOUNDS, 10)
    assert ev == []


# ---------- Fase 11: B-roll ----------
from app.services import broll as broll_svc  # noqa: E402


def _bcaps():
    caps = _caps([(0.2, 2.0, "Você ainda aplica base"), (4.1, 6.0, "essa base Ruby Rose é ótima"), (10.5, 12.5, "olha a Ruby Rose de novo"), (14.0, 16.0, "e o gloss brilhante")])
    return caps


def test_broll_only_where_product_is_mentioned():
    clips = [broll_svc.Clip("c1", "base Ruby Rose, ruby rose", 5.0), broll_svc.Clip("c2", "kit renovação", 5.0)]
    ev = broll_svc.plan_broll(_bcaps(), clips, 20)
    assert [e["clipId"] for e in ev] == ["c1", "c1"]  # "kit renovação" nunca é falado: sem B-roll
    assert ev[0]["startSec"] >= broll_svc.HOOK_SAFE_SEC
    assert all(e["endSec"] - e["startSec"] <= broll_svc.DEFAULT_SEC + 1e-6 for e in ev)
    assert all(b["startSec"] - a["endSec"] >= broll_svc.MIN_GAP_SEC - 1e-6 for a, b in zip(ev, ev[1:]))


def test_broll_respects_hook_coverage_and_clip_length():
    clips = [broll_svc.Clip("c1", "ainda aplica", 5.0)]  # citado em 0,2 s: empurrado para depois do gancho
    ev = broll_svc.plan_broll(_bcaps(), clips, 20)
    assert ev and ev[0]["startSec"] == broll_svc.HOOK_SAFE_SEC
    short = [broll_svc.Clip("c1", "ainda aplica", 1.0)]
    assert broll_svc.plan_broll(_bcaps(), short, 20)[0]["endSec"] - 1.5 == 1.0  # não passa do tamanho do clipe
    assert broll_svc.plan_broll(_bcaps(), [broll_svc.Clip("c1", "ainda aplica", 0.5)], 20) == []  # curto demais
    assert broll_svc.plan_broll(_bcaps(), clips, 4.0) == []  # sem espaço no vídeo
    assert broll_svc.plan_broll(_bcaps(), [], 20) == []


# ---------- mensagens de erro da transcrição local ----------
def test_local_transcription_errors_are_friendly(monkeypatch, tmp_path):
    import sys
    import types

    from app.errors import ProcessingError
    from app.services import transcribe as tr

    class Boom(Exception):
        pass

    def fake_model(error):
        mod = types.ModuleType("faster_whisper")

        def WhisperModel(*a, **k):  # noqa: N802
            raise error

        mod.WhisperModel = WhisperModel
        return mod

    monkeypatch.setattr(tr, "_local_model", None)
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_model(ConnectionError("Connection aborted")))
    try:
        tr._local(tmp_path / "x.wav", [])
        raise AssertionError("deveria falhar")
    except ProcessingError as e:
        assert "baixar o modelo" in e.user_message and "Connection aborted" in e.detail

    monkeypatch.setitem(sys.modules, "faster_whisper", fake_model(Boom("algo estranho")))
    try:
        tr._local(tmp_path / "x.wav", [])
        raise AssertionError("deveria falhar")
    except ProcessingError as e:
        assert "diagnostico" in e.user_message and "Traceback" not in e.user_message
