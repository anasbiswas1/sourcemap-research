"""Tests for src/analysis.py on a two-report fixture: a proposing report and a later re-measurement."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
A = importlib.import_module("analysis")
schema_mod = importlib.import_module("schema")

M = {c: "matched" for c in schema_mod.CONDITIONS}


def _ev(i, did, attacker="static", access="black_box"):
    return {"id": i, "defence_id": did, "benchmark": "SEP test", "attacker_type": attacker, "attacker_access": access,
            "judge": "substring match on the payload", "layout_same_as_defence": "yes", "measured_by": "x", "page": 3}


def _res(i, ev, q, v, direction="lower_better", unit="percent", also=None):
    r = {"id": i, "evaluation_id": ev, "quantity": q, "coverage": "direct", "metric_as_printed": q + " rate", "value": v,
         "unit": unit, "direction": direction, "qualifier": "exact", "value_source": "table", "page": 3}
    if also:
        r["also_quantity"] = also
    return r


def fixture():
    a = {"report": {"id": "a", "slug": "a", "role": "proposes", "read": "F", "first_date": "2025-01-01"},
         "coverage": {q: "not_reported" for q in A.QUANTITIES} | {"R1": "direct", "R3ns": "direct"},
         "defences": [{"id": "sa", "name": "SecAlign", "origin": "this_report", "base_checkpoint": "M", "axis1": ["delimiters_markers"],
                       "axis2": ["preference_optimisation"], "isolation": "ablation_present", "signal_dependence": "measured",
                       "trains_instruction_pair": "no", "trains_carry_through": "no", "page": 2,
                       "layout_compat": {"user_turn": "supported", "separate_role": "untested"}},
                      {"id": "abl", "name": "SecAlign without delimiters", "origin": "this_report", "base_checkpoint": "M",
                       "axis1": ["no_signal"], "axis2": ["preference_optimisation"], "isolation": "not_applicable",
                       "signal_dependence": "not_applicable", "trains_instruction_pair": "no", "trains_carry_through": "no", "page": 2},
                      {"id": "sw", "name": "Sandwich defence", "origin": "other_report", "base_checkpoint": "M", "axis1": ["position"],
                       "axis2": ["prompting"], "isolation": "not_applicable", "signal_dependence": "baseline_only",
                       "trains_instruction_pair": "not_applicable", "trains_carry_through": "not_applicable", "page": 2}],
         "evaluations": [_ev("e0", "none:M"), _ev("e1", "sa"), _ev("e2", "sw"), _ev("e3", "sa", "adaptive", "white_box")],
         "results": [_res("r0", "e0", "R1", "50.0"), _res("i0", "e0", "R3ns", "10.0"),
                     _res("r1", "e1", "R1", "10.0"), _res("i1", "e1", "R3ns", "30.0"), _res("u1", "e1", "R2attack", "60.0", "higher_better"),
                     _res("r2", "e2", "R1", "20.0"), _res("r3", "e3", "R1", "40.0")],
         "comparisons": [{"id": "c1", "left": "e1", "right": "e0", "purpose": "W", "varies": "defence", **M, "page": 3},
                         {"id": "c2", "left": "e1", "right": "e2", "purpose": "W", "varies": "defence", **M, "page": 3},
                         {"id": "c3", "left": "e1", "right": "e0", "purpose": "W", "varies": "defence", **M | {"c5_judge": "unreported"}, "page": 3}],
         "claims": [{"id": "k1", "text": "SecAlign stops attacks", "location": "abstract", "anchor": "a", "jobs": ["R1"],
                     "supported_by": ["c1"], "page": 1},
                    {"id": "k2", "text": "utility is kept", "location": "abstract", "anchor": "b", "jobs": ["general_utility"],
                     "supported_by": ["c3"], "page": 1}]}
    b = {"report": {"id": "b", "slug": "b", "role": "re_measures", "read": "F", "first_date": "2026-01-01"},
         "coverage": {q: "not_reported" for q in A.QUANTITIES} | {"R3cp": "direct"},
         "defences": [{"id": "s2", "name": "SecAlign (re-measured)", "origin": "other_report", "base_checkpoint": "M",
                       "axis1": ["delimiters_markers"], "axis2": ["preference_optimisation"], "isolation": "not_applicable",
                       "signal_dependence": "not_reported", "trains_instruction_pair": "no", "trains_carry_through": "no", "page": 2}],
         "evaluations": [_ev("f1", "s2", "optimisation")],
         "results": [_res("x1", "f1", "R3cp", "70.0", "higher_better"), _res("x2", "f1", "R1", "30.0"),
                     _res("x3", "f1", "R2attack", "50.0", "higher_better", also=["R3safe"])]}
    return {"a": a, "b": b}


def test_methods_map_and_families():
    recs = fixture()
    ms = A.methods(recs)
    assert [m["name"] for m in ms] == ["SecAlign"]                       # the variant and the other report's baseline are not methods
    m = ms[0]
    assert m["layout_user_turn"] == "supported" and m["layout_system_context"] == "untested" and m["signal_dependence"] == "measured"
    cells = {(r["axis1"], r["axis2"]): r for r in A.map_table(ms)}
    assert cells[("delimiters_markers", "preference_optimisation")]["methods"] == 1 and cells[("no_signal", "sft")]["methods"] == 0
    assert A.family("Meta-SecAlign-70B + EP-DPO") is None and A.family("SecAlign++ LoRA") == "Meta-SecAlign"
    assert A.family("repeat the user's prompt").startswith("Sandwich") and A.family("White-box defence: reminder") is None


def test_coverage_original_and_by_anyone_and_joint():
    recs = fixture()
    cfg = A.configuration_coverage(recs)
    by = {r["defence_uid"]: r for r in cfg}
    assert by["a:sa"]["R1"] == "direct" and by["a:sa"]["R3ns"] == "direct" and by["a:sa"]["joint_all_three"] == "yes"
    assert by["b:s2"]["R3safe"] == "proxy" and by["b:s2"]["joint_all_three"] == "yes"
    fam = {r["family_key"]: r for r in A.family_coverage(recs, cfg, A.methods(recs))}
    f = fam["SecAlign | trained"]
    assert f["R3cp_original"] == "no" and f["R3cp_anyone"] == "yes" and f["reports_measuring_it_later"] == "b"


def test_crosswalk_claims_orderings_stress_and_scs():
    recs = fixture()
    cw = A.crosswalk(recs)
    r1 = next(r for r in cw if r["quantity"] == "R1")
    assert r1["judge_rule"] == "string or answer match" and "Rp" in r1["cannot_see"]
    cs = {r["claim_uid"]: r for r in A.claim_support(recs, schema_mod.grade)}
    assert cs["a:k1"]["best_grade"] == "A" and cs["a:k2"]["best_grade"] == "U"
    assert cs["a:k2"]["utility_basis"] == "R2 results"
    od = A.orderings(recs, schema_mod.grade)
    assert [o["comparison_uid"] for o in od] == ["a:c2"] and od[0]["paired_results"] == 1
    st = {r["method_uid"]: r for r in A.stress_tests(recs, A.methods(recs))}
    s = st["a:secalign"]
    assert s["own_stress_attackers"] == "adaptive" and s["own_white_box"] == 1 and s["later_stress_attackers"] == "optimisation"
    sc = A.scs_pairs(recs, schema_mod.grade)
    assert len(sc) == 1 and sc[0]["SCS"] == 0.5                         # (90 - 70) / (90 - 50)
