from pathlib import Path

import pytest
from PIL import Image

from classifieds.items import load_item
from classifieds.listings import ListingError, check_listing, floor_patterns, load_listing, web_photos
from classifieds.profiles import load_profile
from .conftest import add_listing, add_research, make_item


def _photo(item_dir: Path, name: str, size=(400, 300)) -> Path:
    web = item_dir / "photos" / "web"
    web.mkdir(parents=True, exist_ok=True)
    p = web / name
    Image.new("RGB", size, "gray").save(p, "JPEG")
    return p


def _setup(repo: Path, **listing_meta):
    d = make_item(repo, status="priced", ask=3000, floor=2500)
    add_research(d)
    add_listing(d, **listing_meta)
    _photo(d, "01-hero.jpg")
    item = load_item(d)
    listing = load_listing(d, "testmarket")
    profile = load_profile(repo / "marketplaces" / "testmarket.md")
    return d, item, listing, profile


def test_good_listing_passes(repo: Path):
    d, item, listing, profile = _setup(repo)
    assert check_listing(item, listing, profile, web_photos(d)) == []


def test_load_listing_missing(repo: Path):
    d = make_item(repo)
    with pytest.raises(ListingError, match="testmarket"):
        load_listing(d, "testmarket")


def test_title_too_long(repo: Path):
    d, item, listing, profile = _setup(repo, title="x" * 41)
    assert any("title" in p and "40" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_description_too_long(repo: Path):
    d, item, listing, profile = _setup(repo)
    listing.body = "y" * 301
    assert any("description" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_empty_description(repo: Path):
    d, item, listing, profile = _setup(repo)
    listing.body = "  \n"
    assert any("description" in p and "empty" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_missing_required_field(repo: Path):
    d, item, listing, profile = _setup(repo)
    del listing.meta["condition"]
    assert any("condition" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_option_not_allowed(repo: Path):
    d, item, listing, profile = _setup(repo, condition="mint")
    assert any("condition" in p and "mint" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_price_below_floor(repo: Path):
    d, item, listing, profile = _setup(repo, price=2000)
    assert any("floor" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_price_must_be_int(repo: Path):
    d, item, listing, profile = _setup(repo, price="three grand")
    assert any("price" in p and "int" in p for p in check_listing(item, listing, profile, web_photos(d)))


@pytest.mark.parametrize("leak", ["2500", "2,500", "$2500", "$2,500"])
def test_floor_leak_in_body(repo: Path, leak: str):
    d, item, listing, profile = _setup(repo)
    listing.body = f"Would take {leak} today.\n"
    assert any("floor" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_floor_patterns():
    assert floor_patterns(2500) == ["2500", "2,500", "$2500", "$2,500"]
    assert floor_patterns(800) == ["800", "$800"]


def test_no_photos(repo: Path):
    d, item, listing, profile = _setup(repo)
    assert any("photo" in p for p in check_listing(item, listing, profile, []))


def test_too_many_photos(repo: Path):
    d, item, listing, profile = _setup(repo)
    for i in range(2, 5):
        _photo(d, f"{i:02d}-more.jpg")
    assert any("photo_max" in p or "at most 3" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_photo_too_small(repo: Path):
    d, item, listing, profile = _setup(repo)
    _photo(d, "02-tiny.jpg", size=(50, 50))
    assert any("02-tiny.jpg" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_web_photos_sorted_jpg_only(repo: Path):
    d = make_item(repo)
    _photo(d, "02-b.jpg")
    _photo(d, "01-a.jpg")
    (d / "photos" / "web" / "notes.txt").write_text("x")
    assert [p.name for p in web_photos(d)] == ["01-a.jpg", "02-b.jpg"]
