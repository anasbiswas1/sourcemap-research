"""Overlap assessment forms for the closest reviews, their verification against the PDFs, and gate G1."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import yaml

ANSWER_VALUES = {"yes", "partial", "no", "unknown"}
TEXT_FIELDS = ["scope", "corpus_cutoff", "organising_dimensions", "treatment_user_task", "treatment_document_handling",
               "treatment_comparability", "evidence_granularity", "what_this_review_adds"]
ANSWER_FIELDS = ["a_source_axis", "b_three_jobs_together", "c_equal_layout_rule"]
QUESTIONS = {
    "a_source_axis": "organises defences by how the model is shown where the instruction came from",
    "b_three_jobs_together": "reports security, the user's task and document handling together, per defence",
    "c_equal_layout_rule": "states or applies a rule that numbers are comparable only in the same prompt layout",
}
GRADING = {
    "a_source_axis": {
        "yes": "an axis whose values are forms of the source signal (chat roles, delimiters or markers, encodings, "
               "learned tokens or embeddings, position, no signal)",
        "partial": "defences are grouped by where they act or where the attack enters (a stage, level or component "
                   "axis), or signal forms appear as scattered categories but not as one axis",
        "no": "neither",
    },
    "b_three_jobs_together": {
        "yes": "security, the user's task and the handling of the document content reported together per defence",
        "partial": "two of the three reported together per defence, or their joint reporting measured as coverage",
        "no": "security alone, or utility discussed in prose or recommended but not extracted per defence",
    },
    "c_equal_layout_rule": {
        "yes": "the prompt layout (template, roles, delimiters) is named as a condition for comparing numbers",
        "partial": "a comparability condition or reporting standard is stated or applied (model, benchmark, attacker, "
                   "judge, decoding) but the layout is not among its items, or the layout is named only as a "
                   "reporting item",
        "no": "no comparability condition",
    },
}


def blank_form(record_id: str, title: str, kind: str) -> dict:
    form = {"id": record_id, "title": title, "kind": kind}
    for f in TEXT_FIELDS:
        form[f] = ""
    for f in ANSWER_FIELDS:
        form[f] = "unknown"
    form["pages"] = {"a": "", "b": "", "c": ""}
    form["anchors"] = {"a": "", "b": "", "c": ""}
    form["page_basis"] = "PDF page index, 1-based, of the file in data/surveys/"
    form["read_basis"] = ""
    form["confirmed_from_pdf"] = False
    form["pdf_sha256"] = ""
    form["verification"] = ""
    return form


def write_form(path: Path, form: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = {k: v for k, v in form.items() if not k.startswith("_")}
    path.write_text(yaml.safe_dump(clean, sort_keys=False, allow_unicode=True, width=110))


def write_form_if_missing(path: Path, form: dict) -> bool:
    if Path(path).exists():
        return False
    write_form(path, form)
    return True


def load_forms(folder: Path) -> list[dict]:
    forms = []
    for path in sorted(Path(folder).glob("*.yaml")):
        form = yaml.safe_load(path.read_text()) or {}
        form["_path"] = str(path)
        forms.append(form)
    return forms


def validate(form: dict) -> list[str]:
    problems = []
    for f in ["id", "title", "kind", "read_basis"]:
        if not form.get(f):
            problems.append(f"{f} missing")
    for f in TEXT_FIELDS:
        if not str(form.get(f, "")).strip():
            problems.append(f"{f} empty")
    for f in ANSWER_FIELDS:
        if form.get(f) not in ANSWER_VALUES:
            problems.append(f"{f} must be one of {sorted(ANSWER_VALUES)}")
    if form.get("confirmed_from_pdf"):
        if not form.get("pdf_sha256"):
            problems.append("confirmed_from_pdf is true but pdf_sha256 is empty")
        for key, f in zip("abc", ANSWER_FIELDS):
            if form.get(f) in {"yes", "partial"} and not str((form.get("pages") or {}).get(key, "")).strip():
                problems.append(f"{f} is {form.get(f)} but pages.{key} is empty")
        if any(form.get(f) == "unknown" for f in ANSWER_FIELDS):
            problems.append("confirmed_from_pdf is true but an answer is still unknown")
    return problems


# ---- verification against the PDF on disk -------------------------------------------------------------------

def norm_text(s: str) -> str:
    """Lower-case alphanumerics only, so spacing, hyphenation, ligatures and punctuation cannot break a match."""
    s = unicodedata.normalize("NFKC", s or "").replace("­", "")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def pdf_page_texts(path: Path) -> list[str]:
    from pypdf import PdfReader
    return [norm_text(page.extract_text() or "") for page in PdfReader(str(path)).pages]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_form(form: dict, pdf_path: Path, page_texts: list[str] | None = None) -> dict:
    """Locate each anchor phrase in the PDF, correct the page to where it was found, and set confirmed_from_pdf.

    An anchor is a short phrase copied from the paper. A question with an empty anchor is not checked; one whose
    anchor is not found leaves the form unconfirmed. Page numbers are PDF page indices (1-based).
    """
    pdf_path = Path(pdf_path)
    notes = []
    if not pdf_path.exists():
        form["confirmed_from_pdf"] = False
        form["verification"] = "PDF missing"
        return form
    texts = page_texts if page_texts is not None else pdf_page_texts(pdf_path)
    form.setdefault("pages", {}); form.setdefault("anchors", {})
    all_found = True
    for key in "abc":
        anchor = (form["anchors"] or {}).get(key, "")
        if not anchor:
            continue
        hits = [i + 1 for i, t in enumerate(texts) if norm_text(anchor) in t]
        straddle = ""
        if not hits:                                   # a phrase can run over a page break; try adjacent pages
            hits = [i + 1 for i in range(len(texts) - 1) if norm_text(anchor) in texts[i] + texts[i + 1]]
            straddle = " (runs over the page break)" if hits else ""
        stated = str(form["pages"].get(key, "")).strip()
        if not hits:
            all_found = False
            notes.append(f"{key}: anchor not found")
            continue
        if stated and stated.isdigit() and int(stated) in hits:
            notes.append(f"{key}: p.{stated} ok{straddle}")
        else:
            notes.append(f"{key}: p.{stated or '?'} -> p.{hits[0]}" + (f" (also {hits[1:]})" if len(hits) > 1 else "") + straddle)
            form["pages"][key] = str(hits[0])
    form["pdf_sha256"] = sha256_of(pdf_path)
    form["pdf_pages"] = len(texts)
    form["confirmed_from_pdf"] = all_found
    form["verification"] = "; ".join(notes) if notes else "no anchors to check"
    return form


# ---- gate G1 ---------------------------------------------------------------------------------------------------

def decide(forms: list[dict]) -> tuple[str, list[str]]:
    """UNRESOLVED if any form is unconfirmed or invalid; NARROW if any confirmed form answers yes; else SUPPORTED."""
    reasons = []
    unconfirmed = [f["id"] for f in forms if not f.get("confirmed_from_pdf")]
    invalid = {f["id"]: validate(f) for f in forms}
    invalid = {k: v for k, v in invalid.items() if v}
    if invalid:
        reasons += [f"{k}: {'; '.join(v)}" for k, v in invalid.items()]
    if unconfirmed:
        reasons.append("not yet confirmed from the PDF: " + ", ".join(unconfirmed))
    if invalid or unconfirmed:
        return "UNRESOLVED", reasons
    narrow = []
    for f in forms:
        for field in ANSWER_FIELDS:
            if f.get(field) == "yes":
                narrow.append(f"{f['id']} answers yes to {field} ({QUESTIONS[field]}); that claim must be narrowed or dropped")
    if narrow:
        return "NARROW", narrow
    partials = [f"{f['id']} ({', '.join(k for k in ANSWER_FIELDS if f.get(k) == 'partial')})"
                for f in forms if any(f.get(k) == "partial" for k in ANSWER_FIELDS)]
    reasons = ["no confirmed form answers yes to any of the three questions"]
    if partials:
        reasons.append("partial overlaps to be named in the related-work table: " + "; ".join(partials))
    return "SUPPORTED", reasons


def render_markdown(forms: list[dict], outcome: str, reasons: list[str], when: str) -> str:
    lines = [f"# Overlap assessment (gate G1), {when}", "", f"Outcome: **{outcome}**", ""]
    lines += [f"- {r}" for r in reasons] + [""]
    lines += ["## How the three questions were graded", ""]
    for field in ANSWER_FIELDS:
        lines.append(f"**{field}**: {QUESTIONS[field]}.")
        for value in ("yes", "partial", "no"):
            lines.append(f"- {value}: {GRADING[field][value]}")
        lines.append("")
    lines += ["Pages are 1-based page indices of the PDF in `data/surveys/`; each page was located by searching the PDF "
              "text for the anchor phrase recorded in the form (`verification` field).", ""]
    lines += ["| id | kind | a: source axis | b: three jobs | c: layout rule | pages a / b / c | confirmed | read basis |",
              "|---|---|---|---|---|---|---|---|"]
    for f in forms:
        p = f.get("pages") or {}
        lines.append(f"| {f.get('id')} | {f.get('kind')} | {f.get('a_source_axis')} | {f.get('b_three_jobs_together')} | "
                     f"{f.get('c_equal_layout_rule')} | {p.get('a', '')} / {p.get('b', '')} / {p.get('c', '')} | "
                     f"{'yes' if f.get('confirmed_from_pdf') else 'no'} | {f.get('read_basis')} |")
    lines.append("")
    for f in forms:
        lines += [f"## {f.get('id')}: {f.get('title')}", ""]
        for field in TEXT_FIELDS:
            lines.append(f"- **{field.replace('_', ' ')}**: {f.get(field, '')}")
        anchors = f.get("anchors") or {}
        pages = f.get("pages") or {}
        for key, field in zip("abc", ANSWER_FIELDS):
            if anchors.get(key):
                lines.append(f"- **{field}** = {f.get(field)}; p.{pages.get(key, '')}: \"{anchors.get(key)}\"")
            else:
                lines.append(f"- **{field}** = {f.get(field)}; no passage to point to")
        lines.append(f"- **verification**: {f.get('verification', '')}; sha256 {str(f.get('pdf_sha256', ''))[:12]}")
        lines.append("")
    return "\n".join(lines)
