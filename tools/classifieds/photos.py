"""Turn raw phone photos into ordered, resized, metadata-free web JPEGs."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:  # pragma: no cover - HEIC support is optional at import time
    pass

from .frontmatter import load

WEB_NAME_RE = re.compile(r"^\d{2}-[a-z0-9]+(-[a-z0-9]+)*\.jpg$")
DEFAULT_MAX_LONG_EDGE = 2048
DEFAULT_QUALITY = 88


class PhotoError(ValueError):
    """The manifest or a raw photo is missing or invalid."""


@dataclass
class ManifestRow:
    raw: str
    web: str
    caption: str


@dataclass
class Manifest:
    max_long_edge: int
    quality: int
    rows: list[ManifestRow]


def parse_manifest_table(body: str) -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    header: list[str] | None = None
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        record = dict(zip(header, cells))
        rows.append(ManifestRow(
            raw=record.get("raw", ""),
            web=record.get("web", ""),
            caption=record.get("caption", ""),
        ))
    return rows


def load_manifest(item_dir: Path) -> Manifest:
    path = item_dir / "photos" / "manifest.md"
    if not path.exists():
        raise PhotoError(f"no manifest.md at {path}")
    doc = load(path)
    rows = parse_manifest_table(doc.body)
    seen: set[str] = set()
    for row in rows:
        if not row.raw:
            raise PhotoError(f"manifest row for '{row.web}' has an empty raw file name")
        if not WEB_NAME_RE.match(row.web):
            raise PhotoError(f"web name '{row.web}' must look like 01-descriptor.jpg")
        if row.web in seen:
            raise PhotoError(f"duplicate web name '{row.web}' in manifest")
        seen.add(row.web)
    settings = {}
    for key, default in (("max_long_edge", DEFAULT_MAX_LONG_EDGE), ("quality", DEFAULT_QUALITY)):
        value = doc.meta.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int):
            raise PhotoError(f"{path}: {key} must be an int, got {value!r}")
        settings[key] = value
    return Manifest(max_long_edge=settings["max_long_edge"], quality=settings["quality"], rows=rows)


def process_photos(item_dir: Path, manifest: Manifest, force: bool = False) -> list[tuple[str, str]]:
    raw_dir = item_dir / "photos" / "raw"
    web_dir = item_dir / "photos" / "web"

    missing = [row.raw for row in manifest.rows if not (raw_dir / row.raw).exists()]
    if missing:
        raise PhotoError("missing raw photos: " + ", ".join(missing))

    web_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = item_dir / "photos" / "manifest.md"
    manifest_mtime = manifest_path.stat().st_mtime if manifest_path.exists() else 0.0
    wanted = {row.web for row in manifest.rows}
    results: list[tuple[str, str]] = []
    for stale in sorted(web_dir.glob("*.jpg")):
        if stale.name not in wanted:
            stale.unlink()
            results.append((stale.name, "removed"))
    for row in manifest.rows:
        src = raw_dir / row.raw
        dst = web_dir / row.web
        newest_input = max(src.stat().st_mtime, manifest_mtime)
        if not force and dst.exists() and dst.stat().st_mtime >= newest_input:
            results.append((row.web, "skipped"))
            continue
        try:
            img = Image.open(src)
        except UnidentifiedImageError as exc:
            raise PhotoError(f"{src.name} is not a readable image") from exc
        with img:
            upright = ImageOps.exif_transpose(img)
            rgb = upright.convert("RGB")
            rgb.thumbnail((manifest.max_long_edge, manifest.max_long_edge), Image.LANCZOS)
            rgb.save(dst, "JPEG", quality=manifest.quality, optimize=True)
        results.append((row.web, "written"))
    return results
