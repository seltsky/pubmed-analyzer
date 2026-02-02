import httpx
import xml.etree.ElementTree as ET
from typing import Optional
from app.config import PUBMED_ESEARCH_URL, PUBMED_EFETCH_URL, NCBI_API_KEY
from app.models.schemas import Paper


async def search_pubmed(
    query: str,
    author: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "relevance",
) -> tuple[int, list[str]]:
    """PubMed에서 논문을 검색하고 PMID 목록을 반환합니다."""

    # 검색 쿼리 구성
    search_term = query
    if author:
        search_term += f" AND {author}[Author]"

    # 날짜 범위 추가
    if start_date and end_date:
        search_term += f" AND {start_date}:{end_date}[dp]"
    elif start_date:
        search_term += f" AND {start_date}:3000[dp]"
    elif end_date:
        search_term += f" AND 1900:{end_date}[dp]"

    # PubMed 정렬 옵션 매핑
    pubmed_sort = "relevance"
    if sort_by == "date":
        pubmed_sort = "pub_date"  # 최신순
    # citations는 PubMed에서 지원하지 않으므로 클라이언트 측 정렬

    params = {
        "db": "pubmed",
        "term": search_term,
        "retmax": page_size,
        "retstart": (page - 1) * page_size,
        "retmode": "json",
        "sort": pubmed_sort,
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    async with httpx.AsyncClient() as client:
        response = await client.get(PUBMED_ESEARCH_URL, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

    result = data.get("esearchresult", {})
    total = int(result.get("count", 0))
    pmids = result.get("idlist", [])

    return total, pmids


async def fetch_paper_details(pmids: list[str]) -> list[Paper]:
    """PMID 목록으로 논문 상세 정보를 가져옵니다."""

    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    async with httpx.AsyncClient() as client:
        response = await client.get(PUBMED_EFETCH_URL, params=params, timeout=30.0)
        response.raise_for_status()
        xml_data = response.text

    return parse_pubmed_xml(xml_data)


def parse_pubmed_xml(xml_data: str) -> list[Paper]:
    """PubMed XML 응답을 파싱하여 Paper 객체 목록을 반환합니다."""

    papers = []
    root = ET.fromstring(xml_data)

    for article in root.findall(".//PubmedArticle"):
        try:
            # PMID
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            # 제목
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None and title_elem.text else ""

            # 저자 목록
            authors = []
            for author in article.findall(".//Author"):
                lastname = author.find("LastName")
                forename = author.find("ForeName")
                if lastname is not None and lastname.text:
                    name = lastname.text
                    if forename is not None and forename.text:
                        name += f" {forename.text}"
                    authors.append(name)

            # 초록
            abstract_parts = []
            for abstract_text in article.findall(".//AbstractText"):
                if abstract_text.text:
                    label = abstract_text.get("Label", "")
                    if label:
                        abstract_parts.append(f"{label}: {abstract_text.text}")
                    else:
                        abstract_parts.append(abstract_text.text)
            abstract = " ".join(abstract_parts)

            # 출판일
            pub_date = ""
            pub_date_elem = article.find(".//PubDate")
            if pub_date_elem is not None:
                year = pub_date_elem.find("Year")
                month = pub_date_elem.find("Month")
                day = pub_date_elem.find("Day")

                if year is not None and year.text:
                    pub_date = year.text
                    if month is not None and month.text:
                        pub_date += f"-{month.text}"
                        if day is not None and day.text:
                            pub_date += f"-{day.text}"

            # 저널명
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None and journal_elem.text else ""

            # 키워드
            keywords = []
            for keyword in article.findall(".//Keyword"):
                if keyword.text:
                    keywords.append(keyword.text)

            # MeSH 용어도 키워드에 추가
            for mesh in article.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    keywords.append(mesh.text)

            # PMC ID 추출 (무료 전문 PDF 제공 여부)
            pmc_id = None
            for article_id in article.findall(".//ArticleId"):
                if article_id.get("IdType") == "pmc":
                    pmc_id = article_id.text
                    break

            papers.append(Paper(
                pmid=pmid,
                title=title,
                authors=authors,
                abstract=abstract,
                pub_date=pub_date,
                journal=journal,
                keywords=keywords,
                pmc_id=pmc_id,
            ))
        except Exception as e:
            print(f"Error parsing article: {e}")
            continue

    return papers


async def get_paper_by_pmid(pmid: str) -> Optional[Paper]:
    """단일 논문의 상세 정보를 가져옵니다."""
    papers = await fetch_paper_details([pmid])
    return papers[0] if papers else None
