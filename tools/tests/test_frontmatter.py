from datetime import date
from pathlib import Path

import pytest

from classifieds.frontmatter import Document, FrontmatterError, load, parse, render, save


def test_parse_splits_meta_and_body():
    doc = parse("---\ntitle: Hi\nyear: 2021\n---\nBody text\n")
    assert doc.meta == {"title": "Hi", "year": 2021}
    assert doc.body == "Body text\n"


def test_parse_without_frontmatter_gives_empty_meta():
    doc = parse("Just body\n")
    assert doc.meta == {}
    assert doc.body == "Just body\n"


def test_parse_dates_become_date_objects():
    doc = parse("---\ncreated: 2026-09-28\n---\n")
    assert doc.meta["created"] == date(2026, 9, 28)


def test_parse_unterminated_frontmatter_raises():
    with pytest.raises(FrontmatterError, match="unterminated"):
        parse("---\ntitle: Hi\nBody\n")


def test_render_round_trips():
    doc = Document({"slug": "x", "year": 2021, "created": date(2026, 9, 28)}, "# Heading\n")
    text = render(doc)
    assert text.startswith("---\nslug: x\nyear: 2021\ncreated: 2026-09-28\n---\n# Heading\n")
    assert parse(text) == doc


def test_load_names_file_on_error(tmp_path: Path):
    bad = tmp_path / "item.md"
    bad.write_text("---\nslug: x\nno close\n")
    with pytest.raises(FrontmatterError, match="item.md"):
        load(bad)


def test_save_and_load(tmp_path: Path):
    p = tmp_path / "doc.md"
    save(p, Document({"a": 1}, "body\n"))
    assert load(p) == Document({"a": 1}, "body\n")
