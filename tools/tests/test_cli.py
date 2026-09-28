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
