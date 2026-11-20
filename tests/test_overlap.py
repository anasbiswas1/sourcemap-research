
"""The gate G1 decision rule and the anchor verification."""
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


def test_supported_lists_partial_overlaps():
    outcome, reasons = overlap.decide([confirmed("x", a="partial"), confirmed("y", c="partial")])
    assert outcome == "SUPPORTED"
    assert any("x (a_source_axis)" in r and "y (c_equal_layout_rule)" in r for r in reasons)


def test_confirmed_form_needs_pages_for_partial_answers():
    form = confirmed("x", a="partial")
    form["pages"]["a"] = ""
    assert any("pages.a" in p for p in overlap.validate(form))


def test_norm_text_ignores_spacing_hyphenation_and_ligatures():
    assert overlap.norm_text("Defense-to-threat   cover-\nage map") == "defensetothreatcoverage map".replace(" ", "")
    assert overlap.norm_text("\ufb01delity") == "fidelity"
    assert overlap.norm_text("t h er e s e a r c h") == overlap.norm_text("the research")


def test_verify_form_corrects_page_and_confirms(tmp_path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    pages = [overlap.norm_text(t) for t in ["intro", "we define fidelity as 1 - ignored rate", "structural separation"]]
    form = confirmed("x", a="partial", b="partial")
    form["anchors"] = {"a": "structural separation", "b": "Fidelity as 1 - Ignored Rate", "c": ""}
    form["pages"] = {"a": "2", "b": "2", "c": ""}
    out = overlap.verify_form(form, pdf, page_texts=pages)
    assert out["confirmed_from_pdf"] is True
    assert out["pages"] == {"a": "3", "b": "2", "c": ""}
    assert out["pdf_sha256"] and out["pdf_pages"] == 3
    assert "a: p.2 -> p.3" in out["verification"] and "b: p.2 ok" in out["verification"]


def test_verify_form_accepts_a_phrase_that_runs_over_a_page_break(tmp_path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    pages = [overlap.norm_text(t) for t in ["intro", "constrains prompts via provenance", "marking, delimiting, paraphrasing"]]
    form = confirmed("x", a="partial")
    form["anchors"] = {"a": "provenance marking, delimiting", "b": "", "c": ""}
    form["pages"] = {"a": "", "b": "", "c": ""}
    out = overlap.verify_form(form, pdf, page_texts=pages)
    assert out["confirmed_from_pdf"] is True and out["pages"]["a"] == "2"
    assert "runs over the page break" in out["verification"]


def test_verify_form_leaves_unconfirmed_when_anchor_missing_or_pdf_missing(tmp_path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    form = confirmed("x")
    form["anchors"] = {"a": "phrase that is not there", "b": "", "c": ""}
    out = overlap.verify_form(form, pdf, page_texts=["nothing"])
    assert out["confirmed_from_pdf"] is False and "a: anchor not found" in out["verification"]
    gone = overlap.verify_form(confirmed("y"), tmp_path / "missing.pdf")
    assert gone["confirmed_from_pdf"] is False and gone["verification"] == "PDF missing"
