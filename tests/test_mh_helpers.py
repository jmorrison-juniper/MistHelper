import importlib.metadata as ilm
import mh_helpers


def test_parse_version_basic():
    assert mh_helpers._parse_version("0.59.3") == (0, 59, 3)


def test_parse_version_alpha():
    assert mh_helpers._parse_version("1.2.3a1") == (1, 2, 3)


def test_get_installed_version_monkeypatch(monkeypatch):
    def fake_version(name):
        return "2.0.1"

    monkeypatch.setattr(ilm, "version", fake_version)
    assert mh_helpers._get_installed_version("somepkg") == "2.0.1"
