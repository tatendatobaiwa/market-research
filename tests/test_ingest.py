import sys
from datetime import date
import pytest
from market import data, ingest, store


def run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["market.ingest", *args])
    ingest.main()


def test_cli_saves_validated_snapshot(monkeypatch, tmp_path, capsys):
    calls = []
    monkeypatch.setattr(ingest, "fetch", lambda s, e: calls.append((s, e)) or data.demo())
    path = tmp_path / "cli.sqlite"
    run(monkeypatch, "--start", "2024-01-02", "--end", "2024-06-28", "--db", str(path))
    assert calls == [(date(2024, 1, 2), date(2024, 6, 28))]
    [record] = store.catalog(path)
    assert record["id"] in capsys.readouterr().out
    assert (record["start"], record["end"]) == ("2024-01-02", "2024-06-28")


def test_cli_reports_failure_without_saving(monkeypatch, tmp_path, capsys):
    def fail(start, end):
        raise ValueError("Missing, duplicate or unexpected symbol/session. Snapshot rejected.")
    monkeypatch.setattr(ingest, "fetch", fail)
    path = tmp_path / "cli.sqlite"
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, "--start", "2024-01-02", "--end", "2024-06-28", "--db", str(path))
    assert exit_info.value.code == 1
    assert "Import failed: Missing" in capsys.readouterr().err
    assert not path.exists()


def test_env_file_supplies_missing_credentials_only(monkeypatch, tmp_path):
    monkeypatch.setenv("APCA_API_KEY_ID", "")
    monkeypatch.delenv("APCA_API_KEY_ID")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "from-shell")
    env = tmp_path / ".env"
    env.write_text('﻿# comment\nAPCA_API_KEY_ID = "file-id"\nAPCA_API_SECRET_KEY=file-secret\nOTHER=x\n',
                   encoding="utf-8")
    ingest.load_env(env)
    assert ingest.os.environ["APCA_API_KEY_ID"] == "file-id"
    assert ingest.os.environ["APCA_API_SECRET_KEY"] == "from-shell"
    assert "OTHER" not in ingest.os.environ
    ingest.load_env(tmp_path / "missing.env")


def test_env_file_is_ignored_by_git():
    import shutil
    import subprocess
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not on PATH")
    result = subprocess.run([git, "check-ignore", "-q", ".env"], capture_output=True,
                            cwd=ingest.ENV_FILE.parent)
    if result.returncode == 128:
        pytest.skip("not a git checkout")
    assert result.returncode == 0


def test_cli_rejects_malformed_date(monkeypatch):
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, "--start", "2024/01/02", "--end", "2024-06-28")
    assert exit_info.value.code == 2
