"""Parsers, merging and the screening-decision checks of the search module."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import search  # noqa: E402

ARXIV_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>2</opensearch:totalResults>
  <entry>
    <id>http://arxiv.org/abs/2402.06363v2</id>
    <published>2024-02-09T00:00:00Z</published><updated>2024-05-01T00:00:00Z</updated>
    <title>StruQ: Defending Against Prompt Injection
  with Structured Queries</title>
    <summary>We propose structured queries.</summary>
    <author><name>Sizhe Chen</name></author><author><name>Other Author</name></author>
    <arxiv:primary_category term="cs.CR"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2403.14720v1</id>
    <published>2024-03-21T00:00:00Z</published><updated>2024-03-21T00:00:00Z</updated>
    <title>Defending Against Indirect Prompt Injection Attacks With Spotlighting</title>
    <summary>Spotlighting.</summary>
    <author><name>Keegan Hines</name></author>
    <arxiv:journal_ref>Some venue 2024</arxiv:journal_ref>
    <arxiv:doi>10.1000/EXAMPLE</arxiv:doi>
  </entry>
</feed>"""

OPENALEX_PAGE = {
    "meta": {"next_cursor": None},
    "results": [
        {"id": "https://openalex.org/W1", "doi": "https://doi.org/10.48550/arXiv.2402.06363", "title": "StruQ: Defending Against Prompt Injection with Structured Queries",
         "publication_year": 2024, "publication_date": "2024-02-09", "type": "preprint",
         "primary_location": {"source": {"display_name": "arXiv (Cornell University)"}}, "locations": [],
         "authorships": [{"author": {"display_name": "Sizhe Chen"}}],
         "abstract_inverted_index": {"We": [0], "propose": [1], "structured": [2], "queries.": [3]}},
        {"id": "https://openalex.org/W2", "doi": "https://doi.org/10.1109/SP.2025.1", "title": "StruQ: Defending Against Prompt Injection with Structured Queries",
         "publication_year": 2025, "publication_date": "2025-05-01", "type": "article",
         "primary_location": {"source": {"display_name": "USENIX Security"}}, "locations": [{"landing_page_url": "https://www.usenix.org/x"}],
         "authorships": [{"author": {"display_name": "Sizhe Chen"}}], "abstract_inverted_index": None},
    ],
}

DBLP_PAGE = {"result": {"hits": {"@total": "1", "hit": [
    {"info": {"key": "conf/uss/Chen25", "title": "StruQ: Defending Against Prompt Injection with Structured Queries.",
              "venue": "USENIX Security Symposium", "year": "2025", "doi": "10.1109/SP.2025.1", "ee": "https://doi.org/10.1109/SP.2025.1",
              "type": "Conference and Workshop Papers", "authors": {"author": [{"text": "Sizhe Chen"}, {"text": "Other"}]}}}]}}}


def test_parse_arxiv_feed_reads_ids_versions_titles_and_total():
    recs, total = search.parse_arxiv_feed(ARXIV_FEED)
    assert total == 2 and [r["arxiv"] for r in recs] == ["2402.06363", "2403.14720"]
    assert recs[0]["arxiv_version"] == 2 and recs[0]["title"].endswith("with Structured Queries")
    assert recs[0]["first_author"] == "Sizhe Chen" and recs[0]["primary_category"] == "cs.CR"
    assert recs[1]["doi"] == "10.1000/example" and recs[1]["venue"] == "Some venue 2024"


def test_arxiv_query_string_quotes_phrases_and_adds_window():
    q = search.arxiv_query_string(["prompt injection", "defense"], "20230101", "20261120")
    assert q.startswith('abs:"prompt injection" AND abs:defense AND (cat:cs.CR OR cat:cs.CL OR cat:cs.LG OR cat:cs.AI)')
    assert q.endswith("submittedDate:[202301010000 TO 202611202359]")


def test_parse_openalex_page_recovers_arxiv_id_and_abstract():
    recs = search.parse_openalex_page(OPENALEX_PAGE)
    assert recs[0]["arxiv"] == "2402.06363" and recs[0]["doi"] == "" and recs[0]["abstract"] == "We propose structured queries."
    assert recs[1]["doi"] == "10.1109/sp.2025.1" and recs[1]["venue"] == "USENIX Security" and recs[1]["abstract"] == ""


def test_parse_dblp_page():
    recs = search.parse_dblp_page(DBLP_PAGE)
    assert recs[0]["title"] == "StruQ: Defending Against Prompt Injection with Structured Queries"
    assert recs[0]["doi"] == "10.1109/sp.2025.1" and recs[0]["first_author"] == "Sizhe Chen" and recs[0]["year"] == "2025"


def test_arxiv_id_regex_accepts_only_2023_to_2026_ids():
    assert search.arxiv_id_from_text("see arXiv:2402.06363v2 for details") == "2402.06363"
    assert search.arxiv_id_from_text("arXiv preprint arXiv:2106.09685") == ""
    assert search.arxiv_id_from_text("doi 10.1234/5678.91011") == ""


def test_merge_hits_dedupes_across_sources_and_links_versions():
    a, _ = search.parse_arxiv_feed(ARXIV_FEED)
    o = search.parse_openalex_page(OPENALEX_PAGE)
    d = search.parse_dblp_page(DBLP_PAGE)
    hits = [("arxiv", "q01", a[0]), ("arxiv", "q05", a[0]), ("arxiv", "q01", a[1]),
            ("openalex", "o01", o[0]), ("openalex", "o01", o[1]), ("dblp", "d01", d[0])]
    rows = search.merge_hits(hits)
    by_key = {r["key"]: r for r in rows}
    struq = by_key["arxiv:2402.06363"]
    assert struq["n_hits"] == 3 and struq["sources"] == "arxiv;openalex" and struq["queries"] == "o01;q01;q05"
    published = by_key["doi:10.1109/sp.2025.1"]
    assert published["linked_to"] == "arxiv:2402.06363" and published["sources"] == "dblp;openalex"
    assert by_key["arxiv:2403.14720"]["linked_to"] == ""
    assert rows[0]["linked_to"] == "" and rows[-1]["linked_to"] != ""


def test_apply_decisions_flags_bad_values_and_unknown_keys():
    rows = [{"key": "arxiv:1"}, {"key": "arxiv:2"}, {"key": "arxiv:3"}]
    decisions = [{"key": "arxiv:1", "decision": "include"}, {"key": "arxiv:2", "decision": "exclude", "reason": "made up"},
                 {"key": "arxiv:9", "decision": "exclude", "reason": "attack only"}]
    rows, problems = search.apply_decisions(rows, decisions)
    assert rows[0]["decision"] == "include" and rows[2]["decision"] == "pending"
    assert any("arxiv:2" in p for p in problems) and any("arxiv:9" in p for p in problems)


def test_prisma_counts():
    log = [{"source": "arxiv", "count": "10"}, {"source": "arxiv", "count": "5"}, {"source": "dblp", "count": "offline"}]
    rows = [{"key": "a", "linked_to": "", "decision": "include"}, {"key": "b", "linked_to": "a", "decision": "include"},
            {"key": "c", "linked_to": "", "decision": "exclude", "reason": "attack only"}, {"key": "d", "linked_to": "", "decision": "pending"}]
    c = search.prisma_counts(log, rows)
    assert c["records_identified_per_source"] == {"arxiv": 15} and c["unique_records_after_dedup"] == 4
    assert c["studies_after_version_linking"] == 3 and c["included"] == 1 and c["pending"] == 1
    assert c["excluded_by_reason"] == {"attack only": 1}


def test_parse_ris_and_bibtex():
    ris = "TY  - JOUR\nTI  - A Title\nAU  - Doe, J.\nAU  - Roe, R.\nPY  - 2025\nDO  - https://doi.org/10.1/ABC\nAB  - Part one.\nAB  - Part two.\nER  - \n"
    r = search.parse_ris(ris)[0]
    assert r["title"] == "A Title" and r["first_author"] == "Doe, J." and r["doi"] == "10.1/abc" and r["abstract"] == "Part one. Part two."
    bib = '@inproceedings{x,\n title={Another {Title}},\n author={Jane Doe and John Roe},\n year={2024},\n booktitle={Proc. X},\n eprint={2402.06363}\n}\n'
    b = search.parse_bibtex(bib)[0]
    assert b["first_author"] == "Jane Doe" and b["venue"] == "Proc. X" and b["arxiv"] == "2402.06363" and b["year"] == "2024"


def test_search_functions_report_failure_instead_of_raising():
    def boom(url, timeout=90):
        raise OSError("HTTP Error 503")
    recs, status = search.arxiv_search("abs:x", fetch=boom)
    assert recs == [] and status.startswith("failed")
    recs, status, _ = search.openalex_search("x", "2023-01-01", fetch=boom)
    assert recs == [] and status.startswith("failed")
    recs, status, _ = search.dblp_search("x", fetch=boom)
    assert recs == [] and status.startswith("failed")


def test_search_functions_parse_fixture_responses():
    calls = []
    def fake(url, timeout=90):
        calls.append(url)
        if url.startswith(search.ARXIV_API):
            return ARXIV_FEED
        if url.startswith(search.OPENALEX_API):
            return json.dumps(OPENALEX_PAGE).encode()
        return json.dumps(DBLP_PAGE).encode()
    recs, status = search.arxiv_search('abs:"prompt injection"', fetch=fake)
    assert status == "ok" and len(recs) == 2
    recs, status, url = search.openalex_search('"prompt injection"', "2023-01-01", api_key="k", fetch=fake)
    assert status == "ok" and len(recs) == 2 and "title_and_abstract.search" in url and "api_key" not in url
    recs, status, url = search.dblp_search("prompt injection", fetch=fake)
    assert status == "ok" and len(recs) == 1 and "format=json" in url


def test_openalex_without_key_stops_after_the_first_page_and_says_so():
    big = {"meta": {"count": 350}, "results": OPENALEX_PAGE["results"]}
    recs, status, _ = search.openalex_search("x", "2023-01-01", fetch=lambda url, timeout=90: json.dumps(big).encode())
    assert len(recs) == 2 and status.startswith("first page only") and "API key" in status


def test_openalex_401_on_a_later_page_is_reported_not_raised():
    import urllib.error
    big = {"meta": {"count": 350}, "results": OPENALEX_PAGE["results"]}
    def fake(url, timeout=90):
        if "page=1&" in url or url.endswith("page=1"):
            return json.dumps(big).encode()
        raise urllib.error.HTTPError(url, 401, "Unauthorized", None, None)
    recs, status, _ = search.openalex_search("x", "2023-01-01", api_key="bad", fetch=fake)
    assert len(recs) == 2 and "401" in status


def test_dblp_reports_non_json_body():
    search_gap = search.time.sleep
    search.time.sleep = lambda s: None
    try:
        recs, status, _ = search.dblp_search("x", fetch=lambda url, timeout=90: b"<html>Too Many Requests</html>")
    finally:
        search.time.sleep = search_gap
    assert recs == [] and "not JSON" in status and "Too Many Requests" in status


# ---- full-text retrieval -----------------------------------------------------------------------------------------

def test_pdf_slug_prefers_arxiv_then_doi_then_title():
    assert search.pdf_slug({"arxiv": "2402.06363", "doi": "10.1/x"}) == "2402.06363"
    assert search.pdf_slug({"doi": "10.1109/ICASSP55912.2026.11463282"}) == "doi_10_1109_icassp55912_2026_11463282"
    assert search.pdf_slug({"title": "Prompt Injection Defenses"}) == "title_promptinjectiondefenses"


def test_zenodo_payload_first_pdf_in_both_api_shapes():
    legacy = {"id": "20307701", "files": [{"key": "code.zip", "links": {}}, {"key": "paper v1.pdf", "links": {"self": "meta"}}, {"key": "b.pdf"}]}
    url, note = search.zenodo_pdf_from_payload(legacy)
    assert url == search.ZENODO_API + "/20307701/files/paper%20v1.pdf/content" and "first of 2 PDFs" in note
    rdm = {"id": "1", "files": {"entries": {"a.pdf": {"key": "a.pdf", "links": {"content": "https://zenodo.org/api/records/1/files/a.pdf/content"}}}}}
    assert search.zenodo_pdf_from_payload(rdm)[0].endswith("/files/a.pdf/content")
    url, note = search.zenodo_pdf_from_payload({"id": "2", "files": [{"key": "code.zip"}]})
    assert url == "" and "no PDF file" in note and "code.zip" in note


def test_figshare_and_openalex_payloads():
    assert search.figshare_pdf_from_payload({"files": [{"name": "r.pdf", "download_url": "https://nd/1"}]})[0] == "https://nd/1"
    assert search.figshare_pdf_from_payload({"files": [{"name": "r.csv"}]})[0] == ""
    work = {"best_oa_location": {"pdf_url": None}, "primary_location": {"pdf_url": "https://x/p.pdf"}}
    assert search.openalex_pdf_from_payload(work) == ("https://x/p.pdf", "openalex primary_location pdf_url")
    assert search.openalex_pdf_from_payload({"open_access": {"oa_url": "https://land"}})[0] == "https://land"
    assert search.openalex_pdf_from_payload({})[0] == ""


def test_resolve_pdf_url_dispatches_and_keeps_the_key_out_of_notes():
    calls = []

    def fetch(url):
        calls.append(url)
        if url.startswith(search.ZENODO_API):
            return json.dumps({"id": "5", "files": [{"key": "p.pdf"}]}).encode()
        if url.startswith(search.FIGSHARE_API):
            return json.dumps({"files": [{"name": "r.pdf", "download_url": "https://nd/1"}]}).encode()
        if "?search=" in url:
            return json.dumps({"results": [{"title": "Other paper", "best_oa_location": {"pdf_url": "https://oa/other.pdf"}},
                                           {"title": "Prompt Injection Defenses", "best_oa_location": {"pdf_url": "https://oa/x.pdf"}}]}).encode()
        return json.dumps({"best_oa_location": None, "primary_location": {"pdf_url": None}, "open_access": {"oa_url": "https://land"}}).encode()

    assert search.resolve_pdf_url({"arxiv": "2402.06363", "arxiv_version": "2"}, "SECRET", fetch) == (search.ARXIV_PDF + "/2402.06363v2", "arxiv")
    if search.OFFLINE:
        assert search.resolve_pdf_url({"doi": "10.5281/zenodo.5"}, "SECRET", fetch) == ("", "offline")
        return
    assert search.resolve_pdf_url({"doi": "10.5281/zenodo.5"}, "SECRET", fetch)[0] == search.ZENODO_API + "/5/files/p.pdf/content"
    assert search.resolve_pdf_url({"doi": "10.6084/m9.figshare.35040148"}, "SECRET", fetch)[0] == "https://nd/1"
    assert search.resolve_pdf_url({"doi": "10.3390/computers15090570"}, "SECRET", fetch)[0] == "https://land"
    url, note = search.resolve_pdf_url({"title": "Prompt Injection Defenses"}, "SECRET", fetch)
    assert url == "https://oa/x.pdf" and "matched by title" in note
    assert search.resolve_pdf_url({"title": "Nothing like this"}, "SECRET", fetch)[0] == ""
    assert all("SECRET" not in note for _, note in [search.resolve_pdf_url({"doi": "10.1/x"}, "SECRET", fetch)])
    assert sum("api_key=SECRET" in c for c in calls) >= 2        # the key goes to OpenAlex only, and only in the request


def test_resolve_pdf_url_reports_lookup_failures_without_raising():
    def fetch(url):
        raise RuntimeError("boom SECRET")
    if search.OFFLINE:
        return
    url, note = search.resolve_pdf_url({"doi": "10.5281/zenodo.9"}, "SECRET", fetch)
    assert url == "" and note.startswith("lookup failed") and "SECRET" not in note
