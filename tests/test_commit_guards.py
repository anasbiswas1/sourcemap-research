"""Checks the refusal rules of tools/commit_cell.py without touching git."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_commit_cell():
    spec = importlib.util.spec_from_file_location("commit_cell", ROOT / "tools" / "commit_cell.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_secret_patterns_fire_on_token_shapes():
    cc = load_commit_cell()
    samples = ["hf_" + "a" * 24, "ghp_" + "b" * 36, "github_pat_" + "c" * 44, "sk-" + "d" * 40,
               "AKIA" + "E" * 16, "AIza" + "f" * 35]
    for s in samples:
        assert any(p.search(s) for p in cc.SECRET_PATTERNS), s


def test_secret_patterns_quiet_on_ordinary_text():
    cc = load_commit_cell()
    for s in ["sourcemap-research", "sha256", "ghp_short", "sk-abc", "AKIA1234"]:
        assert not any(p.search(s) for p in cc.SECRET_PATTERNS), s


def test_forbidden_prefixes_cover_data():
    cc = load_commit_cell()
    assert any("data/surveys/x.pdf".startswith(p) for p in cc.FORBIDDEN_PREFIXES)
    assert not any("reports/records/x.yaml".startswith(p) for p in cc.FORBIDDEN_PREFIXES)
    assert ".git-credentials" in cc.FORBIDDEN_NAMES
