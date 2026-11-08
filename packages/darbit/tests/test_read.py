"""Reading text: the parsers, decoding with some characters, trimming, `d.read` with a fake reader, the missing extra,
and the real RapidOCR models when the ocr extra is installed."""

import json
import warnings

import cv2
import numpy as np
import pytest

import darbit as d
from darbit.core import rapid
from darbit.core.geometry import Region
from darbit.core.reading import PLAIN, Prepare, Reading, characters, decode, parse_number, parse_time, trim
from darbit.core.targets import Match, Target, save
from darbit.platform import screen
from darbit.runtime import read, readers


def test_numbers_are_read_as_games_show_them():
    assert parse_number("4.99M") == 4990000.0  # exact, not 4990000.000000001
    assert parse_number("126.62B") == 126620000000.0
    assert parse_number("1,234") == 1234.0
    assert parse_number("12,345.5") == 12345.5
    assert parse_number("12%") == 12.0
    assert parse_number("1.5k") == 1500.0
    assert parse_number(" 4.99 M ") == 4990000.0
    assert parse_number("-3") == -3.0
    assert parse_number("1,5") == 1.5  # a decimal comma
    assert parse_number("42") == 42.0


def test_what_isnt_a_number_is_none():
    for text in (None, "", "abc", "4.9.9", "12x", "M", "1,2,3", "02:31"):
        assert parse_number(text) is None, text


def test_times_are_read_as_seconds():
    assert parse_time("02:31") == 151.0
    assert parse_time("1:02:03") == 3723.0
    assert parse_time("2m 30s") == 150.0
    assert parse_time("2m30s") == 150.0
    assert parse_time("45s") == 45.0
    assert parse_time("1h 5m") == 3900.0
    assert parse_time("1d 2h") == 93600.0
    assert parse_time("02:31.5") == 151.5


def test_what_isnt_a_time_is_none():
    for text in (None, "", "abc", "2x 30s", "12", "5 coins", "1::2"):
        assert parse_time(text) is None, text


def test_character_sets_by_name_or_as_given():
    assert characters("digits") == "0123456789"
    assert "M" in characters("number") and ":" not in characters("number")
    assert ":" in characters("time")
    assert characters("0123ABC") == "0123ABC"
    assert characters(None) is None


ALPHABET = ["blank", "0", "O", "1", "l", ":"]


def chances(*steps: int) -> np.ndarray:
    """Chances per step where each step's likeliest character is the given index, and the next likeliest index 1
    (the digit 0) a little behind it."""
    rows = np.full((len(steps), len(ALPHABET)), 0.01, np.float32)
    for row, index in enumerate(steps):
        rows[row, index] = 0.6
        if index != 1:
            rows[row, 1] = 0.3
    return rows


def test_decoding_collapses_repeats_and_drops_blanks():
    assert decode(chances(3, 3, 0, 3, 0, 5), ALPHABET).text == "11:"
    assert decode(chances(0, 0), ALPHABET) == Reading("", 0.0)


def test_decoding_with_only_some_characters_picks_the_likeliest_allowed_one():
    steps = chances(2, 0, 2)  # an O likelier than a 0, twice
    assert decode(steps, ALPHABET).text == "OO"  # control: any character
    limited = decode(steps, ALPHABET, "0123456789")
    assert limited.text == "00"
    assert limited.confidence == pytest.approx(0.3)


def test_trimming_cuts_to_the_text():
    pixels = np.full((120, 300, 3), 40, np.uint8)
    cv2.putText(pixels, "123", (120, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1, cv2.LINE_AA)
    cut = trim(pixels)
    assert cut.shape[0] < 30 and cut.shape[1] < 60
    plain = np.full((120, 300, 3), 40, np.uint8)
    assert trim(plain).shape == plain.shape  # control: nothing stands out, nothing is cut


def test_preparing_options_come_from_a_table():
    assert Prepare.from_dict(None) is PLAIN
    assert PLAIN.trim and not PLAIN.lines and PLAIN.upscale == 1.0
    how = Prepare.from_dict({"upscale": True, "invert": True, "threshold": True, "lines": True, "trim": False})
    assert how == Prepare(upscale=2.0, invert=True, threshold=0, lines=True, trim=False)
    assert Prepare.from_dict({"threshold": 128}).threshold == 128


class FakeReader:
    """Gives what it's told, and notes what it was asked."""

    def __init__(self):
        self.answer = Reading("4.99M", 0.97)
        self.found: list[Reading] = []
        self.asked: list[tuple[str, tuple, str | None]] = []

    def line(self, pixels, allowed):
        self.asked.append(("line", pixels.shape, allowed))
        return self.answer

    def lines(self, pixels, allowed):
        self.asked.append(("lines", pixels.shape, allowed))
        return self.found


@pytest.fixture
def screen_with_text(tmp_path, monkeypatch):
    """A 400 x 300 screen, a fake reader, and what was recorded."""
    pixels = np.full((300, 400, 3), 30, np.uint8)
    grabbed = []

    def grab(region=None):
        whole = Region(0, 0, 400, 300)
        area = whole if region is None else region.intersect(whole)
        grabbed.append(area)
        if area is None:
            return np.zeros((0, 0, 3), np.uint8), Region(0, 0, 0, 0)
        return pixels[area.y : area.bottom, area.x : area.right].copy(), area

    recorded = []

    def note(event, **fields):
        recorded.append((event, fields))

    fake = FakeReader()
    monkeypatch.setattr(screen, "grab", grab)
    monkeypatch.setattr(read, "record", note)
    monkeypatch.setattr(readers, "current", lambda: fake)
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "read", {"trim": False})
    return fake, grabbed, recorded, pixels


def test_reading_a_region_grabs_it_and_records_the_confidence(screen_with_text):
    fake, grabbed, recorded, _ = screen_with_text
    assert d.read(Region(10, 20, 100, 30)) == "4.99M"
    assert grabbed == [Region(10, 20, 100, 30)]
    assert fake.asked == [("line", (30, 100, 3), None)]
    event, fields = recorded[0]
    assert event == "read"
    assert fields["text"] == "4.99M" and fields["confidence"] == 0.97 and fields["counted"]


def test_numbers_and_times_are_parsed_and_limited_to_their_characters(screen_with_text):
    fake, _, _, _ = screen_with_text
    assert d.read_number(Region(0, 0, 50, 20)) == 4990000.0
    assert fake.asked[-1][2] == characters("number")
    fake.answer = Reading("02:31", 0.9)
    assert d.read_time(d.Region(0, 0, 50, 20)) == 151.0
    assert fake.asked[-1][2] == characters("time")
    fake.answer = Reading("hello", 0.9)
    assert d.read_number(Region(0, 0, 50, 20)) is None  # read, but not a number


def test_an_unsure_read_is_none(screen_with_text, monkeypatch):
    fake, _, recorded, _ = screen_with_text
    fake.answer = Reading("4.99M", 0.3)
    assert d.read(Region(0, 0, 50, 20)) is None
    assert recorded[-1][1]["counted"] is False
    monkeypatch.setattr(d.settings, "read_confidence", 0.2)
    assert d.read(Region(0, 0, 50, 20)) == "4.99M"  # control: counts with a lower bar


def test_an_unsure_single_line_is_read_again_line_by_line(screen_with_text):
    fake, _, _, _ = screen_with_text
    fake.answer = Reading("4m", 0.3)
    fake.found = [Reading("Daily", 0.9), Reading("quest", 0.8)]
    assert d.read(Region(0, 0, 200, 60)) == "Daily\nquest"
    assert [kind for kind, _, _ in fake.asked] == ["line", "lines"]


def test_lines_on_finds_each_line_first(screen_with_text, monkeypatch):
    fake, _, _, _ = screen_with_text
    fake.found = [Reading("one", 0.9), Reading("two", 0.9)]
    monkeypatch.setattr(d.settings, "read", {"lines": True})
    assert d.read(Region(0, 0, 200, 60)) == "one\ntwo"
    assert [kind for kind, _, _ in fake.asked] == ["lines"]


def test_a_named_region_is_read_where_it_is_with_its_own_characters(screen_with_text, tmp_path):
    fake, grabbed, _, _ = screen_with_text
    region = {"kind": "region", "region": [40, 50, 120, 30], "text": "digits", "read": {"upscale": 2}}
    (tmp_path / "Shop.Coins.json").write_text(json.dumps(region), encoding="utf-8")
    fake.answer = Reading("1234", 0.9)
    assert d.read_number("Shop.Coins") == 1234.0
    assert grabbed[-1] == Region(40, 50, 120, 30)
    assert fake.asked[-1] == ("line", (60, 240, 3), "0123456789")  # upscaled twice, digits only
    assert d.area("Shop.Coins").read() == "1234"
    assert d.read("Shop.Coins", chars="AB") == "1234"
    assert fake.asked[-1][2] == "AB"  # chars= over the Region's own


def test_a_named_image_is_read_inside_where_it_is_found(screen_with_text, tmp_path):
    fake, grabbed, _, pixels = screen_with_text
    badge = np.random.default_rng(4).integers(0, 255, (20, 40, 3), dtype=np.uint8)
    save(tmp_path / "Shop.Badge", badge)
    assert d.read("Shop.Badge") is None  # control: not on screen, nothing read
    assert fake.asked == []
    pixels[100:120, 200:240] = badge
    assert d.read("Shop.Badge") == "4.99M"
    assert grabbed[-1] == Region(200, 100, 40, 20)


def test_a_match_and_a_region_read_themselves(screen_with_text):
    fake, grabbed, _, _ = screen_with_text
    found = Match(5, 6, 70, 20, 0.99, Target(name="Timer", text="time"))
    fake.answer = Reading("1:02:03", 0.95)
    assert found.read_time() == 3723.0
    assert grabbed[-1] == Region(5, 6, 70, 20)
    assert found.read() == "1:02:03"
    assert fake.asked[-1][2] == characters("time")
    fake.answer = Reading("12%", 0.95)
    assert found.read_number() == 12.0
    assert d.Region(0, 0, 30, 10).read_number() == 12.0


def test_a_name_with_nothing_to_read_in_is_a_mistake(screen_with_text, tmp_path):
    (tmp_path / "Bag.Slot.json").write_text(json.dumps({"kind": "location", "location": [5, 5]}), encoding="utf-8")
    with pytest.raises(d.TargetError):
        d.read("Bag.Slot")


def test_without_the_extra_a_read_warns_once_and_is_none(monkeypatch):
    def missing(threads):
        raise ImportError("No module named 'rapidocr'")

    monkeypatch.setattr(rapid, "reader", missing)
    monkeypatch.setattr(readers, "_made", {})
    monkeypatch.setattr(readers, "_missing", set())
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(screen, "grab", lambda region=None: (np.zeros((10, 10, 3), np.uint8), region))
    with pytest.warns(UserWarning, match="ocr extra"):
        assert d.read(Region(0, 0, 10, 10)) is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # the second read says nothing more
        assert d.read(Region(0, 0, 10, 10)) is None


def test_an_unknown_reader_is_a_mistake(monkeypatch):
    monkeypatch.setattr(d.settings, "reader", "no-such-reader")
    with pytest.raises(ValueError, match="no reader called"):
        readers.current()


def test_the_bot_can_set_reading_in_darbit_toml(tmp_path):
    from darbit.project import manifest

    (tmp_path / "darbit.toml").write_text(
        '[bot]\nname = "x"\n[settings]\nreader = "rapidocr"\nread_confidence = 0.6\nread_threads = 2\n'
        "[settings.read]\nupscale = 2\n",
        encoding="utf-8",
    )
    project = manifest.load(tmp_path)
    assert project.settings["read"] == {"upscale": 2}
    assert project.settings["read_threads"] == 2


def drawn(text: str, room: int = 0) -> np.ndarray:
    size, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    pixels = np.full((size[1] + baseline + 12 + 2 * room, size[0] + 16 + 2 * room, 3), 30, np.uint8)
    origin = (8 + room, size[1] + 6 + room)
    cv2.putText(pixels, text, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (240, 240, 240), 2, cv2.LINE_AA)
    return pixels


@pytest.fixture(scope="module")
def real_reader():
    pytest.importorskip("rapidocr", reason="the ocr extra isn't installed")
    pytest.importorskip("onnxruntime", reason="the ocr extra isn't installed")
    return rapid.RapidReader(2)


def test_the_real_models_read_a_number_and_a_timer(real_reader):
    for text in ("4.99M", "126.62B", "1,234", "02:31", "Daily quest"):
        reading = real_reader.line(drawn(text), None)
        assert reading.text == text
        assert reading.confidence > 0.9


def test_the_real_models_read_only_the_allowed_characters(real_reader):
    reading = real_reader.line(drawn("4.99M"), "0123456789")
    assert set(reading.text) <= set("0123456789")
    assert real_reader.line(drawn("02:31"), characters("time")).text == "02:31"


def test_the_real_models_find_lines_in_a_loose_region(real_reader):
    loose = drawn("126.62B", room=50)
    assert [reading.text for reading in real_reader.lines(loose, None)] == ["126.62B"]
    assert real_reader.line(trim(loose), None).text == "126.62B"
