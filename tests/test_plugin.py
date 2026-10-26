"""Tests for birthday_wishes plugin."""

import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType

fake_base = ModuleType("src.plugins.base")


class PluginBase:
    def __init__(self, manifest=None):
        self.manifest = manifest or {}
        self.config = {}

    def clear_cache(self):
        pass


class PluginResult:
    def __init__(self, available=True, data=None, error=None):
        self.available = available
        self.data = data or {}
        self.error = error


fake_base.PluginBase = PluginBase
fake_base.PluginResult = PluginResult
sys.modules.setdefault("src", ModuleType("src"))
sys.modules.setdefault("src.plugins", ModuleType("src.plugins"))
sys.modules["src.plugins.base"] = fake_base

spec = importlib.util.spec_from_file_location(
    "birthday_wishes", Path(__file__).resolve().parent.parent / "__init__.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_plugin_id():
    assert mod.BirthdayWishesPlugin({}).plugin_id == "birthday_wishes"


def test_parse_uk_date():
    people = mod._parse_people("Alice Smith, 15/03")
    assert len(people) == 1
    assert people[0]["forename"] == "Alice"
    assert people[0]["surname"] == "Smith"
    assert people[0]["day"] == 15
    assert people[0]["month"] == 3


def test_parse_iso():
    people = mod._parse_people("Bob, 1990-06-22")
    assert people[0]["day"] == 22
    assert people[0]["month"] == 6


def test_note_rows_max_15():
    block, r1, r2, r3, c1, c2 = mod._format_note("Alice", True, 0, 0)
    assert mod._tile_len(r1) <= 15
    assert len(r2) == 15
    assert len(r3) == 15
    assert "BIRTHDAY" in r2
    assert "ALICE" in r3


def test_happy_block():
    assert mod._happy_block("Alice") == "Happy Birthday Alice"


def test_fetch():
    p = mod.BirthdayWishesPlugin({})
    p.config = {
        "birthdays": "Alice Smith, 15/03\nBob Jones, 22/06",
        "display_mode": "today_or_next",
        "refresh_seconds": 3600,
    }
    r = p.fetch_data()
    assert r.available
    assert r.data["forename"]
    assert len(r.data["note_row2"]) == 15
    assert len(r.data["note_row3"]) == 15
    assert "Happy Birthday" in r.data["happy_block"]
