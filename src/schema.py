"""Record schema: load it, validate record files against it and against the PDFs they cite, grade comparisons."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

CONDITIONS = ["c1_base", "c2_layout", "c3_benchmark", "c4_attacker", "c5_judge", "c6_decoding"]


class _Loader(yaml.SafeLoader):
    """YAML loader that reads only true/false as booleans, so the enum words yes and no stay words (YAML 1.1 would
    silently turn yes, no, on and off into booleans)."""


_Loader.yaml_implicit_resolvers = {k: [r for r in v if r[0] != "tag:yaml.org,2002:bool"]
                                   for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
_Loader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
                              list("tTfF"))


def load_yaml(path: Path):
    return yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_Loader)


def load_schema(path: Path) -> dict:
    return load_yaml(path)


def load_record(path: Path) -> dict:
    return load_yaml(path) or {}


def norm_text(s: str) -> str:
    """Lower-case alphanumerics only (the same rule as the overlap and full-text anchor checks)."""
    s = unicodedata.normalize("NFKC", s or "").replace("­", "")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def norm_value(s: str) -> str:
    """A printed number as it can be searched for: NFKC, unicode minus as hyphen, runs of whitespace as one space."""
    s = unicodedata.normalize("NFKC", str(s)).replace("\u2212", "-").replace("\u2013", "-")
    return re.sub(r"\s+", " ", s).strip()


def value_on_page(value: str, page_text: str) -> bool:
    """True when the printed value appears on the page as a number of its own (not inside a longer number).
    A space before % is allowed (3.10% matches 3.10 %); a trailing % may sit in a table header instead."""
    v = norm_value(value).replace(" ", "")
    t = norm_value(page_text)
    if not v:
        return False
    pat = re.escape(v).replace("%", r"\s?%")
    if re.search(rf"(?<![\d.]){pat}(?![\d])", t):
        return True
    if v.endswith("%"):
        core = re.escape(v[:-1])
        return bool(re.search(rf"(?<![\d.]){core}(?![\d])", t))
    return False


def grade(comp: dict) -> str:
    """Plan v2 equation (4): A if every condition is matched or is the one declared manipulated variable; U if any
    condition is unreported; B if exactly one is unmatched; C if two or more are unmatched. For a whole-configuration
    (W) comparison the layout may differ by design and is left out of the grade. "matched_unstated" (both arms ran in
    one harness but the value is not printed) counts as matched inside one report and as unreported in a cross-report
    (X) comparison, where the reader cannot know it was the same."""
    conds = [c for c in CONDITIONS if not (comp.get("purpose") == "W" and c == "c2_layout")]
    vals = [comp.get(c) for c in conds]
    if comp.get("purpose") == "X":
        vals = ["unreported" if v == "matched_unstated" else v for v in vals]
    if "unreported" in vals:
        return "U"
    if vals.count("manipulated") > 1:
        return "C"
    n = vals.count("unmatched")
    return "A" if n == 0 else "B" if n == 1 else "C"


def _check_field(kind: str, rid: str, name: str, spec: dict, val, out: list[str]) -> None:
    t = spec.get("type")
    where = f"{kind}:{rid}:{name}"
    if t == "enum" and val not in spec["values"]:
        out.append(f"{where}: {val!r} is not one of {spec['values']}")
    elif t == "enum_list":
        if not isinstance(val, list) or not val:
            out.append(f"{where}: needs a non-empty list")
        else:
            out += [f"{where}: {v!r} is not one of {spec['values']}" for v in val if v not in spec["values"]]
    elif t == "map":
        if not isinstance(val, dict):
            out.append(f"{where}: needs a mapping")
        else:
            for k, v in val.items():
                if k not in spec["keys"]:
                    out.append(f"{where}: key {k!r} is not one of {spec['keys']}")
                elif v not in spec["values"]:
                    out.append(f"{where}.{k}: {v!r} is not one of {spec['values']}")
    elif t == "pages":
        if not isinstance(val, dict) or not all(isinstance(v, int) and v >= 1 for v in val.values()):
            out.append(f"{where}: needs a mapping of field names to positive page numbers")
    elif t == "map_free" and not isinstance(val, dict):
        out.append(f"{where}: needs a mapping")
    elif t == "page" and not (isinstance(val, int) and val >= 1):
        out.append(f"{where}: page must be a positive integer")
    elif t == "int" and not isinstance(val, int):
        out.append(f"{where}: must be an integer")
    elif t == "list" and not isinstance(val, list):
        out.append(f"{where}: must be a list")
    elif t == "str" and not isinstance(val, (str, int, float)):
        out.append(f"{where}: must be text")


def validate_record(rec: dict, schema: dict, page_texts: list[str] | None = None,
                    page_layouts: list[str] | None = None) -> tuple[list[str], list[str]]:
    """Return (problems, notes). Problems break the schema or fail a check against the PDF; notes are free-text
    workarounds the coder recorded in schema_gaps. page_texts are the plain text of each PDF page (anchors are found
    there); page_layouts, when given, are the same pages extracted with column spacing kept, so that numbers in table
    rows are not glued together (values are looked for in either)."""
    problems: list[str] = []
    kinds = schema["kinds"]
    for k in rec:
        if k not in kinds:
            problems.append(f"unknown record kind: {k}")
    ids: dict[str, set] = {}
    for kind, kspec in kinds.items():
        fields = kspec["fields"]
        items = rec.get(kind)
        if items is None:
            if kind in ("report", "coverage", "defences"):
                problems.append(f"missing record kind: {kind}")
            continue
        rows = [items] if kspec.get("one") else items
        if not isinstance(rows, list):
            problems.append(f"{kind}: must be a list")
            continue
        seen = ids.setdefault(kind, set())
        for row in rows:
            if not isinstance(row, dict):
                problems.append(f"{kind}: every entry must be a mapping")
                continue
            rid = str(row.get("id", kind))
            if "id" in fields and rid in seen:
                problems.append(f"{kind}:{rid}: duplicate id")
            seen.add(rid)
            for name in row:
                if name not in fields:
                    problems.append(f"{kind}:{rid}: unknown field {name!r}")
            for name, spec in fields.items():
                if name not in row or row[name] in (None, ""):
                    if spec.get("required"):
                        problems.append(f"{kind}:{rid}: missing required field {name!r}")
                    continue
                _check_field(kind, rid, name, spec, row[name], problems)
            needs_page = any(spec.get("from_paper") and name in row for name, spec in fields.items())
            page = row.get("page")
            if needs_page and "page" in fields and not isinstance(page, int):
                problems.append(f"{kind}:{rid}: fields read from the paper need a page")
            if page_texts is not None and isinstance(page, int):
                if page > len(page_texts):
                    problems.append(f"{kind}:{rid}: page {page} is beyond the PDF's {len(page_texts)} pages")
                else:
                    text = page_texts[page - 1]
                    lay = page_layouts[page - 1] if page_layouts else ""
                    if kind == "results" and row.get("value_source") != "figure_only":
                        if row.get("value") in (None, ""):
                            problems.append(f"{kind}:{rid}: a printed result needs its value")
                        elif not (value_on_page(row["value"], text) or value_on_page(row["value"], lay)):
                            problems.append(f"{kind}:{rid}: value {row['value']!r} not found on page {page}")
                    if row.get("anchor") and len(str(row["anchor"]).split()) > 14:
                        problems.append(f"{kind}:{rid}: anchor is longer than 14 words; keep it a short phrase")
                    if row.get("anchor") and norm_text(row["anchor"]) not in norm_text(text):
                        nxt = page_texts[page] if page < len(page_texts) else ""
                        if norm_text(row["anchor"]) not in norm_text(text + nxt):
                            problems.append(f"{kind}:{rid}: anchor not found on page {page}")
            if page_texts is not None and isinstance(row.get("pages"), dict):
                for fld, pg in row["pages"].items():
                    if isinstance(pg, int) and pg > len(page_texts):
                        problems.append(f"{kind}:{rid}: pages.{fld} = {pg} is beyond the PDF's {len(page_texts)} pages")
    rep_id = (rec.get("report") or {}).get("id")
    defence_ids = ids.get("defences", set())
    eval_ids = ids.get("evaluations", set())
    for ev in rec.get("evaluations") or []:
        d = str(ev.get("defence_id", ""))
        if not d.startswith("none:") and d not in defence_ids and ":" not in d:
            problems.append(f"evaluations:{ev.get('id')}: defence_id {d!r} is not a defence in this file")
        mb = ev.get("measured_by")
        if mb and mb != rep_id and not str(mb).endswith("_ext"):
            pass                                            # another report's id: checked across files in notebook 04
    for r in rec.get("results") or []:
        if r.get("evaluation_id") not in eval_ids:
            problems.append(f"results:{r.get('id')}: evaluation_id {r.get('evaluation_id')!r} is not in this file")
    comp_ids = ids.get("comparisons", set())
    for c in rec.get("comparisons") or []:
        for side in ("left", "right"):
            if c.get(side) not in eval_ids:
                problems.append(f"comparisons:{c.get('id')}: {side} {c.get(side)!r} is not an evaluation in this file")
        if c.get("purpose") == "M" and [c.get(x) for x in CONDITIONS].count("manipulated") > 1:
            problems.append(f"comparisons:{c.get('id')}: a mechanism comparison can manipulate at most one condition")
    for k in rec.get("claims") or []:
        for s in k.get("supported_by") or []:
            if s not in comp_ids:
                problems.append(f"claims:{k.get('id')}: supported_by {s!r} is not a comparison in this file")
    res_ids = ids.get("results", set())
    for k in rec.get("claims") or []:
        for r_ in k.get("contradicted_by") or []:
            if r_ not in res_ids:
                problems.append(f"claims:{k.get('id')}: contradicted_by {r_!r} is not a result in this file")
    for ev in rec.get("evaluations") or []:
        sc = ev.get("same_checkpoint_as")
        if sc and ":" not in str(sc):
            problems.append(f"evaluations:{ev.get('id')}: same_checkpoint_as must read <report_id>:<defence_id>")
    notes = [f"{g.get('where')}: {g.get('note')}" for g in rec.get("schema_gaps") or []]
    return problems, notes
