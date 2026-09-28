from pathlib import Path

import pytest

from classifieds.frontmatter import Document, save
from classifieds.items import ItemError, latest_research, load_item, validate_item
from .conftest import add_listing, add_research, make_item


def test_load_item_reads_meta_and_body(repo: Path):
    d = make_item(repo)
    item = load_item(d)
    assert item.slug == "test-item"
    assert item.status == "draft"
    assert "Private notes" in item.body


def test_load_item_missing_file(repo: Path):
    with pytest.raises(ItemError, match="item.md"):
        load_item(repo / "items" / "nope")


def test_valid_draft_has_no_problems(repo: Path):
    assert validate_item(load_item(make_item(repo))) == []


def test_missing_required_key(repo: Path):
    d = make_item(repo, brand=None)
    problems = validate_item(load_item(d))
    assert any("brand" in p for p in problems)


def test_wrong_type_reports_key(repo: Path):
    d = make_item(repo, year="twenty twenty one")
    problems = validate_item(load_item(d))
    assert any("year" in p and "int" in p for p in problems)


def test_boolean_is_not_an_int(repo: Path):
    d = make_item(repo, year=True)
    problems = validate_item(load_item(d))
    assert any("year" in p for p in problems)


def test_slug_must_match_folder(repo: Path):
    d = make_item(repo)
    doc = Document(dict(load_item(d).meta, slug="other"), load_item(d).body)
    save(d / "item.md", doc)
    assert any("slug" in p for p in validate_item(load_item(d)))


def test_unknown_status(repo: Path):
    d = make_item(repo, status="pending")
    assert any("status" in p for p in validate_item(load_item(d)))


def test_floor_above_ask(repo: Path):
    d = make_item(repo, ask=100, floor=200)
    assert any("floor" in p for p in validate_item(load_item(d)))


def test_priced_requires_ask_floor_and_research(repo: Path):
    d = make_item(repo, status="priced")
    problems = validate_item(load_item(d))
    assert any("ask" in p for p in problems)
    assert any("floor" in p for p in problems)
    assert any("research" in p for p in problems)


def test_priced_with_everything_is_valid(repo: Path):
    d = make_item(repo, status="priced", ask=3000, floor=2500)
    add_research(d)
    assert validate_item(load_item(d)) == []


def test_listed_requires_marketplaces_and_listing_files(repo: Path):
    d = make_item(repo, status="listed", ask=3000, floor=2500)
    add_research(d)
    problems = validate_item(load_item(d))
    assert any("marketplaces" in p for p in problems)
    d2 = make_item(repo, slug="two", status="listed", ask=3000, floor=2500, marketplaces=["testmarket"])
    add_research(d2)
    assert any("listings/testmarket.md" in p for p in validate_item(load_item(d2)))
    add_listing(d2)
    assert validate_item(load_item(d2)) == []


def test_missing_log(repo: Path):
    d = make_item(repo)
    (d / "log.md").unlink()
    assert any("log.md" in p for p in validate_item(load_item(d)))


def test_latest_research_picks_newest_by_name(repo: Path):
    d = make_item(repo)
    assert latest_research(d) is None
    add_research(d)
    (d / "research" / "2026-10-01-pricing.md").write_text("---\n---\n")
    assert latest_research(d).name == "2026-10-01-pricing.md"
