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
