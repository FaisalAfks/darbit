import numpy as np

from darbit.capture import distinct
from darbit.core.geometry import Region


def test_distinct_scores_low_for_a_unique_image():
    shot = np.random.default_rng(1).integers(0, 255, (200, 300, 3), dtype=np.uint8)
    image = shot[50:70, 100:130].copy()
    assert distinct(image, shot, Region(100, 50, 30, 20)) < 0.7


def test_distinct_scores_high_for_a_repeated_image():
    shot = np.random.default_rng(1).integers(0, 255, (200, 300, 3), dtype=np.uint8)
    image = shot[50:70, 100:130].copy()
    shot[150:170, 200:230] = image
    assert distinct(image, shot, Region(100, 50, 30, 20)) > 0.99


def test_images_in_a_script_skips_comments(tmp_path):
    from darbit.capture import images_in

    script = tmp_path / "bot.py"
    script.write_text('a = "Gui.Play.png" #"Old.png"\n#b = ["Gone.png"]\nc = ["x.png","Gui.Play.png"]\n',
                      encoding="utf-8")
    assert images_in(script) == ["Gui.Play.png", "x.png"]


def test_item_kinds():
    from darbit.capture import Item

    assert Item.parse("Gui.Play") == Item("Gui.Play", "image")
    assert Item.parse("location:afk/spot") == Item("afk/spot", "location")
    assert Item.parse("region:menus/bag") == Item("menus/bag", "region")
