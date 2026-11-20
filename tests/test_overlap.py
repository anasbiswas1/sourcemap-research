
"""The gate G1 decision rule."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import overlap  # noqa: E402


def confirmed(record_id, a="no", b="no", c="no"):
    form = overlap.blank_form(record_id, "t", "survey")
    for f in overlap.TEXT_FIELDS:
        form[f] = "x"
    form.update(a_source_axis=a, b_three_jobs_together=b, c_equal_layout_rule=c, read_basis="full PDF",
                confirmed_from_pdf=True, pdf_sha256="abc")
    form["pages"] = {"a": "3", "b": "4", "c": "5"}
    return form


def test_unresolved_when_a_form_is_unconfirmed():
    forms = [confirmed("x"), overlap.blank_form("y", "t", "survey")]
    outcome, reasons = overlap.decide(forms)
    assert outcome == "UNRESOLVED"
    assert any("not yet confirmed" in r for r in reasons)


def test_narrow_when_a_confirmed_form_answers_yes():
    outcome, reasons = overlap.decide([confirmed("x"), confirmed("y", b="yes")])
    assert outcome == "NARROW"
    assert "b_three_jobs_together" in reasons[0]


def test_supported_when_all_confirmed_and_no_yes():
    outcome, _ = overlap.decide([confirmed("x", a="partial"), confirmed("y", c="partial")])
    assert outcome == "SUPPORTED"


def test_confirmed_form_needs_pages_for_partial_answers():
    form = confirmed("x", a="partial")
    form["pages"]["a"] = ""
    assert any("pages.a" in p for p in overlap.validate(form))
