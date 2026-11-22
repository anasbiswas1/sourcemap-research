"""Record files to CSV tables, the second-pass sample, value cards and agreement statistics (plan v2, B4).

Notebook 04 writes this module. Nothing here calls a model or the network."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict

SEED = 2026
SHARE = 0.2
CARDS_PER_REPORT = 6
QUANTITIES = ["R1", "R2clean", "R2attack", "R3ns", "R3cp", "R3safe"]
DEF_CATEGORICAL = ["origin", "isolation", "signal_dependence", "trains_instruction_pair", "trains_carry_through"]
DEF_MULTI = ["axis1", "axis2"]
EXACT_MIN, KAPPA_MIN, JACCARD_MIN = 0.8, 0.6, 0.8
MISSING = "(missing)"


def rank_key(seed, *parts) -> str:
    return hashlib.sha256("|".join([str(seed), *map(str, parts)]).encode()).hexdigest()


def second_pass_sample(included_slugs, seed: int = SEED, share: float = SHARE) -> list[str]:
    """The seeded sample: every included study ranked by a hash of the seed and its slug, the first
    ceil(share * N) kept. Removing a study from the frame does not reorder the others."""
    slugs = sorted(set(included_slugs))
    n = math.ceil(share * len(slugs))
    return sorted(slugs, key=lambda s: rank_key(seed, s))[:n]


def value_cards(rec: dict, k: int = CARDS_PER_REPORT, seed: int = SEED) -> list[dict]:
    """Up to k printed results per report, chosen by hash rank, given by their address only (never the value)."""
    rid = rec["report"]["id"]
    evs = {e["id"]: e for e in rec.get("evaluations") or []}
    dfs = {d["id"]: d for d in rec.get("defences") or []}
    printed = [r for r in rec.get("results") or [] if r.get("value_source") != "figure_only" and r.get("value") not in (None, "")]
    printed.sort(key=lambda r: rank_key(seed, rid, r["id"]))
    cards = []
    for r in printed[:k]:
        e = evs[r["evaluation_id"]]
        d = dfs.get(e["defence_id"])
        arm = f"{d['name']} on {d['base_checkpoint']}" if d else f"no defence ({str(e['defence_id'])[5:]}, {e.get('baseline_kind', '')})"
        extra = "; ".join(f"{f}: {e[f]}" for f in ("split", "run", "injection_position", "attacker_budget", "subset_of") if e.get(f))
        cards.append({"report": rid, "result": r["id"], "page": r.get("page"), "location": r.get("location", ""),
                      "arm": arm, "benchmark": e["benchmark"], "attacker": e["attacker_type"], "judge": e["judge"],
                      "metric": r["metric_as_printed"], "quantity": r["quantity"], "unit": r["unit"], "detail": extra})
    return cards


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ";".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    return v


def build_tables(records: dict, schema: dict, grade) -> dict:
    """The five extraction tables (defences, evaluations, results, comparisons, claims) and a report index, with
    ids made global as <report_id>:<local_id>. Derived columns: the defence each result belongs to, whether an
    evaluation is the original or a later measurement, and the grade of each comparison."""
    k = schema["kinds"]
    out = {name: [] for name in ("reports", "defences", "evaluations", "results", "comparisons", "claims")}
    for rid in sorted(records):
        rec = records[rid]
        rep, cov = rec["report"], rec.get("coverage") or {}
        dfs = {d["id"]: d for d in rec.get("defences") or []}
        evs = {e["id"]: e for e in rec.get("evaluations") or []}
        out["reports"].append({**{f: _cell(rep.get(f)) for f in k["report"]["fields"]},
                               **{f"cov_{q}": cov.get(q, "") for q in QUANTITIES},
                               "cov_where": _cell(cov.get("where")),
                               **{f"n_{x}": len(rec.get(x) or []) for x in ("defences", "evaluations", "results", "comparisons", "claims")}})
        for d in rec.get("defences") or []:
            out["defences"].append({"report_id": rid, "defence_uid": f"{rid}:{d['id']}", **{f: _cell(d.get(f)) for f in k["defences"]["fields"]}})

        def duid(did):
            did = str(did)
            return did if did.startswith("none:") or ":" in did else f"{rid}:{did}"

        def measurement(e):
            d = dfs.get(e["defence_id"])
            if d is None:
                return "undefended" if str(e["defence_id"]).startswith("none:") else "other_record"
            if d.get("origin") == "this_report" and e.get("measured_by") == rid:
                return "original"
            if d.get("origin") == "this_report":
                return "original_reprinted"
            return "later"

        for e in rec.get("evaluations") or []:
            out["evaluations"].append({"report_id": rid, "evaluation_uid": f"{rid}:{e['id']}", "defence_uid": duid(e["defence_id"]),
                                       "measurement": measurement(e), **{f: _cell(e.get(f)) for f in k["evaluations"]["fields"]}})
        for r in rec.get("results") or []:
            e = evs.get(r["evaluation_id"], {})
            out["results"].append({"report_id": rid, "result_uid": f"{rid}:{r['id']}", "evaluation_uid": f"{rid}:{r['evaluation_id']}",
                                   "defence_uid": duid(e.get("defence_id", "")), "measurement": measurement(e) if e else "",
                                   **{f: _cell(r.get(f)) for f in k["results"]["fields"]}})
        for c in rec.get("comparisons") or []:
            out["comparisons"].append({"report_id": rid, "comparison_uid": f"{rid}:{c['id']}", "left_uid": f"{rid}:{c['left']}",
                                       "right_uid": f"{rid}:{c['right']}", "grade": grade(c),
                                       **{f: _cell(c.get(f)) for f in k["comparisons"]["fields"]}})
        for cl in rec.get("claims") or []:
            row = {"report_id": rid, "claim_uid": f"{rid}:{cl['id']}", **{f: _cell(cl.get(f)) for f in k["claims"]["fields"]}}
            row["supported_by"] = ";".join(f"{rid}:{s}" for s in cl.get("supported_by") or [])
            row["contradicted_by"] = ";".join(f"{rid}:{s}" for s in cl.get("contradicted_by") or [])
            out["claims"].append(row)
    fields = {name: (list(rows[0].keys()) if rows else []) for name, rows in out.items()}
    return {name: (rows, fields[name]) for name, rows in out.items()}


def cross_record_problems(records: dict, included_slugs, page_counts: dict | None = None) -> list[str]:
    """Checks that need the whole corpus: one record per included study, references to other reports resolve,
    every record read in full, and (when page counts are given) every page within its PDF."""
    probs = []
    by_slug = defaultdict(list)
    for rid, rec in records.items():
        by_slug[rec["report"]["slug"]].append(rid)
    inc = set(included_slugs)
    for s in sorted(inc - set(by_slug)):
        probs.append(f"included study {s} has no record")
    for s in sorted(set(by_slug) - inc):
        probs.append(f"record(s) {by_slug[s]} belong to {s}, which is not an included study")
    for s, rids in by_slug.items():
        if len(rids) > 1:
            probs.append(f"included study {s} has {len(rids)} records: {rids}")
    defences = {f"{rid}:{d['id']}" for rid, rec in records.items() for d in rec.get("defences") or []}
    for rid, rec in records.items():
        if rec["report"].get("read") != "F":
            probs.append(f"{rid}: read is {rec['report'].get('read')!r}, not F")
        for e in rec.get("evaluations") or []:
            mb = e.get("measured_by")
            if mb != rid and mb not in records:
                probs.append(f"{rid}:{e['id']}: measured_by {mb!r} is neither this report nor another record")
            sc = e.get("same_checkpoint_as")
            if sc and sc not in defences:
                probs.append(f"{rid}:{e['id']}: same_checkpoint_as {sc!r} is not a defence in the corpus")
            did = str(e.get("defence_id", ""))
            if ":" in did and not did.startswith("none:") and did not in defences:
                probs.append(f"{rid}:{e['id']}: defence_id {did!r} is not a defence in the corpus")
        if page_counts and rid in page_counts:
            n = page_counts[rid]
            for kind in ("defences", "evaluations", "results", "comparisons", "claims"):
                for row in rec.get(kind) or []:
                    pages = [row.get("page")] + list((row.get("pages") or {}).values())
                    for p in pages:
                        if isinstance(p, int) and p > n:
                            probs.append(f"{rid}:{kind}:{row.get('id')}: page {p} beyond the PDF's {n} pages")
    return probs


def validate_second_pass(doc: dict, schema: dict, cards: list[dict], first: dict, match_line: list) -> list[str]:
    """Allowed values in a second-pass document, value answers for exactly the drawn cards, and match lines that
    point at first-pass defences of the same report."""
    k, rid, out = schema["kinds"], doc.get("report"), []
    if doc.get("role") not in k["report"]["fields"]["role"]["values"]:
        out.append(f"{rid}: role {doc.get('role')!r} not allowed")
    for q in QUANTITIES:
        if (doc.get("coverage") or {}).get(q) not in k["coverage"]["fields"][q]["values"]:
            out.append(f"{rid}: coverage {q} {(doc.get('coverage') or {}).get(q)!r} not allowed")
    for e in doc.get("defences") or []:
        for f in DEF_CATEGORICAL:
            if e.get(f) not in k["defences"]["fields"][f]["values"]:
                out.append(f"{rid}: {e.get('name')}: {f} {e.get(f)!r} not allowed")
        for f in DEF_MULTI:
            vals = e.get(f) or []
            if not vals or any(v not in k["defences"]["fields"][f]["values"] for v in vals):
                out.append(f"{rid}: {e.get('name')}: {f} {vals!r} not allowed")
        if not e.get("bases"):
            out.append(f"{rid}: {e.get('name')}: no base models listed")
    answered = [v["result"] for v in doc.get("values") or []]
    drawn = [c["result"] for c in cards]
    if sorted(answered) != sorted(drawn):
        out.append(f"{rid}: values answered {sorted(answered)} differ from the cards drawn {sorted(drawn)}")
    ids = {d["id"] for d in first.get("defences") or []}
    if len(match_line or []) != len(doc.get("defences") or []):
        out.append(f"{rid}: {len(match_line or [])} match lines for {len(doc.get('defences') or [])} defence entries")
    for ids_ in match_line or []:
        for i in ids_ or []:
            if i not in ids:
                out.append(f"{rid}: match {i!r} is not a first-pass defence")
    used = [i for ids_ in match_line or [] for i in ids_ or []]
    for i in {x for x in used if used.count(x) > 1}:
        out.append(f"{rid}: first-pass defence {i!r} matched twice")
    return out


# ---- agreement --------------------------------------------------------------------------------------------------

def cohen_kappa(pairs: list[tuple]) -> float | None:
    """Cohen's kappa over (first, second) pairs; missing values are a category. None when chance agreement is 1
    (every value in one category), where kappa is undefined and exact agreement is reported alone."""
    n = len(pairs)
    if not n:
        return None
    pairs = [(MISSING if a in (None, "") else a, MISSING if b in (None, "") else b) for a, b in pairs]
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / (n * n)
    return None if pe >= 1 else (po - pe) / (1 - pe)


def jaccard(a, b) -> float:
    a, b = set(a or []), set(b or [])
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def _number(s):
    t = str(s).strip().replace(",", "").replace("−", "-").replace("%", "").replace("+", "").strip()
    m = re.fullmatch(r"-?\d+(\.\d+)?", t)
    if not m:
        return None, None
    return float(t), len(m.group(1)) - 1 if m.group(1) else 0


def values_agree(first, second) -> bool:
    """Exact match within rounding: both printed numbers rounded to the coarser of their two precisions."""
    a, da = _number(first)
    b, db = _number(second)
    if a is None or b is None:
        return re.sub(r"\s+", "", str(first)) == re.sub(r"\s+", "", str(second))
    d = min(da, db)
    return round(a, d) == round(b, d)


def agreement(first: dict, second: dict, matches: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """Agreement between the first coding (record files) and the second pass, before any disagreement is resolved.
    first: report id -> record; second: report id -> second-pass document; matches: report id -> list (one entry per
    second-pass defence, in order) of first-pass defence ids. Returns (field rows, per-report rows, disagreements)."""
    cat = defaultdict(list)          # field -> [(first, second)]
    multi = defaultdict(list)        # field -> [jaccard]
    multi_exact = defaultdict(list)
    vals, set_j, dis, per_report = [], [], [], []
    for rid in sorted(second):
        rec, sp, mt = first[rid], second[rid], matches[rid]
        cat["role"].append((rec["report"]["role"], sp["role"]))
        if rec["report"]["role"] != sp["role"]:
            dis.append({"report": rid, "unit": "report", "field": "role", "first": rec["report"]["role"], "second": sp["role"]})
        for q in QUANTITIES:
            a, b = rec["coverage"].get(q), sp["coverage"].get(q)
            cat[f"coverage.{q}"].append((a, b))
            if a != b:
                dis.append({"report": rid, "unit": "coverage", "field": q, "first": a, "second": b})
        dfs = {d["id"]: d for d in rec.get("defences") or []}
        if len(mt) != len(sp["defences"]):
            raise ValueError(f"{rid}: {len(mt)} match lines for {len(sp['defences'])} second-pass defences")
        matched = set()
        for entry, ids in zip(sp["defences"], mt):
            for did in ids or []:
                if did not in dfs:
                    raise ValueError(f"{rid}: match {did!r} is not a first-pass defence")
                matched.add(did)
                d = dfs[did]
                for f in DEF_CATEGORICAL:
                    cat[f"defence.{f}"].append((d.get(f), entry.get(f)))
                    if d.get(f) != entry.get(f):
                        dis.append({"report": rid, "unit": did, "field": f, "first": d.get(f), "second": entry.get(f)})
                for f in DEF_MULTI:
                    j = jaccard(d.get(f), entry.get(f))
                    multi[f"defence.{f}"].append(j)
                    multi_exact[f"defence.{f}"].append(set(d.get(f) or []) == set(entry.get(f) or []))
                    if j < 1:
                        dis.append({"report": rid, "unit": did, "field": f, "first": ";".join(d.get(f) or []),
                                    "second": ";".join(entry.get(f) or [])})
        # defence set at the method level: second-pass entries against first-pass groups; first-pass defences no
        # entry matched are grouped by name (with the base model removed) so one missed method counts once
        unmatched_first = [d for i, d in dfs.items() if i not in matched]
        groups = {re.sub(r"\s+on\s+.*$", "", d["name"]).strip().lower() for d in unmatched_first}
        n_entries = len(sp["defences"])
        n_matched_entries = sum(1 for ids in mt if ids)
        j = n_matched_entries / (n_entries + len(groups)) if (n_entries + len(groups)) else 1.0
        set_j.append(j)
        for d in unmatched_first:
            dis.append({"report": rid, "unit": d["id"], "field": "defence set", "first": d["name"], "second": "(not coded)"})
        for entry, ids in zip(sp["defences"], mt):
            if not ids:
                dis.append({"report": rid, "unit": "second pass", "field": "defence set", "first": "(not coded)", "second": entry["name"]})
        res = {r["id"]: r for r in rec.get("results") or []}
        n_ok = 0
        for v in sp.get("values") or []:
            r = res.get(v["result"])
            if r is None:
                raise ValueError(f"{rid}: value card {v['result']!r} is not a first-pass result")
            ok = values_agree(r["value"], v["value"])
            n_ok += ok
            vals.append(ok)
            if not ok:
                dis.append({"report": rid, "unit": v["result"], "field": "value", "first": r["value"], "second": v["value"]})
        per_report.append({"report": rid, "first_defences": len(dfs), "second_entries": n_entries,
                           "matched_entries": n_matched_entries, "unmatched_first_groups": len(groups),
                           "defence_set_jaccard": round(j, 3), "values": len(sp.get("values") or []), "values_agree": n_ok})
    rows = []

    def add(ftype, field, n, exact=None, kappa=None, jac=None):
        ok = True
        if exact is not None and exact < EXACT_MIN:
            ok = False
        if kappa is not None and kappa < KAPPA_MIN:
            ok = False
        if jac is not None and jac < JACCARD_MIN:
            ok = False
        rows.append({"field_type": ftype, "field": field, "pairs": n,
                     "exact_agreement": "" if exact is None else round(exact, 3),
                     "kappa": "" if kappa is None else round(kappa, 3),
                     "mean_jaccard": "" if jac is None else round(jac, 3),
                     "meets_threshold": "yes" if ok else "no", "action": "none" if ok else "re-code this field in full"})
    for f, pairs in cat.items():
        add("categorical", f, len(pairs), sum(a == b for a, b in pairs) / len(pairs), cohen_kappa(pairs))
    allc = [p for ps in cat.values() for p in ps]
    add("categorical (pooled)", "all categorical fields", len(allc), sum(a == b for a, b in allc) / len(allc), cohen_kappa(allc))
    rows[-1]["action"] = "summary row (the rule applies field by field)"
    for f, js in multi.items():
        add("multi-label", f, len(js), sum(multi_exact[f]) / len(js), None, sum(js) / len(js))
    add("multi-label", "defence set (method level, per report)", len(set_j), None, None, sum(set_j) / len(set_j))
    add("numeric", "printed values re-read from their addresses", len(vals), sum(vals) / len(vals) if vals else 0)
    return rows, per_report, dis


# ---------------------------------------------------------------- 04r: applying a listed re-code, and the amended rules as checks
CHANGE_FIELDS = ["report", "unit", "field", "old", "new", "reason", "page"]
LIST_FIELDS = {"axis1", "axis2", "also_quantity"}
PROMPT_OR_RULE = {"prompting", "fixed_inference_rule"}


def encode(v) -> str:
    """One cell for a field value: lists joined by ';', absent as ''."""
    if v is None:
        return ""
    return ";".join(str(x) for x in v) if isinstance(v, list) else str(v)


def _decode(field: str, s: str):
    if s == "":
        return None
    if field.split(".")[-1] in LIST_FIELDS:
        return s.split(";")
    if field.startswith("pages."):
        return int(s)
    return s


def _target(rec: dict, unit: str) -> dict:
    if unit in ("report", "coverage"):
        return rec[unit]
    kind, _, rid = unit.partition(":")
    for row in rec.get(kind) or []:
        if row.get("id") == rid:
            return row
    raise KeyError(unit)


def field_value(rec: dict, unit: str, field: str):
    obj = _target(rec, unit)
    if "." in field:
        a, b = field.split(".", 1)
        return (obj.get(a) or {}).get(b)
    return obj.get(field)


def apply_changes(records: dict, rows: list[dict]) -> list[str]:
    """Applies listed changes in place. A row whose old value is not the value on file is refused, so a change list
    built from other files than the committed ones cannot be applied by mistake."""
    problems = []
    for r in rows:
        rec = records.get(r["report"])
        if rec is None:
            problems.append(f"{r['report']}: no such record")
            continue
        try:
            obj = _target(rec, r["unit"])
        except KeyError:
            problems.append(f"{r['report']}:{r['unit']}: no such unit")
            continue
        cur = encode(field_value(rec, r["unit"], r["field"]))
        if cur != r["old"]:
            problems.append(f"{r['report']}:{r['unit']}:{r['field']} is {cur!r} on file, the change list expects {r['old']!r}")
            continue
        new = _decode(r["field"], r["new"])
        if "." in r["field"]:
            a, b = r["field"].split(".", 1)
            sub = obj.get(a) or {}
            if new is None:
                sub.pop(b, None)
            else:
                sub[b] = new
            if sub:
                obj[a] = sub
            else:
                obj.pop(a, None)
        elif new is None:
            obj.pop(r["field"], None)
        else:
            obj[r["field"]] = new
    return problems


def rule_problems(rec: dict) -> list[str]:
    """Amended rules 8, 9 and 32 (coding_rules.md, Amendment 2) checked on one record."""
    out = []
    has_none = any(str(e.get("defence_id", "")).startswith("none:") for e in rec.get("evaluations") or [])
    for d in rec.get("defences") or []:
        a1, sig = d["axis1"], d["signal_dependence"]
        trained = not set(d["axis2"]) <= PROMPT_OR_RULE
        tag = f"defences:{d['id']}"
        if "no_signal" in a1 and len(a1) > 1:
            out.append(f"{tag}: no_signal combined with another axis 1 value")
        if (a1 == ["no_signal"]) != (sig == "not_applicable"):
            out.append(f"{tag}: axis 1 {encode(a1)} with signal_dependence {sig} (not_applicable exactly when axis 1 is no_signal)")
        if trained and sig == "baseline_only":
            out.append(f"{tag}: baseline_only on a trained defence")
        if not trained and sig == "stated":
            out.append(f"{tag}: stated on a prompting defence or fixed rule (measured, baseline_only or not_reported)")
        if sig == "baseline_only" and not has_none:
            out.append(f"{tag}: baseline_only but the report has no undefended evaluation")
        if sig == "measured_other_checkpoint" and not d.get("signal_dependence_detail"):
            out.append(f"{tag}: measured_other_checkpoint without signal_dependence_detail naming the checkpoint")
        if d["origin"] == "other_report" and d["isolation"] == "no_ablation":
            out.append(f"{tag}: no_ablation on another report's defence (not_applicable unless this report ablates it)")
    cov = rec.get("coverage") or {}
    for q in ("R1", "R3ns", "R3cp", "R3safe"):
        rs = [x for x in rec.get("results") or [] if x.get("quantity") == q or q in (x.get("also_quantity") or [])]
        if cov.get(q) in ("direct", "proxy") and not rs:
            out.append(f"coverage {q} is {cov.get(q)} but no result carries {q}")
        if cov.get(q) in ("not_reported", "not_applicable") and rs:
            out.append(f"coverage {q} is {cov.get(q)} but {len(rs)} results carry {q}")
        main = [x["coverage"] for x in rs if x.get("quantity") == q]
        if main and len(main) == len(rs) and cov.get(q) in ("direct", "proxy"):
            best = "direct" if "direct" in main else "proxy"
            if best != cov.get(q):
                out.append(f"coverage {q} is {cov.get(q)} but the best result coded for it is {best}")
    return out
