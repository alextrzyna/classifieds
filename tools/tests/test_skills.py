from pathlib import Path

import pytest

from classifieds.frontmatter import load

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ["new-item", "prep-photos", "price-research", "write-listing", "post-listing", "sell-item"]


@pytest.mark.parametrize("name", SKILLS)
def test_skill_has_frontmatter_and_gate(name: str):
    doc = load(ROOT / ".claude" / "skills" / name / "SKILL.md")
    assert doc.meta["name"] == name
    assert len(doc.meta["description"]) > 20
    assert "classifieds validate" in doc.body


def test_post_listing_never_submits():
    body = load(ROOT / ".claude" / "skills" / "post-listing" / "SKILL.md").body
    assert "never click" in body.lower()


def test_post_listing_handles_already_listed_item():
    body = load(ROOT / ".claude" / "skills" / "post-listing" / "SKILL.md").body
    assert "already `listed`" in body


def test_price_research_repricing_updates_listing():
    body = load(ROOT / ".claude" / "skills" / "price-research" / "SKILL.md").body
    assert "listings/" in body and "do not post again" in body.lower()


def test_prep_photos_previews_heic():
    body = load(ROOT / ".claude" / "skills" / "prep-photos" / "SKILL.md").body
    assert "sips" in body


def test_raw_photos_are_gitignored():
    import subprocess
    if not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    for name in ("IMG_1.jpg", "IMG_2.HEIC", "photo.png"):
        rc = subprocess.run(["git", "check-ignore", "-q", f"items/x/photos/raw/{name}"], cwd=ROOT).returncode
        assert rc == 0, f"{name} should be ignored"
    rc = subprocess.run(["git", "check-ignore", "-q", "items/x/photos/raw/.gitkeep"], cwd=ROOT).returncode
    assert rc == 1, ".gitkeep should not be ignored"
