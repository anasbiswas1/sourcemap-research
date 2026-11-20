"""Overlap assessment forms for the closest reviews, and the decision rule of gate G1."""
from __future__ import annotations

from pathlib import Path

import yaml

ANSWER_VALUES = {"yes", "partial", "no", "unknown"}
TEXT_FIELDS = ["scope", "corpus_cutoff", "organising_dimensions", "treatment_user_task", "treatment_document_handling",
               "treatment_comparability", "evidence_granularity", "what_this_review_adds"]
ANSWER_FIELDS = ["a_source_axis", "b_three_jobs_together", "c_equal_layout_rule"]
QUESTIONS = {
    "a_source_axis": "organises defences by where the model is given the instruction's source",
    "b_three_jobs_together": "reports security, the user's task and document handling together",
    "c_equal_layout_rule": "states or applies a rule that numbers are comparable only in the same prompt layout",
}


def blank_form(record_id: str, title: str, kind: str) -> dict:
    form = {"id": record_id, "title": title, "kind": kind}
    for f in TEXT_FIELDS:
        form[f] = ""
    for f in ANSWER_FIELDS:
        form[f] = "unknown"
    form["pages"] = {"a": "", "b": "", "c": ""}
    form["read_basis"] = ""
    form["confirmed_from_pdf"] = False
    form["pdf_sha256"] = ""
    return form


def write_form_if_missing(path: Path, form: dict) -> bool:
    path = Path(path)
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(form, sort_keys=False, allow_unicode=True, width=110))
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
    return "SUPPORTED", ["no confirmed form answers yes to any of the three questions"]


def render_markdown(forms: list[dict], outcome: str, reasons: list[str], when: str) -> str:
    lines = [f"# Overlap assessment (gate G1), {when}", "", f"Outcome: **{outcome}**", ""]
    lines += [f"- {r}" for r in reasons] + [""]
    lines += ["| id | kind | a: source axis | b: three jobs | c: layout rule | confirmed | read basis |",
              "|---|---|---|---|---|---|---|"]
    for f in forms:
        lines.append(f"| {f.get('id')} | {f.get('kind')} | {f.get('a_source_axis')} | {f.get('b_three_jobs_together')} | "
                     f"{f.get('c_equal_layout_rule')} | {'yes' if f.get('confirmed_from_pdf') else 'no'} | {f.get('read_basis')} |")
    lines.append("")
    for f in forms:
        lines += [f"## {f.get('id')}: {f.get('title')}", ""]
        for field in TEXT_FIELDS:
            lines.append(f"- **{field.replace('_', ' ')}**: {f.get(field, '')}")
        pages = f.get("pages") or {}
        lines.append(f"- **pages**: a {pages.get('a', '')}; b {pages.get('b', '')}; c {pages.get('c', '')}")
        lines.append("")
    return "\n".join(lines)
