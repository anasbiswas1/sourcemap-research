"""Systematic search for defence papers: arXiv, OpenAlex and DBLP by API, exported record files, citation lists."""
from __future__ import annotations

import csv
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ARXIV_API = os.environ.get("SOURCEMAP_ARXIV_API", "https://export.arxiv.org/api/query")      # overridable for dry runs
OPENALEX_API = os.environ.get("SOURCEMAP_OPENALEX_API", "https://api.openalex.org/works")
DBLP_API = os.environ.get("SOURCEMAP_DBLP_API", "https://dblp.org/search/publ/api")
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
USER_AGENT = "Mozilla/5.0 (compatible; sourcemap-research literature search; +https://github.com/anasbiswas1/sourcemap-research)"
OFFLINE = os.environ.get("SOURCEMAP_OFFLINE") == "1"
GAP = 3.0                      # seconds between requests to one service
ARXIV_CATS = ["cs.CR", "cs.CL", "cs.LG", "cs.AI"]
ARXIV_ID_RE = re.compile(r"(?<![\d.])((?:2[3-6])(?:0[1-9]|1[0-2])\.\d{4,5})(?:v\d+)?(?!\d)")   # 2301.xxxxx to 2612.xxxxx

EXCLUSION_REASONS = ["detector only", "system level", "attack only", "benchmark only", "jailbreak or direct injection only",
                     "survey, position or other", "duplicate version", "out of period", "no full text obtainable",
                     "not about prompt injection"]
DECISIONS = {"include", "exclude", "unsure"}

RECORD_FIELDS = ["key", "title", "first_author", "year", "date", "venue", "arxiv", "arxiv_version", "doi", "abstract",
                 "sources", "queries", "n_hits", "linked_to"]
SCREEN_FIELDS = RECORD_FIELDS + ["decision", "reason", "access_status", "note"]
LOG_FIELDS = ["date", "source", "query_id", "query_as_sent", "fields", "filters", "count", "status", "file"]


# ---- small helpers ------------------------------------------------------------------------------------------

def norm_title(title: str) -> str:
    s = unicodedata.normalize("NFKC", title or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def norm_key(title: str) -> str:
    return re.sub(r"\s+", "", norm_title(title))[:90]


def _get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def read_csv(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fieldnames})


def arxiv_id_from_text(s: str) -> str:
    m = ARXIV_ID_RE.search(s or "")
    return m.group(1) if m else ""


# ---- arXiv --------------------------------------------------------------------------------------------------

def arxiv_query_string(must: list[str], date_from: str, date_to: str, cats: list[str] = ARXIV_CATS, field: str = "abs") -> str:
    """must: phrases or words that must all appear in the abstract; dates as YYYYMMDD."""
    parts = []
    for term in must:
        term = term.strip()
        parts.append(f'{field}:"{term}"' if " " in term or "-" in term else f"{field}:{term}")
    cat = " OR ".join(f"cat:{c}" for c in cats)
    return " AND ".join(parts) + f" AND ({cat}) AND submittedDate:[{date_from}0000 TO {date_to}2359]"


def parse_arxiv_feed(xml_bytes: bytes) -> tuple[list[dict], int]:
    """Records of an arXiv API feed and the feed's total-results count."""
    root = ET.fromstring(xml_bytes)
    total = int(root.findtext("os:totalResults", default="0", namespaces=ATOM) or 0)
    out = []
    for e in root.findall("a:entry", ATOM):
        full = (e.findtext("a:id", default="", namespaces=ATOM) or "").rsplit("/", 1)[-1]
        m = re.match(r"(.+?)v(\d+)$", full)
        base, version = (m.group(1), int(m.group(2))) if m else (full, "")
        if not base:
            continue
        authors = [a.findtext("a:name", default="", namespaces=ATOM) for a in e.findall("a:author", ATOM)]
        out.append({
            "arxiv": base, "arxiv_version": version,
            "title": " ".join((e.findtext("a:title", default="", namespaces=ATOM) or "").split()),
            "abstract": " ".join((e.findtext("a:summary", default="", namespaces=ATOM) or "").split()),
            "date": (e.findtext("a:published", default="", namespaces=ATOM) or "")[:10],
            "updated": (e.findtext("a:updated", default="", namespaces=ATOM) or "")[:10],
            "first_author": authors[0] if authors else "", "authors": authors,
            "primary_category": (e.find("arxiv:primary_category", ATOM).get("term") if e.find("arxiv:primary_category", ATOM) is not None else ""),
            "journal_ref": e.findtext("arxiv:journal_ref", default="", namespaces=ATOM) or "",
            "doi": (e.findtext("arxiv:doi", default="", namespaces=ATOM) or "").lower(),
            "venue": e.findtext("arxiv:journal_ref", default="", namespaces=ATOM) or "arXiv",
        })
    return out, total


def arxiv_search(query: str, max_total: int = 3000, page: int = 200, fetch=None) -> tuple[list[dict], str]:
    """All records for an arXiv API search_query, paged; returns (records, status)."""
    if OFFLINE and fetch is None:
        return [], "offline"
    fetch = fetch or _get
    records, start, total = [], 0, None
    while True:
        url = f"{ARXIV_API}?search_query={urllib.parse.quote(query)}&start={start}&max_results={page}&sortBy=submittedDate&sortOrder=descending"
        try:
            batch, total = parse_arxiv_feed(fetch(url))
        except (urllib.error.URLError, ET.ParseError, OSError) as exc:
            return records, f"failed at start={start}: {exc}"
        records.extend(batch)
        start += page
        if not batch or start >= min(total, max_total):
            break
        time.sleep(GAP)
    return records, "ok"


# ---- OpenAlex -----------------------------------------------------------------------------------------------

def abstract_from_inverted(index: dict | None) -> str:
    if not index:
        return ""
    positions = []
    for word, places in index.items():
        for p in places:
            positions.append((p, word))
    return " ".join(w for _, w in sorted(positions))


def parse_openalex_page(payload: dict) -> list[dict]:
    out = []
    for w in payload.get("results", []):
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        arxiv = ""
        if doi.startswith("10.48550/arxiv."):
            arxiv = doi.split("arxiv.", 1)[1]
        for loc in w.get("locations") or []:
            for u in (loc.get("landing_page_url") or "", loc.get("pdf_url") or ""):
                if not arxiv and "arxiv.org" in u:
                    arxiv = arxiv_id_from_text(u)
        src = (w.get("primary_location") or {}).get("source") or {}
        authors = [(a.get("author") or {}).get("display_name", "") for a in w.get("authorships") or []]
        out.append({
            "openalex": (w.get("id") or "").rsplit("/", 1)[-1],
            "title": " ".join((w.get("title") or w.get("display_name") or "").split()),
            "abstract": abstract_from_inverted(w.get("abstract_inverted_index")),
            "year": w.get("publication_year") or "", "date": w.get("publication_date") or "",
            "venue": src.get("display_name") or "", "type": w.get("type") or "",
            "doi": "" if doi.startswith("10.48550/arxiv.") else doi, "arxiv": arxiv,
            "first_author": authors[0] if authors else "", "authors": authors,
        })
    return out


def openalex_search(text: str, date_from: str, api_key: str = "", max_total: int = 5000, fetch=None) -> tuple[list[dict], str, str]:
    """Title-and-abstract search, page by page (OpenAlex allows up to 10,000 results this way).

    Since February 2026 OpenAlex requires an API key for more than a first page; without one the first page is
    returned and the status says so. The key is never written to the log: the URL is logged without it."""
    first_url = ""
    if OFFLINE and fetch is None:
        return [], "offline", first_url
    fetch = fetch or _get
    records, page, total = [], 1, None
    flt = f"title_and_abstract.search:{text},from_publication_date:{date_from}"
    while True:
        base = (f"{OPENALEX_API}?filter={urllib.parse.quote(flt, safe=':,')}&per-page=100&page={page}"
                f"&select=id,doi,title,display_name,publication_year,publication_date,type,primary_location,locations,authorships,abstract_inverted_index")
        first_url = first_url or base
        url = base + (f"&api_key={api_key}" if api_key else "")
        try:
            payload = json.loads(fetch(url))
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and page > 1:
                return records, f"first page only: a page {page} request was refused (401); an API key is needed for more", first_url
            return records, f"failed after {len(records)}: HTTP Error {exc.code}", first_url
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
            return records, f"failed after {len(records)}: {exc}", first_url
        results = payload.get("results") or []
        records.extend(parse_openalex_page(payload))
        total = int((payload.get("meta") or {}).get("count") or 0)
        if not results or len(records) >= min(total, max_total):
            break
        if not api_key:
            return records, f"first page only ({len(records)} of {total}): no OpenAlex API key in .secrets/openalex_key.txt", first_url
        page += 1
        time.sleep(1.0)
    return records, "ok", first_url


# ---- DBLP ---------------------------------------------------------------------------------------------------

def parse_dblp_page(payload: dict) -> list[dict]:
    out = []
    hits = ((payload.get("result") or {}).get("hits") or {}).get("hit") or []
    for h in hits:
        info = h.get("info") or {}
        authors = info.get("authors", {}).get("author", []) if isinstance(info.get("authors"), dict) else []
        if isinstance(authors, dict):
            authors = [authors]
        names = [a.get("text", "") if isinstance(a, dict) else str(a) for a in authors]
        ee = info.get("ee") or ""
        out.append({
            "dblp": info.get("key", ""), "title": " ".join((info.get("title") or "").rstrip(".").split()),
            "year": info.get("year", ""), "date": "", "venue": info.get("venue", "") if isinstance(info.get("venue"), str) else " / ".join(info.get("venue") or []),
            "doi": (info.get("doi") or "").lower(), "arxiv": arxiv_id_from_text(ee) if "arxiv" in ee.lower() else "",
            "type": info.get("type", ""), "first_author": names[0] if names else "", "authors": names, "abstract": "",
        })
    return out


def dblp_search(text: str, max_total: int = 3000, fetch=None) -> tuple[list[dict], str, str]:
    first_url = ""
    if OFFLINE and fetch is None:
        return [], "offline", first_url
    fetch = fetch or _get
    records, offset = [], 0
    while True:
        url = f"{DBLP_API}?q={urllib.parse.quote(text)}&h=1000&f={offset}&format=json"
        first_url = first_url or url
        body = b""
        for attempt in range(2):
            try:
                body = fetch(url)
                payload = json.loads(body)
                break
            except json.JSONDecodeError:
                snippet = body[:160].decode("utf-8", "ignore").replace("\n", " ")
                if attempt == 0:
                    time.sleep(10.0)
                    continue
                return records, f"failed after {len(records)}: response is not JSON: {snippet}", first_url
            except (urllib.error.URLError, OSError) as exc:
                if attempt == 0:
                    time.sleep(10.0)
                    continue
                return records, f"failed after {len(records)}: {exc}", first_url
        batch = parse_dblp_page(payload)
        records.extend(batch)
        total = int(((payload.get("result") or {}).get("hits") or {}).get("@total", 0) or 0)
        offset += 1000
        if not batch or offset >= min(total, max_total):
            break
        time.sleep(2.0)
    return records, "ok", first_url


# ---- exported record files (RIS, BibTeX, CSV) ------------------------------------------------------------------

def parse_ris(text: str) -> list[dict]:
    out, cur = [], {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            cur = {"authors": []}
        elif tag == "ER":
            if cur:
                out.append(_ris_record(cur))
            cur = {}
        elif tag in ("TI", "T1"):
            cur["title"] = val
        elif tag in ("AU", "A1"):
            cur["authors"].append(val)
        elif tag in ("PY", "Y1"):
            cur["year"] = val[:4]
        elif tag == "DO":
            cur["doi"] = val.lower().replace("https://doi.org/", "")
        elif tag in ("AB", "N2"):
            cur["abstract"] = (cur.get("abstract", "") + " " + val).strip()
        elif tag in ("JO", "T2", "JF", "BT"):
            cur.setdefault("venue", val)
        elif tag == "UR":
            cur.setdefault("url", val)
    return out


def _ris_record(cur: dict) -> dict:
    return {"title": cur.get("title", ""), "first_author": (cur.get("authors") or [""])[0], "authors": cur.get("authors", []),
            "year": cur.get("year", ""), "date": "", "venue": cur.get("venue", ""), "doi": cur.get("doi", ""),
            "arxiv": arxiv_id_from_text(cur.get("url", "")) if "arxiv" in cur.get("url", "") else "", "abstract": cur.get("abstract", "")}


def parse_bibtex(text: str) -> list[dict]:
    out = []
    for entry in re.split(r"\n@", "\n" + text)[1:]:
        fields = dict((k.lower(), re.sub(r"\s+", " ", v.strip().strip("{}\",")))
                      for k, v in re.findall(r"(\w+)\s*=\s*[{\"]((?:[^{}]|\{[^{}]*\})*)[}\"]", entry))
        authors = [a.strip() for a in re.split(r"\s+and\s+", fields.get("author", "")) if a.strip()]
        out.append({"title": fields.get("title", ""), "first_author": authors[0] if authors else "", "authors": authors,
                    "year": fields.get("year", ""), "date": "", "venue": fields.get("journal") or fields.get("booktitle") or "",
                    "doi": fields.get("doi", "").lower(), "arxiv": arxiv_id_from_text(fields.get("eprint", "") or fields.get("url", "")),
                    "abstract": fields.get("abstract", "")})
    return out


def parse_export_file(path: Path) -> list[dict]:
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".ris":
        return parse_ris(text)
    if path.suffix.lower() in (".bib", ".bibtex"):
        return parse_bibtex(text)
    if path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(text.splitlines()))
        out = []
        for r in rows:
            low = {k.lower().strip(): (v or "") for k, v in r.items() if k}
            title = low.get("title") or low.get("document title") or low.get("item title") or ""
            out.append({"title": title, "first_author": (low.get("authors") or low.get("author") or "").split(";")[0].strip(),
                        "year": (low.get("year") or low.get("publication year") or "")[:4], "date": "",
                        "venue": low.get("publication title") or low.get("source title") or low.get("venue") or "",
                        "doi": (low.get("doi") or "").lower(), "arxiv": arxiv_id_from_text(low.get("url", "") or low.get("pdf link", "")),
                        "abstract": low.get("abstract") or ""})
        return out
    return []


# ---- citation lists from PDFs ----------------------------------------------------------------------------------

def arxiv_ids_in_pdf(path: Path) -> list[str]:
    from pypdf import PdfReader
    text = " ".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    text = re.sub(r"\s+", " ", text)
    return sorted(set(m.group(1) for m in ARXIV_ID_RE.finditer(text)))


def arxiv_metadata_for_ids(ids: list[str], cache_path: Path, batch: int = 50, fetch=None) -> dict:
    cache_path = Path(cache_path)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    missing = [i for i in ids if i not in cache]
    if (OFFLINE and fetch is None) or not missing:
        return cache
    fetch = fetch or _get
    for s in range(0, len(missing), batch):
        chunk = missing[s:s + batch]
        url = f"{ARXIV_API}?id_list={','.join(chunk)}&max_results={len(chunk)}"
        try:
            recs, _ = parse_arxiv_feed(fetch(url))
        except (urllib.error.URLError, ET.ParseError, OSError) as exc:
            print("arXiv id_list request failed:", exc)
            break
        for r in recs:
            cache[r["arxiv"]] = r
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False))
        time.sleep(GAP)
    return cache


# ---- merging and screening ------------------------------------------------------------------------------------

def record_key(rec: dict) -> str:
    if rec.get("arxiv"):
        return f"arxiv:{rec['arxiv']}"
    if rec.get("doi"):
        return f"doi:{rec['doi']}"
    return f"title:{norm_key(rec.get('title', ''))}"


def merge_hits(hits: list[tuple[str, str, dict]]) -> list[dict]:
    """hits: (source, query_id, record). One row per key; sources and queries aggregated; preprint and published
    versions of one title linked through linked_to (the arXiv record is the root when present)."""
    merged: dict[str, dict] = {}
    for source, qid, rec in hits:
        key = record_key(rec)
        row = merged.get(key)
        if row is None:
            row = {"key": key, "title": rec.get("title", ""), "first_author": rec.get("first_author", ""),
                   "year": str(rec.get("year") or (rec.get("date") or "")[:4]), "date": rec.get("date", ""),
                   "venue": rec.get("venue", ""), "arxiv": rec.get("arxiv", ""), "arxiv_version": rec.get("arxiv_version", ""),
                   "doi": rec.get("doi", ""), "abstract": rec.get("abstract", ""), "_sources": set(), "_queries": set(),
                   "n_hits": 0, "linked_to": ""}
            merged[key] = row
        for f in ("title", "first_author", "venue", "doi", "abstract", "date", "arxiv_version"):
            if not row.get(f) and rec.get(f):
                row[f] = rec[f]
        if not row.get("year") and (rec.get("year") or rec.get("date")):
            row["year"] = str(rec.get("year") or rec["date"][:4])
        row["_sources"].add(source)
        row["_queries"].add(qid)
        row["n_hits"] += 1
    by_title: dict[str, str] = {}
    for key, row in merged.items():
        t = norm_key(row["title"])
        if not t:
            continue
        root = by_title.get(t)
        if root is None:
            by_title[t] = key
        else:
            # prefer the arXiv record as the root so the preprint and the published article count once
            if key.startswith("arxiv:") and not root.startswith("arxiv:"):
                merged[root]["linked_to"] = key
                by_title[t] = key
            else:
                row["linked_to"] = root
    rows = []
    for row in merged.values():
        row["sources"] = ";".join(sorted(row.pop("_sources")))
        row["queries"] = ";".join(sorted(row.pop("_queries")))
        rows.append(row)
    rows.sort(key=lambda r: (r["linked_to"] != "", -(r["n_hits"]), r["key"]))
    return rows


def apply_decisions(rows: list[dict], decisions: list[dict]) -> tuple[list[dict], list[str]]:
    """Attach decision, reason, access_status and note by key; report keys with invalid values or no match."""
    problems = []
    by_key = {d["key"]: d for d in decisions}
    for row in rows:
        d = by_key.get(row["key"], {})
        row["decision"] = d.get("decision", "pending")
        row["reason"] = d.get("reason", "")
        row["access_status"] = d.get("access_status", "")
        row["note"] = d.get("note", "")
        if d and d.get("decision") not in DECISIONS:
            problems.append(f"{row['key']}: decision must be one of {sorted(DECISIONS)}")
        if d.get("decision") == "exclude" and d.get("reason") not in EXCLUSION_REASONS:
            problems.append(f"{row['key']}: exclusion needs one reason from the fixed list")
    unknown = [k for k in by_key if k not in {r["key"] for r in rows}]
    problems += [f"decision for a key not in the screening table: {k}" for k in unknown]
    return rows, problems


def prisma_counts(log_rows: list[dict], rows: list[dict]) -> dict:
    per_source: dict[str, int] = {}
    for r in log_rows:
        if str(r.get("count", "")).isdigit():
            per_source[r["source"]] = per_source.get(r["source"], 0) + int(r["count"])
    roots = [r for r in rows if not r.get("linked_to")]
    out = {"records_identified_per_source": per_source,
           "records_identified_total": sum(per_source.values()),
           "unique_records_after_dedup": len(rows),
           "studies_after_version_linking": len(roots),
           "screened": sum(1 for r in roots if r.get("decision") not in ("", "pending", None)),
           "pending": sum(1 for r in roots if r.get("decision") in ("", "pending", None)),
           "included": sum(1 for r in roots if r.get("decision") == "include"),
           "unsure_to_full_text": sum(1 for r in roots if r.get("decision") == "unsure"),
           "excluded_by_reason": {}}
    for r in roots:
        if r.get("decision") == "exclude":
            out["excluded_by_reason"][r.get("reason", "")] = out["excluded_by_reason"].get(r.get("reason", ""), 0) + 1
    return out
