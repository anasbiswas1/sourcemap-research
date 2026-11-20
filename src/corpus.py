"""Candidate records, arXiv metadata, PDF downloads and hashes for the survey corpus."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
USER_AGENT = "sourcemap-research corpus builder"
OFFLINE = os.environ.get("SOURCEMAP_OFFLINE") == "1"
REQUEST_GAP_SECONDS = 3.0

CANDIDATE_FIELDS = ["id", "kind", "title", "first_author", "arxiv", "doi", "venue", "first_date", "access", "pdf_url",
                    "origin", "closest", "arxiv_title", "arxiv_published", "arxiv_updated", "arxiv_latest_version",
                    "arxiv_journal_ref", "arxiv_doi", "linked_to"]
SURVEY_FIELDS = CANDIDATE_FIELDS + ["pdf_path", "pdf_status", "sha256", "pages"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def page_count(path: Path):
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(path)).pages)
    except Exception:
        return None


def normalise_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def read_csv(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def link_versions(rows: list[dict]) -> list[dict]:
    """Mark records that share a normalised title or a DOI as versions of one study (linked_to = the first id)."""
    seen_title: dict[str, str] = {}
    seen_doi: dict[str, str] = {}
    for row in rows:
        key_t = normalise_title(row.get("title", ""))
        key_d = (row.get("doi") or "").lower().strip()
        first = seen_title.get(key_t) or (seen_doi.get(key_d) if key_d else None)
        root = first if first and first != row["id"] else row["id"]
        row["linked_to"] = "" if root == row["id"] else root
        seen_title.setdefault(key_t, root)
        if key_d:
            seen_doi.setdefault(key_d, root)
    return rows


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_arxiv_feed(xml_bytes: bytes) -> dict:
    """Entries of an arXiv API Atom feed keyed by the versionless arXiv id."""
    out = {}
    root = ET.fromstring(xml_bytes)
    for entry in root.findall("a:entry", ATOM):
        full_id = (entry.findtext("a:id", default="", namespaces=ATOM) or "").rsplit("/", 1)[-1]
        m = re.match(r"(.+?)v(\d+)$", full_id)
        base, version = (m.group(1), int(m.group(2))) if m else (full_id, None)
        if not base:
            continue
        out[base] = {
            "title": " ".join((entry.findtext("a:title", default="", namespaces=ATOM) or "").split()),
            "published": (entry.findtext("a:published", default="", namespaces=ATOM) or "")[:10],
            "updated": (entry.findtext("a:updated", default="", namespaces=ATOM) or "")[:10],
            "latest_version": version,
            "authors": [a.findtext("a:name", default="", namespaces=ATOM) for a in entry.findall("a:author", ATOM)],
            "journal_ref": entry.findtext("arxiv:journal_ref", default="", namespaces=ATOM) or "",
            "doi": entry.findtext("arxiv:doi", default="", namespaces=ATOM) or "",
            "comment": entry.findtext("arxiv:comment", default="", namespaces=ATOM) or "",
        }
    return out


def fetch_arxiv_metadata(ids: list[str], cache_path: Path, batch: int = 40) -> dict:
    """Title, dates, latest version, journal reference and DOI for each arXiv id, cached as JSON."""
    cache_path = Path(cache_path)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    missing = [i for i in ids if i and i not in cache]
    if OFFLINE or not missing:
        return cache
    for start in range(0, len(missing), batch):
        chunk = missing[start:start + batch]
        url = f"{ARXIV_API}?id_list={','.join(chunk)}&max_results={len(chunk)}"
        try:
            cache.update(parse_arxiv_feed(_get(url)))
        except (urllib.error.URLError, ET.ParseError, OSError) as exc:
            print("arXiv API request failed:", exc)
            break
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
        time.sleep(REQUEST_GAP_SECONDS)
    return cache


def download_pdf(url: str, dest: Path) -> str:
    """Download to dest; returns 'downloaded', 'present', 'offline' or 'failed: <reason>'."""
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 1000:
        return "present"
    if OFFLINE:
        return "offline"
    try:
        data = _get(url, timeout=120)
    except Exception as exc:  # network and HTTP errors alike are reported, not raised
        return f"failed: {exc}"
    if not data.startswith(b"%PDF"):
        return "failed: response is not a PDF"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    time.sleep(REQUEST_GAP_SECONDS)
    return "downloaded"


def pdf_url_for(row: dict) -> str:
    if row.get("arxiv"):
        version = row.get("arxiv_latest_version") or ""
        return f"https://arxiv.org/pdf/{row['arxiv']}" + (f"v{version}" if version else "")
    return row.get("pdf_url") or ""
