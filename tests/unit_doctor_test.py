"""T12: doctor.py unit tests — E1(scan missing) + E5(.honne/ not writable)."""
import os
import sys
import stat
import tempfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from honne_py.doctor import main


# ── E5: .honne/ not writable → exit 73 ────────────────────────────────────────

def test_doctor_returns_0_normally(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main() == 0
    assert (tmp_path / ".honne").is_dir()


def test_doctor_creates_honne_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / ".honne").exists()
    main()
    assert (tmp_path / ".honne").exists()


def test_doctor_honne_dir_not_writable_returns_73(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    honne_dir = tmp_path / ".honne"
    honne_dir.mkdir()
    honne_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)  # read+exec only
    try:
        result = main()
        assert result == 73
    finally:
        honne_dir.chmod(stat.S_IRWXU)  # restore for cleanup


def test_doctor_oserror_on_mkdir_returns_73(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with mock.patch("honne_py.doctor.Path.mkdir", side_effect=OSError("no perm")):
        assert main() == 73


# ── python3 not found → exit 71 ────────────────────────────────────────────────

def test_doctor_no_python3_returns_71(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with mock.patch("shutil.which", return_value=None):
        assert main() == 71


# ── honne_py not importable → exit 71 ─────────────────────────────────────────

def test_doctor_module_not_importable_returns_71(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with mock.patch("builtins.__import__", side_effect=ImportError("no module")):
        assert main() == 71


# ── E1: scan.json missing (doctor doesn't test this; axis run does) ────────────
# E1 is tested via axis run exit 66 in unit_axis_contract_test.py
