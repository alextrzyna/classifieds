from pathlib import Path

import pytest

from classifieds.items import load_item, validate_item

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("item_dir", sorted((ROOT / "items").glob("*/")), ids=lambda p: p.name)
def test_every_real_item_validates(item_dir: Path):
    assert validate_item(load_item(item_dir)) == []
