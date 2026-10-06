import pytest

from saltshaker.cli import main


def test_cli_visibility(capsys):
    assert main(["visibility", "--ra", "100", "--dec", "-30", "2026-01-15"]) == 0
    assert "->" in capsys.readouterr().out


def test_cli_never_observable(capsys):
    assert main(["observable", "--ra", "10", "--dec", "60"]) == 1
    assert "never observable" in capsys.readouterr().out


def test_cli_requires_target():
    with pytest.raises(SystemExit):
        main(["observable"])


def test_cli_observable_needs_only_dec(capsys):
    assert main(["observable", "--dec", "-30"]) == 0
    assert "observable" in capsys.readouterr().out
