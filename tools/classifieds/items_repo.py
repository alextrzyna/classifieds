"""Create the private items/ directory, optionally as its own git repo."""
from __future__ import annotations

import subprocess
from pathlib import Path

GITIGNORE = """# Raw photos carry GPS and camera metadata; only photos/web/ is committed.
*/photos/raw/*
!*/photos/raw/.gitkeep
.DS_Store
"""

README = """# items

Private item data for the classifieds toolkit: one folder per item with
the item sheet, photos, pricing research, listings, and log. This
directory is ignored by the toolkit repo one level up, so the toolkit
can be shared without this data. If it is a git repository of its own,
commit here with `git -C items ...`.

The floor price and the Private notes section of each item.md never
leave this directory except into log.md and research files here.
"""


def init_items(root: Path, use_git: bool = True) -> list[str]:
    """Create root/items with a .gitignore and README; return what happened."""
    if not (root / "marketplaces").is_dir():
        raise ValueError(f"{root} has no marketplaces/ directory; run this from the toolkit repo root")
    items = root / "items"
    actions: list[str] = []

    if items.is_dir():
        actions.append("items/ already exists")
    else:
        items.mkdir()
        actions.append("created items/")

    for name, text in ((".gitignore", GITIGNORE), ("README.md", README)):
        path = items / name
        if path.exists():
            actions.append(f"kept existing items/{name}")
        else:
            path.write_text(text, encoding="utf-8")
            actions.append(f"wrote items/{name}")

    if use_git:
        if (items / ".git").exists():
            actions.append("items/ is already a git repo")
        else:
            subprocess.run(["git", "init", "-q"], cwd=items, check=True, capture_output=True)
            subprocess.run(["git", "add", "-A"], cwd=items, check=True, capture_output=True)
            result = subprocess.run(
                ["git", "commit", "-q", "-m", "Initialize private items repo"],
                cwd=items, capture_output=True, text=True,
            )
            if result.returncode == 0:
                actions.append("initialized git repo in items/ with one commit")
            else:
                actions.append("initialized git repo in items/; initial commit failed: " + result.stderr.strip())
    return actions
