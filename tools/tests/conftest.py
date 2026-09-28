"""Shared fixtures: a throwaway repo with one marketplace and one item."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from classifieds.frontmatter import Document, save

PROFILE_TEXT = """---
name: Test Market
url: https://example.com/sell
title_max: 40
description_max: 300
photo_max: 3
photo_min_px: 100
fee_rate: 0.0
required_fields: [title, price, condition]
field_options:
  condition: [new, used]
---
# Test Market

## Posting flow
1. Open the sell page.
"""

ITEM_BODY = """# 2021 Test Bike

## Overview
A bike.

## Private notes
Do not publish.
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "marketplaces").mkdir()
    (tmp_path / "marketplaces" / "testmarket.md").write_text(PROFILE_TEXT)
    (tmp_path / "items").mkdir()
    return tmp_path


def base_meta(**overrides) -> dict:
    meta = {
        "slug": "test-item",
        "status": "draft",
        "category": "bike",
        "brand": "Test",
        "model": "Bike",
        "year": 2021,
        "condition": "used",
        "location": "Seattle, WA",
        "currency": "USD",
        "created": date(2026, 9, 28),
    }
    meta.update(overrides)
    return {k: v for k, v in meta.items() if v is not None}


def make_item(repo: Path, body: str = ITEM_BODY, **overrides) -> Path:
    item_dir = repo / "items" / overrides.get("slug", "test-item")
    item_dir.mkdir(parents=True, exist_ok=True)
    save(item_dir / "item.md", Document(base_meta(**overrides), body))
    (item_dir / "log.md").write_text("2026-09-28  created  test item\n")
    return item_dir


def add_research(item_dir: Path, ask: int = 3000, floor: int = 2500) -> Path:
    research = item_dir / "research"
    research.mkdir(exist_ok=True)
    p = research / "2026-09-28-pricing.md"
    save(p, Document(
        {"item": "test-item", "date": date(2026, 9, 28), "recommended_ask": ask,
         "floor": floor, "currency": "USD", "sources": ["example"]},
        "| source | price |\n|---|---|\n| example | 3000 |\n",
    ))
    return p


def add_listing(item_dir: Path, marketplace: str = "testmarket", body: str = "A fine bike.\n", **meta) -> Path:
    listings = item_dir / "listings"
    listings.mkdir(exist_ok=True)
    full = {"title": "2021 Test Bike", "price": 3000, "condition": "used"}
    full.update(meta)
    p = listings / f"{marketplace}.md"
    save(p, Document(full, body))
    return p
