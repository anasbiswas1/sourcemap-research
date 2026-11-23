"""The analyses of plan v2 A7 over the re-coded records: the map, signal dependence, layout compatibility, coverage
(by paper, by configuration, jointly, original and by anyone), the metric crosswalk, claim support, supported
orderings, stress-test coverage and the suppression cost per security point.

Notebook 05 writes this module. Nothing here calls a model or the network. Every row keeps the record ids it was
counted from, so every number in the findings can be traced to its records."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

QUANTITIES = ["R1", "R2clean", "R2attack", "R3ns", "R3cp", "R3safe"]
AXIS1 = ["chat_roles", "delimiters_markers", "encodings", "learned_token_features", "fixed_embedding_transform", "position",
         "internal_intervention", "no_signal"]
AXIS2 = ["prompting", "soft_tokens_frozen", "sft", "preference_optimisation", "distillation", "adversarial_rl", "fixed_inference_rule"]
LAYOUTS = ["user_turn", "separate_role", "system_context", "agent_tool_result"]
PROMPT_OR_RULE = {"prompting", "fixed_inference_rule"}
STRESS = {"adaptive", "optimisation", "rl", "human"}
SIG_ORDER = ["measured", "measured_other_checkpoint", "stated", "baseline_only", "not_reported", "not_applicable"]
GRADE_ORDER = ["A", "B", "C", "U"]

# method families: other papers' runs of a method are linked to it by name (first rule that matches wins)
FAMILY_RULES = [
    (r"meta[\s-]*sec\s*align|metasec\b|secalign\s*\+\+", "Meta-SecAlign"),
    (r"\bsec\s*align\b", "SecAlign"),
    (r"\bstruq\b", "StruQ"),
    (r"defensive\s*tokens?", "DefensiveTokens"),
    (r"spotlight", "Spotlighting"),
    (r"sandwich|repeat\w*\s+(the\s+)?(user('s)?\s+)?(prompt|instruction)|\brup\b", "Sandwich (instruction repeated after the data)"),
    (r"instruction\s+hierarchy", "Instruction Hierarchy"),
    (r"^reminder\b|explicit reminder", "Reminder prompt"),
    (r"instructional|instruction\s+defen[cs]e", "Instructional prompt"),
    (r"\bise\b", "ISE"), (r"\baside\b", "ASIDE"), (r"jatmo", "Jatmo"), (r"\bdrip\b", "DRIP"), (r"secopd", "SecOPD"),
    (r"verih", "VerIH"), (r"\breta\b", "RETA"), (r"agentalign", "AgentAlign"), (r"reasalign", "ReasAlign"),
    (r"polymorphic\s+prompt|\bppa\b", "Polymorphic Prompt Assembling"), (r"\bfath\b", "FATH"),
]


def stem(name: str) -> str:
    """The method's name without trailing parentheses: 'ACT (activation consistency training)' -> 'ACT'."""
    s = name.strip()
    while True:
        t = re.sub(r"\s*\([^()]*\)\s*$", "", s).strip()
        if t == s or not t:
            return s
        s = t


NOT_A_FAMILY = r"\s\+\s|\binto\b|hardened|guardrail with|white-box defence"   # a new method built on a named one is its own


def family(name: str) -> str | None:
    """The named method family, or None when the name matches no rule (a generic name is never linked across reports)."""
    n = name.lower()
    if re.search(NOT_A_FAMILY, n):
        return None
    for pat, fam in FAMILY_RULES:
        if re.search(pat, n):
            return fam
    return None


def trained(d: dict) -> bool:
    return not set(d["axis2"]) <= PROMPT_OR_RULE


def family_key(d: dict, rid: str) -> str:
    """Records of the same named family and the same kind (trained, or prompting and fixed rules) share a key across
    reports; any other method keeps a key of its own report."""
    fam = family(d["name"])
    kind = "trained" if trained(d) else "prompting or rule"
    return f"{fam} | {kind}" if fam else f"{rid} | {stem(d['name'])} | {kind}"


def _num(v) -> float | None:
    m = re.match(r"\s*([-+]?\d*\.?\d+)", str(v or ""))
    return float(m.group(1)) if m else None


def as_percent(r: dict) -> float | None:
    """A rate on the 0 to 100 scale, or None when the unit is not a rate."""
    x = _num(r.get("value"))
    if x is None:
        return None
    if r.get("unit") == "percent":
        return x
    if r.get("unit") == "fraction":
        return 100 * x
    return None


def _results_by_eval(rec):
    out = defaultdict(list)
    for r in rec.get("results") or []:
        out[r["evaluation_id"]].append(r)
    return out


def _quantities(r: dict) -> list[tuple[str, str]]:
    """(quantity, coverage) pairs a result speaks to; a second quantity in also_quantity counts as a proxy."""
    out = [(r["quantity"], r["coverage"])]
    out += [(q, "proxy") for q in r.get("also_quantity") or [] if q != r["quantity"]]
    return out


# ---------------------------------------------------------------- methods and the map (A7.1)
# reports whose own records are one method under several names (training recipes, schedules, channels, strengths, a
# scale study, or variants the paper presents as one defence); every main record of the report joins one method
MERGE_REPORTS = {"air_arxiv2025": "AIR", "guardrag_uwthesis2026": "GuardRAG with SAGE-C", "gwdpo_arxiv2026": "GW-DPO",
                 "secpo_arxiv2026": "SecPO", "tracer_emnlp2026": "TRACER", "trustmi_arxiv2026": "trust steering",
                 "spotlighting_arxiv2024": "Spotlighting"}

def methods(records: dict) -> list[dict]:
    """A method is a defence a report runs as its own (origin this_report, not a variant or control record), on any
    number of base checkpoints. Its records are the base-checkpoint records of the same name."""
    groups = defaultdict(list)
    for rid, rec in records.items():
        for d in rec.get("defences") or []:
            if d["origin"] == "this_report" and d["isolation"] != "not_applicable":
                groups[(rid, MERGE_REPORTS.get(rid) or stem(d["name"]))].append(d)
    out = []
    for (rid, name), ds in sorted(groups.items()):
        rep = records[rid]["report"]
        a1 = sorted({a for d in ds for a in d["axis1"]}, key=AXIS1.index)
        a2 = sorted({b for d in ds for b in d["axis2"]}, key=AXIS2.index)
        sig = min((d["signal_dependence"] for d in ds), key=SIG_ORDER.index)
        lc = {}
        for lay in LAYOUTS:
            vals = {(d.get("layout_compat") or {}).get(lay, "untested") for d in ds}
            lc[lay] = "supported" if "supported" in vals else ("unsupported" if "unsupported" in vals else "untested")
        out.append({"method_uid": f"{rid}:{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}", "report": rid, "name": name,
                    "family": family(name) or "", "year": str(rep_year(rep)), "role": rep["role"], "axis1": ";".join(a1),
                    "axis2": ";".join(a2), "trained": "yes" if any(trained(d) for d in ds) else "no",
                    "base_records": len(ds), "isolation": ds[0]["isolation"], "signal_dependence": sig,
                    "signal_dependence_detail": next((d.get("signal_dependence_detail") for d in ds
                                                      if d["signal_dependence"] == sig and d.get("signal_dependence_detail")), ""),
                    "released_weights": "yes" if any(d.get("released_weights") for d in ds) else "no",
                    **{f"layout_{k}": v for k, v in lc.items()},
                    "defence_uids": ";".join(f"{rid}:{d['id']}" for d in ds)})
    return out


def rep_year(rep: dict) -> int:
    return int(str(rep.get("first_date", "0000"))[:4] or 0)


def map_table(meths: list[dict]) -> list[dict]:
    """Methods per cell of the map (axis 1 by axis 2), by year; a two-cell method counts in each of its cells."""
    years = sorted({m["year"] for m in meths})
    rows = []
    for a in AXIS1:
        for b in AXIS2:
            ms = [m for m in meths if a in m["axis1"].split(";") and b in m["axis2"].split(";")]
            rows.append({"axis1": a, "axis2": b, "methods": len(ms), "reports": len({m["report"] for m in ms}),
                         **{f"methods_{y}": sum(m["year"] == y for m in ms) for y in years},
                         "released_weights": sum(m["released_weights"] == "yes" for m in ms),
                         "method_uids": ";".join(m["method_uid"] for m in ms)})
    return rows


# ---------------------------------------------------------------- coverage (A7.2)
def configuration_coverage(records: dict) -> list[dict]:
    """By evaluated configuration: for every defence record, the best coverage of each quantity in its own report's
    evaluations, and whether one evaluation scores the jobs jointly on the same replies."""
    rows = []
    for rid, rec in sorted(records.items()):
        by_eval = _results_by_eval(rec)
        evs = defaultdict(list)
        for e in rec.get("evaluations") or []:
            evs[e["defence_id"]].append(e)
        for d in rec.get("defences") or []:
            best, joint3, joint12 = {}, [], []
            for e in evs.get(d["id"], []):
                qs = {}
                for r in by_eval.get(e["id"], []):
                    for q, c in _quantities(r):
                        if q in QUANTITIES:
                            qs[q] = "direct" if "direct" in (qs.get(q), c) else "proxy"
                for q, c in qs.items():
                    best[q] = "direct" if "direct" in (best.get(q), c) else "proxy"
                has3 = any(q.startswith("R3") for q in qs)
                if "R3safe" in qs or ("R1" in qs and "R2attack" in qs and has3):
                    joint3.append(e["id"])
                if "R1" in qs and "R2attack" in qs:
                    joint12.append(e["id"])
            rows.append({"defence_uid": f"{rid}:{d['id']}", "report": rid, "name": d["name"], "origin": d["origin"],
                         "family_key": family_key(d, rid), **{q: best.get(q, "none") for q in QUANTITIES},
                         "joint_all_three": "yes" if joint3 else "no", "joint_R1_R2attack": "yes" if joint12 else "no",
                         "joint_evaluations": ";".join(f"{rid}:{x}" for x in joint3)})
    return rows


def family_coverage(records: dict, cfg_rows: list[dict], meths: list[dict]) -> list[dict]:
    """Original measurement against measurement by anyone: per method family proposed in the corpus, which quantities
    its own report covers and which any report in the corpus covers for the same family."""
    by_fam = defaultdict(list)
    for r in cfg_rows:
        by_fam[r["family_key"]].append(r)
    rows = []
    mkey = {m["method_uid"]: family_key({"name": m["name"], "axis2": m["axis2"].split(";")}, m["report"]) for m in meths}
    for fk in sorted(set(mkey.values())):
        if not fk.split(" | ")[0] in {f for _, f in FAMILY_RULES}:
            continue                                    # only named families can be measured by others
        own_reports = {m["report"] for m in meths if mkey[m["method_uid"]] == fk}
        rs = by_fam.get(fk, [])
        own = [r for r in rs if r["report"] in own_reports and r["origin"] == "this_report"]
        other = [r for r in rs if r["report"] not in own_reports]
        row = {"family_key": fk, "proposing_reports": ";".join(sorted(own_reports)),
               "reports_measuring_it_later": ";".join(sorted({r["report"] for r in other}))}
        for q in QUANTITIES:
            row[f"{q}_original"] = "yes" if any(r[q] != "none" for r in own) else "no"
            row[f"{q}_anyone"] = "yes" if any(r[q] != "none" for r in rs) else "no"
        rows.append(row)
    return rows


# ---------------------------------------------------------------- metric crosswalk (A7.2)
BENCH_RULES = [(r"agentdojo|agentdyn", "AgentDojo or AgentDyn"), (r"injecagent", "InjecAgent"), (r"\bsep\b", "SEP"),
               (r"alpaca\s*eval", "AlpacaEval"), (r"alpaca\s*farm", "AlpacaFarm"), (r"bipia", "BIPIA"),
               (r"\bmmlu\b", "MMLU"), (r"\basb\b|agent security bench", "ASB"), (r"wasp", "WASP"),
               (r"open\s*prompt\s*injection|\bopi\b", "OpenPromptInjection"), (r"tasktracker", "TaskTracker"),
               (r"piarena", "PIArena"), (r"cyberseceval", "CyberSecEval"), (r"llmail", "LLMail-Inject"),
               (r"tensor\s*trust", "TensorTrust"), (r"squad", "SQuAD-based"), (r"gsm8k", "GSM8K"),
               (r"natural questions|\bnq\b|hotpot|realtime\s*qa|triviaqa", "Open-domain QA sets"),
               (r"secfid", "SecFid"), (r"mind2web", "Mind2Web")]
JUDGE_RULES = [(r"not (stated|named|described|detailed)|judge not", "not stated"),
               (r"\bhuman\b|raters", "human raters"),
               (r"gpt|claude|gemini|llama|qwen|deepseek|llm|judge|win rate|grader|rubric|evaluator", "model judge"),
               (r"string|substring|literal|starts with|begins with|contains only|keyword|regex|appears in (the )?(response|reply|output)"
                r"|phrase in the response|hacked|uuid|exact|signature|contains the answer|answer changes|target option|\bterm\b|outputs the",
                "string or answer match"),
               (r"checker|checks|check\b|environment|state|tool|function|call|parser|executable|probe|verifier|validator|\bapi\b"
                r"|send_email|exfiltrat|executes", "programmatic checker"),
               (r"accuracy|label|gold|answer key|reference|f1|gleu|rouge|metric|scor|rating", "reference metric"),
               (r"goal|success|rule|protocol|criteri|compliance|elicited|attack|desired|carries out|as ev_", "success rule given, judge not named")]
CANNOT_SEE = {
    "R1": {"string or answer match": "cannot tell an executed injection (E) from a quoted or translated one (Rp); blind to P and S",
           "model judge": "counts E as the judge's prompt defines it; blind to P and S unless scored separately",
           "programmatic checker": "sees the actions or state the attacker wanted, not what the reply says; blind to P and S",
           "reference metric": "counts a wrong answer as attack success whatever caused it; blind to Rp, P and S",
           "not stated": "the rule that counts E is not given",
           "human raters": "counts E as the raters judged it; blind to P and S unless scored separately",
           "success rule given, judge not named": "the success rule is stated, but not whether a string, a model or a person applied it",
           "unclassified": "the record's judge text does not say how E is counted"},
    "R2clean": "no injection in the data: blind to E, Rp and to the user's task under attack",
    "R2attack": "counts P under attack; blind to whether the injection was also executed unless paired with R1 on the same replies",
    "R3ns": "counts S (text dropped); blind to E",
    "R3cp": "counts correct handling of the asked-for content; blind to E unless scored jointly",
    "R3safe": "counts P and not E on the same replies (joint)",
    "general_utility": "not the user's task on the document: blind to E, Rp, P under attack and S",
    "other": "not mapped onto the outcome codes",
}
COUNTS = {"R1": "E (as 1 - Pr[E])", "R2clean": "P on clean data", "R2attack": "P under attack", "R3ns": "S (as 1 - Pr[S])",
          "R3cp": "P restricted to the asked-for content", "R3safe": "P and not E", "general_utility": "none of E, Rp, P, S, F",
          "other": "not mapped"}


def classify(text: str, rules) -> str:
    t = (text or "").lower()
    for pat, lab in rules:
        if re.search(pat, t):
            return lab
    return "the report's own set" if rules is BENCH_RULES else "unclassified"


def crosswalk(records: dict) -> list[dict]:
    groups = defaultdict(lambda: {"results": 0, "reports": set(), "metrics": Counter(), "ids": []})
    for rid, rec in records.items():
        evs = {e["id"]: e for e in rec.get("evaluations") or []}
        for r in rec.get("results") or []:
            e = evs.get(r["evaluation_id"], {})
            judge = classify(e.get("judge", ""), JUDGE_RULES)
            key = (classify(e.get("benchmark", ""), BENCH_RULES), r["quantity"], judge)
            g = groups[key]
            g["results"] += 1
            g["reports"].add(rid)
            g["metrics"][r["metric_as_printed"]] += 1
            g["ids"].append(f"{rid}:{r['id']}")
    rows = []
    for (bench, q, judge), g in sorted(groups.items(), key=lambda kv: (-kv[1]["results"], kv[0])):
        cs = CANNOT_SEE[q]
        rows.append({"benchmark_family": bench, "quantity": q, "judge_rule": judge, "outcome_counted": COUNTS[q],
                     "cannot_see": cs.get(judge, cs["unclassified"]) if isinstance(cs, dict) else cs,
                     "results": g["results"], "reports": len(g["reports"]),
                     "metric_names": "; ".join(f"{m} ({n})" for m, n in g["metrics"].most_common(5)),
                     "result_uids": ";".join(g["ids"])})
    return rows


# ---------------------------------------------------------------- claim support and orderings (A7.3)
def claim_support(records: dict, grade) -> list[dict]:
    rows = []
    for rid, rec in sorted(records.items()):
        comps = {c["id"]: c for c in rec.get("comparisons") or []}
        by_eval = _results_by_eval(rec)
        for k in rec.get("claims") or []:
            sup = [comps[c] for c in k.get("supported_by") or [] if c in comps]
            grades = Counter(grade(c) for c in sup)
            best = next((g for g in GRADE_ORDER if grades[g]), "none")
            qs = {q for c in sup for side in ("left", "right") for r in by_eval.get(c[side], []) for q, _ in _quantities(r)}
            jobs = k["jobs"]
            utility = ""
            if "R2" in jobs or "general_utility" in jobs:
                utility = ("R2 results" if qs & {"R2clean", "R2attack"} else
                           "general utility only" if "general_utility" in qs else "no utility result in its comparisons")
            rows.append({"claim_uid": f"{rid}:{k['id']}", "report": rid, "role": rec["report"]["role"], "location": k["location"],
                         "jobs": ";".join(jobs), "supporting_comparisons": len(sup),
                         **{f"grade_{g}": grades[g] for g in GRADE_ORDER},
                         "purposes": ";".join(sorted({c["purpose"] for c in sup})), "best_grade": best,
                         "contradicted_by": len(k.get("contradicted_by") or []), "utility_basis": utility,
                         "quantities_in_support": ";".join(q for q in QUANTITIES + ["general_utility", "other"] if q in qs),
                         "text": k["text"]})
    return rows


def orderings(records: dict, grade) -> list[dict]:
    """Supported orderings: grade-A comparisons between two defended arms inside one report. Cross-report readings
    (purpose X) are listed with their grade; the review states an ordering only inside a grade-A set."""
    rows = []
    for rid, rec in sorted(records.items()):
        evs = {e["id"]: e for e in rec.get("evaluations") or []}
        names = {d["id"]: d["name"] for d in rec.get("defences") or []}
        by_eval = _results_by_eval(rec)
        for c in rec.get("comparisons") or []:
            l, r = evs.get(c["left"], {}), evs.get(c["right"], {})
            ld, rd = str(l.get("defence_id", "")), str(r.get("defence_id", ""))
            if c["purpose"] != "X" and (ld.startswith("none:") or rd.startswith("none:")):
                continue
            pairs = [(a, b) for a in by_eval.get(c["left"], []) for b in by_eval.get(c["right"], [])
                     if a["quantity"] == b["quantity"] and a["metric_as_printed"] == b["metric_as_printed"]
                     and a.get("unit") == b.get("unit") and _num(a.get("value")) is not None and _num(b.get("value")) is not None]
            rows.append({"comparison_uid": f"{rid}:{c['id']}", "report": rid, "purpose": c["purpose"], "grade": grade(c),
                         "left_arm": names.get(ld, ld), "right_arm": names.get(rd, rd), "varies": c.get("varies", ""),
                         "paired_results": len(pairs),
                         "result_pairs": ";".join(f"{rid}:{a['id']}|{rid}:{b['id']}" for a, b in pairs)})
    return rows


# ---------------------------------------------------------------- stress tests (A7.4)
def stress_tests(records: dict, meths: list[dict]) -> list[dict]:
    """Per method: the attackers its configurations faced, in its own report and in later reports of the same family."""
    later = defaultdict(list)
    for rid, rec in records.items():
        dk = {d["id"]: family_key(d, rid) for d in rec.get("defences") or []}
        for e in rec.get("evaluations") or []:
            if e["defence_id"] in dk:
                later[dk[e["defence_id"]]].append((rid, e))
    rows = []
    for m in meths:
        fk = family_key({"name": m["name"], "axis2": m["axis2"].split(";")}, m["report"])
        own_ids = {u.split(":", 1)[1] for u in m["defence_uids"].split(";")}
        own = [e for e in records[m["report"]].get("evaluations") or [] if e["defence_id"] in own_ids]
        out = [(rid, e) for rid, e in later.get(fk, []) if rid != m["report"]]
        def kinds(es):
            return sorted({e["attacker_type"] for e in es if e["attacker_type"] in STRESS})
        rows.append({"method_uid": m["method_uid"], "axis1": m["axis1"], "axis2": m["axis2"], "trained": m["trained"], "family": m["family"],
                     "own_static": sum(e["attacker_type"] == "static" for e in own),
                     "own_stress_attackers": ";".join(kinds(own)),
                     "own_white_box": sum(e["attacker_access"] == "white_box" for e in own),
                     "signal_removal_run": "yes" if m["signal_dependence"] in ("measured", "measured_other_checkpoint") else "no",
                     "later_reports": ";".join(sorted({rid for rid, _ in out})),
                     "later_stress_attackers": ";".join(kinds([e for _, e in out])),
                     "later_white_box": sum(e["attacker_access"] == "white_box" for _, e in out),
                     "pushed_hard": "yes" if kinds(own) or kinds([e for _, e in out]) else "no"})
    return rows


# ---------------------------------------------------------------- suppression cost per security point (A7.5)
def scs_pairs(records: dict, grade) -> list[dict]:
    """SCS = (R3ns undefended - R3ns defended) / (R1 defended - R1 undefended), from one grade-A comparison of a
    defended and the undefended evaluation that both carry an R1 and an R3ns rate. Rates on the 0 to 100 scale;
    a rate printed as 'lower is better' (attack success, ignored rate) is turned into R1 or R3ns as 100 minus it."""
    def rate(rs, q):
        for r in rs:
            if q in [x for x, _ in _quantities(r)]:
                v = as_percent(r)
                if v is not None:
                    return (100 - v if r.get("direction") == "lower_better" else v), r
        return None, None
    rows = []
    for rid, rec in sorted(records.items()):
        evs = {e["id"]: e for e in rec.get("evaluations") or []}
        by_eval = _results_by_eval(rec)
        names = {d["id"]: d["name"] for d in rec.get("defences") or []}
        for c in rec.get("comparisons") or []:
            if grade(c) != "A":
                continue
            sides = {s: evs.get(c[s], {}) for s in ("left", "right")}
            und = [s for s, e in sides.items() if str(e.get("defence_id", "")).startswith("none:")]
            if len(und) != 1:
                continue
            u = und[0]
            dsd = "right" if u == "left" else "left"
            r1d, xr1d = rate(by_eval[c[dsd]], "R1")
            r1u, xr1u = rate(by_eval[c[u]], "R1")
            r3d, xr3d = rate(by_eval[c[dsd]], "R3ns")
            r3u, xr3u = rate(by_eval[c[u]], "R3ns")
            if None in (r1d, r1u, r3d, r3u) or r1d == r1u:
                continue
            rows.append({"comparison_uid": f"{rid}:{c['id']}", "report": rid,
                         "defence": names.get(sides[dsd]["defence_id"], sides[dsd]["defence_id"]),
                         "base": sides[u]["defence_id"][5:], "R1_defended": round(r1d, 1), "R1_undefended": round(r1u, 1),
                         "R3ns_defended": round(r3d, 1), "R3ns_undefended": round(r3u, 1),
                         "SCS": round((r3u - r3d) / (r1d - r1u), 2),
                         "result_uids": ";".join(f"{rid}:{x['id']}" for x in (xr1d, xr1u, xr3d, xr3u))})
    return rows
