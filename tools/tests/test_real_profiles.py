from pathlib import Path

import pytest

from classifieds.profiles import load_profile

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["pinkbike", "facebook", "craigslist", "ebay"])
def test_real_profile_loads(name: str):
    profile = load_profile(ROOT / "marketplaces" / f"{name}.md")
    assert profile.title_max > 0
    assert profile.photo_max > 0
    assert "title" in profile.required_fields
    assert "price" in profile.required_fields
    assert "## Posting flow" in profile.body
