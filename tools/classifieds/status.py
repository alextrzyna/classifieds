"""Status transitions for items, with an append-only log."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .frontmatter import Document, save
from .items import Item, load_item, validate_item

TRANSITIONS: dict[str, set[str]] = {
    "draft": {"priced"},
    "priced": {"listed"},
    "listed": {"sold", "withdrawn", "priced"},
    "withdrawn": {"priced"},
    "sold": set(),
}


class StatusError(ValueError):
    """The requested status change is not allowed."""


def can_transition(old: str, new: str) -> bool:
    return new in TRANSITIONS.get(old, set())


def append_log(item_dir: Path, day: date, event: str, detail: str) -> None:
    with (item_dir / "log.md").open("a", encoding="utf-8") as fh:
        fh.write(f"{day.isoformat()}  {event}  {detail}\n")


def apply_status(
    item_dir: Path,
    new_status: str,
    price: int | None = None,
    floor: int | None = None,
    note: str | None = None,
    today: date | None = None,
) -> Item:
    today = today or date.today()
    item = load_item(item_dir)
    if not can_transition(item.status, new_status):
        raise StatusError(f"illegal transition {item.status} -> {new_status}")

    meta = dict(item.meta)
    meta["status"] = new_status
    meta["updated"] = today
    if price is not None:
        meta["ask"] = price
    if floor is not None:
        meta["floor"] = floor
    candidate = Item(dir=item_dir, meta=meta, body=item.body)

    problems = validate_item(candidate)
    if problems:
        raise StatusError("cannot set status:\n  " + "\n  ".join(problems))

    save(item_dir / "item.md", Document(meta, item.body))

    parts: list[str] = []
    if price is not None:
        parts.append(f"ask {price}")
    if floor is not None:
        parts.append(f"floor {floor}")
    if note:
        parts.append(note)
    append_log(item_dir, today, new_status, " ".join(parts) or f"from {item.status}")
    return candidate
