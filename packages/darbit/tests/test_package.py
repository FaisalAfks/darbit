import darbit


def test_version():
    assert darbit.__version__


def test_the_version_matches_the_package_metadata():
    import tomllib
    from pathlib import Path

    import darbit

    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    assert darbit.__version__ == tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
