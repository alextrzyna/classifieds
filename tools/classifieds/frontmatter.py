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
