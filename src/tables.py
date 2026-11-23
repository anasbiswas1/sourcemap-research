"""The manuscript tables (plan v2 B3, notebook 07), built from the committed tables in reports/analysis/ and
reports/extraction/, written as Word files with a record-id column, and the claim-to-result check between a Word
manuscript and the records.

Every numeric cell carries the record ids it was counted from (a derived count) or the result id it was read from
(a published value), and the trace file lists them all. Nothing here calls a model or the network."""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

AXIS1 = ["chat_roles", "delimiters_markers", "encodings", "learned_token_features", "fixed_embedding_transform", "position",
         "internal_intervention", "no_signal"]
AXIS2 = ["prompting", "soft_tokens_frozen", "sft", "preference_optimisation", "distillation", "adversarial_rl", "fixed_inference_rule"]
NAME = {"chat_roles": "Chat roles", "delimiters_markers": "Delimiters or markers", "encodings": "Encodings",
        "learned_token_features": "Learned token features", "fixed_embedding_transform": "Fixed embedding transform", "position": "Position",
        "internal_intervention": "Internal intervention", "no_signal": "No explicit signal", "prompting": "Prompting only",
        "soft_tokens_frozen": "Soft tokens, frozen weights", "sft": "Supervised fine-tuning", "preference_optimisation": "Preference optimisation",
        "distillation": "Distillation", "adversarial_rl": "Adversarial training or RL", "fixed_inference_rule": "Fixed inference rule"}
QUANT = {"R1": "Resists the injection (R1)", "R2clean": "User's task, clean data (R2clean)", "R2attack": "User's task under attack (R2attack)",
         "R3ns": "Non-suppression (R3ns)", "R3cp": "Correct processing (R3cp)", "R3safe": "Safe processing (R3safe)"}
QUANTITIES = list(QUANT)
LAYOUT = {"user_turn": "Document in the user turn", "separate_role": "Document in a separate role", "system_context": "Document in the system prompt",
          "agent_tool_result": "Document as an agent tool result"}
SIGNAL = {"measured": "Measured: run with the signal removed or moved", "measured_other_checkpoint": "Measured on another checkpoint of the method",
          "stated": "Stated without numbers", "baseline_only": "Undefended run only", "not_reported": "Not tested", "not_applicable": "No signal"}
ATTACK = {"static": "Fixed injections", "adaptive": "Adaptive attacker", "optimisation": "Optimisation attack", "rl": "RL attacker", "human": "Human red team"}
COND = {"c1_base": "Base model", "c2_layout": "Layout", "c3_benchmark": "Benchmark and split", "c4_attacker": "Attacker", "c5_judge": "Judge and denominator",
        "c6_decoding": "Decoding"}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load(reports: Path) -> dict:
    a, e = reports / "analysis", reports / "extraction"
    return {"methods": read_csv(a / "methods.csv"), "map": read_csv(a / "map.csv"), "stress": read_csv(a / "stress_tests.csv"),
            "cfg": read_csv(a / "coverage_by_configuration.csv"), "paper": read_csv(a / "coverage_by_paper.csv"),
            "family": read_csv(a / "coverage_by_family.csv"), "crosswalk": read_csv(a / "crosswalk.csv"),
            "claims": read_csv(a / "claim_support.csv"), "layout": read_csv(a / "layout_compat.csv"), "scs": read_csv(a / "scs.csv"),
            "orderings": read_csv(a / "orderings.csv"), "gaps": read_csv(a / "reporting_gaps.csv"),
            "results": read_csv(e / "results.csv"), "evaluations": read_csv(e / "evaluations.csv"), "reports": read_csv(e / "reports.csv"),
            "comparisons": read_csv(e / "comparisons.csv")}


def share(a: int, b: int) -> str:
    return f"{a} ({round(100 * a / b)} in 100)" if b else str(a)


class Table:
    """A manuscript table: a title, column names, rows of cells, and for every row the record ids behind it."""

    def __init__(self, key: str, title: str, columns: list[str], note: str = ""):
        self.key, self.title, self.columns, self.note = key, title, columns, note
        self.rows: list[list] = []
        self.ids: list[str] = []        # one entry per row: ';'-joined record ids
        self.rule: list[str] = []       # how the row's numbers were derived

    def add(self, cells: list, ids, rule: str):
        self.rows.append([str(c) for c in cells])
        self.ids.append(";".join(sorted(set(ids))) if not isinstance(ids, str) else ids)
        self.rule.append(rule)


# ---------------------------------------------------------------- the tables
def table_map(d: dict) -> Table:
    t = Table("t01_map", "The map: methods per cell, how the source is shown at inference (columns) against how the behaviour was built (rows)",
              ["How the behaviour was built"] + [NAME[a] for a in AXIS1] + ["Total"],
              f"A method with two values on an axis counts in each of its cells, so the totals count cell occupancies; the corpus has {len(d['methods'])} distinct methods.")
    cells = {(r["axis1"], r["axis2"]): r for r in d["map"]}
    for b in AXIS2:
        row, ids, tot = [NAME[b]], [], 0
        for a in AXIS1:
            c = cells[(a, b)]
            row.append(c["methods"] if c["methods"] != "0" else "")
            tot += int(c["methods"])
            ids += [u for u in c["method_uids"].split(";") if u]
        row.append(tot)
        t.add(row, ids, "count of methods in the cell (analysis/map.csv, column methods)")
    row, ids = ["Total"], []
    for a in AXIS1:
        n = sum(int(cells[(a, b)]["methods"]) for b in AXIS2)
        row.append(n)
        ids += [u for b in AXIS2 for u in cells[(a, b)]["method_uids"].split(";") if u]
    row.append(sum(int(r["methods"]) for r in d["map"]))
    t.add(row, ids, "column totals over the cells")
    return t


def table_coverage(d: dict) -> Table:
    t = Table("t02_coverage", "Coverage of the three jobs: papers reporting each quantity, evaluated configurations covering it, and joint scoring",
              ["Quantity", "Papers: direct", "Papers: proxy", "Papers: pooled only", "Papers: any (of 124)", "Configurations covering it (of 843)",
               "Configurations with all three jobs on the same replies"],
              "Paper coverage from the report-level coverage field; configuration coverage from the results of each defence record's own evaluations.")
    paper, cfg = d["paper"], d["cfg"]
    joint = [c for c in cfg if c["joint_all_three"] == "yes"]
    for q in QUANTITIES:
        dirs = [p["report"] for p in paper if p[q] == "direct"]
        prox = [p["report"] for p in paper if p[q] == "proxy"]
        agg = [p["report"] for p in paper if p[q] == "aggregate_only"]
        cov = [c["defence_uid"] for c in cfg if c[q] != "none"]
        t.add([QUANT[q], len(dirs), len(prox), len(agg), share(len(dirs) + len(prox) + len(agg), len(paper)), share(len(cov), len(cfg)),
               share(len(joint), len(cfg)) if q == "R3safe" else ""],
              dirs + prox + agg + cov + ([j["defence_uid"] for j in joint] if q == "R3safe" else []),
              "counts over analysis/coverage_by_paper.csv and analysis/coverage_by_configuration.csv")
    return t


def table_family(d: dict) -> Table:
    t = Table("t03_family", "Named method families: which quantities the proposing paper measured and which any paper in the corpus measured",
              ["Family", "Proposing report(s)", "Later reports measuring it", "R2attack: own / anyone", "R3 (any reading): own / anyone"],
              "Own: the proposing paper's own evaluations. Anyone: any report in the corpus that ran the family, matched by name and kind.")
    for f in d["family"]:
        later = [x for x in f["reports_measuring_it_later"].split(";") if x]
        r3o = any(f[q + "_original"] == "yes" for q in ("R3ns", "R3cp", "R3safe"))
        r3a = any(f[q + "_anyone"] == "yes" for q in ("R3ns", "R3cp", "R3safe"))
        t.add([f["family_key"].replace(" | ", ", "), f["proposing_reports"].replace(";", ", "), len(later),
               f"{f['R2attack_original']} / {f['R2attack_anyone']}", f"{'yes' if r3o else 'no'} / {'yes' if r3a else 'no'}"],
              f["proposing_reports"].split(";") + later, "analysis/coverage_by_family.csv")
    return t


def table_crosswalk(d: dict) -> Table:
    t = Table("t04_crosswalk", "Metric crosswalk: what each kind of metric in the corpus counts and what it cannot see",
              ["Quantity", "Judge rule", "Outcome counted", "Cannot see", "Results", "Reports"],
              "Grouped over benchmark families; the full table with benchmark families and metric names is analysis/crosswalk.csv.")
    groups = defaultdict(lambda: {"results": 0, "reports": set(), "ids": [], "counted": "", "cannot": ""})
    for r in d["crosswalk"]:
        g = groups[(r["quantity"], r["judge_rule"])]
        g["results"] += int(r["results"])
        g["ids"] += r["result_uids"].split(";")
        g["counted"], g["cannot"] = r["outcome_counted"], r["cannot_see"]
    rep_of = {x["result_uid"]: x["report_id"] for x in d["results"]}
    order = QUANTITIES + ["general_utility", "other"]
    for (q, j), g in sorted(groups.items(), key=lambda kv: (order.index(kv[0][0]), -kv[1]["results"])):
        reps = {rep_of.get(u, u.split(":")[0]) for u in g["ids"]}
        t.add([QUANT.get(q) or {"general_utility": "General utility", "other": "Other"}[q], j, g["counted"], g["cannot"], g["results"], len(reps)],
              g["ids"], "results grouped by quantity and judge rule (analysis/crosswalk.csv)")
    return t


def table_claims(d: dict) -> Table:
    t = Table("t05_claims", "Support for headline claims: claims by job and by the best grade of their supporting comparisons",
              ["Job the claim speaks to", "Claims", "Grade A", "Grade B", "Grade C", "Grade U", "No comparison", "Utility claims on general benchmarks only"],
              "A claim that speaks to two jobs is counted under both. Grades per plan equation 4.")
    jobs = [("R1", "Security (R1)"), ("R2", "User's task (R2)"), ("R3", "Document handling (R3)"), ("general_utility", "General utility")]
    for job, lab in jobs:
        ks = [k for k in d["claims"] if job in k["jobs"].split(";")]
        g = Counter(k["best_grade"] for k in ks)
        gen = [k["claim_uid"] for k in ks if k["utility_basis"] == "general utility only"]
        t.add([lab, len(ks), g["A"], g["B"], g["C"], g["U"], g["none"], len(gen) if job in ("R2", "general_utility") else ""],
              [k["claim_uid"] for k in ks], "counts over analysis/claim_support.csv")
    ks = d["claims"]
    g = Counter(k["best_grade"] for k in ks)
    t.add(["All claims (each once)", len(ks), g["A"], g["B"], g["C"], g["U"], g["none"],
           sum(k["utility_basis"] == "general utility only" for k in ks)], [k["claim_uid"] for k in ks], "counts over analysis/claim_support.csv")
    return t


def table_below_a(d: dict) -> Table:
    t = Table("t06_claims_below_a", "Headline claims whose best supporting comparison is below grade A, with the condition at fault",
              ["Report", "Claim", "Jobs", "Best grade", "Condition unmatched or unreported"],
              "From analysis/claim_support.csv and the comparisons of the same report; layout is left out for whole-configuration comparisons by design.")
    byrep = defaultdict(list)
    for c in d["comparisons"]:
        byrep[c["report_id"]].append(c)
    for k in d["claims"]:
        if k["best_grade"] in ("B", "C", "U"):
            g = k["best_grade"]
            conds = sorted({COND[c3] for c2 in byrep[k["report"]] if c2["grade"] == g for c3 in COND
                            if c2.get(c3) in ("unmatched", "unreported") and not (c3 == "c2_layout" and c2["purpose"] == "W")})
            t.add([k["report"], k["text"], k["jobs"].replace(";", ", "), g, ", ".join(conds) or "see analysis/claim_support.csv"],
                  [k["claim_uid"]], "analysis/claim_support.csv")
    return t


def table_signal(d: dict) -> Table:
    t = Table("t07_signal", "Signal dependence: whether a method with an inference-time signal was run with that signal removed or moved",
              ["Kind of method", "Methods with a signal", "Measured", "Measured on another checkpoint", "Stated without numbers", "Undefended run only", "Not tested"],
              "Trained methods: any axis-2 value beyond prompting and fixed rules. Methods with no explicit signal are left out.")
    for kind, lab in (("yes", "Trained"), ("no", "Prompting or fixed rule")):
        ms = [m for m in d["methods"] if m["trained"] == kind and m["axis1"] != "no_signal"]
        c = Counter(m["signal_dependence"] for m in ms)
        t.add([lab, len(ms), c["measured"], c["measured_other_checkpoint"], c["stated"], c["baseline_only"], c["not_reported"]],
              [m["method_uid"] for m in ms], "counts over analysis/methods.csv (column signal_dependence)")
    return t


def table_measured(d: dict) -> Table:
    t = Table("t08_signal_measured", "Methods run with their signal removed or moved, and what the run showed",
              ["Method", "Report", "Signal (axis 1)", "Result as recorded"], "From the signal_dependence_detail field of the records.")
    for m in d["methods"]:
        if m["signal_dependence"].startswith("measured"):
            t.add([m["name"], m["report"], ", ".join(NAME[a] for a in m["axis1"].split(";")), m["signal_dependence_detail"] or "see the record"],
                  m["defence_uids"].split(";"), "analysis/methods.csv")
    return t


def table_stress(d: dict) -> Table:
    t = Table("t09_stress", "Stress tests: methods that faced an attacker beyond fixed injections, white-box attacks, signal-removal runs and later re-measurement",
              ["Kind of method", "Methods", "Pushed beyond fixed injections", "In their own paper", "Only in a later paper", "White-box attack in own paper",
               "Signal-removal run", "Re-measured by a later paper"], "From analysis/stress_tests.csv.")
    for kind, lab in (("yes", "Trained"), ("no", "Prompting or fixed rule"), (None, "All methods")):
        st = [r for r in d["stress"] if kind is None or r["trained"] == kind]
        own = [r for r in st if r["own_stress_attackers"]]
        later_only = [r for r in st if r["later_stress_attackers"] and not r["own_stress_attackers"]]
        t.add([lab, len(st), share(sum(r["pushed_hard"] == "yes" for r in st), len(st)), len(own), len(later_only),
               sum(int(r["own_white_box"]) > 0 for r in st), sum(r["signal_removal_run"] == "yes" for r in st), sum(bool(r["later_reports"]) for r in st)],
              [r["method_uid"] for r in st], "counts over analysis/stress_tests.csv")
    return t


def table_scs(d: dict) -> Table:
    t = Table("t10_scs", "Suppression cost per security point, from published pairs in one re-measurement",
              ["Defence", "Base", "R1 undefended", "R1 defended", "R3ns undefended", "R3ns defended", "SCS"],
              "SCS = (R3ns undefended minus R3ns defended) / (R1 defended minus R1 undefended); rates in 100. The four result ids per row are the printed values.")
    for s in d["scs"]:
        t.add([s["defence"], s["base"], s["R1_undefended"], s["R1_defended"], s["R3ns_undefended"], s["R3ns_defended"], s["SCS"]],
              s["result_uids"].split(";"), "analysis/scs.csv; R1 = 100 minus the printed executed rate, R3ns = 100 minus the printed ignored rate")
    return t


def table_layout(d: dict) -> Table:
    t = Table("t11_layout", "Layout compatibility: methods marked supported, unsupported or untested for each deployment layout",
              ["Deployment layout", "Supported", "Unsupported", "Untested"], "From the layout_compat field of the records, per method.")
    for k, lab in LAYOUT.items():
        c = Counter(r[f"layout_{k}"] for r in d["layout"])
        t.add([lab, c["supported"], c["unsupported"], c["untested"]], [r["method_uid"] for r in d["layout"]], "counts over analysis/layout_compat.csv")
    return t


def table_gaps(d: dict) -> Table:
    t = Table("t12_gaps", "Conditions left unreported in the coded comparisons, the lines the Injection Defence Card asks for",
              ["Condition", "Comparisons with it unreported", "Reports"], "From analysis/reporting_gaps.csv; a grade-U comparison has at least one such condition.")
    for g in d["gaps"]:
        t.add([COND[g["condition"]], g["comparisons_unreported"], g["reports"]], g["comparison_uids"].split(";") if g["comparison_uids"] else [],
              "analysis/reporting_gaps.csv")
    return t


def table_methods(d: dict) -> Table:
    t = Table("ta1_methods", "Appendix: the methods in the corpus with their position on the map, signal dependence and released weights",
              ["Method", "Report", "Year", "Axis 1", "Axis 2", "Trained", "Signal dependence", "Weights released"],
              "One row per method; base-checkpoint records are listed in the record-id column.")
    for m in sorted(d["methods"], key=lambda m: (AXIS1.index(m["axis1"].split(";")[0]), AXIS2.index(m["axis2"].split(";")[0]), m["name"].lower())):
        t.add([m["name"], m["report"], m["year"], ", ".join(NAME[a] for a in m["axis1"].split(";")), ", ".join(NAME[b] for b in m["axis2"].split(";")),
               m["trained"], SIGNAL[m["signal_dependence"]], m["released_weights"]], m["defence_uids"].split(";"), "analysis/methods.csv")
    return t


def build_all(d: dict) -> list[Table]:
    return [table_map(d), table_coverage(d), table_family(d), table_crosswalk(d), table_claims(d), table_below_a(d), table_signal(d),
            table_measured(d), table_stress(d), table_scs(d), table_layout(d), table_gaps(d), table_methods(d)]


# ---------------------------------------------------------------- output
def trace_rows(tables: list[Table]) -> list[dict]:
    out = []
    for t in tables:
        for i, (row, ids, rule) in enumerate(zip(t.rows, t.ids, t.rule)):
            for col, cell in zip(t.columns, row):
                if re.search(r"\d", cell):
                    out.append({"table": t.key, "row": i + 1, "row_label": row[0], "column": col, "value": cell, "rule": rule, "record_ids": ids})
    return out


def write_docx(t: Table, path: Path) -> None:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.section import WD_ORIENT
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Arial"
    st.font.size = Pt(8 if len(t.columns) <= 6 else 7)
    if len(t.columns) > 6:                                   # wide tables go on a landscape page
        sec = doc.sections[0]
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    doc.add_paragraph(f"{t.title}.")
    tab = doc.add_table(rows=1, cols=len(t.columns) + 1)
    tab.style = "Table Grid"
    for j, c in enumerate(t.columns + ["Record ids"]):
        tab.rows[0].cells[j].text = c
    for i, (row, ids) in enumerate(zip(t.rows, t.ids)):
        cells = tab.add_row().cells
        idlist = [x for x in ids.split(";") if x]
        shown = "; ".join(idlist) if len(idlist) <= 8 else f"{len(idlist)} record ids: reports/trace_07.csv, {t.key} row {i + 1}"
        for j, v in enumerate(row + [shown]):
            cells[j].text = v
    if t.note:
        doc.add_paragraph(t.note)
    doc.save(str(path))


def write_csv(t: Table, path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(t.columns + ["record_ids", "rule"])
        for row, ids, rule in zip(t.rows, t.ids, t.rule):
            w.writerow(row + [ids, rule])


# ---------------------------------------------------------------- the claim-to-result check against a Word manuscript
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")


def manuscript_numbers(docx_path: Path) -> list[dict]:
    """Every number in the manuscript's paragraphs and table cells, with where it was found and the id tag beside it,
    if the cell carries one in square brackets ([report:result_id])."""
    from docx import Document
    doc = Document(str(docx_path))
    out = []
    for i, p in enumerate(doc.paragraphs):
        for n in NUM.findall(p.text):
            out.append({"where": f"paragraph {i + 1}", "text": p.text[:80], "number": n, "id_tag": ""})
    for ti, tab in enumerate(doc.tables):
        for ri, row in enumerate(tab.rows):
            for ci, cell in enumerate(row.cells):
                tags = re.findall(r"\[([a-z0-9_]+:[a-z0-9_]+)\]", cell.text)
                for n in NUM.findall(re.sub(r"\[[^\]]*\]", "", cell.text)):
                    out.append({"where": f"table {ti + 1} row {ri + 1} col {ci + 1}", "text": cell.text[:80], "number": n, "id_tag": ";".join(tags)})
    return out


def check_manuscript(docx_path: Path, results: list[dict], trace: list[dict]) -> list[dict]:
    """Each number in the manuscript is matched to a result id (value as printed, with its evaluation's model, metric,
    unit and page returned for the reader) or to a traced derived count; anything else is a stray numeral."""
    by_id = {r["result_uid"]: r for r in results}
    traced = defaultdict(list)
    for t in trace:
        for n in NUM.findall(t["value"]):
            traced[n].append(f"{t['table']} r{t['row']} {t['column']}")
    out = []
    for m in manuscript_numbers(docx_path):
        n = m["number"]
        status, detail = "stray numeral", ""
        if m["id_tag"]:
            hits = [by_id[t] for t in m["id_tag"].split(";") if t in by_id]
            ok = [h for h in hits if h["value"].rstrip("%") == n]
            if ok:
                h = ok[0]
                status, detail = "matches result id", f"{h['result_uid']}: {h['metric_as_printed']} = {h['value']} {h['unit']}, page {h['page']}"
            else:
                status, detail = "ID TAG DOES NOT MATCH", m["id_tag"]
        elif n in traced:
            status, detail = "matches derived count", "; ".join(traced[n][:3])
        elif any(r["value"].rstrip("%") == n for r in results):
            status, detail = "matches a printed value, no id tag", ""
        out.append({**m, "status": status, "detail": detail})
    return out
