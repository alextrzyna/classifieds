"""Check a marketplace listing file against the item and the marketplace profile."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .frontmatter import load
from .items import Item
from .profiles import Profile


class ListingError(ValueError):
    """The listing file is missing or unreadable."""


@dataclass
class Listing:
    meta: dict
    body: str


def load_listing(item_dir: Path, marketplace: str) -> Listing:
    path = item_dir / "listings" / f"{marketplace}.md"
    if not path.exists():
        raise ListingError(f"no listing for {marketplace}: {path}")
    doc = load(path)
    return Listing(meta=doc.meta, body=doc.body)


def web_photos(item_dir: Path) -> list[Path]:
    web = item_dir / "photos" / "web"
    return sorted(web.glob("*.jpg")) if web.is_dir() else []


def floor_patterns(floor: int) -> list[str]:
    plain = str(floor)
    forms = [plain]
    grouped = f"{floor:,}"
    if grouped != plain:
        forms.append(grouped)
    return forms + [f"${f}" for f in forms]


def check_listing(item: Item, listing: Listing, profile: Profile, photos: list[Path]) -> list[str]:
    problems: list[str] = []
    meta = listing.meta
    body = listing.body.strip()

    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        problems.append("title is missing")
    elif len(title) > profile.title_max:
        problems.append(f"title is {len(title)} chars; {profile.name} allows {profile.title_max}")

    if not body:
        problems.append("description is empty")
    elif len(body) > profile.description_max:
        problems.append(f"description is {len(body)} chars; {profile.name} allows {profile.description_max}")

    for key in profile.required_fields:
        if key not in meta or meta[key] in ("", None):
            problems.append(f"required field missing: {key}")

    for key, allowed in profile.field_options.items():
        if key in meta and meta[key] not in allowed:
            problems.append(f"field {key} is {meta[key]!r}; allowed: {', '.join(map(str, allowed))}")

    price = meta.get("price")
    if price is not None:
        if isinstance(price, bool) or not isinstance(price, int):
            problems.append(f"price must be an int, got {type(price).__name__}")
        elif item.floor is not None and price < item.floor:
            problems.append(f"price {price} is below floor {item.floor}")

    if item.floor is not None:
        for pattern in floor_patterns(item.floor):
            if pattern in body:
                problems.append(f"floor price appears in description as '{pattern}'")
                break

    if not photos:
        problems.append("no web photos; run `classifieds photos` first")
    elif len(photos) > profile.photo_max:
        problems.append(f"{len(photos)} photos; {profile.name} allows at most {profile.photo_max}")
    for photo in photos:
        with Image.open(photo) as img:
            shortest = min(img.size)
        if shortest < profile.photo_min_px:
            problems.append(f"{photo.name} shortest side is {shortest}px; {profile.name} needs {profile.photo_min_px}px")

    return problems
