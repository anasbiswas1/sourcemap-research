"""Tests for src/figures.py: the checks that guard every figure, and the card."""
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
F = importlib.import_module("figures")


def test_overlap_and_code_checks_see_what_they_should():
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.text(0.5, 0.5, "chat roles", transform=ax.transAxes)
    assert F.text_overlaps(fig) == 0 and F.code_leaks(fig) == []
    ax.text(0.5, 0.5, "delimiters_markers", transform=ax.transAxes)
    assert F.text_overlaps(fig) == 1 and F.code_leaks(fig) == ["delimiters_markers"]
    plt.close(fig)


def test_save_writes_png_at_600_dpi_and_pdf(tmp_path):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("Resists the injection (R1)")
    r = F.save(fig, tmp_path, "t")
    assert (tmp_path / "t.png").exists() and (tmp_path / "t.pdf").stat().st_size > 0
    c = F.check_png(tmp_path / "t.png")
    assert c["dpi"] == 600 and abs(c["width_in_at_dpi"] - 3) < 0.6 and r["text_overlaps"] == 0


def test_card_template_and_cell_positions():
    t = F.card_template()["injection_defence_card"]
    assert [s["section"] for s in t["sections"]][:2] == ["Defence", "Position on the map"]
    assert all(v == "" for s in t["sections"] for v in s["fields"].values())
    pos = F._cell_positions(5)
    assert len(pos) == 5 and all(0 < x < 1 and 0 < y < 1 for x, y in pos)
