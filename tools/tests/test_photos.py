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


SMALL = "---\nmax_long_edge: 1000\nquality: 80\n---\n"


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
    d = _with_manifest(repo, SMALL + "| raw | web | caption |\n|---|---|---|\n| IMG_1.jpg | 01-hero.jpg | A |\n")
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
    d = _with_manifest(repo, SMALL + "| raw | web | caption |\n|---|---|---|\n| IMG_1.HEIC | 01-hero.jpg | A |\n")
    _raw(d, "IMG_1.HEIC", size=(1200, 900), fmt="HEIF")
    process_photos(d, load_manifest(d))
    with Image.open(d / "photos" / "web" / "01-hero.jpg") as out:
        assert out.size == (1000, 750)
