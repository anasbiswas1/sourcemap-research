"""The record schema, the validator and the comparison grade."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import schema  # noqa: E402

SCHEMA = schema.load_schema(ROOT / "schema" / "record_schema.yaml")


def comp(purpose="W", **kw):
    c = {"purpose": purpose, "c1_base": "matched", "c2_layout": "matched", "c3_benchmark": "matched",
         "c4_attacker": "matched", "c5_judge": "matched", "c6_decoding": "matched"}
    c.update(kw)
    return c


def test_grade_follows_plan_equation_4():
    assert schema.grade(comp()) == "A"
    assert schema.grade(comp(c5_judge="unmatched")) == "B"
    assert schema.grade(comp(c1_base="unmatched", c3_benchmark="unmatched")) == "C"
    assert schema.grade(comp(c6_decoding="unreported")) == "U"
    assert schema.grade(comp("M", c2_layout="manipulated")) == "A"
    assert schema.grade(comp("M", c2_layout="manipulated", c4_attacker="manipulated")) == "C"


def test_whole_configuration_comparison_ignores_layout():
    assert schema.grade(comp("W", c2_layout="unmatched")) == "A"
    assert schema.grade(comp("M", c2_layout="unmatched")) == "B"


def test_matched_unstated_is_matched_within_a_report_and_unknown_across_reports():
    assert schema.grade(comp("W", c6_decoding="matched_unstated")) == "A"
    assert schema.grade(comp("X", c6_decoding="matched_unstated")) == "U"


def test_value_search_keeps_table_cells_apart():
    assert schema.value_on_page("59", "None 59 2 0")
    assert schema.value_on_page("3.10%", "reduced to 3.10 % with")
    assert schema.value_on_page("13.6", "Vanilla 13.6±0.2 17.9")
    assert not schema.value_on_page("65", "cells 6 5 here")
    assert not schema.value_on_page("1", "only 11 and 0.1")
    assert not schema.value_on_page("0.5", "10.5 and 0.55")


def test_loader_keeps_yes_and_no_as_words(tmp_path):
    f = tmp_path / "r.yaml"
    f.write_text("a: yes\nb: no\nc: true\n")
    d = schema.load_record(f)
    assert d == {"a": "yes", "b": "no", "c": True}


def test_schema_flags_are_booleans_and_enum_words_are_text():
    for kind in SCHEMA["kinds"].values():
        for spec in kind["fields"].values():
            for flag in ("required", "from_paper"):
                if flag in spec:
                    assert isinstance(spec[flag], bool)
            for v in spec.get("values", []):
                assert isinstance(v, str)


def minimal_record():
    return {
        "report": {"id": "r", "slug": "2401.00001", "title": "t", "first_author": "a", "venue": "v", "peer_reviewed": "no",
                   "version_read": "arXiv v1", "first_date": "2024-01-01", "read": "F", "role": "proposes",
                   "extraction_scope": "whole report"},
        "defences": [{"id": "d", "name": "D", "origin": "this_report", "base_checkpoint": "M", "axis1": ["chat_roles"],
                      "axis2": ["sft"], "isolation": "no_ablation", "signal_dependence": "not_reported",
                      "trains_instruction_pair": "no", "trains_carry_through": "no", "page": 2}],
        "evaluations": [{"id": "e", "defence_id": "d", "benchmark": "B", "attacker_type": "static", "attacker_access": "black_box",
                         "judge": "j", "layout_same_as_defence": "yes", "measured_by": "r", "page": 3},
                        {"id": "e0", "defence_id": "none:M", "benchmark": "B", "attacker_type": "static", "attacker_access": "black_box",
                         "judge": "j", "layout_same_as_defence": "yes", "measured_by": "r", "page": 3}],
        "results": [{"id": "x", "evaluation_id": "e", "quantity": "R1", "coverage": "direct", "metric_as_printed": "ASR",
                     "value": "4.5", "unit": "percent", "direction": "lower_better", "qualifier": "exact", "value_source": "table", "page": 3},
                    {"id": "y", "evaluation_id": "e", "quantity": "R2clean", "coverage": "proxy", "metric_as_printed": "chart",
                     "unit": "percent", "direction": "higher_better", "qualifier": "approximate", "value_source": "figure_only", "page": 3}],
        "comparisons": [dict(comp(), id="c", left="e", right="e0", varies="the defence", page=3)],
        "claims": [{"id": "k", "text": "t", "location": "abstract", "anchor": "a short phrase", "jobs": ["R1"],
                    "supported_by": ["c"], "contradicted_by": ["y"], "page": 1}],
        "coverage": {"R1": "direct", "R2clean": "proxy", "R2attack": "not_reported", "R3ns": "not_reported",
                     "R3cp": "not_reported", "R3safe": "not_reported"},
    }


def test_a_valid_record_passes_with_its_pages():
    pages = ["intro", "method", "Table 2: ASR 4.5 under attack", "x"]
    pages[0] = "a short phrase in the abstract"
    probs, notes = schema.validate_record(minimal_record(), SCHEMA, pages)
    assert probs == [] and notes == []


def test_validator_reports_each_kind_of_fault():
    rec = minimal_record()
    rec["defences"][0]["axis1"] = ["telepathy"]
    rec["results"][0]["value"] = "9.9"
    rec["results"][0]["page"] = 9
    rec["comparisons"][0]["right"] = "nowhere"
    rec["claims"][0]["anchor"] = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen"
    del rec["report"]["extraction_scope"]
    probs, _ = schema.validate_record(rec, SCHEMA, ["one two", "b", "c", "d"])
    text = "\n".join(probs)
    assert "telepathy" in text
    assert "page 9 is beyond" in text
    assert "right 'nowhere'" in text
    assert "longer than 14 words" in text
    assert "extraction_scope" in text


def test_a_printed_result_needs_its_value_but_a_figure_only_one_does_not():
    rec = minimal_record()
    del rec["results"][0]["value"]
    probs, _ = schema.validate_record(rec, SCHEMA, ["a short phrase", "b", "Table 2", "d"])
    assert any("needs its value" in p for p in probs)
    assert not any(":y:" in p for p in probs)


def test_the_pilot_records_follow_the_frozen_schema():
    files = sorted((ROOT / "reports" / "records").glob("*.yaml"))
    assert len(files) >= 6
    for f in files:
        probs, _ = schema.validate_record(schema.load_record(f), SCHEMA)
        assert probs == [], (f.name, probs[:3])
