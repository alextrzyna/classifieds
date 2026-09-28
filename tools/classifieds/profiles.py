"""Marketplace profiles: frontmatter limits plus a prose body for skills."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .frontmatter import load

REQUIRED_KEYS = ("name", "url", "title_max", "description_max", "photo_max", "photo_min_px", "required_fields")


class ProfileError(ValueError):
    """A marketplace profile is missing or malformed."""


@dataclass
class Profile:
    name: str
    url: str
    title_max: int
    description_max: int
    photo_max: int
    photo_min_px: int
    required_fields: list[str]
    fee_rate: float = 0.0
    field_options: dict[str, list[str]] = field(default_factory=dict)
    body: str = ""


def find_repo_root(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "marketplaces").is_dir():
            return candidate
    raise ProfileError(f"no marketplaces/ directory found above {start}")


def profile_path(repo_root: Path, marketplace: str) -> Path:
    return repo_root / "marketplaces" / f"{marketplace}.md"


def load_profile(path: Path) -> Profile:
    if not path.exists():
        raise ProfileError(f"no such marketplace profile: {path}")
    doc = load(path)
    missing = [k for k in REQUIRED_KEYS if k not in doc.meta]
    if missing:
        raise ProfileError(f"{path}: missing keys: {', '.join(missing)}")
    m = doc.meta
    return Profile(
        name=str(m["name"]),
        url=str(m["url"]),
        title_max=int(m["title_max"]),
        description_max=int(m["description_max"]),
        photo_max=int(m["photo_max"]),
        photo_min_px=int(m["photo_min_px"]),
        required_fields=list(m["required_fields"]),
        fee_rate=float(m.get("fee_rate", 0.0)),
        field_options={k: list(v) for k, v in (m.get("field_options") or {}).items()},
        body=doc.body,
    )
