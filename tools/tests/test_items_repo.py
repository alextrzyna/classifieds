import subprocess
from pathlib import Path

import pytest

from classifieds.cli import main
from classifieds.items_repo import init_items


def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def test_init_items_creates_dir_gitignore_and_readme(tmp_path: Path):
    (tmp_path / "marketplaces").mkdir()
    (tmp_path / "items").rmdir() if (tmp_path / "items").exists() else None
    actions = init_items(tmp_path, use_git=False)
    items = tmp_path / "items"
    assert items.is_dir()
    assert "*/photos/raw/*" in (items / ".gitignore").read_text()
    assert "!*/photos/raw/.gitkeep" in (items / ".gitignore").read_text()
    assert "private" in (items / "README.md").read_text().lower()
    assert not (items / ".git").exists()
    assert any("created items/" in a for a in actions)


def test_init_items_with_git_makes_a_repo_with_one_commit(tmp_path: Path):
    if not _git_available():
        pytest.skip("git not available")
    (tmp_path / "marketplaces").mkdir()
    init_items(tmp_path, use_git=True)
    items = tmp_path / "items"
    assert (items / ".git").is_dir()
    log = subprocess.run(["git", "log", "--oneline"], cwd=items, capture_output=True, text=True).stdout
    assert len(log.strip().splitlines()) == 1
    rc = subprocess.run(["git", "check-ignore", "-q", "x/photos/raw/a.jpg"], cwd=items).returncode
    assert rc == 0


def test_init_items_is_idempotent(tmp_path: Path):
    (tmp_path / "marketplaces").mkdir()
    init_items(tmp_path, use_git=False)
    (tmp_path / "items" / "README.md").write_text("custom\n")
    actions = init_items(tmp_path, use_git=False)
    assert (tmp_path / "items" / "README.md").read_text() == "custom\n"
    assert all("already" in a or "kept" in a for a in actions)


def test_init_items_refuses_outside_repo(tmp_path: Path):
    with pytest.raises(ValueError, match="marketplaces"):
        init_items(tmp_path, use_git=False)


def test_cli_init_items(repo: Path, capsys):
    assert main(["init-items", str(repo), "--no-git"]) == 0
    out = capsys.readouterr().out
    assert "items/.gitignore" in out
    assert (repo / "items" / ".gitignore").exists()
