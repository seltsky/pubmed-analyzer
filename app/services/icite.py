import httpx
from typing import Optional

ICITE_API_URL = "https://icite.od.nih.gov/api/pubs"


async def fetch_citation_counts(pmids: list[str]) -> dict[str, int]:
    """iCite API를 사용하여 피인용 횟수를 가져옵니다."""

    if not pmids:
        return {}

    citation_counts = {}

    # iCite API는 한 번에 최대 1000개의 PMID를 처리할 수 있음
    batch_size = 1000

    async with httpx.AsyncClient() as client:
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]

            try:
                response = await client.get(
                    ICITE_API_URL,
                    params={
                        "pmids": ",".join(batch),
                        "format": "json"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                # iCite 응답에서 피인용 횟수 추출
                for paper in data.get("data", []):
                    pmid = str(paper.get("pmid", ""))
                    citation_count = paper.get("citation_count", 0)
                    citation_counts[pmid] = citation_count if citation_count else 0

            except Exception as e:
                print(f"iCite API 오류: {e}")
                # 오류 시 해당 배치의 PMID들은 0으로 설정
                for pmid in batch:
                    if pmid not in citation_counts:
                        citation_counts[pmid] = 0

    return citation_counts


async def get_citation_count(pmid: str) -> Optional[int]:
    """단일 논문의 피인용 횟수를 가져옵니다."""
    counts = await fetch_citation_counts([pmid])
    return counts.get(pmid)
