"""Tests for src/tables.py: the trace, the Word output and the claim-to-result check on a small manuscript."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
T = importlib.import_module("tables")


def _table():
    t = T.Table("t_test", "A test table", ["Row", "Count", "Share"], "note")
    t.add(["first", 3, "3 (50 in 100)"], ["r_a:d1", "r_b:d2"], "count")
    t.add(["second", 0, ""], [], "count")
    return t


def test_trace_lists_every_numeric_cell_with_its_ids():
    rows = T.trace_rows([_table()])
    assert [(r["row_label"], r["column"], r["value"]) for r in rows] == [("first", "Count", "3"), ("first", "Share", "3 (50 in 100)"), ("second", "Count", "0")]
    assert rows[0]["record_ids"] == "r_a:d1;r_b:d2"


def test_docx_round_trip_and_manuscript_check(tmp_path):
    from docx import Document
    t = _table()
    T.write_docx(t, tmp_path / "t.docx")
    doc = Document(str(tmp_path / "t.docx"))
    assert doc.tables[0].rows[0].cells[-1].text == "Record ids" and doc.tables[0].rows[1].cells[1].text == "3"
    ms = Document()
    ms.add_paragraph("The undefended model executed 49.1 of 100 injections; 3 methods did so; 77 is a stray number.")
    tab = ms.add_table(rows=1, cols=2)
    tab.rows[0].cells[0].text = "5.7 [secfid:r_aside_e]"
    tab.rows[0].cells[1].text = "6.0 [secfid:r_aside_e]"
    ms.save(str(tmp_path / "m.docx"))
    results = [{"result_uid": "secfid:r_base_e", "value": "49.1", "metric_as_printed": "Exec.", "unit": "percent", "page": "6"},
               {"result_uid": "secfid:r_aside_e", "value": "5.7", "metric_as_printed": "Exec.", "unit": "percent", "page": "6"}]
    out = {(r["number"], r["where"][:5]): r["status"] for r in T.check_manuscript(tmp_path / "m.docx", results, T.trace_rows([t]))}
    assert out[("49.1", "parag")] == "matches a printed value, no id tag"
    assert out[("3", "parag")] == "matches derived count" and out[("77", "parag")] == "stray numeral"
    assert out[("5.7", "table")] == "matches result id" and out[("6.0", "table")] == "ID TAG DOES NOT MATCH"
