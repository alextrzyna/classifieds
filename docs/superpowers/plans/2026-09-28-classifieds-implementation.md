# Classifieds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `classifieds` repo: a Python toolkit for validating items, preparing photos, checking listings, and moving item status, plus six Claude Code skills and four marketplace profiles that take an item from draft to a filled Pinkbike sell form.

**Architecture:** All item and marketplace data is markdown with YAML frontmatter under `items/` and `marketplaces/`. A small pure-Python package in `tools/classifieds/` reads that frontmatter and does the mechanical work through a `classifieds` CLI. Skills in `.claude/skills/` do the prose and browser work and call the CLI as a gate between steps.

**Tech Stack:** Python 3.11+, uv, PyYAML, Pillow, pillow-heif, pytest, argparse. Markdown skills. Claude in Chrome for posting.

**Spec:** `docs/superpowers/specs/2026-09-28-classifieds-design.md`

## Global Constraints

- Python 3.11 or newer; project managed with `uv`; run everything as `uv run ...`.
- Runtime dependencies limited to PyYAML, Pillow, pillow-heif. Test dependency: pytest.
- The toolkit never generates prose and never touches the network.
- Item status values are exactly: `draft`, `priced`, `listed`, `sold`, `withdrawn`.
- Legal status transitions: draft->priced, priced->listed, listed->sold, listed->withdrawn, listed->priced, withdrawn->priced.
- Web photo names match `NN-descriptor.jpg` (two digits, dash, lowercase slug, `.jpg`).
- The floor price is private: it lives only in item.md, research files, and log.md, and must never appear in listing text.
- Automation never clicks Post. The owner submits every listing.
- Every commit message ends with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

Inputs the spec implies but did not spell out. Each has a test in the task that owns it.

1. A frontmatter value of `true` or `false` where an int is required (YAML booleans are Python ints). Expected: reported as a type error, not accepted. Test in Task 4.
2. A raw photo shot in portrait with an EXIF orientation tag. Expected: the web photo is upright and still has no EXIF. Test in Task 7.
3. A listing whose description contains the floor as a number with a thousands separator, like `3,400`. Expected: check-listing fails. Test in Task 6.
4. A manifest that names the same web file twice. Expected: photos command refuses to run rather than silently overwriting. Test in Task 7.
5. An item.md with a frontmatter block that is never closed. Expected: a clear error naming the file, not a traceback from YAML. Test in Task 2.

---

### Task 1: Project scaffold and CLI smoke test

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `tools/classifieds/__init__.py`
- Create: `tools/classifieds/cli.py`
- Create: `tools/tests/__init__.py`
- Create: `tools/tests/test_cli_smoke.py`

**Interfaces:**
- Produces: `classifieds.cli.main(argv: list[str] | None = None) -> int`. Later tasks add subcommands to it.

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "classifieds"
version = "0.1.0"
description = "Toolkit for selling items on online marketplaces"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "pillow>=10.0",
    "pillow-heif>=0.16",
]

[project.scripts]
classifieds = "classifieds.cli:main"

[dependency-groups]
dev = ["pytest>=8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tools/classifieds"]

[tool.pytest.ini_options]
testpaths = ["tools/tests"]
```

- [ ] **Step 2: Write .gitignore**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
items/*/photos/raw/*.HEIC
items/*/photos/raw/*.heic
```

Note: raw HEIC files are ignored because they are large and the web copies are the deliverable. Raw JPEGs are committed. The README (Task 11) explains this.

- [ ] **Step 3: Write the failing smoke test**

`tools/tests/__init__.py` is empty. `tools/tests/test_cli_smoke.py`:

```python
import pytest

from classifieds.cli import main


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "classifieds" in out


def test_no_args_prints_usage_and_fails(capsys):
    code = main([])
    assert code == 2
    assert "usage" in capsys.readouterr().err.lower()
```

- [ ] **Step 4: Run it to verify it fails**

Run: `uv sync && uv run pytest tools/tests/test_cli_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifieds'` or `ImportError: cannot import name 'main'`.

- [ ] **Step 5: Write the package init and minimal CLI**

`tools/classifieds/__init__.py`:

```python
"""Toolkit for selling items on online marketplaces."""
```

`tools/classifieds/cli.py`:

```python
"""Command line entry point. All I/O lives here; modules stay pure."""
from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classifieds",
        description="Validate items, prepare photos, check listings, and move status.",
    )
    parser.add_subparsers(dest="command", metavar="command")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tools/tests/test_cli_smoke.py -v`
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore tools uv.lock
git commit -m "feat: project scaffold with classifieds CLI stub

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Frontmatter documents

**Files:**
- Create: `tools/classifieds/frontmatter.py`
- Create: `tools/tests/test_frontmatter.py`

**Interfaces:**
- Produces:
  - `class Document` dataclass with `meta: dict` and `body: str`
  - `class FrontmatterError(ValueError)`
  - `parse(text: str) -> Document`
  - `render(doc: Document) -> str`
  - `load(path: Path) -> Document` (raises `FrontmatterError` naming the path)
  - `save(path: Path, doc: Document) -> None`

- [ ] **Step 1: Write the failing tests**

```python
from datetime import date
from pathlib import Path

import pytest

from classifieds.frontmatter import Document, FrontmatterError, load, parse, render, save


def test_parse_splits_meta_and_body():
    doc = parse("---\ntitle: Hi\nyear: 2021\n---\nBody text\n")
    assert doc.meta == {"title": "Hi", "year": 2021}
    assert doc.body == "Body text\n"


def test_parse_without_frontmatter_gives_empty_meta():
    doc = parse("Just body\n")
    assert doc.meta == {}
    assert doc.body == "Just body\n"


def test_parse_dates_become_date_objects():
    doc = parse("---\ncreated: 2026-09-28\n---\n")
    assert doc.meta["created"] == date(2026, 9, 28)


def test_parse_unterminated_frontmatter_raises():
    with pytest.raises(FrontmatterError, match="unterminated"):
        parse("---\ntitle: Hi\nBody\n")


def test_render_round_trips():
    doc = Document({"slug": "x", "year": 2021, "created": date(2026, 9, 28)}, "# Heading\n")
    text = render(doc)
    assert text.startswith("---\nslug: x\nyear: 2021\ncreated: 2026-09-28\n---\n# Heading\n")
    assert parse(text) == doc


def test_load_names_file_on_error(tmp_path: Path):
    bad = tmp_path / "item.md"
    bad.write_text("---\nslug: x\nno close\n")
    with pytest.raises(FrontmatterError, match="item.md"):
        load(bad)


def test_save_and_load(tmp_path: Path):
    p = tmp_path / "doc.md"
    save(p, Document({"a": 1}, "body\n"))
    assert load(p) == Document({"a": 1}, "body\n")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_frontmatter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifieds.frontmatter'`.

- [ ] **Step 3: Implement frontmatter.py**

```python
"""Markdown files with a YAML frontmatter block."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

FENCE = "---\n"


class FrontmatterError(ValueError):
    """The file's frontmatter block could not be read."""


@dataclass
class Document:
    meta: dict
    body: str


def parse(text: str) -> Document:
    if not text.startswith(FENCE):
        return Document({}, text)
    end = text.find("\n" + FENCE, len(FENCE) - 1)
    if end == -1:
        raise FrontmatterError("unterminated frontmatter block")
    raw_meta = text[len(FENCE):end + 1]
    try:
        meta = yaml.safe_load(raw_meta) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"invalid YAML in frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    body = text[end + 1 + len(FENCE):]
    return Document(meta, body)


def render(doc: Document) -> str:
    meta_text = yaml.safe_dump(doc.meta, sort_keys=False, allow_unicode=True)
    return FENCE + meta_text + FENCE + doc.body


def load(path: Path) -> Document:
    try:
        return parse(path.read_text(encoding="utf-8"))
    except FrontmatterError as exc:
        raise FrontmatterError(f"{path}: {exc}") from exc


def save(path: Path, doc: Document) -> None:
    path.write_text(render(doc), encoding="utf-8")
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tools/tests/test_frontmatter.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/classifieds/frontmatter.py tools/tests/test_frontmatter.py
git commit -m "feat: frontmatter document parsing and rendering

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Marketplace profiles and repo root discovery

**Files:**
- Create: `tools/classifieds/profiles.py`
- Create: `tools/tests/conftest.py`
- Create: `tools/tests/test_profiles.py`

**Interfaces:**
- Consumes: `frontmatter.load`
- Produces:
  - `class Profile` dataclass: `name: str, url: str, title_max: int, description_max: int, photo_max: int, photo_min_px: int, fee_rate: float, required_fields: list[str], field_options: dict[str, list[str]], body: str`
  - `class ProfileError(ValueError)`
  - `find_repo_root(start: Path) -> Path` walks up until a directory containing `marketplaces/` is found; raises `ProfileError` if none.
  - `load_profile(path: Path) -> Profile`
  - `profile_path(repo_root: Path, marketplace: str) -> Path` returns `repo_root / "marketplaces" / f"{marketplace}.md"`
- Test fixtures in conftest used by every later task:
  - `repo(tmp_path) -> Path`: a repo root with `marketplaces/testmarket.md`
  - `make_item(repo, **overrides) -> Path`: helper that writes `items/test-item/item.md` and `log.md`, returns the item dir

- [ ] **Step 1: Write conftest.py**

```python
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
```

- [ ] **Step 2: Write the failing profile tests**

```python
from pathlib import Path

import pytest

from classifieds.profiles import Profile, ProfileError, find_repo_root, load_profile, profile_path


def test_load_profile_reads_fields(repo: Path):
    p = load_profile(repo / "marketplaces" / "testmarket.md")
    assert p.name == "Test Market"
    assert p.title_max == 40
    assert p.photo_max == 3
    assert p.required_fields == ["title", "price", "condition"]
    assert p.field_options == {"condition": ["new", "used"]}
    assert "Posting flow" in p.body


def test_load_profile_defaults_optional_fields(repo: Path):
    p = repo / "marketplaces" / "bare.md"
    p.write_text("---\nname: Bare\nurl: https://x\ntitle_max: 10\ndescription_max: 10\n"
                 "photo_max: 1\nphoto_min_px: 10\nrequired_fields: [title]\n---\n")
    prof = load_profile(p)
    assert prof.fee_rate == 0.0
    assert prof.field_options == {}


def test_load_profile_reports_missing_keys(repo: Path):
    p = repo / "marketplaces" / "broken.md"
    p.write_text("---\nname: Broken\n---\n")
    with pytest.raises(ProfileError, match="title_max"):
        load_profile(p)


def test_find_repo_root_walks_up(repo: Path):
    deep = repo / "items" / "x" / "photos" / "web"
    deep.mkdir(parents=True)
    assert find_repo_root(deep) == repo


def test_find_repo_root_fails_outside_repo(tmp_path: Path):
    with pytest.raises(ProfileError, match="marketplaces"):
        find_repo_root(tmp_path)


def test_profile_path(repo: Path):
    assert profile_path(repo, "pinkbike") == repo / "marketplaces" / "pinkbike.md"
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tools/tests/test_profiles.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifieds.profiles'`.

- [ ] **Step 4: Implement profiles.py**

```python
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
```

- [ ] **Step 5: Run to verify pass**

Run: `uv run pytest tools/tests/test_profiles.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add tools/classifieds/profiles.py tools/tests/conftest.py tools/tests/test_profiles.py
git commit -m "feat: marketplace profile loading and repo root discovery

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Item loading and validation

**Files:**
- Create: `tools/classifieds/items.py`
- Create: `tools/tests/test_items.py`

**Interfaces:**
- Consumes: `frontmatter.load`, conftest `make_item`, `add_research`, `add_listing`
- Produces:
  - `STATUSES: tuple[str, ...]`
  - `class ItemError(ValueError)`
  - `class Item` dataclass: `dir: Path, meta: dict, body: str`; properties `slug`, `status`, `ask: int | None`, `floor: int | None`, `marketplaces: list[str]`
  - `load_item(item_dir: Path) -> Item` (raises `ItemError` if item.md missing)
  - `validate_item(item: Item) -> list[str]` returns problem strings; empty list means valid
  - `latest_research(item_dir: Path) -> Path | None` newest `research/*-pricing.md` by name

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

import pytest

from classifieds.frontmatter import Document, save
from classifieds.items import ItemError, latest_research, load_item, validate_item
from .conftest import add_listing, add_research, make_item


def test_load_item_reads_meta_and_body(repo: Path):
    d = make_item(repo)
    item = load_item(d)
    assert item.slug == "test-item"
    assert item.status == "draft"
    assert "Private notes" in item.body


def test_load_item_missing_file(repo: Path):
    with pytest.raises(ItemError, match="item.md"):
        load_item(repo / "items" / "nope")


def test_valid_draft_has_no_problems(repo: Path):
    assert validate_item(load_item(make_item(repo))) == []


def test_missing_required_key(repo: Path):
    d = make_item(repo, brand=None)
    problems = validate_item(load_item(d))
    assert any("brand" in p for p in problems)


def test_wrong_type_reports_key(repo: Path):
    d = make_item(repo, year="twenty twenty one")
    problems = validate_item(load_item(d))
    assert any("year" in p and "int" in p for p in problems)


def test_boolean_is_not_an_int(repo: Path):
    d = make_item(repo, year=True)
    problems = validate_item(load_item(d))
    assert any("year" in p for p in problems)


def test_slug_must_match_folder(repo: Path):
    d = make_item(repo)
    doc = Document(dict(load_item(d).meta, slug="other"), load_item(d).body)
    save(d / "item.md", doc)
    assert any("slug" in p for p in validate_item(load_item(d)))


def test_unknown_status(repo: Path):
    d = make_item(repo, status="pending")
    assert any("status" in p for p in validate_item(load_item(d)))


def test_floor_above_ask(repo: Path):
    d = make_item(repo, ask=100, floor=200)
    assert any("floor" in p for p in validate_item(load_item(d)))


def test_priced_requires_ask_floor_and_research(repo: Path):
    d = make_item(repo, status="priced")
    problems = validate_item(load_item(d))
    assert any("ask" in p for p in problems)
    assert any("floor" in p for p in problems)
    assert any("research" in p for p in problems)


def test_priced_with_everything_is_valid(repo: Path):
    d = make_item(repo, status="priced", ask=3000, floor=2500)
    add_research(d)
    assert validate_item(load_item(d)) == []


def test_listed_requires_marketplaces_and_listing_files(repo: Path):
    d = make_item(repo, status="listed", ask=3000, floor=2500)
    add_research(d)
    problems = validate_item(load_item(d))
    assert any("marketplaces" in p for p in problems)
    d2 = make_item(repo, slug="two", status="listed", ask=3000, floor=2500, marketplaces=["testmarket"])
    add_research(d2)
    assert any("listings/testmarket.md" in p for p in validate_item(load_item(d2)))
    add_listing(d2)
    assert validate_item(load_item(d2)) == []


def test_missing_log(repo: Path):
    d = make_item(repo)
    (d / "log.md").unlink()
    assert any("log.md" in p for p in validate_item(load_item(d)))


def test_latest_research_picks_newest_by_name(repo: Path):
    d = make_item(repo)
    assert latest_research(d) is None
    add_research(d)
    (d / "research" / "2026-10-01-pricing.md").write_text("---\n---\n")
    assert latest_research(d).name == "2026-10-01-pricing.md"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_items.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifieds.items'`.

- [ ] **Step 3: Implement items.py**

```python
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
    files = sorted((item_dir / "research").glob("*-pricing.md")) if (item_dir / "research").is_dir() else []
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
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tools/tests/test_items.py -v`
Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/classifieds/items.py tools/tests/test_items.py
git commit -m "feat: item loading and validation

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Status transitions and log entries

**Files:**
- Create: `tools/classifieds/status.py`
- Create: `tools/tests/test_status.py`

**Interfaces:**
- Consumes: `items.load_item`, `items.validate_item`, `frontmatter.save`, `frontmatter.Document`
- Produces:
  - `TRANSITIONS: dict[str, set[str]]`
  - `class StatusError(ValueError)`
  - `can_transition(old: str, new: str) -> bool`
  - `append_log(item_dir: Path, day: date, event: str, detail: str) -> None` appends `f"{day}  {event}  {detail}\n"`
  - `apply_status(item_dir: Path, new_status: str, price: int | None = None, floor: int | None = None, note: str | None = None, today: date | None = None) -> Item` validates the would-be item before writing; raises `StatusError` with the problem list if invalid

- [ ] **Step 1: Write the failing tests**

```python
from datetime import date
from pathlib import Path

import pytest

from classifieds.items import load_item
from classifieds.status import StatusError, append_log, apply_status, can_transition
from .conftest import add_listing, add_research, make_item

TODAY = date(2026, 9, 29)


@pytest.mark.parametrize("old,new,ok", [
    ("draft", "priced", True),
    ("priced", "listed", True),
    ("listed", "sold", True),
    ("listed", "withdrawn", True),
    ("listed", "priced", True),
    ("withdrawn", "priced", True),
    ("draft", "listed", False),
    ("sold", "listed", False),
    ("priced", "sold", False),
])
def test_transitions(old, new, ok):
    assert can_transition(old, new) is ok


def test_append_log_writes_dated_line(repo: Path):
    d = make_item(repo)
    append_log(d, TODAY, "note", "hello")
    assert (d / "log.md").read_text().endswith("2026-09-29  note  hello\n")


def test_apply_status_draft_to_priced(repo: Path):
    d = make_item(repo)
    add_research(d)
    item = apply_status(d, "priced", price=3000, floor=2500, today=TODAY)
    assert item.status == "priced"
    assert item.ask == 3000 and item.floor == 2500
    reloaded = load_item(d)
    assert reloaded.meta["updated"] == TODAY
    assert reloaded.meta["ask"] == 3000
    log = (d / "log.md").read_text()
    assert "2026-09-29  priced  ask 3000 floor 2500" in log


def test_apply_status_note_goes_in_log(repo: Path):
    d = make_item(repo, status="priced", ask=3000, floor=2500, marketplaces=["testmarket"])
    add_research(d)
    add_listing(d)
    apply_status(d, "listed", note="https://example.com/listing/1", today=TODAY)
    assert "listed  https://example.com/listing/1" in (d / "log.md").read_text()


def test_illegal_transition_does_not_write(repo: Path):
    d = make_item(repo)
    before = (d / "item.md").read_text()
    with pytest.raises(StatusError, match="draft -> listed"):
        apply_status(d, "listed", today=TODAY)
    assert (d / "item.md").read_text() == before


def test_invalid_result_does_not_write(repo: Path):
    d = make_item(repo)
    before = (d / "item.md").read_text()
    with pytest.raises(StatusError, match="research"):
        apply_status(d, "priced", price=3000, floor=2500, today=TODAY)
    assert (d / "item.md").read_text() == before
    assert "priced" not in (d / "log.md").read_text()


def test_reprice_from_listed_keeps_marketplaces(repo: Path):
    d = make_item(repo, status="listed", ask=3000, floor=2500, marketplaces=["testmarket"])
    add_research(d)
    add_listing(d)
    item = apply_status(d, "priced", price=2800, today=TODAY)
    assert item.ask == 2800
    assert item.marketplaces == ["testmarket"]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_status.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifieds.status'`.

- [ ] **Step 3: Implement status.py**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tools/tests/test_status.py -v`
Expected: 15 passed (9 parametrized plus 6).

- [ ] **Step 5: Commit**

```bash
git add tools/classifieds/status.py tools/tests/test_status.py
git commit -m "feat: status transitions with validation gate and log

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Listing checks

**Files:**
- Create: `tools/classifieds/listings.py`
- Create: `tools/tests/test_listings.py`

**Interfaces:**
- Consumes: `items.Item`, `profiles.Profile`, `frontmatter.load`
- Produces:
  - `class Listing` dataclass: `meta: dict, body: str`
  - `class ListingError(ValueError)`
  - `load_listing(item_dir: Path, marketplace: str) -> Listing` (raises `ListingError` if missing)
  - `web_photos(item_dir: Path) -> list[Path]` sorted `photos/web/*.jpg`
  - `check_listing(item: Item, listing: Listing, profile: Profile, photos: list[Path]) -> list[str]`
  - `floor_patterns(floor: int) -> list[str]` the strings that count as a floor leak: plain, with thousands separators, and with a currency sign prefix on each

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

import pytest
from PIL import Image

from classifieds.items import load_item
from classifieds.listings import ListingError, check_listing, floor_patterns, load_listing, web_photos
from classifieds.profiles import load_profile
from .conftest import add_listing, add_research, make_item


def _photo(item_dir: Path, name: str, size=(400, 300)) -> Path:
    web = item_dir / "photos" / "web"
    web.mkdir(parents=True, exist_ok=True)
    p = web / name
    Image.new("RGB", size, "gray").save(p, "JPEG")
    return p


def _setup(repo: Path, **listing_meta):
    d = make_item(repo, status="priced", ask=3000, floor=2500)
    add_research(d)
    add_listing(d, **listing_meta)
    _photo(d, "01-hero.jpg")
    item = load_item(d)
    listing = load_listing(d, "testmarket")
    profile = load_profile(repo / "marketplaces" / "testmarket.md")
    return d, item, listing, profile


def test_good_listing_passes(repo: Path):
    d, item, listing, profile = _setup(repo)
    assert check_listing(item, listing, profile, web_photos(d)) == []


def test_load_listing_missing(repo: Path):
    d = make_item(repo)
    with pytest.raises(ListingError, match="testmarket"):
        load_listing(d, "testmarket")


def test_title_too_long(repo: Path):
    d, item, listing, profile = _setup(repo, title="x" * 41)
    assert any("title" in p and "40" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_description_too_long(repo: Path):
    d, item, listing, profile = _setup(repo)
    listing.body = "y" * 301
    assert any("description" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_empty_description(repo: Path):
    d, item, listing, profile = _setup(repo)
    listing.body = "  \n"
    assert any("description" in p and "empty" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_missing_required_field(repo: Path):
    d, item, listing, profile = _setup(repo)
    del listing.meta["condition"]
    assert any("condition" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_option_not_allowed(repo: Path):
    d, item, listing, profile = _setup(repo, condition="mint")
    assert any("condition" in p and "mint" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_price_below_floor(repo: Path):
    d, item, listing, profile = _setup(repo, price=2000)
    assert any("floor" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_price_must_be_int(repo: Path):
    d, item, listing, profile = _setup(repo, price="three grand")
    assert any("price" in p and "int" in p for p in check_listing(item, listing, profile, web_photos(d)))


@pytest.mark.parametrize("leak", ["2500", "2,500", "$2500", "$2,500"])
def test_floor_leak_in_body(repo: Path, leak: str):
    d, item, listing, profile = _setup(repo)
    listing.body = f"Would take {leak} today.\n"
    assert any("floor" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_floor_patterns():
    assert floor_patterns(2500) == ["2500", "2,500", "$2500", "$2,500"]
    assert floor_patterns(800) == ["800", "$800"]


def test_no_photos(repo: Path):
    d, item, listing, profile = _setup(repo)
    assert any("photo" in p for p in check_listing(item, listing, profile, []))


def test_too_many_photos(repo: Path):
    d, item, listing, profile = _setup(repo)
    for i in range(2, 5):
        _photo(d, f"{i:02d}-more.jpg")
    assert any("photo_max" in p or "at most 3" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_photo_too_small(repo: Path):
    d, item, listing, profile = _setup(repo)
    _photo(d, "02-tiny.jpg", size=(50, 50))
    assert any("02-tiny.jpg" in p for p in check_listing(item, listing, profile, web_photos(d)))


def test_web_photos_sorted_jpg_only(repo: Path):
    d = make_item(repo)
    _photo(d, "02-b.jpg")
    _photo(d, "01-a.jpg")
    (d / "photos" / "web" / "notes.txt").write_text("x")
    assert [p.name for p in web_photos(d)] == ["01-a.jpg", "02-b.jpg"]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_listings.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifieds.listings'`.

- [ ] **Step 3: Implement listings.py**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tools/tests/test_listings.py -v`
Expected: 18 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/classifieds/listings.py tools/tests/test_listings.py
git commit -m "feat: listing checks against marketplace profile and floor

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Photo pipeline

**Files:**
- Create: `tools/classifieds/photos.py`
- Create: `tools/tests/test_photos.py`

**Interfaces:**
- Consumes: `frontmatter.load`
- Produces:
  - `WEB_NAME_RE` compiled regex `^\d{2}-[a-z0-9]+(-[a-z0-9]+)*\.jpg$`
  - `class PhotoError(ValueError)`
  - `class ManifestRow` dataclass: `raw: str, web: str, caption: str`
  - `class Manifest` dataclass: `max_long_edge: int, quality: int, rows: list[ManifestRow]`
  - `parse_manifest_table(body: str) -> list[ManifestRow]` reads the first markdown table with columns raw, web, caption
  - `load_manifest(item_dir: Path) -> Manifest` (defaults 2048 and 88; raises `PhotoError` on missing file, bad web names, duplicate web names)
  - `process_photos(item_dir: Path, manifest: Manifest, force: bool = False) -> list[tuple[str, str]]` returns `(web name, "written" | "skipped")`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

import pytest
from PIL import Image

from classifieds.photos import Manifest, ManifestRow, PhotoError, load_manifest, parse_manifest_table, process_photos
from .conftest import make_item

MANIFEST = """---
max_long_edge: 1000
quality: 80
---
# Photos

| raw | web | caption |
|---|---|---|
| IMG_1.jpg | 01-hero.jpg | Drive side |
| IMG_2.jpg | 02-detail.jpg | Rear shock |
"""


def _raw(item_dir: Path, name: str, size=(4000, 3000), exif=None, fmt="JPEG") -> Path:
    raw = item_dir / "photos" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    p = raw / name
    img = Image.new("RGB", size, "blue")
    if exif is not None:
        img.save(p, fmt, exif=exif)
    else:
        img.save(p, fmt)
    return p


def _with_manifest(repo: Path, text: str = MANIFEST) -> Path:
    d = make_item(repo)
    (d / "photos").mkdir(exist_ok=True)
    (d / "photos" / "manifest.md").write_text(text)
    return d


def test_parse_manifest_table():
    rows = parse_manifest_table("| raw | web | caption |\n|---|---|---|\n| a.jpg | 01-a.jpg | A |\n")
    assert rows == [ManifestRow(raw="a.jpg", web="01-a.jpg", caption="A")]


def test_load_manifest_reads_settings_and_rows(repo: Path):
    d = _with_manifest(repo)
    m = load_manifest(d)
    assert m.max_long_edge == 1000 and m.quality == 80
    assert [r.web for r in m.rows] == ["01-hero.jpg", "02-detail.jpg"]


def test_load_manifest_defaults(repo: Path):
    d = _with_manifest(repo, "| raw | web | caption |\n|---|---|---|\n| a.jpg | 01-a.jpg | A |\n")
    m = load_manifest(d)
    assert m.max_long_edge == 2048 and m.quality == 88


def test_load_manifest_missing(repo: Path):
    d = make_item(repo)
    with pytest.raises(PhotoError, match="manifest.md"):
        load_manifest(d)


def test_load_manifest_rejects_bad_web_name(repo: Path):
    d = _with_manifest(repo, "| raw | web | caption |\n|---|---|---|\n| a.jpg | Hero.JPG | A |\n")
    with pytest.raises(PhotoError, match="Hero.JPG"):
        load_manifest(d)


def test_load_manifest_rejects_duplicate_web_name(repo: Path):
    d = _with_manifest(repo, "| raw | web | caption |\n|---|---|---|\n| a.jpg | 01-a.jpg | A |\n| b.jpg | 01-a.jpg | B |\n")
    with pytest.raises(PhotoError, match="duplicate"):
        load_manifest(d)


def test_process_resizes_and_strips_exif(repo: Path):
    d = _with_manifest(repo)
    exif = Image.Exif()
    exif[0x010F] = "TestCam"
    _raw(d, "IMG_1.jpg", exif=exif.tobytes())
    _raw(d, "IMG_2.jpg", size=(500, 500))
    result = process_photos(d, load_manifest(d))
    assert result == [("01-hero.jpg", "written"), ("02-detail.jpg", "written")]
    with Image.open(d / "photos" / "web" / "01-hero.jpg") as out:
        assert out.size == (1000, 750)
        assert out.format == "JPEG"
        assert dict(out.getexif()) == {}
    with Image.open(d / "photos" / "web" / "02-detail.jpg") as out:
        assert out.size == (500, 500)


def test_process_applies_orientation_then_strips(repo: Path):
    d = _with_manifest(repo, "| raw | web | caption |\n|---|---|---|\n| IMG_1.jpg | 01-hero.jpg | A |\n")
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees clockwise
    _raw(d, "IMG_1.jpg", size=(4000, 3000), exif=exif.tobytes())
    process_photos(d, load_manifest(d))
    with Image.open(d / "photos" / "web" / "01-hero.jpg") as out:
        assert out.size == (750, 1000)
        assert dict(out.getexif()) == {}


def test_process_skips_up_to_date_and_force_rewrites(repo: Path):
    d = _with_manifest(repo, "| raw | web | caption |\n|---|---|---|\n| IMG_1.jpg | 01-hero.jpg | A |\n")
    _raw(d, "IMG_1.jpg")
    m = load_manifest(d)
    assert process_photos(d, m) == [("01-hero.jpg", "written")]
    assert process_photos(d, m) == [("01-hero.jpg", "skipped")]
    assert process_photos(d, m, force=True) == [("01-hero.jpg", "written")]


def test_process_missing_raw_fails_before_writing(repo: Path):
    d = _with_manifest(repo)
    _raw(d, "IMG_1.jpg")
    with pytest.raises(PhotoError, match="IMG_2.jpg"):
        process_photos(d, load_manifest(d))
    assert not (d / "photos" / "web" / "01-hero.jpg").exists()


def test_process_reads_heic(repo: Path):
    pytest.importorskip("pillow_heif")
    d = _with_manifest(repo, "| raw | web | caption |\n|---|---|---|\n| IMG_1.HEIC | 01-hero.jpg | A |\n")
    _raw(d, "IMG_1.HEIC", size=(1200, 900), fmt="HEIF")
    process_photos(d, load_manifest(d))
    with Image.open(d / "photos" / "web" / "01-hero.jpg") as out:
        assert out.size == (1000, 750)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_photos.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifieds.photos'`.

- [ ] **Step 3: Implement photos.py**

```python
"""Turn raw phone photos into ordered, resized, metadata-free web JPEGs."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

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
        if not WEB_NAME_RE.match(row.web):
            raise PhotoError(f"web name '{row.web}' must look like 01-descriptor.jpg")
        if row.web in seen:
            raise PhotoError(f"duplicate web name '{row.web}' in manifest")
        seen.add(row.web)
    return Manifest(
        max_long_edge=int(doc.meta.get("max_long_edge", DEFAULT_MAX_LONG_EDGE)),
        quality=int(doc.meta.get("quality", DEFAULT_QUALITY)),
        rows=rows,
    )


def process_photos(item_dir: Path, manifest: Manifest, force: bool = False) -> list[tuple[str, str]]:
    raw_dir = item_dir / "photos" / "raw"
    web_dir = item_dir / "photos" / "web"

    missing = [row.raw for row in manifest.rows if not (raw_dir / row.raw).exists()]
    if missing:
        raise PhotoError("missing raw photos: " + ", ".join(missing))

    web_dir.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str]] = []
    for row in manifest.rows:
        src = raw_dir / row.raw
        dst = web_dir / row.web
        if not force and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            results.append((row.web, "skipped"))
            continue
        with Image.open(src) as img:
            upright = ImageOps.exif_transpose(img)
            rgb = upright.convert("RGB")
            rgb.thumbnail((manifest.max_long_edge, manifest.max_long_edge), Image.LANCZOS)
            rgb.save(dst, "JPEG", quality=manifest.quality, optimize=True)
        results.append((row.web, "written"))
    return results
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tools/tests/test_photos.py -v`
Expected: 11 passed. If `test_process_reads_heic` fails with a save error for HEIF, check that `pillow_heif` is installed in the venv with `uv run python -c "import pillow_heif; print(pillow_heif.__version__)"`.

- [ ] **Step 5: Commit**

```bash
git add tools/classifieds/photos.py tools/tests/test_photos.py
git commit -m "feat: photo pipeline from manifest to web JPEGs

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Wire the four CLI commands

**Files:**
- Modify: `tools/classifieds/cli.py`
- Create: `tools/tests/test_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 3 through 7.
- Produces: `classifieds validate <item>`, `classifieds photos <item> [--force]`, `classifieds check-listing <item> <marketplace>`, `classifieds status <item> <new-status> [--price N] [--floor N] [--note TEXT]`. Exit 0 on success, 1 on problems, 2 on usage errors. Problems print one per line prefixed with `- ` to stdout; the first line is a summary.

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from PIL import Image

from classifieds.cli import main
from .conftest import add_listing, add_research, make_item

MANIFEST = "| raw | web | caption |\n|---|---|---|\n| IMG_1.jpg | 01-hero.jpg | Hero |\n"


def _raw(item_dir: Path):
    (item_dir / "photos" / "raw").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (400, 300), "red").save(item_dir / "photos" / "raw" / "IMG_1.jpg", "JPEG")
    (item_dir / "photos" / "manifest.md").write_text(MANIFEST)


def test_validate_ok(repo: Path, capsys):
    d = make_item(repo)
    assert main(["validate", str(d)]) == 0
    assert "ok" in capsys.readouterr().out


def test_validate_reports_problems(repo: Path, capsys):
    d = make_item(repo, brand=None)
    assert main(["validate", str(d)]) == 1
    out = capsys.readouterr().out
    assert "- missing required field: brand" in out


def test_validate_missing_item_dir(repo: Path, capsys):
    assert main(["validate", str(repo / "items" / "nope")]) == 1
    assert "item.md" in capsys.readouterr().out


def test_photos_writes_and_reports(repo: Path, capsys):
    d = make_item(repo)
    _raw(d)
    assert main(["photos", str(d)]) == 0
    assert "01-hero.jpg written" in capsys.readouterr().out
    assert main(["photos", str(d)]) == 0
    assert "01-hero.jpg skipped" in capsys.readouterr().out
    assert main(["photos", str(d), "--force"]) == 0
    assert "01-hero.jpg written" in capsys.readouterr().out


def test_photos_missing_manifest(repo: Path, capsys):
    d = make_item(repo)
    assert main(["photos", str(d)]) == 1
    assert "manifest" in capsys.readouterr().out


def test_check_listing_ok(repo: Path, capsys):
    d = make_item(repo, status="priced", ask=3000, floor=2500)
    add_research(d)
    add_listing(d)
    _raw(d)
    main(["photos", str(d)])
    assert main(["check-listing", str(d), "testmarket"]) == 0
    assert "ok" in capsys.readouterr().out


def test_check_listing_reports(repo: Path, capsys):
    d = make_item(repo, status="priced", ask=3000, floor=2500)
    add_research(d)
    add_listing(d, price=1000)
    _raw(d)
    main(["photos", str(d)])
    assert main(["check-listing", str(d), "testmarket"]) == 1
    assert "below floor" in capsys.readouterr().out


def test_check_listing_unknown_marketplace(repo: Path, capsys):
    d = make_item(repo)
    add_listing(d, marketplace="nowhere")
    assert main(["check-listing", str(d), "nowhere"]) == 1
    assert "nowhere" in capsys.readouterr().out


def test_status_command(repo: Path, capsys):
    d = make_item(repo)
    add_research(d)
    assert main(["status", str(d), "priced", "--price", "3000", "--floor", "2500"]) == 0
    assert "priced" in capsys.readouterr().out
    assert "ask: 3000" in (d / "item.md").read_text()


def test_status_illegal(repo: Path, capsys):
    d = make_item(repo)
    assert main(["status", str(d), "sold"]) == 1
    assert "illegal transition" in capsys.readouterr().out


def test_status_rejects_unknown_value(repo: Path, capsys):
    d = make_item(repo)
    try:
        main(["status", str(d), "pending"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected argparse to reject unknown status")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_cli.py -v`
Expected: most tests FAIL with `error: argument command: invalid choice` (exit 2) since no subcommands exist yet.

- [ ] **Step 3: Replace cli.py**

```python
"""Command line entry point. All I/O lives here; modules stay pure."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .items import STATUSES, ItemError, load_item, validate_item
from .listings import ListingError, check_listing, load_listing, web_photos
from .photos import PhotoError, load_manifest, process_photos
from .profiles import ProfileError, find_repo_root, load_profile, profile_path
from .status import StatusError, apply_status


def _report(summary: str, problems: list[str]) -> int:
    if not problems:
        print(f"ok: {summary}")
        return 0
    print(f"{summary}: {len(problems)} problem(s)")
    for p in problems:
        print(f"- {p}")
    return 1


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        item = load_item(Path(args.item))
    except ItemError as exc:
        return _report("validate", [str(exc)])
    return _report(f"validate {item.slug}", validate_item(item))


def cmd_photos(args: argparse.Namespace) -> int:
    item_dir = Path(args.item)
    try:
        manifest = load_manifest(item_dir)
        results = process_photos(item_dir, manifest, force=args.force)
    except PhotoError as exc:
        return _report("photos", [str(exc)])
    for name, outcome in results:
        print(f"{name} {outcome}")
    return 0


def cmd_check_listing(args: argparse.Namespace) -> int:
    item_dir = Path(args.item)
    try:
        item = load_item(item_dir)
        root = find_repo_root(item_dir)
        profile = load_profile(profile_path(root, args.marketplace))
        listing = load_listing(item_dir, args.marketplace)
    except (ItemError, ProfileError, ListingError) as exc:
        return _report(f"check-listing {args.marketplace}", [str(exc)])
    problems = check_listing(item, listing, profile, web_photos(item_dir))
    return _report(f"check-listing {item.slug} on {profile.name}", problems)


def cmd_status(args: argparse.Namespace) -> int:
    try:
        item = apply_status(
            Path(args.item), args.new_status, price=args.price, floor=args.floor, note=args.note,
        )
    except (ItemError, StatusError) as exc:
        return _report("status", [str(exc)])
    print(f"ok: {item.slug} is now {item.status}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classifieds",
        description="Validate items, prepare photos, check listings, and move status.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    p = sub.add_parser("validate", help="check an item folder against the data model")
    p.add_argument("item", help="path to items/<slug>")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("photos", help="build photos/web from photos/raw per the manifest")
    p.add_argument("item")
    p.add_argument("--force", action="store_true", help="rewrite even if up to date")
    p.set_defaults(func=cmd_photos)

    p = sub.add_parser("check-listing", help="check listings/<marketplace>.md against its profile")
    p.add_argument("item")
    p.add_argument("marketplace", help="name of a file in marketplaces/ without .md")
    p.set_defaults(func=cmd_check_listing)

    p = sub.add_parser("status", help="move an item to a new status and log it")
    p.add_argument("item")
    p.add_argument("new_status", choices=STATUSES)
    p.add_argument("--price", type=int, help="set the asking price")
    p.add_argument("--floor", type=int, help="set the private floor")
    p.add_argument("--note", help="text to append to the log entry, e.g. the listing URL")
    p.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -v`
Expected: all tests pass, including the two smoke tests from Task 1.

- [ ] **Step 5: Try the installed script**

Run: `uv run classifieds --help`
Expected: usage text listing validate, photos, check-listing, status.

- [ ] **Step 6: Commit**

```bash
git add tools/classifieds/cli.py tools/tests/test_cli.py
git commit -m "feat: wire validate, photos, check-listing, and status commands

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Marketplace profiles

**Files:**
- Create: `marketplaces/pinkbike.md`
- Create: `marketplaces/facebook.md`
- Create: `marketplaces/craigslist.md`
- Create: `marketplaces/ebay.md`
- Create: `tools/tests/test_real_profiles.py`

**Interfaces:**
- Consumes: `profiles.load_profile`
- Produces: four profile files that load without error. The Pinkbike body carries the posting flow the `post-listing` skill follows.

Values marked `unverified` in the body were not confirmed against the live form. The first `post-listing` run confirms them and removes the marker.

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

import pytest

from classifieds.profiles import load_profile

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["pinkbike", "facebook", "craigslist", "ebay"])
def test_real_profile_loads(name: str):
    profile = load_profile(ROOT / "marketplaces" / f"{name}.md")
    assert profile.title_max > 0
    assert profile.photo_max > 0
    assert "title" in profile.required_fields
    assert "price" in profile.required_fields
    assert "## Posting flow" in profile.body
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_real_profiles.py -v`
Expected: 4 FAIL with `ProfileError: no such marketplace profile`.

- [ ] **Step 3: Write marketplaces/pinkbike.md**

```markdown
---
name: Pinkbike BuySell
url: https://www.pinkbike.com/buysell/sell/
title_max: 100
description_max: 5000
photo_max: 12
photo_min_px: 800
fee_rate: 0.0
required_fields:
  - title
  - price
  - currency
  - category
  - condition
  - frame_size
  - wheel_size
  - frame_material
  - front_travel
  - rear_travel
  - country
  - region
  - city
  - shipping
field_options:
  condition: [New, Excellent, Good, Fair, Poor]
  wheel_size: ["29", "27.5", "27.5+", "26", "Mullet", "700c", "650b"]
  frame_material: [Carbon, Aluminum, Steel, Titanium]
  shipping: [Local pickup only, Will ship, Will ship internationally]
---
# Pinkbike BuySell

Pinkbike is the main used-bike market for mountain bikers in North America.
Buyers are enthusiasts who know the parts and will ask about them. Listings
that get replies show the drive side clearly, state the frame size early,
and list the build honestly, including wear.

Limits and dropdown options above are `unverified` until the first real
posting run. On that run, compare every field against the live form and
correct this file before filling anything.

## What buyers care about

- Frame size and rider height range, stated in the title or first line.
- Full build: fork, shock, drivetrain, brakes, wheels, dropper, tires.
- Upgrades from stock, and what is still stock.
- Wear: paint chips, bearing play, suspension service dates, drivetrain life.
- Whether it has been crashed, and any warranty or frame history.
- Location and whether you will ship. Shipping a bike costs the buyer
  real money, so local sales close faster.

## Tone

Plain and specific. No marketing language. Short paragraphs. A bulleted
build list reads well on Pinkbike. Mention the reason for selling in one
sentence if it is ordinary (new bike, moved, not riding).

## Posting flow

Each step names the field in the listing frontmatter it fills.

1. Open the URL above in a new tab. Confirm the owner is logged in; if a
   login page appears, stop and ask the owner to log in.
2. Choose the listing category (`category`). For a full bike this is a
   bike category such as Enduro or Trail; the exact list is `unverified`.
3. Fill title (`title`).
4. Fill price (`price`) and currency (`currency`).
5. Fill condition (`condition`).
6. Fill the bike specifics: frame size (`frame_size`), wheel size
   (`wheel_size`), frame material (`frame_material`), front travel
   (`front_travel`), rear travel (`rear_travel`).
7. Fill location: country (`country`), region (`region`), city (`city`).
8. Fill shipping (`shipping`).
9. Paste the description body into the description box.
10. Upload photos from `photos/web/` in manifest order. The first is the
    hero image.
11. Stop. Take a screenshot, tell the owner the form is filled, and wait
    for them to review and click Post.

## Gotchas

- None recorded yet. Add anything learned during a real post here.
```

- [ ] **Step 4: Write marketplaces/facebook.md**

```markdown
---
name: Facebook Marketplace
url: https://www.facebook.com/marketplace/create/item
title_max: 99
description_max: 5000
photo_max: 10
photo_min_px: 600
fee_rate: 0.0
required_fields:
  - title
  - price
  - category
  - condition
  - location
field_options:
  condition: [New, Used - Like New, Used - Good, Used - Fair]
---
# Facebook Marketplace

Local buyers, wide range of knowledge, many low offers. Good for reach,
weak for negotiating with people who know the bike.

Limits above are `unverified` until a real posting run.

## What buyers care about

- Price and whether you will take less. Expect low offers.
- Location and pickup convenience.
- A clear hero photo. Most browsing happens in the phone app on thumbnails.

## Tone

Short. First line states what it is and the size. Keep the build list
brief; link out to nothing. Say "price is firm" or "open to reasonable
offers" explicitly.

## Posting flow

1. Open the URL above in a new tab. If a login page appears, stop and ask
   the owner to log in.
2. Upload photos from `photos/web/` in manifest order.
3. Fill title (`title`), price (`price`), category (`category`),
   condition (`condition`).
4. Paste the description body.
5. Fill location (`location`).
6. Stop and wait for the owner to review and click Publish.

## Gotchas

- None recorded yet.
```

- [ ] **Step 5: Write marketplaces/craigslist.md**

```markdown
---
name: Craigslist
url: https://post.craigslist.org/
title_max: 70
description_max: 8000
photo_max: 24
photo_min_px: 600
fee_rate: 0.0
required_fields:
  - title
  - price
  - condition
  - postal_code
  - city
field_options:
  condition: [new, like new, excellent, good, fair, salvage]
---
# Craigslist

Local, anonymous, no fees. Expect scam replies. Buyers search by keyword,
so the title should contain brand, model, year, and size.

Limits above are `unverified` until a real posting run.

## What buyers care about

- Keywords in the title.
- Cash, local, and when they can see it.

## Tone

Plain. State "cash only, local pickup" and "no shipping" if true.

## Posting flow

1. Open the URL above in a new tab and choose the owner's city.
2. Choose "for sale by owner" then the bike category.
3. Fill title (`title`), price (`price`), postal code (`postal_code`),
   city (`city`), condition (`condition`).
4. Paste the description body.
5. Upload photos from `photos/web/` in manifest order.
6. Stop and wait for the owner to review and publish. Craigslist sends an
   email confirmation the owner must click.

## Gotchas

- None recorded yet.
```

- [ ] **Step 6: Write marketplaces/ebay.md**

```markdown
---
name: eBay
url: https://www.ebay.com/sl/sell
title_max: 80
description_max: 4000
photo_max: 24
photo_min_px: 500
fee_rate: 0.1325
required_fields:
  - title
  - price
  - condition
  - category
  - shipping
field_options:
  condition: [New, Used]
  shipping: [Local pickup only, Calculated, Flat rate, Freight]
---
# eBay

National reach, buyer protection, and fees. `fee_rate` above is the
approximate final value fee for sporting goods and is `unverified`; check
the current rate before pricing. Shipping a full bike needs a bike box
and usually a bike shop's help, so price the ask to cover fees and
packing.

## What buyers care about

- Exact model, year, and size in the title.
- Item specifics filled in, since eBay search filters on them.
- Shipping cost and handling time.

## Tone

Factual. Lead with specifics. Describe flaws with photos.

## Posting flow

1. Open the URL above in a new tab. If a login page appears, stop and ask
   the owner to log in.
2. Search the item name and pick or skip the catalog match.
3. Fill title (`title`), category (`category`), condition (`condition`).
4. Upload photos from `photos/web/` in manifest order.
5. Fill item specifics from the listing frontmatter where field names
   match.
6. Paste the description body.
7. Fill price (`price`) as a fixed price, and shipping (`shipping`).
8. Stop and wait for the owner to review and list it.

## Gotchas

- None recorded yet.
```

- [ ] **Step 7: Run to verify pass**

Run: `uv run pytest tools/tests/test_real_profiles.py -v`
Expected: 4 passed.

- [ ] **Step 8: Commit**

```bash
git add marketplaces tools/tests/test_real_profiles.py
git commit -m "feat: starter marketplace profiles for Pinkbike, Facebook, Craigslist, eBay

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Item-side skills: new-item and prep-photos

**Files:**
- Create: `.claude/skills/new-item/SKILL.md`
- Create: `.claude/skills/prep-photos/SKILL.md`
- Create: `tools/tests/test_skills.py`

**Interfaces:**
- Consumes: the CLI from Task 8.
- Produces: two skills. `new-item` leaves an item at status draft. `prep-photos` expects draft or later and leaves status unchanged with `photos/web/` populated.

- [ ] **Step 1: Write the failing skill-structure test**

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_skills.py -v`
Expected: 2 FAIL with `FileNotFoundError`.

- [ ] **Step 3: Write .claude/skills/new-item/SKILL.md**

```markdown
---
name: new-item
description: Use when the owner wants to sell something new and no items/<slug>/ folder exists for it yet. Interviews the owner and creates the item sheet at status draft.
---

# New item

Creates `items/<slug>/` with `item.md`, `log.md`, an empty `photos/raw/`,
and a manifest with no rows. Ends at status `draft`.

## Slug

`<year>-<brand>-<model>` lowercased, spaces and punctuation replaced with
dashes, e.g. `2021-ibis-ripmo-v2`. Confirm the slug with the owner before
creating anything. If the folder already exists, stop and say so.

## Interview

Ask in this order, one topic per message, and accept "skip" for anything
the owner does not know. Keep answers verbatim in the item body; do not
polish them into listing prose here.

1. What is it: category, brand, model, year, size.
2. Build and specs: for a bike, fork, shock, drivetrain, brakes, wheels,
   tires, dropper, cockpit, and anything else notable.
3. Upgrades and changes from stock, and what is still stock.
4. Condition and wear: honest and specific. Chips, scratches, bearing
   play, suspension feel, drivetrain wear, tire life. Any crashes.
5. Service history with approximate dates.
6. Included extras: spare parts, tools, original boxes, receipts.
7. Reason for selling, in one sentence.
8. Location as it should appear publicly, e.g. "Seattle, WA".
9. Private notes: anything the owner wants remembered but never published,
   such as the lowest price they would truly take, or who else has asked.

## Write the files

`item.md` frontmatter, all keys required unless noted:

```yaml
---
slug: <slug>
status: draft
category: <bike | bike-part | electronics | ...>
brand: <Brand>
model: <Model>
year: <int>
size: <string, omit if not applicable>
condition: <short label, e.g. "very good, used">
location: <City, ST>
currency: USD
created: <today as YYYY-MM-DD>
---
```

Body headings, in this order, each filled from the interview:

```
# <year> <brand> <model>

## Overview
## Build and specs
## Upgrades and changes from stock
## Condition and wear
## Service history
## Included extras
## Reason for selling
## Private notes
```

`log.md` gets one line: `<today>  created  <one-line summary>`.

`photos/manifest.md`:

```markdown
---
max_long_edge: 2048
quality: 88
---
# Photos

Drop raw photos in photos/raw/, then run the prep-photos skill.

| raw | web | caption |
|---|---|---|
```

## Gate

Run `uv run classifieds validate items/<slug>` and show the output. Fix
any reported problem before finishing. Tell the owner the next step is to
put photos in `items/<slug>/photos/raw/` and run the prep-photos skill.
```

- [ ] **Step 4: Write .claude/skills/prep-photos/SKILL.md**

```markdown
---
name: prep-photos
description: Use when raw photos have been dropped into items/<slug>/photos/raw/ and the owner needs them ordered, captioned, resized, and stripped of metadata for a listing. Writes the manifest and runs the photos command.
---

# Prep photos

Turns `photos/raw/` into ordered `photos/web/` JPEGs via the manifest.
Expects status `draft` or later. Leaves status unchanged.

## Gate

Run `uv run classifieds validate items/<slug>`. Stop on any problem.
Then list `photos/raw/`. If it is empty, tell the owner where to put the
photos and stop.

## Choose the order

Read the target marketplace profile in `marketplaces/<name>.md` (ask which
one if not given; default pinkbike for bikes). Note its `photo_max` and
what its "What buyers care about" section says to show.

View every raw photo with the Read tool. For each, note what it shows and
whether it is sharp and well lit. Then propose an order:

1. Hero: the whole item, side-on, best light, clean background. For a bike
   this is the drive side.
2. The other side.
3. Detail shots of the parts buyers ask about, in the order the profile
   lists them.
4. Every flaw the item sheet's "Condition and wear" section mentions.
   Buyers trust listings that show the damage.
5. Extras included.

Drop photos that are blurry, redundant, or show nothing a buyer needs.
Stay at or under `photo_max`. Show the owner the proposed list with one
line per photo and ask for changes before writing anything.

## Write the manifest

Rewrite the table in `photos/manifest.md`. Web names are `NN-descriptor.jpg`
with two digits, a dash, and a short lowercase slug: `01-hero.jpg`,
`02-non-drive-side.jpg`, `03-fork.jpg`. Captions are one short phrase.

## Build and check

Run `uv run classifieds photos items/<slug>`. Every row should print
`written` the first time. Open two or three results with the Read tool
and confirm they are upright and cropped as expected. If a photo needs
cropping, tell the owner which one and why; do not edit raw files.

Finish by stating how many web photos exist and which is the hero.
```

- [ ] **Step 5: Run to verify pass**

Run: `uv run pytest tools/tests/test_skills.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/new-item .claude/skills/prep-photos tools/tests/test_skills.py
git commit -m "feat: new-item and prep-photos skills

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Research, listing, posting, and orchestrator skills

**Files:**
- Create: `.claude/skills/price-research/SKILL.md`
- Create: `.claude/skills/write-listing/SKILL.md`
- Create: `.claude/skills/post-listing/SKILL.md`
- Create: `.claude/skills/sell-item/SKILL.md`
- Modify: `tools/tests/test_skills.py` (extend `SKILLS`)

**Interfaces:**
- Consumes: CLI from Task 8, profiles from Task 9, skills from Task 10.
- Produces: `price-research` takes draft to priced. `write-listing` expects priced and writes `listings/<marketplace>.md`. `post-listing` expects priced with a checked listing and takes it to listed. `sell-item` chains them.

- [ ] **Step 1: Extend the skill test**

In `tools/tests/test_skills.py` change the list to:

```python
SKILLS = ["new-item", "prep-photos", "price-research", "write-listing", "post-listing", "sell-item"]
```

and add:

```python
def test_post_listing_never_submits():
    body = load(ROOT / ".claude" / "skills" / "post-listing" / "SKILL.md").body
    assert "never click" in body.lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_skills.py -v`
Expected: 4 new parametrized cases and the submit test FAIL with `FileNotFoundError`.

- [ ] **Step 3: Write .claude/skills/price-research/SKILL.md**

```markdown
---
name: price-research
description: Use when an item is at status draft and needs an asking price and floor before listing. Gathers comparable listings, writes a dated research file, and moves the item to priced.
---

# Price research

Produces `research/<today>-pricing.md` with a comps table, a recommended
ask, and a private floor. Ends by moving the item from `draft` to
`priced` (or refreshing an already priced item, which leaves status as is
and just adds a new research file).

## Gate

Run `uv run classifieds validate items/<slug>`. Stop on any problem.
Read `item.md` fully: the size, build tier, upgrades, and condition drive
the comps you look for.

## Gather comps

Aim for at least five comparable listings, more if easy. Prefer sold or
recently removed listings over active ones; active asks run high.

Sources, in order of weight for a bike:

1. Pinkbike BuySell, searched in the browser (load the Chrome tools with
   one ToolSearch call, get tab context, open a new tab). Search the exact
   model and year, then the model across adjacent years. Note listed date
   and whether the listing is marked sold.
2. Web search for the model with "sold" and "for sale" across Pinkbike,
   The Pro's Closet, eBay sold listings, and forum threads.
3. Any marketplace the owner named.

For each comp record: source, URL, title, size, build tier or key parts,
condition as stated, price, currency, listed date, sold or active, and a
note on how it differs from ours.

## Adjust and recommend

Reason about: frame size (unusual sizes sell slower), build tier
relative to ours, upgrades that buyers actually pay for versus ones they
do not, condition, region, and season (bikes sell for more in spring
than in fall). State each adjustment in a sentence.

Recommend an ask that is near the top of the realistic range if the owner
wants a fair price and time, or the middle if they want speed. Ask which.
Set the floor at the price below which the owner would rather keep it;
propose a number and let them change it. The floor never leaves the repo.

## Write the file

`research/<today>-pricing.md`:

```markdown
---
item: <slug>
date: <today>
recommended_ask: <int>
floor: <int>
currency: USD
sources:
  - <source name or URL>
---
# Pricing research: <year> <brand> <model>

## Comps

| source | url | title | size | build | condition | price | listed | status | notes |
|---|---|---|---|---|---|---|---|---|---|

## Reasoning

## Recommendation

Ask <n>. Floor <n>. What would move it: ...
```

## Gate out

After the owner agrees on ask and floor:

- If status is `draft`, `listed`, or `withdrawn`, run
  `uv run classifieds status items/<slug> priced --price <ask> --floor <floor>`
  and show the output.
- If status is already `priced` (a refresh), the status command has no
  transition to apply. Edit `ask`, `floor`, and `updated` in item.md by
  hand, then append `<today>  priced  ask <ask> floor <floor> (refresh)`
  to log.md, and run `uv run classifieds validate items/<slug>`.
```

- [ ] **Step 4: Write .claude/skills/write-listing/SKILL.md**

```markdown
---
name: write-listing
description: Use when an item is priced and needs listing text and form fields for a specific marketplace. Drafts listings/<marketplace>.md from the item sheet, research, and marketplace profile, then checks it.
---

# Write listing

Produces `listings/<marketplace>.md`. Expects status `priced` (or
`listed`, when adding a second marketplace). Leaves status unchanged.

## Gate

Run `uv run classifieds validate items/<slug>`. Stop on any problem.
Read: `item.md`, the newest `research/*-pricing.md`, and
`marketplaces/<marketplace>.md` in full. Read `photos/manifest.md` to know
what the photos show, so the text and photos agree.

## Never include

- Anything under `## Private notes` in item.md.
- The floor, in any form. `check-listing` will catch a literal match, but
  do not paraphrase it either ("would go as low as...").
- Claims the item sheet does not support.

## Frontmatter

One key per field the profile's `required_fields` lists, plus any field
its `field_options` covers, using values from those options exactly. Take
`price` from `ask` in item.md. Derive bike specifics from the item body.
Anything the item sheet does not say, ask the owner rather than guess.

## Description

Follow the profile's "Tone" and "What buyers care about" sections. Shape:

1. One line: year, brand, model, size, and who it fits.
2. One short paragraph on the bike and why it is good, in plain words.
3. Build list as bullets, upgrades marked.
4. Condition and wear, specific, matched to the photos that show it.
5. Service history.
6. Extras included.
7. Logistics: location, pickup or shipping, payment, and how to reach out.
8. Reason for selling, one sentence, if ordinary.

Stay under `description_max`. Do not use the word "mint" unless it is new.

## Check

Run `uv run classifieds check-listing items/<slug> <marketplace>`. Fix
every problem and rerun until it prints `ok`. Then show the owner the
title and description and ask for edits. Apply edits and check again.
```

- [ ] **Step 5: Write .claude/skills/post-listing/SKILL.md**

```markdown
---
name: post-listing
description: Use when a checked listing exists and the owner wants it entered into the marketplace's sell form in their logged-in Chrome. Fills fields and uploads photos, then stops for the owner to review and submit.
---

# Post listing

Fills the marketplace's sell form from `listings/<marketplace>.md` and
`photos/web/`. Expects status `priced` with a listing that passes
`check-listing`. Ends at `listed` after the owner confirms they posted.

You never click Post, Publish, List it, or any equivalent. The owner does.

## Gate

Run `uv run classifieds validate items/<slug>` and
`uv run classifieds check-listing items/<slug> <marketplace>`. Both must
print `ok`. Read `marketplaces/<marketplace>.md` in full, especially
"Posting flow" and "Gotchas".

## Browser setup

Load the Chrome tools in one ToolSearch call: tabs_context_mcp, navigate,
computer, read_page, find, form_input, file_upload, tabs_create_mcp,
tabs_close_mcp. Call tabs_context_mcp first, then create a new tab. Do not
reuse existing tabs.

## Fill the form

Follow the profile's posting flow step by step. For each step, find the
field, set it from the matching frontmatter key, and confirm the value
took by reading the page back.

If the live form differs from the profile (a field is missing, named
differently, has different options, or a limit differs):

1. Stop filling.
2. Report the exact difference to the owner.
3. Update the profile file: fix the frontmatter value or option list and
   add a line under "Gotchas". Remove the `unverified` marker for any
   value you have now confirmed.
4. If the difference changes the listing (an option value, a length), fix
   `listings/<marketplace>.md`, rerun `check-listing`, then continue.

Upload photos from `photos/web/` in name order using file_upload. Confirm
the count on the page matches.

Paste the description body verbatim.

## Hand off

Take a screenshot of the filled form. Tell the owner: the form is filled,
here is what to check, and they should click Post when satisfied. Wait.

When the owner says it is posted, ask for the listing URL, then run:

`uv run classifieds status items/<slug> listed --note <url>`

If `marketplaces` in item.md does not include this marketplace, add it
before running the status command, or the validation gate will reject
the transition. Show the command output.
```

- [ ] **Step 6: Write .claude/skills/sell-item/SKILL.md**

```markdown
---
name: sell-item
description: Use when the owner says they want to sell something, or wants to continue selling an item already in items/. Orchestrates new-item, prep-photos, price-research, write-listing, and post-listing in order, skipping steps already done.
---

# Sell item

Runs the pipeline for one item on one marketplace. Ask for the item (or
the slug) and the marketplace if not given. Default marketplace for a
bike is pinkbike.

## Decide where to start

If `items/<slug>/` does not exist: run the new-item skill first.

Otherwise run `uv run classifieds validate items/<slug>` and read the
status:

| status | photos/web empty | next skill |
|---|---|---|
| draft | yes | prep-photos, then price-research |
| draft | no | price-research |
| priced | any | write-listing if listings/<marketplace>.md is missing, else post-listing |
| listed | any | ask: re-price, add another marketplace, mark sold, or withdraw |
| sold or withdrawn | any | say so and stop unless the owner wants to relist |

Photos are needed before write-listing, so if `photos/web/` is empty at
`priced`, run prep-photos first.

## Run each skill

Invoke each skill with the Skill tool, one at a time, and let it finish
before starting the next. After each, re-run validate. Stop and report if
any gate fails.

## Finish

State the item's status, the listing URL if posted, and what the owner
should watch for next: inquiries on the marketplace, and running the
status command with `sold` or `withdrawn` when it closes.
```

- [ ] **Step 7: Run to verify pass**

Run: `uv run pytest tools/tests/test_skills.py -v`
Expected: 7 passed.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills tools/tests/test_skills.py
git commit -m "feat: price-research, write-listing, post-listing, and sell-item skills

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: README, CLAUDE.md, and the Ripmo item skeleton

**Files:**
- Create: `README.md`
- Create: `CLAUDE.md`
- Create: `items/2021-ibis-ripmo-v2/item.md`
- Create: `items/2021-ibis-ripmo-v2/log.md`
- Create: `items/2021-ibis-ripmo-v2/photos/manifest.md`
- Create: `items/2021-ibis-ripmo-v2/photos/raw/.gitkeep`
- Create: `tools/tests/test_real_items.py`

**Interfaces:**
- Consumes: CLI from Task 8.
- Produces: a valid draft item for the Ripmo with only the facts known so far. The `new-item` skill's interview fills in the rest with the owner in a later session.

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

import pytest

from classifieds.items import load_item, validate_item

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("item_dir", sorted((ROOT / "items").glob("*/")), ids=lambda p: p.name)
def test_every_real_item_validates(item_dir: Path):
    assert validate_item(load_item(item_dir)) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tools/tests/test_real_items.py -v`
Expected: no tests collected (no items yet), so pytest exits 5. That counts as the failing state.

- [ ] **Step 3: Write the Ripmo item files**

`items/2021-ibis-ripmo-v2/item.md`:

```markdown
---
slug: 2021-ibis-ripmo-v2
status: draft
category: bike
brand: Ibis
model: Ripmo V2
year: 2021
condition: used
location: TBD
currency: USD
created: 2026-09-28
---
# 2021 Ibis Ripmo V2

## Overview
Interview pending. Run the new-item skill to fill this sheet.

## Build and specs

## Upgrades and changes from stock

## Condition and wear

## Service history

## Included extras

## Reason for selling

## Private notes
```

Note: `location: TBD` is a placeholder the interview replaces. It is a
valid string so the skeleton validates; the `write-listing` skill asks
the owner for anything the sheet does not say.

`items/2021-ibis-ripmo-v2/log.md`:

```
2026-09-28  created  skeleton; interview pending
```

`items/2021-ibis-ripmo-v2/photos/manifest.md`:

```markdown
---
max_long_edge: 2048
quality: 88
---
# Photos

Drop raw photos in photos/raw/, then run the prep-photos skill.

| raw | web | caption |
|---|---|---|
```

`items/2021-ibis-ripmo-v2/photos/raw/.gitkeep`: empty file.

- [ ] **Step 4: Write README.md**

```markdown
# classifieds

Skills, a small toolkit, and per-item folders for selling things on
online marketplaces with Claude Code.

## Selling something

1. Start a Claude Code session in this repo and say what you want to
   sell. The `sell-item` skill walks the steps:
   new-item, prep-photos, price-research, write-listing, post-listing.
2. Put photos from your phone in `items/<slug>/photos/raw/`. HEIC is
   fine. Raw HEIC files are gitignored; the generated `photos/web/`
   JPEGs are what get committed and uploaded.
3. Claude fills the marketplace's sell form in your logged-in Chrome.
   You review and click Post.

## Layout

- `items/<slug>/` one folder per item: `item.md`, `photos/`, `research/`,
  `listings/`, `log.md`.
- `marketplaces/` one profile per marketplace with form limits and the
  posting flow.
- `.claude/skills/` the skills.
- `tools/` the Python toolkit and tests.

## Toolkit

```
uv sync
uv run pytest
uv run classifieds validate items/<slug>
uv run classifieds photos items/<slug> [--force]
uv run classifieds check-listing items/<slug> <marketplace>
uv run classifieds status items/<slug> <draft|priced|listed|sold|withdrawn> [--price N] [--floor N] [--note TEXT]
```

Status moves: draft -> priced -> listed -> sold or withdrawn. A listed or
withdrawn item can go back to priced for re-pricing.

## Privacy

The floor price is private. It lives in `item.md`, the research file, and
`log.md`. `check-listing` fails if it appears in listing text. The
"Private notes" section of `item.md` is never copied into a listing.
```

- [ ] **Step 5: Write CLAUDE.md**

```markdown
# CLAUDE.md

This repo sells items on online marketplaces. Read `README.md` first.

## Rules

- Run `uv run classifieds validate items/<slug>` before and after changing
  any item. Skills gate on it.
- Never put the floor or the Private notes section into a listing.
- Never click Post, Publish, or List on a marketplace. The owner submits.
- The toolkit in `tools/` never generates prose and never uses the
  network. Prose and research belong to the skills.
- Marketplace profiles are ground truth for form fields. When a live form
  differs, fix the profile and note it under Gotchas.
- Dates in frontmatter are `YYYY-MM-DD`. Prices are whole currency units.

## Testing

`uv run pytest`. Tests live in `tools/tests/`. Real items and profiles
are validated by `test_real_items.py` and `test_real_profiles.py`, so a
broken item.md fails the suite.
```

- [ ] **Step 6: Run to verify pass**

Run: `uv run pytest -v`
Expected: all tests pass, including `test_every_real_item_validates[2021-ibis-ripmo-v2]`.

- [ ] **Step 7: Run the CLI against the real item**

Run: `uv run classifieds validate items/2021-ibis-ripmo-v2`
Expected: `ok: validate 2021-ibis-ripmo-v2`

- [ ] **Step 8: Commit**

```bash
git add README.md CLAUDE.md items tools/tests/test_real_items.py
git commit -m "docs: README and CLAUDE.md; add Ripmo item skeleton

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
