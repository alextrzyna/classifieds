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
