from datetime import date
from pathlib import Path

import pytest

from classifieds.items import load_item
from classifieds.status import StatusError, append_log, apply_status, can_transition
from .conftest import add_listing, add_research, make_item

TODAY = date(2026, 9, 29)


@pytest.mark.parametrize("old,new,ok", [
    ("draft", "priced", True),
    ("priced", "listed", True),
    ("listed", "sold", True),
    ("listed", "withdrawn", True),
    ("listed", "priced", True),
    ("withdrawn", "priced", True),
    ("draft", "listed", False),
    ("sold", "listed", False),
    ("priced", "sold", False),
])
def test_transitions(old, new, ok):
    assert can_transition(old, new) is ok


def test_append_log_writes_dated_line(repo: Path):
    d = make_item(repo)
    append_log(d, TODAY, "note", "hello")
    assert (d / "log.md").read_text().endswith("2026-09-29  note  hello\n")


def test_apply_status_draft_to_priced(repo: Path):
    d = make_item(repo)
    add_research(d)
    item = apply_status(d, "priced", price=3000, floor=2500, today=TODAY)
    assert item.status == "priced"
    assert item.ask == 3000 and item.floor == 2500
    reloaded = load_item(d)
    assert reloaded.meta["updated"] == TODAY
    assert reloaded.meta["ask"] == 3000
    log = (d / "log.md").read_text()
    assert "2026-09-29  priced  ask 3000 floor 2500" in log


def test_apply_status_note_goes_in_log(repo: Path):
    d = make_item(repo, status="priced", ask=3000, floor=2500, marketplaces=["testmarket"])
    add_research(d)
    add_listing(d)
    apply_status(d, "listed", note="https://example.com/listing/1", today=TODAY)
    assert "listed  https://example.com/listing/1" in (d / "log.md").read_text()


def test_illegal_transition_does_not_write(repo: Path):
    d = make_item(repo)
    before = (d / "item.md").read_text()
    with pytest.raises(StatusError, match="draft -> listed"):
        apply_status(d, "listed", today=TODAY)
    assert (d / "item.md").read_text() == before


def test_invalid_result_does_not_write(repo: Path):
    d = make_item(repo)
    before = (d / "item.md").read_text()
    with pytest.raises(StatusError, match="research"):
        apply_status(d, "priced", price=3000, floor=2500, today=TODAY)
    assert (d / "item.md").read_text() == before
    assert "priced" not in (d / "log.md").read_text()


def test_reprice_from_listed_keeps_marketplaces(repo: Path):
    d = make_item(repo, status="listed", ask=3000, floor=2500, marketplaces=["testmarket"])
    add_research(d)
    add_listing(d)
    item = apply_status(d, "priced", price=2800, today=TODAY)
    assert item.ask == 2800
    assert item.marketplaces == ["testmarket"]
