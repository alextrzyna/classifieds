from pathlib import Path

import pytest

from classifieds.frontmatter import load

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ["new-item", "prep-photos"]


@pytest.mark.parametrize("name", SKILLS)
def test_skill_has_frontmatter_and_gate(name: str):
    doc = load(ROOT / ".claude" / "skills" / name / "SKILL.md")
    assert doc.meta["name"] == name
    assert len(doc.meta["description"]) > 20
    assert "classifieds validate" in doc.body
