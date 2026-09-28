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
