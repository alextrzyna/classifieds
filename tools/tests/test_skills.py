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
