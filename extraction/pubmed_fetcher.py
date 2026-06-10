"""PubMed Entrez API fetcher using History Server for pagination."""

import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

import requests
from tenacity import retry, stop_after_attempt, wait_combine, wait_exponential, wait_random

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
BATCH_SIZE = 100

_BACKOFF = wait_combine(wait_exponential(multiplier=1, min=2, max=30), wait_random(0, 2))


@retry(stop=stop_after_attempt(5), wait=_BACKOFF)
def _get(url: str, params: dict) -> requests.Response:
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp


def esearch(term: str, max_results: int = 500) -> tuple[str, str, int]:
    """Run esearch with usehistory=y. Returns (web_env, query_key, count)."""
    params = {
        "db": "pubmed",
        "term": term,
        "usehistory": "y",
        "retmax": 0,
        "retmode": "xml",
    }
    resp = _get(ESEARCH_URL, params)
    root = ET.fromstring(resp.text)

    web_env = (root.findtext("WebEnv") or "").strip()
    query_key = (root.findtext("QueryKey") or "").strip()
    count_text = root.findtext("Count") or "0"
    count = min(int(count_text), max_results)

    if not web_env or not query_key:
        raise ValueError(f"esearch returned no session: WebEnv={web_env!r} QueryKey={query_key!r}")

    return web_env, query_key, count


def _parse_article(article: ET.Element) -> dict:
    """Flatten a single PubmedArticle XML element into a dict. Missing tags return None."""
    ma = article.find("MedlineCitation")
    if ma is None:
        return {}

    pmid = ma.findtext("PMID")

    art = ma.find("Article")
    if art is None:
        return {"pmid": pmid}

    title = art.findtext("ArticleTitle") or ""

    # Abstract may have multiple AbstractText elements (structured abstracts)
    abstract_parts = []
    abstract_el = art.find("Abstract")
    if abstract_el is not None:
        for part in abstract_el.findall("AbstractText"):
            label = part.get("Label")
            text = (part.text or "").strip()
            if label:
                abstract_parts.append(f"{label}: {text}")
            elif text:
                abstract_parts.append(text)
    abstract = " ".join(abstract_parts)

    # Authors
    authors = []
    author_list = art.find("AuthorList")
    if author_list is not None:
        for author in author_list.findall("Author"):
            last = author.findtext("LastName") or ""
            fore = author.findtext("ForeName") or ""
            name = f"{last} {fore}".strip()
            if name:
                authors.append(name)

    # Journal info
    journal = art.find("Journal")
    journal_title = ""
    pub_year = None
    if journal is not None:
        journal_title = journal.findtext("Title") or ""
        pub_date = journal.find("JournalIssue/PubDate")
        if pub_date is not None:
            pub_year_text = pub_date.findtext("Year")
            if pub_year_text and pub_year_text.isdigit():
                pub_year = int(pub_year_text)

    # MeSH headings
    mesh_terms = []
    mesh_list = ma.find("MeshHeadingList")
    if mesh_list is not None:
        for heading in mesh_list.findall("MeshHeading"):
            descriptor = heading.findtext("DescriptorName")
            if descriptor:
                mesh_terms.append(descriptor)

    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "journal": journal_title,
        "pub_year": pub_year,
        "mesh_terms": mesh_terms,
    }


@retry(stop=stop_after_attempt(5), wait=_BACKOFF)
def _efetch_batch(web_env: str, query_key: str, retstart: int) -> list[dict]:
    """Fetch one batch of RETMAX articles and parse them."""
    params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": web_env,
        "retstart": retstart,
        "retmax": BATCH_SIZE,
        "retmode": "xml",
        "rettype": "abstract",
    }
    resp = _get(EFETCH_URL, params)
    root = ET.fromstring(resp.text)

    records = []
    for article in root.findall("PubmedArticle"):
        parsed = _parse_article(article)
        if parsed.get("pmid") and parsed.get("abstract"):
            records.append(parsed)
    return records


def fetch_pubmed(term: str, max_results: int = 500) -> Iterator[dict]:
    """Yield parsed article dicts for all results matching term."""
    web_env, query_key, count = esearch(term, max_results)

    for retstart in range(0, count, BATCH_SIZE):
        batch = _efetch_batch(web_env, query_key, retstart)
        yield from batch
        # NCBI rate limit: max 3 req/s without API key
        time.sleep(0.4)


def fetch_and_save(term: str, output_path: str, max_results: int = 500) -> int:
    """Fetch PubMed abstracts for term and write to a JSONL file. Returns record count."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with out.open("w", encoding="utf-8") as f:
        for record in fetch_pubmed(term, max_results):
            f.write(json.dumps(record) + "\n")
            count += 1

    return count
