
"""Title normalisation, version linking and arXiv feed parsing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import corpus  # noqa: E402

FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2510.15476v4</id>
    <updated>2026-10-02T12:00:00Z</updated>
    <published>2025-10-17T09:00:00Z</published>
    <title>SoK: Systematizing LLM Prompt Security:
  Taxonomies, Datasets, and Unified Evaluation</title>
    <author><name>First Author</name></author>
    <author><name>Second Author</name></author>
    <arxiv:comment>v4</arxiv:comment>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2505.00976v2</id>
    <updated>2025-12-01T00:00:00Z</updated>
    <published>2025-05-02T00:00:00Z</published>
    <title>Attack and defense techniques in LLMs</title>
    <arxiv:journal_ref>Neural Networks 2025</arxiv:journal_ref>
    <arxiv:doi>10.1016/j.neunet.2025.108388</arxiv:doi>
    <author><name>Only Author</name></author>
  </entry>
</feed>
"""


def test_normalise_title_ignores_case_and_punctuation():
    assert corpus.normalise_title("SoK: Prompt Hacking of LLMs!") == corpus.normalise_title("sok prompt hacking of llms")


def test_link_versions_links_same_title_and_same_doi_to_one_root():
    rows = [
        {"id": "a", "title": "A Survey on X", "doi": ""},
        {"id": "b", "title": "A survey on X.", "doi": "10.1/x"},
        {"id": "c", "title": "Different", "doi": "10.1/X"},
        {"id": "d", "title": "Unrelated", "doi": ""},
    ]
    out = corpus.link_versions(rows)
    assert out[0]["linked_to"] == ""
    assert out[1]["linked_to"] == "a"
    assert out[2]["linked_to"] == "a"
    assert out[3]["linked_to"] == ""


def test_parse_arxiv_feed_reads_version_dates_and_journal_fields():
    meta = corpus.parse_arxiv_feed(FEED)
    assert set(meta) == {"2510.15476", "2505.00976"}
    hong = meta["2510.15476"]
    assert hong["latest_version"] == 4
    assert hong["published"] == "2025-10-17" and hong["updated"] == "2026-10-02"
    assert hong["title"].startswith("SoK: Systematizing LLM Prompt Security: Taxonomies")
    assert hong["authors"] == ["First Author", "Second Author"]
    liao = meta["2505.00976"]
    assert liao["journal_ref"] == "Neural Networks 2025" and liao["doi"] == "10.1016/j.neunet.2025.108388"


def test_pdf_url_uses_latest_version_when_known():
    assert corpus.pdf_url_for({"arxiv": "2510.15476", "arxiv_latest_version": 4}) == "https://arxiv.org/pdf/2510.15476v4"
    assert corpus.pdf_url_for({"arxiv": "2510.15476", "arxiv_latest_version": ""}) == "https://arxiv.org/pdf/2510.15476"
    assert corpus.pdf_url_for({"arxiv": "", "pdf_url": "https://x/y.pdf"}) == "https://x/y.pdf"
    assert corpus.pdf_url_for({"arxiv": "", "pdf_url": ""}) == ""
