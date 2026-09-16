"""Repo herkese açık: gizli bilgiler ve büyük veriler asla git'e girmemeli."""

import shutil
import subprocess

import pytest

from flybrain.paths import ROOT

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git yok")

MUST_BE_IGNORED = [
    "secrets/",
    "secrets/herhangi-bir-dosya.txt",
    ".env",
    ".env.local",
    "browser-profile/",
    "data/raw/x.feather",
    "runs/x.json",
]


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


@pytest.mark.parametrize("path", MUST_BE_IGNORED)
def test_sensitive_paths_are_ignored(path):
    assert _git("check-ignore", "-q", "--no-index", path).returncode == 0, path


def test_no_sensitive_files_tracked():
    tracked = _git("ls-files").stdout.splitlines()
    bad = [p for p in tracked if p.startswith(("secrets/", "browser-profile/", "data/"))
           or p.split("/")[-1].startswith(".env")]
    assert not bad, bad
