"""Tests for src/extract.py: the seeded sample, value cards, tables, cross-record checks and agreement statistics."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
extract = importlib.import_module("extract")
schema_mod = importlib.import_module("schema")


def _rec(rid="r_a", slug="s_a"):
    return {"report": {"id": rid, "slug": slug, "role": "proposes", "read": "F"},
            "coverage": {q: "not_reported" for q in extract.QUANTITIES} | {"R1": "direct"},
            "defences": [{"id": "d1", "name": "Def", "origin": "this_report", "base_checkpoint": "M", "axis1": ["chat_roles"],
                          "axis2": ["sft"], "isolation": "no_ablation", "signal_dependence": "not_reported",
                          "trains_instruction_pair": "no", "trains_carry_through": "no", "page": 2}],
            "evaluations": [{"id": "e1", "defence_id": "d1", "benchmark": "B", "attacker_type": "static", "attacker_access": "black_box",
                             "judge": "J", "layout_same_as_defence": "yes", "measured_by": rid, "page": 3},
                            {"id": "e0", "defence_id": "none:M", "benchmark": "B", "attacker_type": "static", "attacker_access": "black_box",
                             "judge": "J", "layout_same_as_defence": "yes", "measured_by": rid, "page": 3}],
            "results": [{"id": f"x{i}", "evaluation_id": "e1" if i % 2 else "e0", "quantity": "R1", "coverage": "direct",
                         "metric_as_printed": "ASR", "value": f"{i}.5", "unit": "percent", "direction": "lower_better",
                         "qualifier": "exact", "value_source": "table", "page": 3} for i in range(9)],
            "comparisons": [{"id": "c1", "left": "e1", "right": "e0", "purpose": "W", "varies": "defence",
                             **{c: "matched" for c in schema_mod.CONDITIONS}, "page": 3}],
            "claims": [{"id": "k1", "text": "t", "location": "abstract", "anchor": "a", "jobs": ["R1"], "supported_by": ["c1"], "page": 1}]}


def test_sample_is_stable_and_twenty_percent():
    slugs = [f"s{i:03d}" for i in range(124)]
    s = extract.second_pass_sample(slugs)
    assert len(s) == 25 and len(set(s)) == 25
    dropped = [x for x in slugs if x != slugs[-1] and x not in s[:1]]
    s2 = extract.second_pass_sample(dropped)
    assert set(s[1:]) <= set(s2)                       # removing one study does not reorder the others
    assert extract.second_pass_sample(slugs) == s      # deterministic


def test_cards_hide_values_and_are_capped():
    cards = extract.value_cards(_rec())
    assert len(cards) == extract.CARDS_PER_REPORT
    assert all("value" not in c for c in cards)
    assert {c["arm"].startswith(("Def on", "no defence")) for c in cards} == {True}


def test_tables_have_global_ids_and_grades():
    sch = schema_mod.load_schema(Path(__file__).resolve().parent.parent / "schema" / "record_schema.yaml")
    t = extract.build_tables({"r_a": _rec()}, sch, schema_mod.grade)
    assert t["defences"][0][0]["defence_uid"] == "r_a:d1"
    ev = {r["evaluation_uid"]: r for r in t["evaluations"][0]}
    assert ev["r_a:e1"]["measurement"] == "original" and ev["r_a:e0"]["measurement"] == "undefended"
    assert t["comparisons"][0][0]["grade"] == "A"
    assert t["claims"][0][0]["supported_by"] == "r_a:c1"


def test_cross_record_checks():
    recs = {"r_a": _rec()}
    assert extract.cross_record_problems(recs, ["s_a"]) == []
    probs = extract.cross_record_problems(recs, ["s_a", "s_b"], {"r_a": 2})
    assert any("s_b has no record" in p for p in probs)
    assert any("beyond the PDF's 2 pages" in p for p in probs)


def test_kappa_jaccard_and_rounding():
    assert extract.cohen_kappa([("a", "a"), ("b", "b")]) == 1.0
    assert extract.cohen_kappa([("a", "a"), ("a", "a")]) is None
    assert abs(extract.cohen_kappa([("a", "a"), ("a", "b"), ("b", "b"), ("b", "a")])) < 1e-9
    assert extract.jaccard(["x", "y"], ["x"]) == 0.5
    assert extract.values_agree("45.20%", "45.2") and extract.values_agree("+0.028", "0.028")
    assert not extract.values_agree("45.2", "45.3") and extract.values_agree("12", "12.0")


def test_agreement_counts_disagreements():
    rec = _rec()
    sp = {"report": "r_a", "role": "proposes", "coverage": dict(rec["coverage"]),
          "defences": [{"name": "Def", "bases": ["M"], "origin": "this_report", "axis1": ["chat_roles", "position"], "axis2": ["sft"],
                        "isolation": "ablation_present", "signal_dependence": "not_reported", "trains_instruction_pair": "no",
                        "trains_carry_through": "no"}],
          "values": [{"result": "x1", "value": "1.5"}, {"result": "x2", "value": "9"}]}
    rows, per, dis = extract.agreement({"r_a": rec}, {"r_a": sp}, {"r_a": [["d1"]]})
    by = {r["field"]: r for r in rows}
    assert by["defence.isolation"]["exact_agreement"] == 0.0
    assert by["defence.axis1"]["mean_jaccard"] == 0.5
    assert by["printed values re-read from their addresses"]["exact_agreement"] == 0.5
    assert {d["field"] for d in dis} == {"isolation", "axis1", "value"}
    assert extract.validate_second_pass(sp, schema_mod.load_schema(Path(__file__).resolve().parent.parent / "schema" / "record_schema.yaml"),
                                        [{"result": "x1"}, {"result": "x2"}], rec, [["d1"]]) == []
