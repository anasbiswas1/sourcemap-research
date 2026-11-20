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
    recs, status, url = search.openalex_search('"prompt injection"', "2023-01-01", fetch=fake)
    assert status == "ok" and len(recs) == 2 and "title_and_abstract.search" in url
    recs, status, url = search.dblp_search("prompt injection", fetch=fake)
    assert status == "ok" and len(recs) == 1 and "format=json" in url
