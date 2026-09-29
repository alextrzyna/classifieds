from pathlib import Path

import pytest

from classifieds.frontmatter import load

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ["new-item", "import-photos", "prep-photos", "price-research", "write-listing", "post-listing", "sell-item"]


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


def test_outer_repo_ignores_items_dir():
    import subprocess
    if not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    rc = subprocess.run(["git", "check-ignore", "-q", "items/anything/item.md"], cwd=ROOT).returncode
    assert rc == 0, "items/ must be ignored by the toolkit repo; item data lives in its own repo"


def test_items_repo_ignores_raw_photos():
    import subprocess
    items = ROOT / "items"
    if not (items / ".git").exists():
        pytest.skip("no nested items repo in this checkout")
    for name in ("IMG_1.jpg", "IMG_2.HEIC", "photo.png"):
        rc = subprocess.run(["git", "check-ignore", "-q", f"x/photos/raw/{name}"], cwd=items).returncode
        assert rc == 0, f"{name} should be ignored by the items repo"
    rc = subprocess.run(["git", "check-ignore", "-q", "x/photos/raw/.gitkeep"], cwd=items).returncode
    assert rc == 1, ".gitkeep should not be ignored"
