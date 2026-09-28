"""Item sheets: load item.md and validate it against the data model."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .frontmatter import FrontmatterError, load

STATUSES = ("draft", "priced", "listed", "sold", "withdrawn")
PRICED_OR_LATER = ("priced", "listed", "sold", "withdrawn")

REQUIRED: dict[str, type] = {
    "slug": str,
    "status": str,
    "category": str,
    "brand": str,
    "model": str,
    "year": int,
    "condition": str,
    "location": str,
    "created": date,
}
OPTIONAL: dict[str, type] = {
    "size": str,
    "ask": int,
    "floor": int,
    "currency": str,
    "marketplaces": list,
    "updated": date,
}


class ItemError(ValueError):
    """The item folder is missing or unreadable."""


@dataclass
class Item:
    dir: Path
    meta: dict
    body: str

    @property
    def slug(self) -> str:
        return str(self.meta.get("slug", ""))

    @property
    def status(self) -> str:
        return str(self.meta.get("status", ""))

    @property
    def ask(self) -> int | None:
        return self.meta.get("ask")

    @property
    def floor(self) -> int | None:
        return self.meta.get("floor")

    @property
    def marketplaces(self) -> list[str]:
        return list(self.meta.get("marketplaces") or [])


def load_item(item_dir: Path) -> Item:
    path = item_dir / "item.md"
    if not path.exists():
        raise ItemError(f"no item.md in {item_dir}")
    try:
        doc = load(path)
    except FrontmatterError as exc:
        raise ItemError(str(exc)) from exc
    return Item(dir=item_dir, meta=doc.meta, body=doc.body)


def latest_research(item_dir: Path) -> Path | None:
    research = item_dir / "research"
    files = sorted(research.glob("*-pricing.md")) if research.is_dir() else []
    return files[-1] if files else None


def _type_ok(value, expected: type) -> bool:
    if expected is int and isinstance(value, bool):
        return False
    return isinstance(value, expected)


def validate_item(item: Item) -> list[str]:
    problems: list[str] = []
    meta = item.meta

    for key, expected in REQUIRED.items():
        if key not in meta:
            problems.append(f"missing required field: {key}")
        elif not _type_ok(meta[key], expected):
            problems.append(f"field {key} must be {expected.__name__}, got {type(meta[key]).__name__}")

    for key, expected in OPTIONAL.items():
        if key in meta and not _type_ok(meta[key], expected):
            problems.append(f"field {key} must be {expected.__name__}, got {type(meta[key]).__name__}")

    if "slug" in meta and meta["slug"] != item.dir.name:
        problems.append(f"slug '{meta['slug']}' does not match folder name '{item.dir.name}'")

    status = meta.get("status")
    if status not in STATUSES:
        problems.append(f"status must be one of {', '.join(STATUSES)}; got {status!r}")

    if _type_ok(meta.get("ask"), int) and _type_ok(meta.get("floor"), int) and meta["floor"] > meta["ask"]:
        problems.append(f"floor {meta['floor']} is above ask {meta['ask']}")

    if not (item.dir / "log.md").exists():
        problems.append("log.md is missing")

    if status in PRICED_OR_LATER:
        if "ask" not in meta:
            problems.append(f"status {status} requires ask")
        if "floor" not in meta:
            problems.append(f"status {status} requires floor")
        if latest_research(item.dir) is None:
            problems.append(f"status {status} requires a research/*-pricing.md file")

    if status in ("listed", "sold"):
        if not item.marketplaces:
            problems.append(f"status {status} requires a non-empty marketplaces list")
        for market in item.marketplaces:
            if not (item.dir / "listings" / f"{market}.md").exists():
                problems.append(f"status {status} requires listings/{market}.md")

    return problems
