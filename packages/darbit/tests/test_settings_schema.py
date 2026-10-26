"""A bot's settings: the schema in settings.toml, checking config.toml, and saving it with its comments kept."""

import tomllib

import pytest

from darbit.project.settings_schema import SettingsError, as_json, load_schema, load_values, write_values

SCHEMA = """
[speed_raid]
label = "Speed Raid"
help = "One character every half hour."

  [speed_raid.enabled]
  type = "bool"
  default = true
  help = "The next character, every 30 minutes."

  [speed_raid.every_minutes]
  type = "int"
  default = 30
  min = 10
  max = 120

[controls.skills]
type = "keys"
default = "54132"

[afk.mode]
type = "choice"
options = ["claim", "stay"]
default = "claim"

[regions.bag]
type = "region"
default = [10, 20, 300, 200]
"""


def schema_in(tmp_path, text: str = SCHEMA):
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return load_schema(path)


def test_the_schema_has_sections_and_settings(tmp_path):
    schema = schema_in(tmp_path)
    keys = []
    for setting in schema.settings:
        keys.append(setting.key)
    assert keys == ["speed_raid.enabled", "speed_raid.every_minutes", "controls.skills", "afk.mode", "regions.bag"]
    assert schema.sections[0].label == "Speed Raid"
    assert schema.sections[0].help == "One character every half hour."
    assert schema.settings[1].rules == {"min": 10, "max": 120}
    assert schema.settings[1].label == "Every minutes"
    form = as_json(schema)
    assert form[0]["settings"][0]["help"] == "The next character, every 30 minutes."


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('[a]\ntype = "colour"', "type 'colour' isn't one of"),
        ('[a]\ntype = "int"\ndefault = "ten"', "the default should be a whole number"),
        ('[a]\ntype = "choice"', "a choice needs options"),
        ('[a]\ntype = "str"\nmin = 1', "min and max are for int and float"),
        ('[a]\ntype = "str"\ncolour = "red"', "unknown key 'colour'"),
        ('[a]\nlabel = "A"\nspeed = 3', "unknown key 'speed'"),
        ("[a\n", "settings.toml"),
    ],
)
def test_schema_mistakes_name_the_key(tmp_path, text, message):
    with pytest.raises(SettingsError, match=message):
        schema_in(tmp_path, text)


def test_a_missing_config_is_made_from_the_defaults(tmp_path):
    schema = schema_in(tmp_path)
    config = tmp_path / "config.toml"
    values = load_values(schema, config)
    assert values["speed_raid"] == {"enabled": True, "every_minutes": 30}
    assert values["regions"]["bag"] == [10, 20, 300, 200]
    assert tomllib.loads(config.read_text(encoding="utf-8"))["controls"]["skills"] == "54132"


def test_config_values_are_checked_and_every_problem_listed(tmp_path):
    schema = schema_in(tmp_path)
    config = tmp_path / "config.toml"
    config.write_text('[speed_raid]\nevery_minutes = 5\nenabled = "yes"\n[afk]\nmode = "sleep"\n', encoding="utf-8")
    with pytest.raises(SettingsError) as error:
        load_values(schema, config)
    text = str(error.value)
    assert "speed_raid.enabled should be true or false" in text
    assert "speed_raid.every_minutes should be at least 10" in text
    assert "afk.mode should be one of ['claim', 'stay']" in text


def test_values_not_in_the_file_take_their_default(tmp_path):
    schema = schema_in(tmp_path)
    config = tmp_path / "config.toml"
    config.write_text("[speed_raid]\nevery_minutes = 45\n", encoding="utf-8")
    values = load_values(schema, config)
    assert values["speed_raid"] == {"enabled": True, "every_minutes": 45}


def test_saving_keeps_comments_and_order(tmp_path):
    schema = schema_in(tmp_path)
    config = tmp_path / "config.toml"
    config.write_text(
        "# my settings, don't share\n"
        "[speed_raid]\n"
        "every_minutes = 30  # half an hour feels right\n"
        "enabled = true\n"
        "\n"
        "[notes]\n"
        'url = "https://example.com/#top"  # a link, the # inside isn\'t a comment\n',
        encoding="utf-8",
    )
    write_values(schema, config, {"speed_raid.every_minutes": 60, "afk.mode": "stay", "controls": {"skills": "12345"}})
    text = config.read_text(encoding="utf-8")
    assert text.startswith("# my settings, don't share\n[speed_raid]\nevery_minutes = 60  # half an hour feels right\n")
    assert 'url = "https://example.com/#top"  # a link' in text
    data = tomllib.loads(text)
    assert data["afk"]["mode"] == "stay"
    assert data["controls"]["skills"] == "12345"
    assert data["speed_raid"]["enabled"] is True


def test_saving_refuses_a_bad_value(tmp_path):
    schema = schema_in(tmp_path)
    with pytest.raises(SettingsError, match="should be at most 120"):
        write_values(schema, tmp_path / "config.toml", {"speed_raid.every_minutes": 500})
